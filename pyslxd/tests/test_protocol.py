"""Tests for pyslxd protocol parsing and command building.

TDD RED PHASE: These tests define the expected behavior of the protocol module.
Run these tests to see them fail, then implement protocol.py to make them pass.
"""

import pytest

from pyslxd.protocol import (
    CommandType,
    ParsedResponse,
    build_command,
    parse_response,
    convert_audio_gain,
    convert_audio_level,
    convert_rssi,
    convert_battery_minutes,
    convert_battery_bars,
)
from pyslxd.exceptions import SlxdProtocolError


class TestBuildCommand:
    """Tests for command building functions."""

    def test_build_get_command_device_property(self) -> None:
        """Test building a GET command for device-level property."""
        # Arrange / Act
        result = build_command(CommandType.GET, "MODEL")

        # Assert
        assert result == "< GET MODEL >"

    def test_build_get_command_channel_property(self) -> None:
        """Test building a GET command for channel-level property."""
        # Arrange / Act
        result = build_command(CommandType.GET, "AUDIO_GAIN", channel=1)

        # Assert
        assert result == "< GET 1 AUDIO_GAIN >"

    def test_build_get_all_channels(self) -> None:
        """Test building a GET ALL command for all channels."""
        # Arrange / Act
        result = build_command(CommandType.GET, "ALL", channel=0)

        # Assert
        assert result == "< GET 0 ALL >"

    def test_build_set_command_with_value(self) -> None:
        """Test building a SET command with a value."""
        # Arrange / Act
        result = build_command(CommandType.SET, "AUDIO_GAIN", channel=1, value="040")

        # Assert
        assert result == "< SET 1 AUDIO_GAIN 040 >"

    def test_build_set_flash_device(self) -> None:
        """Test building a SET FLASH command for device."""
        # Arrange / Act
        result = build_command(CommandType.SET, "FLASH", value="ON")

        # Assert
        assert result == "< SET FLASH ON >"

    def test_build_set_flash_channel(self) -> None:
        """Test building a SET FLASH command for specific channel."""
        # Arrange / Act
        result = build_command(CommandType.SET, "FLASH", channel=1, value="ON")

        # Assert
        assert result == "< SET 1 FLASH ON >"

    def test_build_set_meter_rate(self) -> None:
        """Test building a SET METER_RATE command."""
        # Arrange / Act
        result = build_command(CommandType.SET, "METER_RATE", channel=1, value="01000")

        # Assert
        assert result == "< SET 1 METER_RATE 01000 >"

    def test_build_set_channel_name_with_braces(self) -> None:
        """Test building a SET CHAN_NAME command with braces."""
        # Arrange / Act
        result = build_command(CommandType.SET, "CHAN_NAME", channel=1, value="{Lead Vox}")

        # Assert
        assert result == "< SET 1 CHAN_NAME {Lead Vox} >"


