"""Mock TCP server for SLX-D testing.

This module provides a TCP server that simulates a Shure SLX-D
wireless microphone receiver.
"""

from __future__ import annotations

import asyncio
import logging
from asyncio import Server, StreamReader, StreamWriter
from typing import Callable

from pyslxd.mock.protocol import MockSlxdProtocol
from pyslxd.mock.state import MockChannel, MockDevice, MockTransmitter

logger = logging.getLogger(__name__)


class MockSlxdServer:
    """TCP server simulating an SLX-D receiver.

    This server can be used for testing the pyslxd client without
    requiring real hardware.

    Example:
        async with MockSlxdServer() as server:
            # Server is running on server.host:server.port
            client = SlxdClient()
            await client.connect(server.host, server.port)
            model = await client.get_model()
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 0,  # 0 = auto-assign available port
        device: MockDevice | None = None,
    ) -> None:
        """Initialize mock server.

        Args:
            host: Host address to bind to
            port: Port to bind to (0 for auto-assign)
            device: Mock device state (creates default SLXD4D if None)
        """
        self._host = host
        self._port = port
        self._device = device or MockDevice()
        self._protocol = MockSlxdProtocol(self._device)
        self._server: Server | None = None
        self._clients: list[StreamWriter] = []
        self._metering_tasks: dict[int, asyncio.Task] = {}
        self._response_delay: float = 0.0
        self._connection_callback: Callable[[StreamWriter], None] | None = None
        self._command_callback: Callable[[str, str], None] | None = None

    @property
    def host(self) -> str:
        """Get server host address."""
        return self._host

    @property
    def port(self) -> int:
        """Get server port (actual port after binding)."""
        if self._server is not None:
            sockets = self._server.sockets
            if sockets:
                return sockets[0].getsockname()[1]
        return self._port

    @property
    def device(self) -> MockDevice:
        """Get the mock device state."""
        return self._device

    @property
    def is_running(self) -> bool:
        """Check if server is running."""
        return self._server is not None and self._server.is_serving()

    async def start(self) -> None:
        """Start the mock server."""
        self._server = await asyncio.start_server(
            self._handle_client,
            self._host,
            self._port,
        )
        logger.info(f"Mock SLX-D server started on {self.host}:{self.port}")

    async def stop(self) -> None:
        """Stop the mock server and disconnect all clients."""
        # Cancel all metering tasks
        for task in self._metering_tasks.values():
            task.cancel()
        self._metering_tasks.clear()

        # Close all client connections
        for writer in self._clients:
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass
        self._clients.clear()

        # Stop the server
        if self._server is not None:
            self._server.close()
            await self._server.wait_closed()
            self._server = None
            logger.info("Mock SLX-D server stopped")

    async def __aenter__(self) -> "MockSlxdServer":
        """Async context manager enter."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.stop()

    async def _handle_client(
        self, reader: StreamReader, writer: StreamWriter
    ) -> None:
        """Handle a client connection.

        Args:
            reader: Stream reader for client
            writer: Stream writer for client
        """
        self._clients.append(writer)
        peer = writer.get_extra_info("peername")
        logger.debug(f"Client connected: {peer}")

        if self._connection_callback:
            self._connection_callback(writer)

        try:
            while True:
                data = await reader.readline()
                if not data:
                    break

                command = data.decode().strip()
                if not command:
                    continue

                logger.debug(f"Received: {command}")

                # Add artificial delay if configured
                if self._response_delay > 0:
                    await asyncio.sleep(self._response_delay)

                # Handle the command
                response = self._protocol.handle_command(command)

                if self._command_callback:
                    self._command_callback(command, response or "")

                if response:
                    logger.debug(f"Sending: {response}")
                    writer.write(f"{response}\r\n".encode())
                    await writer.drain()

                    # Check for metering start/stop
                    self._check_metering_command(command, writer)

        except (ConnectionResetError, BrokenPipeError):
            logger.debug(f"Client disconnected: {peer}")
        except Exception as e:
            logger.error(f"Error handling client {peer}: {e}")
        finally:
            if writer in self._clients:
                self._clients.remove(writer)
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass

    def _check_metering_command(self, command: str, writer: StreamWriter) -> None:
        """Check if command starts/stops metering and handle accordingly.

        Args:
            command: The command that was processed
            writer: Client writer for sending samples
        """
        # Parse SET METER_RATE commands
        # Format: < SET {ch} METER_RATE {rate} >
        import re

        match = re.match(r"<\s*SET\s+(\d+)\s+METER_RATE\s+(\d+)\s*>", command)
        if not match:
            return

        channel = int(match.group(1))
        rate_ms = int(match.group(2))

        # Cancel existing metering task for this channel
        if channel in self._metering_tasks:
            self._metering_tasks[channel].cancel()
            del self._metering_tasks[channel]

        # Start new metering if rate > 0
        if rate_ms > 0:
            task = asyncio.create_task(
                self._send_metering(channel, writer, rate_ms / 1000.0)
            )
            self._metering_tasks[channel] = task

    async def _send_metering(
        self, channel: int, writer: StreamWriter, interval: float
    ) -> None:
        """Send periodic SAMPLE messages.

        Args:
            channel: Channel number
            writer: Client writer
            interval: Interval in seconds
        """
        try:
            while True:
                await asyncio.sleep(interval)
                sample = self._protocol.generate_sample(channel)
                if sample:
                    writer.write(f"{sample}\r\n".encode())
                    await writer.drain()
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error sending metering for channel {channel}: {e}")

    # Simulation methods for tests

    def connect_transmitter(
        self,
        channel: int,
        model: str = "SLXD2",
        battery_bars: int = 5,
        battery_minutes: int = 480,
    ) -> None:
        """Simulate transmitter connecting to a channel.

        Args:
            channel: Channel number (1-4)
            model: Transmitter model (SLXD1, SLXD2)
            battery_bars: Initial battery bars (0-5)
            battery_minutes: Initial battery minutes
        """
        ch = self._device.get_channel(channel)
        if ch is not None:
            ch.transmitter = MockTransmitter(
                model=model,
                connected=True,
                battery_bars=battery_bars,
                battery_minutes=battery_minutes,
            )
            # Simulate signal
            ch.rssi_a1_raw = 80
            ch.rssi_a2_raw = 75

    def disconnect_transmitter(self, channel: int) -> None:
        """Simulate transmitter disconnecting from a channel.

        Args:
            channel: Channel number (1-4)
        """
        ch = self._device.get_channel(channel)
        if ch is not None:
            ch.transmitter = None
            ch.rssi_a1_raw = 0
            ch.rssi_a2_raw = 0
            ch.audio_peak_raw = 0
            ch.audio_rms_raw = 0

    def set_battery_level(
        self, channel: int, bars: int, minutes: int | None = None
    ) -> None:
        """Simulate battery level change on transmitter.

        Args:
            channel: Channel number (1-4)
            bars: Battery bars (0-5)
            minutes: Battery minutes (optional, calculated from bars if None)
        """
        ch = self._device.get_channel(channel)
        if ch is not None and ch.transmitter is not None:
            ch.transmitter.battery_bars = bars
            if minutes is not None:
                ch.transmitter.battery_minutes = minutes
            else:
                # Estimate minutes from bars (roughly 96 min per bar)
                ch.transmitter.battery_minutes = bars * 96

    def set_audio_level(self, channel: int, peak: int, rms: int) -> None:
        """Simulate audio level on a channel.

        Args:
            channel: Channel number (1-4)
            peak: Peak audio level (raw 0-120)
            rms: RMS audio level (raw 0-120)
        """
        ch = self._device.get_channel(channel)
        if ch is not None:
            ch.audio_peak_raw = max(0, min(120, peak))
            ch.audio_rms_raw = max(0, min(120, rms))

    def set_rssi(self, channel: int, antenna1: int, antenna2: int) -> None:
        """Simulate RSSI levels on a channel.

        Args:
            channel: Channel number (1-4)
            antenna1: RSSI for antenna 1 (raw 0-120)
            antenna2: RSSI for antenna 2 (raw 0-120)
        """
        ch = self._device.get_channel(channel)
        if ch is not None:
            ch.rssi_a1_raw = max(0, min(120, antenna1))
            ch.rssi_a2_raw = max(0, min(120, antenna2))

    def set_response_delay(self, delay: float) -> None:
        """Set artificial delay before responding to commands.

        Useful for testing timeout handling.

        Args:
            delay: Delay in seconds
        """
        self._response_delay = delay

    def on_connection(self, callback: Callable[[StreamWriter], None]) -> None:
        """Set callback for new connections.

        Args:
            callback: Function to call when client connects
        """
        self._connection_callback = callback

    def on_command(self, callback: Callable[[str, str], None]) -> None:
        """Set callback for commands received.

        Args:
            callback: Function to call with (command, response)
        """
        self._command_callback = callback

    async def broadcast_rep(self, message: str) -> None:
        """Broadcast a REP message to all connected clients.

        Useful for simulating unsolicited device state changes.

        Args:
            message: REP message to send
        """
        for writer in self._clients:
            try:
                writer.write(f"{message}\r\n".encode())
                await writer.drain()
            except Exception:
                pass
