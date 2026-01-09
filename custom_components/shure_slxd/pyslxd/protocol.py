"""Protocol handling for Shure SLX-D devices.

This module handles building commands and parsing responses for the
SLX-D ASCII protocol over TCP port 2202.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

from .exceptions import SlxdProtocolError


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


# Constants for value conversions
AUDIO_GAIN_OFFSET = 18
AUDIO_LEVEL_OFFSET = 120
RSSI_OFFSET = 120
BATTERY_MINS_WARNING = 65533
BATTERY_MINS_CALCULATING = 65534
BATTERY_MINS_UNKNOWN = 65535
BATTERY_BARS_UNKNOWN = 255


# Pattern for valid property names (uppercase letters and underscores)
PROPERTY_NAME_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]*$")

# Characters not allowed in values (protocol delimiters)
INVALID_VALUE_CHARS = frozenset("<>\r\n")


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
        ValueError: If property_name or value contains invalid characters
    """
    # Validate property name
    if not PROPERTY_NAME_PATTERN.match(property_name):
        raise ValueError(
            f"Invalid property name '{property_name}': must be uppercase letters, "
            "digits, and underscores only"
        )

    # Validate value doesn't contain protocol delimiters
    if value is not None and any(c in value for c in INVALID_VALUE_CHARS):
        raise ValueError(
            f"Invalid characters in value: cannot contain <, >, CR, or LF"
        )

    parts = [command_type.value]

    if channel is not None:
        parts.append(str(channel))

    parts.append(property_name)

    if value is not None:
        parts.append(value)

    return f"< {' '.join(parts)} >"


def parse_response(response: str) -> ParsedResponse:
    """Parse a response string from SLX-D device.

    Args:
        response: Raw response string from device

    Returns:
        ParsedResponse with extracted data

    Raises:
        SlxdProtocolError: If response is malformed
    """
    if not response:
        raise SlxdProtocolError("Empty response")

    # Check for valid response format
    response = response.strip()
    if not response.startswith("<") or not response.endswith(">"):
        raise SlxdProtocolError(f"Invalid response format: {response}")

    # Remove angle brackets and split
    inner = response[1:-1].strip()
    if not inner:
        raise SlxdProtocolError(f"Empty response content: {response}")

    # Parse command type
    parts = inner.split(None, 1)
    if not parts:
        raise SlxdProtocolError(f"No command type in response: {response}")

    try:
        command_type = CommandType(parts[0])
    except ValueError:
        raise SlxdProtocolError(f"Unknown command type: {parts[0]}")

    if len(parts) < 2:
        raise SlxdProtocolError(f"Incomplete response: {response}")

    remaining = parts[1]

    # Handle SAMPLE responses
    if command_type == CommandType.SAMPLE:
        return _parse_sample_response(remaining)

    # Parse channel number if present (starts with digit)
    channel = None
    if remaining and remaining[0].isdigit():
        channel_match = re.match(r"(\d+)\s+", remaining)
        if channel_match:
            channel = int(channel_match.group(1))
            remaining = remaining[channel_match.end():]

    # Parse property name and value
    return _parse_rep_response(command_type, remaining, channel)


def _parse_sample_response(remaining: str) -> ParsedResponse:
    """Parse a SAMPLE metering response.

    Args:
        remaining: Response content after SAMPLE keyword

    Returns:
        ParsedResponse with metering values

    Raises:
        SlxdProtocolError: If response is malformed or contains invalid values
    """
    parts = remaining.split()
    if len(parts) < 2:
        raise SlxdProtocolError(f"Invalid SAMPLE response: {remaining}")

    try:
        channel = int(parts[0])
        # parts[1] is "ALL"
        values = [int(v) for v in parts[2:]]
    except ValueError as err:
        raise SlxdProtocolError(
            f"Invalid numeric values in SAMPLE response: {remaining}"
        ) from err

    return ParsedResponse(
        command_type=CommandType.SAMPLE,
        property_name="ALL",
        channel=channel,
        values=values,
    )