class TestParseResponse:
    """Tests for response parsing functions."""

    def test_parse_rep_model_returns_parsed_response(self) -> None:
        """Test parsing a MODEL REP response."""
        # Arrange
        response = "< REP MODEL {SLXD4D                          } >"

        # Act
        result = parse_response(response)

        # Assert
        assert result.command_type == CommandType.REP
        assert result.property_name == "MODEL"
        assert result.value == "SLXD4D"
        assert result.channel is None

    def test_parse_rep_device_id(self) -> None:
        """Test parsing a DEVICE_ID REP response."""
        # Arrange
        response = "< REP DEVICE_ID {SLXD4D01} >"

        # Act
        result = parse_response(response)

        # Assert
        assert result.property_name == "DEVICE_ID"
        assert result.value == "SLXD4D01"

    def test_parse_rep_channel_audio_gain(self) -> None:
        """Test parsing a channel AUDIO_GAIN REP response."""
        # Arrange
        response = "< REP 1 AUDIO_GAIN 030 >"

        # Act
        result = parse_response(response)

        # Assert
        assert result.channel == 1
        assert result.property_name == "AUDIO_GAIN"
        assert result.value == "030"
        assert result.raw_value == 30

    def test_parse_rep_channel_name_strips_padding(self) -> None:
        """Test parsing CHAN_NAME response strips whitespace padding."""
        # Arrange
        response = "< REP 1 CHAN_NAME {Lead Vox                       } >"

        # Act
        result = parse_response(response)

        # Assert
        assert result.channel == 1
        assert result.property_name == "CHAN_NAME"
        assert result.value == "Lead Vox"

    def test_parse_rep_frequency(self) -> None:
        """Test parsing FREQUENCY response."""
        # Arrange
        response = "< REP 1 FREQUENCY 0578350 >"

        # Act
        result = parse_response(response)

        # Assert
        assert result.property_name == "FREQUENCY"
        assert result.value == "0578350"
        assert result.raw_value == 578350

    def test_parse_rep_group_channel(self) -> None:
        """Test parsing GROUP_CHANNEL response."""
        # Arrange
        response = "< REP 1 GROUP_CHANNEL {1,1  } >"

        # Act
        result = parse_response(response)

        # Assert
        assert result.property_name == "GROUP_CHANNEL"
        assert result.value == "1,1"

    def test_parse_rep_audio_level_peak(self) -> None:
        """Test parsing AUDIO_LEVEL_PEAK response."""
        # Arrange
        response = "< REP 1 AUDIO_LEVEL_PEAK 102 >"

        # Act
        result = parse_response(response)

        # Assert
        assert result.property_name == "AUDIO_LEVEL_PEAK"
        assert result.raw_value == 102

    def test_parse_rep_rssi_with_antenna(self) -> None:
        """Test parsing RSSI response with antenna number."""
        # Arrange
        response = "< REP 1 RSSI 1 083 >"

        # Act
        result = parse_response(response)

        # Assert
        assert result.property_name == "RSSI"
        assert result.antenna == 1
        assert result.raw_value == 83

    def test_parse_rep_rssi_antenna_2(self) -> None:
        """Test parsing RSSI response for antenna 2."""
        # Arrange
        response = "< REP 1 RSSI 2 064 >"

        # Act
        result = parse_response(response)

        # Assert
        assert result.antenna == 2
        assert result.raw_value == 64

    def test_parse_rep_tx_model(self) -> None:
        """Test parsing TX_MODEL response."""
        # Arrange
        response = "< REP 1 TX_MODEL SLXD2 >"

        # Act
        result = parse_response(response)

        # Assert
        assert result.property_name == "TX_MODEL"
        assert result.value == "SLXD2"

    def test_parse_rep_tx_batt_bars(self) -> None:
        """Test parsing TX_BATT_BARS response."""
        # Arrange
        response = "< REP 1 TX_BATT_BARS 004 >"

        # Act
        result = parse_response(response)

        # Assert
        assert result.property_name == "TX_BATT_BARS"
        assert result.raw_value == 4

    def test_parse_rep_tx_batt_mins(self) -> None:
        """Test parsing TX_BATT_MINS response."""
        # Arrange
        response = "< REP 1 TX_BATT_MINS 00125 >"

        # Act
        result = parse_response(response)

        # Assert
        assert result.property_name == "TX_BATT_MINS"
        assert result.raw_value == 125

    def test_parse_rep_lock_status(self) -> None:
        """Test parsing LOCK_STATUS response."""
        # Arrange
        response = "< REP LOCK_STATUS ALL >"

        # Act
        result = parse_response(response)

        # Assert
        assert result.property_name == "LOCK_STATUS"
        assert result.value == "ALL"

    def test_parse_rep_fw_ver(self) -> None:
        """Test parsing FW_VER response."""
        # Arrange
        response = "< REP FW_VER {2.0.15.2                } >"

        # Act
        result = parse_response(response)

        # Assert
        assert result.property_name == "FW_VER"
        assert result.value == "2.0.15.2"

    def test_parse_rep_audio_out_lvl_switch(self) -> None:
        """Test parsing AUDIO_OUT_LVL_SWITCH response."""
        # Arrange
        response = "< REP 1 AUDIO_OUT_LVL_SWITCH MIC >"

        # Act
        result = parse_response(response)

        # Assert
        assert result.property_name == "AUDIO_OUT_LVL_SWITCH"
        assert result.value == "MIC"

    def test_parse_malformed_response_raises_error(self) -> None:
        """Test that malformed response raises SlxdProtocolError."""
        # Arrange
        response = "invalid response"

        # Act / Assert
        with pytest.raises(SlxdProtocolError):
            parse_response(response)

    def test_parse_empty_response_raises_error(self) -> None:
        """Test that empty response raises SlxdProtocolError."""
        # Arrange
        response = ""

        # Act / Assert
        with pytest.raises(SlxdProtocolError):
            parse_response(response)

    def test_parse_incomplete_response_raises_error(self) -> None:
        """Test that incomplete response raises SlxdProtocolError."""
        # Arrange
        response = "< REP MODEL"

        # Act / Assert
        with pytest.raises(SlxdProtocolError):
            parse_response(response)

    def test_parse_sample_response(self) -> None:
        """Test parsing SAMPLE metering response."""
        # Arrange
        response = "< SAMPLE 1 ALL 102 102 086 >"

        # Act
        result = parse_response(response)

        # Assert
        assert result.command_type == CommandType.SAMPLE
        assert result.channel == 1
        assert result.values == [102, 102, 86]


