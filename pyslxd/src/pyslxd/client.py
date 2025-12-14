"""Async TCP client for Shure SLX-D devices.

Stub file for TDD RED phase - tests are written, implementation pending.
"""

from __future__ import annotations

from pyslxd.protocol import ParsedResponse


class SlxdClient:
    """Async TCP client for SLX-D receivers - stub for TDD."""

    def __init__(self, host: str | None = None, port: int = 2202) -> None:
        """Initialize client."""
        self._host = host
        self._port = port
        self._connected = False

    @property
    def connected(self) -> bool:
        """Check if client is connected."""
        return self._connected

    async def connect(self, host: str | None = None, port: int = 2202) -> None:
        """Connect to device."""
        raise NotImplementedError("TDD RED phase")

    async def disconnect(self) -> None:
        """Disconnect from device."""
        raise NotImplementedError("TDD RED phase")

    async def __aenter__(self) -> "SlxdClient":
        """Async context manager enter."""
        raise NotImplementedError("TDD RED phase")

    async def __aexit__(self, *args: object) -> None:
        """Async context manager exit."""
        raise NotImplementedError("TDD RED phase")

    async def send_command(self, command: str) -> ParsedResponse:
        """Send command and receive response."""
        raise NotImplementedError("TDD RED phase")

    async def get_model(self) -> str:
        """Get device model."""
        raise NotImplementedError("TDD RED phase")

    async def get_device_id(self) -> str:
        """Get device ID."""
        raise NotImplementedError("TDD RED phase")

    async def get_firmware_version(self) -> str:
        """Get firmware version."""
        raise NotImplementedError("TDD RED phase")

    async def get_audio_gain(self, channel: int) -> int:
        """Get audio gain for channel in dB."""
        raise NotImplementedError("TDD RED phase")

    async def set_audio_gain(self, channel: int, gain_db: int) -> None:
        """Set audio gain for channel in dB."""
        raise NotImplementedError("TDD RED phase")

    async def flash_device(self) -> None:
        """Flash device LEDs for identification."""
        raise NotImplementedError("TDD RED phase")

    async def flash_channel(self, channel: int) -> None:
        """Flash channel LED for identification."""
        raise NotImplementedError("TDD RED phase")

    async def start_metering(self, channel: int, rate_ms: int = 1000) -> None:
        """Start metering for a channel."""
        raise NotImplementedError("TDD RED phase")

    async def stop_metering(self, channel: int) -> None:
        """Stop metering for a channel."""
        raise NotImplementedError("TDD RED phase")