def _parse_rep_response(
    command_type: CommandType, remaining: str, channel: int | None
) -> ParsedResponse:
    """Parse a REP response.

    Args:
        command_type: The command type (REP)
        remaining: Response content after channel (if present)
        channel: Channel number or None

    Returns:
        ParsedResponse with property data
    """
    # Handle RSSI which has antenna number
    rssi_match = re.match(r"RSSI\s+(\d+)\s+(\d+)", remaining)
    if rssi_match:
        antenna = int(rssi_match.group(1))
        raw_value = int(rssi_match.group(2))
        return ParsedResponse(
            command_type=command_type,
            property_name="RSSI",
            channel=channel,
            raw_value=raw_value,
            antenna=antenna,
        )

    # Handle braced values (strings with padding)
    brace_match = re.match(r"(\w+)\s+\{(.+)\}", remaining)
    if brace_match:
        property_name = brace_match.group(1)
        value = brace_match.group(2).strip()
        return ParsedResponse(
            command_type=command_type,
            property_name=property_name,
            value=value,
            channel=channel,
        )

    # Handle simple property value pairs
    parts = remaining.split(None, 1)
    if not parts:
        raise SlxdProtocolError(f"No property name in response: {remaining}")

    property_name = parts[0]
    value = parts[1].strip() if len(parts) > 1 else None

    # Try to parse numeric value
    raw_value = None
    if value is not None:
        try:
            raw_value = int(value)
        except ValueError:
            pass  # Not numeric, keep as string

    return ParsedResponse(
        command_type=command_type,
        property_name=property_name,
        value=value,
        channel=channel,
        raw_value=raw_value,
    )


def convert_audio_gain(value: int, to_raw: bool = False) -> int:
    """Convert audio gain between raw and dB values.

    The SLX-D reports/accepts gain with an offset of 18.
    Raw 0 = -18 dB, Raw 60 = +42 dB

    Args:
        value: Value to convert
        to_raw: If True, convert dB to raw; if False, convert raw to dB

    Returns:
        Converted value
    """
    if to_raw:
        return value + AUDIO_GAIN_OFFSET
    return value - AUDIO_GAIN_OFFSET


def convert_audio_level(raw_value: int) -> int:
    """Convert raw audio level to dBFS.

    The SLX-D reports audio levels with an offset of 120.
    Raw 0 = -120 dBFS, Raw 120 = 0 dBFS

    Args:
        raw_value: Raw value from device (0-120)

    Returns:
        Audio level in dBFS (-120 to 0)
    """
    return raw_value - AUDIO_LEVEL_OFFSET


def convert_rssi(raw_value: int) -> int:
    """Convert raw RSSI value to dBm.

    The SLX-D reports RSSI with an offset of 120.
    Raw 0 = -120 dBm, Raw 120 = 0 dBm

    Args:
        raw_value: Raw value from device (0-120)

    Returns:
        RSSI in dBm (-120 to 0)
    """
    return raw_value - RSSI_OFFSET


def convert_battery_minutes(raw_value: int) -> int | None:
    """Convert raw battery minutes to actual minutes.

    Special values:
    - 65533: Battery communication warning
    - 65534: Battery time calculating
    - 65535: Unknown or not applicable

    Args:
        raw_value: Raw value from device

    Returns:
        Minutes remaining, or None for special values
    """
    if raw_value >= BATTERY_MINS_WARNING:
        return None
    return raw_value


def convert_battery_bars(raw_value: int, as_percentage: bool = False) -> int | None:
    """Convert raw battery bars to bars or percentage.

    Args:
        raw_value: Raw value from device (0-5, 255=unknown)
        as_percentage: If True, return as percentage (0-100)

    Returns:
        Battery bars (0-5), percentage (0-100), or None if unknown
    """
    if raw_value == BATTERY_BARS_UNKNOWN:
        return None

    if as_percentage:
        return raw_value * 20  # 0=0%, 1=20%, 2=40%, 3=60%, 4=80%, 5=100%

    return raw_value