class TestValueConversions:
    """Tests for value conversion functions."""

    def test_convert_audio_gain_from_raw(self) -> None:
        """Test converting raw audio gain to dB."""
        # Offset is 18, so 030 raw = 12 dB actual
        assert convert_audio_gain(30) == 12
        assert convert_audio_gain(0) == -18
        assert convert_audio_gain(60) == 42
        assert convert_audio_gain(18) == 0

    def test_convert_audio_gain_to_raw(self) -> None:
        """Test converting dB gain to raw value for SET command."""
        assert convert_audio_gain(12, to_raw=True) == 30
        assert convert_audio_gain(-18, to_raw=True) == 0
        assert convert_audio_gain(42, to_raw=True) == 60
        assert convert_audio_gain(0, to_raw=True) == 18

    def test_convert_audio_level_from_raw(self) -> None:
        """Test converting raw audio level to dBFS."""
        # Offset is 120, so 102 raw = -18 dBFS actual
        assert convert_audio_level(102) == -18
        assert convert_audio_level(120) == 0
        assert convert_audio_level(0) == -120
        assert convert_audio_level(100) == -20

    def test_convert_rssi_from_raw(self) -> None:
        """Test converting raw RSSI to dBm."""
        # Offset is 120, so 083 raw = -37 dBm actual
        assert convert_rssi(83) == -37
        assert convert_rssi(120) == 0
        assert convert_rssi(0) == -120
        assert convert_rssi(64) == -56

    def test_convert_battery_minutes_normal(self) -> None:
        """Test converting normal battery minutes values."""
        assert convert_battery_minutes(125) == 125
        assert convert_battery_minutes(0) == 0
        assert convert_battery_minutes(65532) == 65532

    def test_convert_battery_minutes_special_values(self) -> None:
        """Test converting special battery minutes values."""
        # 65533 = warning, 65534 = calculating, 65535 = unknown
        assert convert_battery_minutes(65533) is None  # Warning
        assert convert_battery_minutes(65534) is None  # Calculating
        assert convert_battery_minutes(65535) is None  # Unknown

    def test_convert_battery_bars_normal(self) -> None:
        """Test converting normal battery bars values."""
        assert convert_battery_bars(0) == 0
        assert convert_battery_bars(3) == 3
        assert convert_battery_bars(5) == 5

    def test_convert_battery_bars_unknown(self) -> None:
        """Test converting unknown battery bars value."""
        assert convert_battery_bars(255) is None

    def test_convert_battery_bars_to_percentage(self) -> None:
        """Test converting battery bars to percentage."""
        assert convert_battery_bars(0, as_percentage=True) == 0
        assert convert_battery_bars(1, as_percentage=True) == 20
        assert convert_battery_bars(2, as_percentage=True) == 40
        assert convert_battery_bars(3, as_percentage=True) == 60
        assert convert_battery_bars(4, as_percentage=True) == 80
        assert convert_battery_bars(5, as_percentage=True) == 100
        assert convert_battery_bars(255, as_percentage=True) is None


class TestParsedResponse:
    """Tests for ParsedResponse dataclass."""

    def test_parsed_response_equality(self) -> None:
        """Test that ParsedResponse instances can be compared."""
        # Arrange
        r1 = ParsedResponse(
            command_type=CommandType.REP,
            property_name="MODEL",
            value="SLXD4D",
        )
        r2 = ParsedResponse(
            command_type=CommandType.REP,
            property_name="MODEL",
            value="SLXD4D",
        )

        # Assert
        assert r1 == r2

    def test_parsed_response_with_channel(self) -> None:
        """Test ParsedResponse with channel number."""
        # Arrange / Act
        response = ParsedResponse(
            command_type=CommandType.REP,
            property_name="AUDIO_GAIN",
            value="030",
            channel=1,
            raw_value=30,
        )

        # Assert
        assert response.channel == 1
        assert response.raw_value == 30
