"""Async TCP client for Shure SLX-D devices.

This module provides an async TCP client for communicating with Shure SLX-D
wireless microphone receivers over their ASCII protocol on port 2202.
"""

from __future__ import annotations

import asyncio
from asyncio import StreamReader, StreamWriter
from typing import TYPE_CHECKING

from pyslxd.exceptions import SlxdConnectionError, SlxdTimeoutError
from pyslxd.protocol import (
    CommandType,
    ParsedResponse,
    build_command,
    convert_audio_gain,
    parse_response,
)

if TYPE_CHECKING:
    from types import TracebackType

# Audio gain limits in dB
AUDIO_GAIN_MIN_DB = -18
AUDIO_GAIN_MAX_DB = 42


class SlxdClient:
    """Async TCP client for SLX-D receivers.

    This client manages TCP connections to Shure SLX-D receivers and provides
    methods for querying device state and controlling settings.

    Can be used as an async context manager:
        async with SlxdClient("192.168.1.100") as client:
            model = await client.get_model()
    """

    def __init__(self, host: str | None = None, port: int = 2202) -> None:
        """Initialize client.

        Args:
            host: Device IP address (can also be provided to connect())
            port: TCP port (default 2202)
        """
        self._host = host
        self._port = port
        self._connected = False
        self._reader: StreamReader | None = None
        self._writer: StreamWriter | None = None

    @property
    def connected(self) -> bool:
        """Check if client is connected."""
        return self._connected

    async def connect(self, host: str | None = None, port: int = 2202) -> None:
        """Connect to device.

        Args:
            host: Device IP address (overrides constructor value)
            port: TCP port (default 2202)

        Raises:
            SlxdConnectionError: If connection fails
        """
        target_host = host or self._host
        if target_host is None:
            raise SlxdConnectionError("No host specified")

        try:
            self._reader, self._writer = await asyncio.open_connection(
                target_host, port
            )
            self._connected = True
            self._host = target_host
            self._port = port
        except asyncio.TimeoutError as err:
            raise SlxdConnectionError(f"Connection timed out: {target_host}") from err
        except ConnectionRefusedError as err:
            raise SlxdConnectionError(f"Connection refused: {target_host}") from err
        except OSError as err:
            raise SlxdConnectionError(f"Connection failed: {err}") from err

    async def disconnect(self) -> None:
        """Disconnect from device."""
        if self._writer is not None:
            self._writer.close()
            await self._writer.wait_closed()
            self._writer = None
            self._reader = None
        self._connected = False

    async def __aenter__(self) -> "SlxdClient":
        """Async context manager enter."""
        await self.connect()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Async context manager exit."""
        await self.disconnect()

    async def send_command(self, command: str) -> ParsedResponse:
        """Send command and receive response.

        Args:
            command: Command string to send

        Returns:
            Parsed response from device

        Raises:
            SlxdConnectionError: If not connected
            SlxdTimeoutError: If response times out
        """
        if not self._connected or self._writer is None or self._reader is None:
            raise SlxdConnectionError("Not connected")

        # Send command with line terminator
        self._writer.write(f"{command}\r\n".encode())
        await self._writer.drain()

        # Read response
        try:
            response_bytes = await self._reader.readline()
            response = response_bytes.decode().strip()
            return parse_response(response)
        except asyncio.TimeoutError as err:
            raise SlxdTimeoutError("Command timed out") from err

    async def get_model(self) -> str:
        """Get device model.

        Returns:
            Model string (e.g., "SLXD4D")
        """
        command = build_command(CommandType.GET, "MODEL")
        response = await self.send_command(command)
        return response.value or ""

    async def get_device_id(self) -> str:
        """Get device ID.

        Returns:
            Device ID string (8 characters)
        """
        command = build_command(CommandType.GET, "DEVICE_ID")
        response = await self.send_command(command)
        return response.value or ""

    async def get_firmware_version(self) -> str:
        """Get firmware version.

        Returns:
            Firmware version string
        """
        command = build_command(CommandType.GET, "FW_VER")
        response = await self.send_command(command)
        return response.value or ""

    async def get_audio_gain(self, channel: int) -> int:
        """Get audio gain for channel in dB.

        Args:
            channel: Channel number (1-4)

        Returns:
            Audio gain in dB (-18 to +42)
        """
        command = build_command(CommandType.GET, "AUDIO_GAIN", channel=channel)
        response = await self.send_command(command)
        raw_value = response.raw_value or 0
        return convert_audio_gain(raw_value, to_raw=False)

    async def set_audio_gain(self, channel: int, gain_db: int) -> None:
        """Set audio gain for channel in dB.

        Args:
            channel: Channel number (1-4)
            gain_db: Gain value in dB (-18 to +42)

        Raises:
            ValueError: If gain is out of range
        """
        if gain_db < AUDIO_GAIN_MIN_DB or gain_db > AUDIO_GAIN_MAX_DB:
            raise ValueError(
                f"Gain must be between {AUDIO_GAIN_MIN_DB} and {AUDIO_GAIN_MAX_DB} dB"
            )

        raw_value = convert_audio_gain(gain_db, to_raw=True)
        command = build_command(
            CommandType.SET, "AUDIO_GAIN", channel=channel, value=f"{raw_value:03d}"
        )
        await self.send_command(command)

    async def flash_device(self) -> None:
        """Flash device LEDs for identification."""
        command = build_command(CommandType.SET, "FLASH", value="ON")
        await self.send_command(command)

    async def flash_channel(self, channel: int) -> None:
        """Flash channel LED for identification.

        Args:
            channel: Channel number (1-4)
        """
        command = build_command(CommandType.SET, "FLASH", channel=channel, value="ON")
        await self.send_command(command)

    async def start_metering(self, channel: int, rate_ms: int = 1000) -> None:
        """Start metering for a channel.

        Args:
            channel: Channel number (1-4)
            rate_ms: Update rate in milliseconds
        """
        command = build_command(
            CommandType.SET, "METER_RATE", channel=channel, value=f"{rate_ms:05d}"
        )
        await self.send_command(command)

    async def stop_metering(self, channel: int) -> None:
        """Stop metering for a channel.

        Args:
            channel: Channel number (1-4)
        """
        command = build_command(
            CommandType.SET, "METER_RATE", channel=channel, value="00000"
        )
        await self.send_command(command)
