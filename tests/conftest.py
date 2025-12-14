"""Fixtures for Shure SLX-D integration tests."""

from __future__ import annotations

import sys
from collections.abc import Generator
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add custom_components to path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

# Import fixtures from pytest-homeassistant-custom-component
pytest_plugins = ["pytest_homeassistant_custom_component"]


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations for all tests."""
    yield


@pytest.fixture
def mock_slxd_client() -> Generator[MagicMock, None, None]:
    """Create a mock SlxdClient."""
    with patch(
        "custom_components.shure_slxd.config_flow.SlxdClient"
    ) as mock_client_class:
        mock_client = MagicMock()
        mock_client.connect = AsyncMock()
        mock_client.disconnect = AsyncMock()
        mock_client.get_model = AsyncMock(return_value="SLXD4D")
        mock_client.get_device_id = AsyncMock(return_value="SLXD4D01")
        mock_client.get_firmware_version = AsyncMock(return_value="2.0.15.2")
        mock_client_class.return_value = mock_client
        yield mock_client


@pytest.fixture
def mock_slxd_client_cannot_connect() -> Generator[MagicMock, None, None]:
    """Create a mock SlxdClient that fails to connect."""
    with patch(
        "custom_components.shure_slxd.config_flow.SlxdClient"
    ) as mock_client_class:
        from pyslxd.exceptions import SlxdConnectionError

        mock_client = MagicMock()
        mock_client.connect = AsyncMock(
            side_effect=SlxdConnectionError("Connection refused")
        )
        mock_client.disconnect = AsyncMock()
        mock_client_class.return_value = mock_client
        yield mock_client
