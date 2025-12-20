"""Pytest fixtures for E2E tests.

These fixtures manage the Docker test environment and provide
HTTP clients for interacting with Home Assistant and the mock server.
"""

from __future__ import annotations

import asyncio
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, AsyncIterator

import aiohttp
import pytest
import pytest_asyncio

# Path to the test environment directory
HA_TEST_ENV_DIR = Path(__file__).parent.parent / "ha_test_env"

# Configuration
HA_URL = "http://localhost:8123"
MOCK_HOST = "mock_slxd"  # Docker network hostname
MOCK_PORT = 2202
INTEGRATION_DOMAIN = "shure_slxd"


@dataclass
class HAClient:
    """HTTP client for Home Assistant REST API."""

    base_url: str
    _session: aiohttp.ClientSession | None = None

    async def __aenter__(self) -> "HAClient":
        """Enter async context."""
        self._session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Exit async context."""
        if self._session:
            await self._session.close()

    async def get(self, path: str) -> dict[str, Any] | list[Any]:
        """GET request to HA API."""
        if not self._session:
            raise RuntimeError("Client not initialized")
        async with self._session.get(f"{self.base_url}{path}") as resp:
            resp.raise_for_status()
            return await resp.json()

    async def post(self, path: str, json: dict[str, Any] | None = None) -> dict[str, Any]:
        """POST request to HA API."""
        if not self._session:
            raise RuntimeError("Client not initialized")
        async with self._session.post(f"{self.base_url}{path}", json=json) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def delete(self, path: str) -> dict[str, Any] | None:
        """DELETE request to HA API."""
        if not self._session:
            raise RuntimeError("Client not initialized")
        async with self._session.delete(f"{self.base_url}{path}") as resp:
            if resp.status == 204:
                return None
            resp.raise_for_status()
            return await resp.json()

    async def wait_for_ready(self, timeout: float = 120) -> bool:
        """Wait for Home Assistant to be ready."""
        start = time.time()
        while time.time() - start < timeout:
            try:
                await self.get("/api/")
                return True
            except (aiohttp.ClientError, asyncio.TimeoutError):
                await asyncio.sleep(2)
        return False

    async def get_states(self) -> list[dict[str, Any]]:
        """Get all entity states."""
        result = await self.get("/api/states")
        if isinstance(result, list):
            return result
        return []

    async def get_state(self, entity_id: str) -> dict[str, Any] | None:
        """Get state of a specific entity."""
        try:
            result = await self.get(f"/api/states/{entity_id}")
            if isinstance(result, dict):
                return result
        except aiohttp.ClientResponseError as e:
            if e.status == 404:
                return None
            raise
        return None

    async def get_config_entries(self) -> list[dict[str, Any]]:
        """Get all config entries."""
        result = await self.get("/api/config/config_entries/entry")
        if isinstance(result, list):
            return result
        return []

    async def start_config_flow(self, handler: str) -> dict[str, Any]:
        """Start a config flow."""
        return await self.post("/api/config/config_entries/flow", json={"handler": handler})

    async def submit_config_flow(self, flow_id: str, data: dict[str, Any]) -> dict[str, Any]:
        """Submit data to a config flow step."""
        return await self.post(f"/api/config/config_entries/flow/{flow_id}", json=data)

    async def delete_config_entry(self, entry_id: str) -> None:
        """Delete a config entry."""
        await self.delete(f"/api/config/config_entries/entry/{entry_id}")

    async def call_service(
        self, domain: str, service: str, data: dict[str, Any] | None = None
    ) -> None:
        """Call a Home Assistant service."""
        await self.post(f"/api/services/{domain}/{service}", json=data or {})


def _run_manage_command(command: str, check: bool = True) -> subprocess.CompletedProcess:
    """Run a manage.sh command."""
    result = subprocess.run(
        ["./manage.sh", command],
        cwd=HA_TEST_ENV_DIR,
        capture_output=True,
        text=True,
    )
    if check and result.returncode != 0:
        print(f"Command failed: {command}")
        print(f"stdout: {result.stdout}")
        print(f"stderr: {result.stderr}")
        result.check_returncode()
    return result


@pytest.fixture(scope="session")
def docker_compose_file() -> Path:
    """Path to docker-compose file."""
    return HA_TEST_ENV_DIR / "docker-compose.yml"


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for session-scoped async fixtures."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def ha_environment(docker_compose_file: Path) -> AsyncIterator[str]:
    """Start the Docker test environment.

    This fixture starts Home Assistant and the mock SLX-D server,
    waits for them to be ready, and tears them down after all tests.
    """
    # Check if Docker is running
    result = subprocess.run(["docker", "info"], capture_output=True)
    if result.returncode != 0:
        pytest.skip("Docker is not running")

    # Start the environment
    print("\nStarting Docker test environment...")
    _run_manage_command("start")

    # Wait for HA to be ready
    async with HAClient(HA_URL) as client:
        if not await client.wait_for_ready(timeout=120):
            _run_manage_command("stop", check=False)
            pytest.fail("Home Assistant did not start in time")

    print("Docker test environment is ready")
    yield HA_URL

    # Cleanup
    print("\nStopping Docker test environment...")
    _run_manage_command("stop", check=False)


@pytest_asyncio.fixture
async def ha_client(ha_environment: str) -> AsyncIterator[HAClient]:
    """Create an HTTP client for the Home Assistant API."""
    async with HAClient(ha_environment) as client:
        yield client


@pytest_asyncio.fixture
async def clean_integration(ha_client: HAClient) -> AsyncIterator[None]:
    """Ensure integration is not configured before and after test."""
    # Remove any existing configuration
    entries = await ha_client.get_config_entries()
    for entry in entries:
        if entry.get("domain") == INTEGRATION_DOMAIN:
            await ha_client.delete_config_entry(entry["entry_id"])
            await asyncio.sleep(2)

    yield

    # Cleanup after test
    entries = await ha_client.get_config_entries()
    for entry in entries:
        if entry.get("domain") == INTEGRATION_DOMAIN:
            await ha_client.delete_config_entry(entry["entry_id"])


@pytest_asyncio.fixture
async def configured_integration(
    ha_client: HAClient, clean_integration: None
) -> AsyncIterator[dict[str, Any]]:
    """Set up the integration via config flow and return the entry."""
    # Start config flow
    flow = await ha_client.start_config_flow(INTEGRATION_DOMAIN)
    flow_id = flow.get("flow_id")
    assert flow_id, f"Failed to start config flow: {flow}"

    # Submit host/port configuration
    result = await ha_client.submit_config_flow(
        flow_id, {"host": MOCK_HOST, "port": MOCK_PORT}
    )

    assert result.get("type") == "create_entry", f"Config flow failed: {result}"

    # Wait for entities to be created
    await asyncio.sleep(5)

    yield result

    # Cleanup is handled by clean_integration fixture


@pytest.fixture
def mock_host() -> str:
    """Return the mock server hostname."""
    return MOCK_HOST


@pytest.fixture
def mock_port() -> int:
    """Return the mock server port."""
    return MOCK_PORT
