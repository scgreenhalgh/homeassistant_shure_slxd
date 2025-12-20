"""Integration tests for error handling with mock server."""

from __future__ import annotations

import asyncio

import pytest

from pyslxd.client import SlxdClient
from pyslxd.exceptions import SlxdConnectionError, SlxdProtocolError, SlxdTimeoutError
from pyslxd.mock.server import MockSlxdServer


class TestConnectionErrors:
    """Tests for connection error handling."""

    @pytest.mark.asyncio
    async def test_connect_to_nonexistent_host(self) -> None:
        """Test connection to non-existent host raises error."""
        client = SlxdClient()

        with pytest.raises(SlxdConnectionError):
            await client.connect("192.0.2.1", 2202)  # TEST-NET, should not exist

    @pytest.mark.asyncio
    async def test_connect_to_closed_port(self) -> None:
        """Test connection to closed port raises error."""
        client = SlxdClient()

        with pytest.raises(SlxdConnectionError):
            # High port unlikely to be in use
            await client.connect("127.0.0.1", 59997)

    @pytest.mark.asyncio
    async def test_send_command_when_not_connected(self) -> None:
        """Test sending command without connection raises error."""
        client = SlxdClient()

        with pytest.raises(SlxdConnectionError):
            await client.send_command("< GET MODEL >")

    @pytest.mark.asyncio
    async def test_get_method_when_not_connected(self) -> None:
        """Test calling get method without connection raises error."""
        client = SlxdClient()

        with pytest.raises(SlxdConnectionError):
            await client.get_model()


class TestCommandTimeout:
    """Tests for command timeout handling."""

    @pytest.mark.asyncio
    async def test_command_timeout_with_delay(self) -> None:
        """Test command times out with delayed response."""
        async with MockSlxdServer() as server:
            # Set 2 second delay
            server.set_response_delay(2.0)

            client = SlxdClient()
            await client.connect(server.host, server.port)

            try:
                # Use 0.5 second timeout, should time out
                with pytest.raises(SlxdTimeoutError):
                    await client.send_command("< GET MODEL >", timeout=0.5)
            finally:
                await client.disconnect()

    @pytest.mark.asyncio
    async def test_command_succeeds_within_timeout(self) -> None:
        """Test command succeeds when within timeout."""
        async with MockSlxdServer() as server:
            # Set small delay
            server.set_response_delay(0.1)

            client = SlxdClient()
            await client.connect(server.host, server.port)

            try:
                # Use 2 second timeout, should succeed
                response = await client.send_command("< GET MODEL >", timeout=2.0)
                assert response.property_name == "MODEL"
            finally:
                await client.disconnect()


class TestServerDisconnect:
    """Tests for handling server disconnection."""

    @pytest.mark.asyncio
    async def test_server_stops_during_connection(self) -> None:
        """Test handling when server stops while connected."""
        server = MockSlxdServer()
        await server.start()

        client = SlxdClient()
        await client.connect(server.host, server.port)

        # Verify connection works
        model = await client.get_model()
        assert model == "SLXD4D"

        # Stop server
        await server.stop()

        # Next command should fail (could be connection, timeout, or protocol error)
        with pytest.raises((SlxdConnectionError, SlxdTimeoutError, SlxdProtocolError, ConnectionError)):
            await client.get_model()

        await client.disconnect()


class TestGracefulRecovery:
    """Tests for graceful error recovery."""

    @pytest.mark.asyncio
    async def test_disconnect_does_not_raise(self) -> None:
        """Test that disconnect doesn't raise even if already disconnected."""
        client = SlxdClient()

        # Disconnect without ever connecting should not raise
        await client.disconnect()

    @pytest.mark.asyncio
    async def test_double_disconnect(
        self, mock_server: MockSlxdServer
    ) -> None:
        """Test that double disconnect doesn't raise."""
        client = SlxdClient()
        await client.connect(mock_server.host, mock_server.port)

        await client.disconnect()
        await client.disconnect()  # Should not raise


class TestInputValidation:
    """Tests for input validation error handling."""

    @pytest.mark.asyncio
    async def test_invalid_channel_raises_immediately(
        self, connected_client: SlxdClient
    ) -> None:
        """Test that invalid channel raises before sending command."""
        with pytest.raises(ValueError):
            await connected_client.get_audio_gain(0)

        with pytest.raises(ValueError):
            await connected_client.get_audio_gain(5)

    @pytest.mark.asyncio
    async def test_invalid_gain_raises_immediately(
        self, connected_client: SlxdClient
    ) -> None:
        """Test that invalid gain raises before sending command."""
        with pytest.raises(ValueError):
            await connected_client.set_audio_gain(1, 100)

        with pytest.raises(ValueError):
            await connected_client.set_audio_gain(1, -50)

    @pytest.mark.asyncio
    async def test_invalid_antenna_raises_immediately(
        self, connected_client: SlxdClient
    ) -> None:
        """Test that invalid antenna raises before sending command."""
        with pytest.raises(ValueError):
            await connected_client.get_rssi(1, antenna=0)

        with pytest.raises(ValueError):
            await connected_client.get_rssi(1, antenna=3)

    @pytest.mark.asyncio
    async def test_invalid_audio_level_raises_immediately(
        self, connected_client: SlxdClient
    ) -> None:
        """Test that invalid audio output level raises."""
        with pytest.raises(ValueError):
            await connected_client.set_audio_out_level(1, "INVALID")


class TestEdgeCases:
    """Tests for edge case handling."""

    @pytest.mark.asyncio
    async def test_empty_channel_name(
        self, mock_server: MockSlxdServer, connected_client: SlxdClient
    ) -> None:
        """Test handling of empty channel name."""
        # Set empty name in mock
        mock_server.device.channels[0].name = ""

        name = await connected_client.get_channel_name(1)
        assert name == ""

    @pytest.mark.asyncio
    async def test_rapid_commands(
        self, mock_server: MockSlxdServer, connected_client: SlxdClient
    ) -> None:
        """Test sending many commands rapidly in sequence.

        Note: The client is not designed for concurrent commands on a single
        connection. Commands must be sent sequentially.
        """
        # Send 20 commands in quick succession (sequentially)
        results = []
        for _ in range(20):
            result = await connected_client.get_model()
            results.append(result)

        assert all(r == "SLXD4D" for r in results)

    @pytest.mark.asyncio
    async def test_interleaved_read_write(
        self, mock_server: MockSlxdServer, connected_client: SlxdClient
    ) -> None:
        """Test interleaved read and write operations."""
        for i in range(-10, 20, 5):
            await connected_client.set_audio_gain(1, i)
            gain = await connected_client.get_audio_gain(1)
            assert gain == i
