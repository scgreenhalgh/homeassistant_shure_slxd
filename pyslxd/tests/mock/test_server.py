"""Tests for mock SLX-D TCP server."""

from __future__ import annotations

import asyncio

import pytest

from pyslxd.mock.server import MockSlxdServer
from pyslxd.mock.state import MockDevice, MockTransmitter


class TestServerLifecycle:
    """Tests for server start/stop lifecycle."""

    @pytest.mark.asyncio
    async def test_start_and_stop(self) -> None:
        """Test server starts and stops correctly."""
        server = MockSlxdServer()
        await server.start()

        assert server.is_running is True
        assert server.port > 0

        await server.stop()
        assert server.is_running is False

    @pytest.mark.asyncio
    async def test_context_manager(self) -> None:
        """Test server as async context manager."""
        async with MockSlxdServer() as server:
            assert server.is_running is True
            assert server.port > 0

        assert server.is_running is False

    @pytest.mark.asyncio
    async def test_auto_assign_port(self) -> None:
        """Test server auto-assigns available port when port=0."""
        async with MockSlxdServer(port=0) as server:
            assert server.port > 0
            assert server.port != 0

    @pytest.mark.asyncio
    async def test_custom_port(self) -> None:
        """Test server uses specified port."""
        # Use a high port that's likely available
        async with MockSlxdServer(port=59999) as server:
            assert server.port == 59999


class TestServerConnection:
    """Tests for client connection handling."""

    @pytest.mark.asyncio
    async def test_accepts_connection(self) -> None:
        """Test server accepts TCP connections."""
        async with MockSlxdServer() as server:
            reader, writer = await asyncio.open_connection(server.host, server.port)

            assert reader is not None
            assert writer is not None

            writer.close()
            await writer.wait_closed()

    @pytest.mark.asyncio
    async def test_responds_to_command(self) -> None:
        """Test server responds to commands."""
        async with MockSlxdServer() as server:
            reader, writer = await asyncio.open_connection(server.host, server.port)

            writer.write(b"< GET MODEL >\r\n")
            await writer.drain()

            response = await asyncio.wait_for(reader.readline(), timeout=5.0)
            assert b"REP MODEL" in response
            assert b"SLXD4D" in response

            writer.close()
            await writer.wait_closed()

    @pytest.mark.asyncio
    async def test_multiple_clients(self) -> None:
        """Test server handles multiple clients."""
        async with MockSlxdServer() as server:
            # Connect two clients
            reader1, writer1 = await asyncio.open_connection(server.host, server.port)
            reader2, writer2 = await asyncio.open_connection(server.host, server.port)

            # Both should work
            writer1.write(b"< GET MODEL >\r\n")
            await writer1.drain()
            response1 = await asyncio.wait_for(reader1.readline(), timeout=5.0)
            assert b"SLXD4D" in response1

            writer2.write(b"< GET DEVICE_ID >\r\n")
            await writer2.drain()
            response2 = await asyncio.wait_for(reader2.readline(), timeout=5.0)
            assert b"2C2A3F01" in response2

            writer1.close()
            writer2.close()
            await writer1.wait_closed()
            await writer2.wait_closed()

    @pytest.mark.asyncio
    async def test_handles_disconnect(self) -> None:
        """Test server handles client disconnect gracefully."""
        async with MockSlxdServer() as server:
            reader, writer = await asyncio.open_connection(server.host, server.port)

            # Send a command
            writer.write(b"< GET MODEL >\r\n")
            await writer.drain()
            await reader.readline()

            # Disconnect
            writer.close()
            await writer.wait_closed()

            # Server should still be running
            assert server.is_running is True

            # Should accept new connections
            reader2, writer2 = await asyncio.open_connection(server.host, server.port)
            writer2.close()
            await writer2.wait_closed()


