"""Async TCP client for Shure SLX-D devices.

This module provides an async TCP client for communicating with Shure SLX-D
wireless microphone receivers over their ASCII protocol on port 2202.
"""

from __future__ import annotations

import asyncio
from asyncio import StreamReader, StreamWriter
from typing import TYPE_CHECKING

from pyslxd.exceptions import SlxdConnectionError, SlxdProtocolError, SlxdTimeoutError
from pyslxd.protocol import (
    CommandType,
    ParsedResponse,
    build_command,
    convert_audio_gain,
    convert_audio_level,
    convert_battery_bars,
    convert_battery_minutes,
    convert_rssi,
    parse_response,
)

if TYPE_CHECKING:
    from types import TracebackType

# Audio gain limits in dB
AUDIO_GAIN_MIN_DB = -18
AUDIO_GAIN_MAX_DB = 42

# Protocol limits
DEFAULT_COMMAND_TIMEOUT = 10.0  # seconds
MAX_RESPONSE_SIZE = 4096  # bytes

# Channel limits
MIN_CHANNEL = 1
MAX_CHANNEL = 4


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

    @staticmethod
    def _validate_channel(channel: int) -> None:
        """Validate channel number is in valid range.

        Args:
            channel: Channel number to validate

        Raises:
            ValueError: If channel is out of range (1-4)
        """
        if not MIN_CHANNEL <= channel <= MAX_CHANNEL:
            raise ValueError(
                f"Channel must be {MIN_CHANNEL}-{MAX_CHANNEL}, got {channel}"
            )

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

    async def send_command(
        self, command: str, timeout: float = DEFAULT_COMMAND_TIMEOUT
    ) -> ParsedResponse:
        """Send command and receive response.

        Args:
            command: Command string to send
            timeout: Response timeout in seconds (default 10.0)

        Returns:
            Parsed response from device

        Raises:
            SlxdConnectionError: If not connected
            SlxdTimeoutError: If response times out
            SlxdProtocolError: If response is too large
        """
        if not self._connected or self._writer is None or self._reader is None:
            raise SlxdConnectionError("Not connected")

        # Send command with line terminator
        self._writer.write(f"{command}\r\n".encode())
        await self._writer.drain()

        # Read response with timeout
        try:
            response_bytes = await asyncio.wait_for(
                self._reader.readline(), timeout=timeout
            )
        except asyncio.TimeoutError as err:
            raise SlxdTimeoutError(f"Command timed out after {timeout}s") from err

        # Check response size limit
        if len(response_bytes) > MAX_RESPONSE_SIZE:
            raise SlxdProtocolError(
                f"Response too large: {len(response_bytes)} bytes (max {MAX_RESPONSE_SIZE})"
            )

        response = response_bytes.decode().strip()
        return parse_response(response)

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

    async def get_rf_band(self) -> str:
        """Get RF frequency band.

        Returns:
            RF band string (e.g., "G55", "H55", "J52")
        """
        command = build_command(CommandType.GET, "RF_BAND")
        response = await self.send_command(command)
        return response.value or ""

    async def get_lock_status(self) -> str:
        """Get front panel lock status.

        Returns:
            Lock status string ("OFF", "MENU", or "ALL")
        """
        command = build_command(CommandType.GET, "LOCK_STATUS")
        response = await self.send_command(command)
        return response.value or "OFF"

    async def get_group_channel(self, channel: int) -> str:
        """Get group/channel preset for channel.

        Args:
            channel: Channel number (1-4)

        Returns:
            Group/channel string (e.g., "1,1")

        Raises:
            ValueError: If channel is out of range
        """
        self._validate_channel(channel)
        command = build_command(CommandType.GET, "GROUP_CHAN", channel=channel)
        response = await self.send_command(command)
        return response.value or ""

    async def get_audio_gain(self, channel: int) -> int:
        """Get audio gain for channel in dB.

        Args:
            channel: Channel number (1-4)

        Returns:
            Audio gain in dB (-18 to +42)

        Raises:
            ValueError: If channel is out of range
        """
        self._validate_channel(channel)
        command = build_command(CommandType.GET, "AUDIO_GAIN", channel=channel)
        response = await self.send_command(command)
        raw_value = response.raw_value if response.raw_value is not None else 0
        return convert_audio_gain(raw_value, to_raw=False)

    async def set_audio_gain(self, channel: int, gain_db: int) -> None:
        """Set audio gain for channel in dB.

        Args:
            channel: Channel number (1-4)
            gain_db: Gain value in dB (-18 to +42)

        Raises:
            ValueError: If channel or gain is out of range
        """
        self._validate_channel(channel)
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

        Raises:
            ValueError: If channel is out of range
        """
        self._validate_channel(channel)
        command = build_command(CommandType.SET, "FLASH", channel=channel, value="ON")
        await self.send_command(command)

    async def start_metering(self, channel: int, rate_ms: int = 1000) -> None:
        """Start metering for a channel.

        Args:
            channel: Channel number (1-4)
            rate_ms: Update rate in milliseconds

        Raises:
            ValueError: If channel is out of range
        """
        self._validate_channel(channel)
        command = build_command(
            CommandType.SET, "METER_RATE", channel=channel, value=f"{rate_ms:05d}"
        )
        await self.send_command(command)

    async def stop_metering(self, channel: int) -> None:
        """Stop metering for a channel.

        Args:
            channel: Channel number (1-4)

        Raises:
            ValueError: If channel is out of range
        """
        self._validate_channel(channel)
        command = build_command(
            CommandType.SET, "METER_RATE", channel=channel, value="00000"
        )
        await self.send_command(command)

    async def get_frequency(self, channel: int) -> int:
        """Get operating frequency for channel in kHz.

        Args:
            channel: Channel number (1-4)

        Returns:
            Frequency in kHz

        Raises:
            ValueError: If channel is out of range
        """
        self._validate_channel(channel)
        command = build_command(CommandType.GET, "FREQUENCY", channel=channel)
        response = await self.send_command(command)
        return response.raw_value if response.raw_value is not None else 0

    async def get_channel_name(self, channel: int) -> str:
        """Get channel name.

        Args:
            channel: Channel number (1-4)

        Returns:
            Channel name string (up to 8 characters)

        Raises:
            ValueError: If channel is out of range
        """
        self._validate_channel(channel)
        command = build_command(CommandType.GET, "CHAN_NAME", channel=channel)
        response = await self.send_command(command)
        return response.value or ""

    async def get_audio_level_peak(self, channel: int) -> int:
        """Get peak audio level for channel in dBFS.

        Args:
            channel: Channel number (1-4)

        Returns:
            Peak audio level in dBFS (-120 to 0)

        Raises:
            ValueError: If channel is out of range
        """
        self._validate_channel(channel)
        command = build_command(CommandType.GET, "AUDIO_LEVEL_PEAK", channel=channel)
        response = await self.send_command(command)
        raw_value = response.raw_value if response.raw_value is not None else 0
        return convert_audio_level(raw_value)

    async def get_audio_level_rms(self, channel: int) -> int:
        """Get RMS audio level for channel in dBFS.

        Args:
            channel: Channel number (1-4)

        Returns:
            RMS audio level in dBFS (-120 to 0)

        Raises:
            ValueError: If channel is out of range
        """
        self._validate_channel(channel)
        command = build_command(CommandType.GET, "AUDIO_LEVEL_RMS", channel=channel)
        response = await self.send_command(command)
        raw_value = response.raw_value if response.raw_value is not None else 0
        return convert_audio_level(raw_value)

    async def get_rssi(self, channel: int, antenna: int) -> int:
        """Get RSSI for channel and antenna in dBm.

        Args:
            channel: Channel number (1-4)
            antenna: Antenna number (1 or 2)

        Returns:
            RSSI in dBm (-120 to 0)

        Raises:
            ValueError: If channel or antenna is out of range
        """
        self._validate_channel(channel)
        if antenna not in (1, 2):
            raise ValueError(f"Antenna must be 1 or 2, got {antenna}")
        command = build_command(
            CommandType.GET, "RSSI", channel=channel, value=str(antenna)
        )
        response = await self.send_command(command)
        raw_value = response.raw_value if response.raw_value is not None else 0
        return convert_rssi(raw_value)

    async def get_tx_model(self, channel: int) -> str:
        """Get transmitter model for channel.

        Args:
            channel: Channel number (1-4)

        Returns:
            Transmitter model (e.g., "SLXD1", "SLXD2", "UNKNOWN")

        Raises:
            ValueError: If channel is out of range
        """
        self._validate_channel(channel)
        command = build_command(CommandType.GET, "TX_MODEL", channel=channel)
        response = await self.send_command(command)
        return response.value or "UNKNOWN"

    async def get_tx_batt_bars(self, channel: int) -> int | None:
        """Get transmitter battery bars for channel.

        Args:
            channel: Channel number (1-4)

        Returns:
            Battery bars (0-5), or None if unknown

        Raises:
            ValueError: If channel is out of range
        """
        self._validate_channel(channel)
        command = build_command(CommandType.GET, "TX_BATT_BARS", channel=channel)
        response = await self.send_command(command)
        raw_value = response.raw_value if response.raw_value is not None else 255
        return convert_battery_bars(raw_value)

    async def get_tx_batt_mins(self, channel: int) -> int | None:
        """Get transmitter battery minutes remaining for channel.

        Args:
            channel: Channel number (1-4)

        Returns:
            Minutes remaining, or None if unknown/calculating

        Raises:
            ValueError: If channel is out of range
        """
        self._validate_channel(channel)
        command = build_command(CommandType.GET, "TX_BATT_MINS", channel=channel)
        response = await self.send_command(command)
        raw_value = response.raw_value if response.raw_value is not None else 65535
        return convert_battery_minutes(raw_value)

    async def get_audio_out_level(self, channel: int) -> str:
        """Get audio output level for channel.

        Args:
            channel: Channel number (1-4)

        Returns:
            Output level string ("MIC" or "LINE")

        Raises:
            ValueError: If channel is out of range
        """
        self._validate_channel(channel)
        command = build_command(CommandType.GET, "AUDIO_OUT_LVL", channel=channel)
        response = await self.send_command(command)
        return response.value or "MIC"

    async def set_audio_out_level(self, channel: int, level: str) -> None:
        """Set audio output level for channel.

        Args:
            channel: Channel number (1-4)
            level: Output level ("MIC" or "LINE")

        Raises:
            ValueError: If channel is out of range or level is invalid
        """
        self._validate_channel(channel)
        level_upper = level.upper()
        if level_upper not in ("MIC", "LINE"):
            raise ValueError(f"Level must be 'MIC' or 'LINE', got '{level}'")
        command = build_command(
            CommandType.SET, "AUDIO_OUT_LVL", channel=channel, value=level_upper
        )
        await self.send_command(command)
