"""Integration tests for client connection with mock server."""

from __future__ import annotations

import asyncio

import pytest

from pyslxd.client import SlxdClient
from pyslxd.exceptions import SlxdConnectionError
from pyslxd.mock.server import MockSlxdServer


class TestClientConnectionIntegration:
    """Integration tests for client connection with real TCP."""

    @pytest.mark.asyncio
    async def test_connect_to_mock_server(self, mock_server: MockSlxdServer) -> None:
        """Test basic connection to mock server."""
        client = SlxdClient()
        await client.connect(mock_server.host, mock_server.port)

        assert client.connected is True

        await client.disconnect()
        assert client.connected is False

    @pytest.mark.asyncio
    async def test_context_manager_with_mock_server(
        self, mock_server: MockSlxdServer
    ) -> None:
        """Test async context manager with real TCP connection."""
        async with SlxdClient(mock_server.host, mock_server.port) as client:
            assert client.connected is True
            model = await client.get_model()
            assert model == "SLXD4D"

        # After context exit, should be disconnected
        assert client.connected is False

    @pytest.mark.asyncio
    async def test_connect_with_host_in_constructor(
        self, mock_server: MockSlxdServer
    ) -> None:
        """Test connection with host provided in constructor."""
        client = SlxdClient(mock_server.host, mock_server.port)
        await client.connect()

        assert client.connected is True

        await client.disconnect()

    @pytest.mark.asyncio
    async def test_connect_override_constructor_host(
        self, mock_server: MockSlxdServer
    ) -> None:
        """Test that connect() can override constructor host."""
        client = SlxdClient("invalid.host", 9999)
        await client.connect(mock_server.host, mock_server.port)

        assert client.connected is True

        await client.disconnect()

    @pytest.mark.asyncio
    async def test_reconnect_after_disconnect(
        self, mock_server: MockSlxdServer
    ) -> None:
        """Test reconnecting after clean disconnect."""
        client = SlxdClient()

        # First connection
        await client.connect(mock_server.host, mock_server.port)
        model1 = await client.get_model()
        await client.disconnect()

        # Reconnect
        await client.connect(mock_server.host, mock_server.port)
        model2 = await client.get_model()
        await client.disconnect()

        assert model1 == model2 == "SLXD4D"

    @pytest.mark.asyncio
    async def test_reconnect_after_server_restart(self) -> None:
        """Test reconnecting after server restarts."""
        server = MockSlxdServer()
        await server.start()

        client = SlxdClient()
        await client.connect(server.host, server.port)
        model1 = await client.get_model()
        await client.disconnect()

        # Stop and restart server
        port = server.port  # Save port
        await server.stop()

        # Start new server on same port
        server2 = MockSlxdServer(port=port)
        await server2.start()

        # Reconnect
        await client.connect(server2.host, server2.port)
        model2 = await client.get_model()
        await client.disconnect()

        await server2.stop()

        assert model1 == model2

    @pytest.mark.asyncio
    async def test_connect_refused_raises_error(self) -> None:
        """Test connection refused raises SlxdConnectionError."""
        client = SlxdClient()

        with pytest.raises(SlxdConnectionError):
            # Port 59998 is unlikely to have anything listening
            await client.connect("127.0.0.1", 59998)

    @pytest.mark.asyncio
    async def test_multiple_clients_same_server(
        self, mock_server: MockSlxdServer
    ) -> None:
        """Test multiple clients connecting to same server."""
        client1 = SlxdClient()
        client2 = SlxdClient()

        await client1.connect(mock_server.host, mock_server.port)
        await client2.connect(mock_server.host, mock_server.port)

        # Both should work independently
        model1 = await client1.get_model()
        model2 = await client2.get_model()

        assert model1 == model2 == "SLXD4D"

        await client1.disconnect()
        await client2.disconnect()

    @pytest.mark.asyncio
    async def test_disconnect_does_not_affect_other_clients(
        self, mock_server: MockSlxdServer
    ) -> None:
        """Test disconnecting one client doesn't affect others."""
        client1 = SlxdClient()
        client2 = SlxdClient()

        await client1.connect(mock_server.host, mock_server.port)
        await client2.connect(mock_server.host, mock_server.port)

        # Disconnect client1
        await client1.disconnect()

        # Client2 should still work
        model = await client2.get_model()
        assert model == "SLXD4D"

        await client2.disconnect()
