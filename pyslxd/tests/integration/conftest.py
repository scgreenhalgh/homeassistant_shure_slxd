"""Pytest fixtures for integration tests.

These fixtures provide mock servers and connected clients for testing
real TCP communication.
"""

from __future__ import annotations

import pytest

from pyslxd.client import SlxdClient
from pyslxd.mock.server import MockSlxdServer
from pyslxd.mock.state import MockDevice, MockTransmitter


@pytest.fixture
async def mock_server():
    """Create and start a mock SLX-D server (SLXD4D)."""
    async with MockSlxdServer() as server:
        yield server


@pytest.fixture
async def mock_server_slxd4():
    """Create a mock server configured as single-channel SLXD4."""
    device = MockDevice(model="SLXD4", device_id="SLXD4001")
    async with MockSlxdServer(device=device) as server:
        yield server


@pytest.fixture
async def mock_server_slxd4q():
    """Create a mock server configured as quad-channel SLXD4Q+."""
    device = MockDevice(model="SLXD4Q+", device_id="SLXD4Q01")
    async with MockSlxdServer(device=device) as server:
        yield server


@pytest.fixture
async def mock_server_with_transmitter():
    """Create a mock server with a connected transmitter on channel 1."""
    device = MockDevice()
    device.channels[0].transmitter = MockTransmitter(
        model="SLXD2",
        connected=True,
        battery_bars=4,
        battery_minutes=240,
    )
    device.channels[0].rssi_a1_raw = 80
    device.channels[0].rssi_a2_raw = 75
    async with MockSlxdServer(device=device) as server:
        yield server


@pytest.fixture
async def connected_client(mock_server: MockSlxdServer):
    """Create a client connected to the mock server."""
    client = SlxdClient()
    await client.connect(mock_server.host, mock_server.port)
    yield client
    await client.disconnect()


@pytest.fixture
async def connected_client_slxd4(mock_server_slxd4: MockSlxdServer):
    """Create a client connected to SLXD4 mock server."""
    client = SlxdClient()
    await client.connect(mock_server_slxd4.host, mock_server_slxd4.port)
    yield client
    await client.disconnect()


@pytest.fixture
async def connected_client_slxd4q(mock_server_slxd4q: MockSlxdServer):
    """Create a client connected to SLXD4Q+ mock server."""
    client = SlxdClient()
    await client.connect(mock_server_slxd4q.host, mock_server_slxd4q.port)
    yield client
    await client.disconnect()


@pytest.fixture
async def connected_client_with_transmitter(
    mock_server_with_transmitter: MockSlxdServer,
):
    """Create a client connected to mock server with transmitter."""
    client = SlxdClient()
    await client.connect(
        mock_server_with_transmitter.host, mock_server_with_transmitter.port
    )
    yield client
    await client.disconnect()