class TestServerDeviceState:
    """Tests for server device state."""

    @pytest.mark.asyncio
    async def test_custom_device(self) -> None:
        """Test server with custom device state."""
        device = MockDevice(
            model="SLXD4Q+",
            device_id="CUSTOM01",
        )
        async with MockSlxdServer(device=device) as server:
            reader, writer = await asyncio.open_connection(server.host, server.port)

            writer.write(b"< GET MODEL >\r\n")
            await writer.drain()
            response = await reader.readline()
            assert b"SLXD4Q+" in response

            writer.write(b"< GET DEVICE_ID >\r\n")
            await writer.drain()
            response = await reader.readline()
            assert b"CUSTOM01" in response

            writer.close()
            await writer.wait_closed()

    @pytest.mark.asyncio
    async def test_device_property_access(self) -> None:
        """Test accessing device state from server."""
        async with MockSlxdServer() as server:
            assert server.device.model == "SLXD4D"
            assert len(server.device.channels) == 2


class TestServerSimulation:
    """Tests for simulation methods."""

    @pytest.mark.asyncio
    async def test_connect_transmitter(self) -> None:
        """Test connecting transmitter simulation."""
        async with MockSlxdServer() as server:
            server.connect_transmitter(1, model="SLXD2", battery_bars=4)

            reader, writer = await asyncio.open_connection(server.host, server.port)

            writer.write(b"< GET 1 TX_MODEL >\r\n")
            await writer.drain()
            response = await reader.readline()
            assert b"SLXD2" in response

            writer.write(b"< GET 1 TX_BATT_BARS >\r\n")
            await writer.drain()
            response = await reader.readline()
            assert b"004" in response

            writer.close()
            await writer.wait_closed()

    @pytest.mark.asyncio
    async def test_disconnect_transmitter(self) -> None:
        """Test disconnecting transmitter simulation."""
        async with MockSlxdServer() as server:
            # First connect
            server.connect_transmitter(1)

            # Then disconnect
            server.disconnect_transmitter(1)

            reader, writer = await asyncio.open_connection(server.host, server.port)

            writer.write(b"< GET 1 TX_MODEL >\r\n")
            await writer.drain()
            response = await reader.readline()
            assert b"UNKNOWN" in response

            writer.close()
            await writer.wait_closed()

    @pytest.mark.asyncio
    async def test_set_battery_level(self) -> None:
        """Test setting battery level simulation."""
        async with MockSlxdServer() as server:
            server.connect_transmitter(1)
            server.set_battery_level(1, bars=2, minutes=120)

            reader, writer = await asyncio.open_connection(server.host, server.port)

            writer.write(b"< GET 1 TX_BATT_BARS >\r\n")
            await writer.drain()
            response = await reader.readline()
            assert b"002" in response

            writer.write(b"< GET 1 TX_BATT_MINS >\r\n")
            await writer.drain()
            response = await reader.readline()
            assert b"00120" in response

            writer.close()
            await writer.wait_closed()

    @pytest.mark.asyncio
    async def test_set_audio_level(self) -> None:
        """Test setting audio level simulation."""
        async with MockSlxdServer() as server:
            server.set_audio_level(1, peak=100, rms=90)

            reader, writer = await asyncio.open_connection(server.host, server.port)

            writer.write(b"< GET 1 AUDIO_LEVEL_PEAK >\r\n")
            await writer.drain()
            response = await reader.readline()
            assert b"100" in response

            writer.write(b"< GET 1 AUDIO_LEVEL_RMS >\r\n")
            await writer.drain()
            response = await reader.readline()
            assert b"090" in response

            writer.close()
            await writer.wait_closed()

    @pytest.mark.asyncio
    async def test_set_rssi(self) -> None:
        """Test setting RSSI simulation."""
        async with MockSlxdServer() as server:
            server.set_rssi(1, antenna1=80, antenna2=75)

            reader, writer = await asyncio.open_connection(server.host, server.port)

            writer.write(b"< GET 1 RSSI 1 >\r\n")
            await writer.drain()
            response = await reader.readline()
            assert b"080" in response

            writer.write(b"< GET 1 RSSI 2 >\r\n")
            await writer.drain()
            response = await reader.readline()
            assert b"075" in response

            writer.close()
            await writer.wait_closed()


