"""Protocol handling for Shure SLX-D devices.

Stub file for TDD RED phase - tests are written, implementation pending.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class CommandType(Enum):
    """Command types for SLX-D protocol."""

    GET = "GET"
    SET = "SET"
    REP = "REP"
    SAMPLE = "SAMPLE"


@dataclass
class ParsedResponse:
    """Parsed response from SLX-D device."""

    command_type: CommandType
    property_name: str
    value: str | None = None
    channel: int | None = None
    raw_value: int | None = None
    antenna: int | None = None
    values: list[int] | None = None


def build_command(
    command_type: CommandType,
    property_name: str,
    channel: int | None = None,
    value: str | None = None,
) -> str:
    """Build a command string for SLX-D device.

    Args:
        command_type: Type of command (GET, SET)
        property_name: Property to get/set
        channel: Optional channel number (0 for all, 1-4 for specific)
        value: Optional value for SET commands

    Returns:
        Formatted command string

    Raises:
        NotImplementedError: Stub - not yet implemented
    """
    raise NotImplementedError("TDD RED phase - implement to make tests pass")


def parse_response(response: str) -> ParsedResponse:
    """Parse a response string from SLX-D device.

    Args:
        response: Raw response string from device

    Returns:
        ParsedResponse with extracted data

    Raises:
        SlxdProtocolError: If response is malformed
        NotImplementedError: Stub - not yet implemented
    """
    raise NotImplementedError("TDD RED phase - implement to make tests pass")


def convert_audio_gain(value: int, to_raw: bool = False) -> int:
    """Convert audio gain between raw and dB values.

    Args:
        value: Value to convert
        to_raw: If True, convert dB to raw; if False, convert raw to dB

    Returns:
        Converted value

    Raises:
        NotImplementedError: Stub - not yet implemented
    """
    raise NotImplementedError("TDD RED phase - implement to make tests pass")


def convert_audio_level(raw_value: int) -> int:
    """Convert raw audio level to dBFS.

    Args:
        raw_value: Raw value from device (0-120)

    Returns:
        Audio level in dBFS (-120 to 0)

    Raises:
        NotImplementedError: Stub - not yet implemented
    """
    raise NotImplementedError("TDD RED phase - implement to make tests pass")


def convert_rssi(raw_value: int) -> int:
    """Convert raw RSSI value to dBm.

    Args:
        raw_value: Raw value from device (0-120)

    Returns:
        RSSI in dBm (-120 to 0)

    Raises:
        NotImplementedError: Stub - not yet implemented
    """
    raise NotImplementedError("TDD RED phase - implement to make tests pass")


def convert_battery_minutes(raw_value: int) -> int | None:
    """Convert raw battery minutes to actual minutes.

    Args:
        raw_value: Raw value from device

    Returns:
        Minutes remaining, or None for special values (warning/calculating/unknown)

    Raises:
        NotImplementedError: Stub - not yet implemented
    """
    raise NotImplementedError("TDD RED phase - implement to make tests pass")


def convert_battery_bars(raw_value: int, as_percentage: bool = False) -> int | None:
    """Convert raw battery bars to bars or percentage.

    Args:
        raw_value: Raw value from device (0-5, 255=unknown)
        as_percentage: If True, return as percentage (0-100)

    Returns:
        Battery bars (0-5), percentage (0-100), or None if unknown

    Raises:
        NotImplementedError: Stub - not yet implemented
    """
    raise NotImplementedError("TDD RED phase - implement to make tests pass")
