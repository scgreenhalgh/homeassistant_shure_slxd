"""Protocol handler for mock SLX-D server.

This module handles parsing incoming commands and generating responses
according to the SLX-D command string protocol.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .state import MockDevice

# Response string padding width
STRING_PADDING_WIDTH = 31


class MockSlxdProtocol:
    """Handles SLX-D protocol commands for mock server.

    This class parses incoming commands and generates appropriate responses
    based on the current device state.
    """

    def __init__(self, device: MockDevice) -> None:
        """Initialize protocol handler.

        Args:
            device: The mock device state to use for responses
        """
        self.device = device

    def handle_command(self, raw_command: str) -> str | None:
        """Process incoming command and return response.

        Args:
            raw_command: Raw command string from client

        Returns:
            Response string, or None if command is invalid
        """
        raw_command = raw_command.strip()

        # Validate command format
        if not raw_command.startswith("<") or not raw_command.endswith(">"):
            return None

        # Extract inner content
        inner = raw_command[1:-1].strip()
        if not inner:
            return None

        # Split into parts
        parts = inner.split()
        if not parts:
            return None

        command_type = parts[0].upper()
        remaining = parts[1:]

        if command_type == "GET":
            return self._handle_get(remaining)
        elif command_type == "SET":
            return self._handle_set(remaining)
        else:
            return None

    def _handle_get(self, parts: list[str]) -> str | None:
        """Handle GET commands.

        Args:
            parts: Command parts after GET keyword

        Returns:
            Response string or None if invalid
        """
        if not parts:
            return None

        # Check if first part is a channel number
        channel: int | None = None
        if parts[0].isdigit():
            channel = int(parts[0])
            parts = parts[1:]

        if not parts:
            return None

        property_name = parts[0].upper()
        args = parts[1:]

        return self._get_property(property_name, channel, args)

    def _handle_set(self, parts: list[str]) -> str | None:
        """Handle SET commands.

        Args:
            parts: Command parts after SET keyword

        Returns:
            Response string or None if invalid
        """
        if not parts:
            return None

        # Check if first part is a channel number
        channel: int | None = None
        if parts[0].isdigit():
            channel = int(parts[0])
            parts = parts[1:]

        if len(parts) < 2:
            return None

        property_name = parts[0].upper()
        value = parts[1]

        return self._set_property(property_name, channel, value)

    def _get_property(
        self, property_name: str, channel: int | None, args: list[str]
    ) -> str | None:
        """Get property value and format response.

        Args:
            property_name: Property to get
            channel: Channel number (optional)
            args: Additional arguments

        Returns:
            Response string or None if invalid
        """
        # Device-level properties (no channel)
        if property_name == "MODEL":
            return self._format_rep_string("MODEL", self.device.model)

        if property_name == "DEVICE_ID":
            return self._format_rep_string("DEVICE_ID", self.device.device_id)

        if property_name == "FW_VER":
            return self._format_rep_string("FW_VER", self.device.firmware_version)

        if property_name == "RF_BAND":
            return f"< REP RF_BAND {self.device.rf_band} >"

        if property_name == "LOCK_STATUS":
            return f"< REP LOCK_STATUS {self.device.lock_status} >"

        # Channel-level properties
        if channel is None:
            return None

        ch = self.device.get_channel(channel)
        if ch is None:
            return None

        if property_name == "CHAN_NAME":
            return self._format_rep_string("CHAN_NAME", ch.name, channel)

        if property_name == "AUDIO_GAIN":
            return f"< REP {channel} AUDIO_GAIN {ch.audio_gain_raw:03d} >"

        if property_name == "AUDIO_OUT_LVL":
            return f"< REP {channel} AUDIO_OUT_LVL {ch.audio_out_level} >"

        if property_name == "FREQUENCY":
            return f"< REP {channel} FREQUENCY {ch.frequency_khz:07d} >"

        if property_name == "GROUP_CHAN":
            return f"< REP {channel} GROUP_CHAN {ch.group_channel} >"

        if property_name == "AUDIO_LEVEL_PEAK":
            return f"< REP {channel} AUDIO_LEVEL_PEAK {ch.audio_peak_raw:03d} >"

        if property_name == "AUDIO_LEVEL_RMS":
            return f"< REP {channel} AUDIO_LEVEL_RMS {ch.audio_rms_raw:03d} >"

        if property_name == "RSSI":
            if not args:
                return None
            try:
                antenna = int(args[0])
            except ValueError:
                return None
            if antenna == 1:
                return f"< REP {channel} RSSI 1 {ch.rssi_a1_raw:03d} >"
            elif antenna == 2:
                return f"< REP {channel} RSSI 2 {ch.rssi_a2_raw:03d} >"
            return None

        # Transmitter properties
        if property_name == "TX_MODEL":
            if ch.transmitter and ch.transmitter.connected:
                return f"< REP {channel} TX_MODEL {ch.transmitter.model} >"
            return f"< REP {channel} TX_MODEL UNKNOWN >"

        if property_name == "TX_BATT_BARS":
            if ch.transmitter and ch.transmitter.connected:
                return f"< REP {channel} TX_BATT_BARS {ch.transmitter.battery_bars:03d} >"
            return f"< REP {channel} TX_BATT_BARS 255 >"

        if property_name == "TX_BATT_MINS":
            if ch.transmitter and ch.transmitter.connected:
                return f"< REP {channel} TX_BATT_MINS {ch.transmitter.battery_minutes:05d} >"
            return f"< REP {channel} TX_BATT_MINS 65535 >"

        if property_name == "METER_RATE":
            # Return 0 (metering off) as default
            return f"< REP {channel} METER_RATE 00000 >"

        return None

    def _set_property(
        self, property_name: str, channel: int | None, value: str
    ) -> str | None:
        """Set property value and format response.

        Args:
            property_name: Property to set
            channel: Channel number (optional)
            value: Value to set

        Returns:
            Response string or None if invalid
        """
        # Device-level SET commands
        if property_name == "FLASH":
            if channel is None:
                return "< REP FLASH ON >"
            ch = self.device.get_channel(channel)
            if ch is None:
                return None
            return f"< REP {channel} FLASH ON >"

        if property_name == "LOCK_STATUS":
            if value in ("OFF", "MENU", "ALL"):
                self.device.lock_status = value
                return f"< REP LOCK_STATUS {value} >"
            return None

        # Channel-level SET commands
        if channel is None:
            return None

        ch = self.device.get_channel(channel)
        if ch is None:
            return None

        if property_name == "AUDIO_GAIN":
            try:
                raw_value = int(value)
                if 0 <= raw_value <= 60:
                    ch.audio_gain_raw = raw_value
                    return f"< REP {channel} AUDIO_GAIN {raw_value:03d} >"
            except ValueError:
                pass
            return None

        if property_name == "AUDIO_OUT_LVL":
            if value in ("MIC", "LINE"):
                ch.audio_out_level = value
                return f"< REP {channel} AUDIO_OUT_LVL {value} >"
            return None

        if property_name == "CHAN_NAME":
            # Accept up to 8 characters
            name = value[:8]
            ch.name = name
            return self._format_rep_string("CHAN_NAME", name, channel)

        if property_name == "METER_RATE":
            try:
                rate = int(value)
                # Just acknowledge the rate setting
                return f"< REP {channel} METER_RATE {rate:05d} >"
            except ValueError:
                return None

        return None

    def _format_rep_string(
        self, property_name: str, value: str, channel: int | None = None
    ) -> str:
        """Format a REP response with padded string value.

        Args:
            property_name: Property name
            value: String value to pad
            channel: Channel number (optional)

        Returns:
            Formatted response string
        """
        padded = value.ljust(STRING_PADDING_WIDTH)
        if channel is not None:
            return f"< REP {channel} {property_name} {{{padded}}} >"
        return f"< REP {property_name} {{{padded}}} >"

    def generate_sample(self, channel: int) -> str | None:
        """Generate a SAMPLE metering response for a channel.

        SAMPLE format: < SAMPLE {ch} ALL {peak} {rms} {rssi1} {rssi2} {antenna} >

        Args:
            channel: Channel number

        Returns:
            SAMPLE response string or None if channel invalid
        """
        ch = self.device.get_channel(channel)
        if ch is None:
            return None

        # Determine which antenna is active (higher RSSI)
        active_antenna = 1 if ch.rssi_a1_raw >= ch.rssi_a2_raw else 2

        return (
            f"< SAMPLE {channel} ALL "
            f"{ch.audio_peak_raw:03d} "
            f"{ch.audio_rms_raw:03d} "
            f"{ch.rssi_a1_raw:03d} "
            f"{ch.rssi_a2_raw:03d} "
            f"{active_antenna} >"
        )