class TestServerResponseDelay:
    """Tests for response delay functionality."""

    @pytest.mark.asyncio
    async def test_response_delay(self) -> None:
        """Test artificial response delay."""
        async with MockSlxdServer() as server:
            server.set_response_delay(0.1)  # 100ms delay

            reader, writer = await asyncio.open_connection(server.host, server.port)

            import time

            start = time.monotonic()
            writer.write(b"< GET MODEL >\r\n")
            await writer.drain()
            await reader.readline()
            elapsed = time.monotonic() - start

            assert elapsed >= 0.1

            writer.close()
            await writer.wait_closed()


class TestServerCallbacks:
    """Tests for server callbacks."""

    @pytest.mark.asyncio
    async def test_connection_callback(self) -> None:
        """Test connection callback is called."""
        connections = []

        async with MockSlxdServer() as server:
            server.on_connection(lambda w: connections.append(w))

            reader, writer = await asyncio.open_connection(server.host, server.port)

            # Give callback time to fire
            await asyncio.sleep(0.1)
            assert len(connections) == 1

            writer.close()
            await writer.wait_closed()

    @pytest.mark.asyncio
    async def test_command_callback(self) -> None:
        """Test command callback is called."""
        commands = []

        async with MockSlxdServer() as server:
            server.on_command(lambda cmd, resp: commands.append((cmd, resp)))

            reader, writer = await asyncio.open_connection(server.host, server.port)

            writer.write(b"< GET MODEL >\r\n")
            await writer.drain()
            await reader.readline()

            # Give callback time to fire
            await asyncio.sleep(0.1)
            assert len(commands) == 1
            assert "GET MODEL" in commands[0][0]
            assert "REP MODEL" in commands[0][1]

            writer.close()
            await writer.wait_closed()


class TestServerBroadcast:
    """Tests for broadcast functionality."""

    @pytest.mark.asyncio
    async def test_broadcast_rep(self) -> None:
        """Test broadcasting REP message to all clients."""
        async with MockSlxdServer() as server:
            reader1, writer1 = await asyncio.open_connection(server.host, server.port)
            reader2, writer2 = await asyncio.open_connection(server.host, server.port)

            # Give connections time to register
            await asyncio.sleep(0.1)

            # Broadcast message
            await server.broadcast_rep("< REP 1 TX_BATT_BARS 003 >")

            # Both clients should receive it
            response1 = await asyncio.wait_for(reader1.readline(), timeout=5.0)
            response2 = await asyncio.wait_for(reader2.readline(), timeout=5.0)

            assert b"TX_BATT_BARS 003" in response1
            assert b"TX_BATT_BARS 003" in response2

            writer1.close()
            writer2.close()
            await writer1.wait_closed()
            await writer2.wait_closed()


class TestServerStateChange:
    """Tests for state changes through commands."""

    @pytest.mark.asyncio
    async def test_set_audio_gain_changes_state(self) -> None:
        """Test SET AUDIO_GAIN updates device state."""
        async with MockSlxdServer() as server:
            reader, writer = await asyncio.open_connection(server.host, server.port)

            # Set new gain
            writer.write(b"< SET 1 AUDIO_GAIN 040 >\r\n")
            await writer.drain()
            await reader.readline()

            # Verify state changed
            assert server.device.channels[0].audio_gain_raw == 40

            # Read back
            writer.write(b"< GET 1 AUDIO_GAIN >\r\n")
            await writer.drain()
            response = await reader.readline()
            assert b"040" in response

            writer.close()
            await writer.wait_closed()

    @pytest.mark.asyncio
    async def test_set_audio_out_lvl_changes_state(self) -> None:
        """Test SET AUDIO_OUT_LVL updates device state."""
        async with MockSlxdServer() as server:
            reader, writer = await asyncio.open_connection(server.host, server.port)

            # Set to LINE
            writer.write(b"< SET 1 AUDIO_OUT_LVL LINE >\r\n")
            await writer.drain()
            await reader.readline()

            # Verify state changed
            assert server.device.channels[0].audio_out_level == "LINE"

            writer.close()
            await writer.wait_closed()
