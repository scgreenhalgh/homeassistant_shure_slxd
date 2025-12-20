"""Tests for mock server protocol handler."""

from __future__ import annotations

import pytest

from pyslxd.mock.protocol import MockSlxdProtocol
from pyslxd.mock.state import MockChannel, MockDevice, MockTransmitter


@pytest.fixture
def device() -> MockDevice:
    """Create a mock device for testing."""
    return MockDevice(
        model="SLXD4D",
        device_id="TEST0001",
        firmware_version="2.0.15.2",
        rf_band="G55",
        lock_status="OFF",
    )


@pytest.fixture
def protocol(device: MockDevice) -> MockSlxdProtocol:
    """Create a protocol handler for testing."""
    return MockSlxdProtocol(device)


class TestProtocolGetDeviceInfo:
    """Tests for GET device info commands."""

    def test_get_model(self, protocol: MockSlxdProtocol) -> None:
        """Test GET MODEL command."""
        response = protocol.handle_command("< GET MODEL >")
        assert response is not None
        assert "REP MODEL" in response
        assert "SLXD4D" in response
        # Check padding format with braces
        assert "{" in response
        assert "}" in response

    def test_get_device_id(self, protocol: MockSlxdProtocol) -> None:
        """Test GET DEVICE_ID command."""
        response = protocol.handle_command("< GET DEVICE_ID >")
        assert response is not None
        assert "REP DEVICE_ID" in response
        assert "TEST0001" in response

    def test_get_firmware_version(self, protocol: MockSlxdProtocol) -> None:
        """Test GET FW_VER command."""
        response = protocol.handle_command("< GET FW_VER >")
        assert response is not None
        assert "REP FW_VER" in response
        assert "2.0.15.2" in response

    def test_get_rf_band(self, protocol: MockSlxdProtocol) -> None:
        """Test GET RF_BAND command."""
        response = protocol.handle_command("< GET RF_BAND >")
        assert response == "< REP RF_BAND G55 >"

    def test_get_lock_status(self, protocol: MockSlxdProtocol) -> None:
        """Test GET LOCK_STATUS command."""
        response = protocol.handle_command("< GET LOCK_STATUS >")
        assert response == "< REP LOCK_STATUS OFF >"


class TestProtocolGetChannelInfo:
    """Tests for GET channel info commands."""

    def test_get_chan_name(self, protocol: MockSlxdProtocol) -> None:
        """Test GET CHAN_NAME command."""
        response = protocol.handle_command("< GET 1 CHAN_NAME >")
        assert response is not None
        assert "REP 1 CHAN_NAME" in response
        assert "CH 1" in response

    def test_get_audio_gain(self, protocol: MockSlxdProtocol) -> None:
        """Test GET AUDIO_GAIN command."""
        response = protocol.handle_command("< GET 1 AUDIO_GAIN >")
        assert response == "< REP 1 AUDIO_GAIN 018 >"

    def test_get_audio_out_lvl(self, protocol: MockSlxdProtocol) -> None:
        """Test GET AUDIO_OUT_LVL command."""
        response = protocol.handle_command("< GET 1 AUDIO_OUT_LVL >")
        assert response == "< REP 1 AUDIO_OUT_LVL MIC >"

    def test_get_frequency(self, protocol: MockSlxdProtocol) -> None:
        """Test GET FREQUENCY command."""
        response = protocol.handle_command("< GET 1 FREQUENCY >")
        assert response is not None
        assert "REP 1 FREQUENCY" in response
        # Frequency should be 7 digits
        assert "0578350" in response

    def test_get_group_chan(self, protocol: MockSlxdProtocol) -> None:
        """Test GET GROUP_CHAN command."""
        response = protocol.handle_command("< GET 1 GROUP_CHAN >")
        assert response == "< REP 1 GROUP_CHAN 1,1 >"

    def test_get_audio_level_peak(self, protocol: MockSlxdProtocol) -> None:
        """Test GET AUDIO_LEVEL_PEAK command."""
        response = protocol.handle_command("< GET 1 AUDIO_LEVEL_PEAK >")
        assert response == "< REP 1 AUDIO_LEVEL_PEAK 000 >"

    def test_get_audio_level_rms(self, protocol: MockSlxdProtocol) -> None:
        """Test GET AUDIO_LEVEL_RMS command."""
        response = protocol.handle_command("< GET 1 AUDIO_LEVEL_RMS >")
        assert response == "< REP 1 AUDIO_LEVEL_RMS 000 >"

    def test_get_rssi_antenna_1(self, protocol: MockSlxdProtocol) -> None:
        """Test GET RSSI 1 command."""
        response = protocol.handle_command("< GET 1 RSSI 1 >")
        assert response == "< REP 1 RSSI 1 000 >"

    def test_get_rssi_antenna_2(self, protocol: MockSlxdProtocol) -> None:
        """Test GET RSSI 2 command."""
        response = protocol.handle_command("< GET 1 RSSI 2 >")
        assert response == "< REP 1 RSSI 2 000 >"

    def test_get_rssi_without_antenna_returns_none(
        self, protocol: MockSlxdProtocol
    ) -> None:
        """Test GET RSSI without antenna number returns None."""
        response = protocol.handle_command("< GET 1 RSSI >")
        assert response is None

    def test_get_meter_rate(self, protocol: MockSlxdProtocol) -> None:
        """Test GET METER_RATE command."""
        response = protocol.handle_command("< GET 1 METER_RATE >")
        assert response == "< REP 1 METER_RATE 00000 >"

    def test_get_channel_2(self, protocol: MockSlxdProtocol) -> None:
        """Test GET command for channel 2."""
        response = protocol.handle_command("< GET 2 AUDIO_GAIN >")
        assert response == "< REP 2 AUDIO_GAIN 018 >"

    def test_get_invalid_channel_returns_none(
        self, protocol: MockSlxdProtocol
    ) -> None:
        """Test GET for invalid channel returns None."""
        response = protocol.handle_command("< GET 5 AUDIO_GAIN >")
        assert response is None


class TestProtocolGetTransmitterInfo:
    """Tests for GET transmitter info commands."""

    def test_get_tx_model_no_transmitter(self, protocol: MockSlxdProtocol) -> None:
        """Test GET TX_MODEL when no transmitter connected."""
        response = protocol.handle_command("< GET 1 TX_MODEL >")
        assert response == "< REP 1 TX_MODEL UNKNOWN >"

    def test_get_tx_model_with_transmitter(self, device: MockDevice) -> None:
        """Test GET TX_MODEL with transmitter connected."""
        device.channels[0].transmitter = MockTransmitter(model="SLXD2", connected=True)
        protocol = MockSlxdProtocol(device)
        response = protocol.handle_command("< GET 1 TX_MODEL >")
        assert response == "< REP 1 TX_MODEL SLXD2 >"

    def test_get_tx_batt_bars_no_transmitter(self, protocol: MockSlxdProtocol) -> None:
        """Test GET TX_BATT_BARS when no transmitter connected."""
        response = protocol.handle_command("< GET 1 TX_BATT_BARS >")
        assert response == "< REP 1 TX_BATT_BARS 255 >"

    def test_get_tx_batt_bars_with_transmitter(self, device: MockDevice) -> None:
        """Test GET TX_BATT_BARS with transmitter connected."""
        device.channels[0].transmitter = MockTransmitter(battery_bars=4, connected=True)
        protocol = MockSlxdProtocol(device)
        response = protocol.handle_command("< GET 1 TX_BATT_BARS >")
        assert response == "< REP 1 TX_BATT_BARS 004 >"

    def test_get_tx_batt_mins_no_transmitter(self, protocol: MockSlxdProtocol) -> None:
        """Test GET TX_BATT_MINS when no transmitter connected."""
        response = protocol.handle_command("< GET 1 TX_BATT_MINS >")
        assert response == "< REP 1 TX_BATT_MINS 65535 >"

    def test_get_tx_batt_mins_with_transmitter(self, device: MockDevice) -> None:
        """Test GET TX_BATT_MINS with transmitter connected."""
        device.channels[0].transmitter = MockTransmitter(
            battery_minutes=240, connected=True
        )
        protocol = MockSlxdProtocol(device)
        response = protocol.handle_command("< GET 1 TX_BATT_MINS >")
        assert response == "< REP 1 TX_BATT_MINS 00240 >"


class TestProtocolSetCommands:
    """Tests for SET commands."""

    def test_set_audio_gain(self, protocol: MockSlxdProtocol, device: MockDevice) -> None:
        """Test SET AUDIO_GAIN command."""
        response = protocol.handle_command("< SET 1 AUDIO_GAIN 030 >")
        assert response == "< REP 1 AUDIO_GAIN 030 >"
        assert device.channels[0].audio_gain_raw == 30

    def test_set_audio_gain_invalid_value(self, protocol: MockSlxdProtocol) -> None:
        """Test SET AUDIO_GAIN with invalid value."""
        response = protocol.handle_command("< SET 1 AUDIO_GAIN 100 >")
        assert response is None

    def test_set_audio_out_lvl_mic(
        self, protocol: MockSlxdProtocol, device: MockDevice
    ) -> None:
        """Test SET AUDIO_OUT_LVL MIC command."""
        device.channels[0].audio_out_level = "LINE"
        response = protocol.handle_command("< SET 1 AUDIO_OUT_LVL MIC >")
        assert response == "< REP 1 AUDIO_OUT_LVL MIC >"
        assert device.channels[0].audio_out_level == "MIC"

    def test_set_audio_out_lvl_line(
        self, protocol: MockSlxdProtocol, device: MockDevice
    ) -> None:
        """Test SET AUDIO_OUT_LVL LINE command."""
        response = protocol.handle_command("< SET 1 AUDIO_OUT_LVL LINE >")
        assert response == "< REP 1 AUDIO_OUT_LVL LINE >"
        assert device.channels[0].audio_out_level == "LINE"

    def test_set_audio_out_lvl_invalid(self, protocol: MockSlxdProtocol) -> None:
        """Test SET AUDIO_OUT_LVL with invalid value."""
        response = protocol.handle_command("< SET 1 AUDIO_OUT_LVL INVALID >")
        assert response is None

    def test_set_chan_name(
        self, protocol: MockSlxdProtocol, device: MockDevice
    ) -> None:
        """Test SET CHAN_NAME command."""
        response = protocol.handle_command("< SET 1 CHAN_NAME LeadVox >")
        assert response is not None
        assert "REP 1 CHAN_NAME" in response
        assert "LeadVox" in response
        assert device.channels[0].name == "LeadVox"

    def test_set_chan_name_truncates_to_8_chars(
        self, protocol: MockSlxdProtocol, device: MockDevice
    ) -> None:
        """Test SET CHAN_NAME truncates to 8 characters."""
        response = protocol.handle_command("< SET 1 CHAN_NAME VeryLongName >")
        assert device.channels[0].name == "VeryLong"

    def test_set_flash_device(self, protocol: MockSlxdProtocol) -> None:
        """Test SET FLASH ON command (device level)."""
        response = protocol.handle_command("< SET FLASH ON >")
        assert response == "< REP FLASH ON >"

    def test_set_flash_channel(self, protocol: MockSlxdProtocol) -> None:
        """Test SET FLASH ON command (channel level)."""
        response = protocol.handle_command("< SET 1 FLASH ON >")
        assert response == "< REP 1 FLASH ON >"

    def test_set_lock_status(
        self, protocol: MockSlxdProtocol, device: MockDevice
    ) -> None:
        """Test SET LOCK_STATUS command."""
        response = protocol.handle_command("< SET LOCK_STATUS MENU >")
        assert response == "< REP LOCK_STATUS MENU >"
        assert device.lock_status == "MENU"

    def test_set_lock_status_invalid(self, protocol: MockSlxdProtocol) -> None:
        """Test SET LOCK_STATUS with invalid value."""
        response = protocol.handle_command("< SET LOCK_STATUS INVALID >")
        assert response is None

    def test_set_meter_rate(self, protocol: MockSlxdProtocol) -> None:
        """Test SET METER_RATE command."""
        response = protocol.handle_command("< SET 1 METER_RATE 01000 >")
        assert response == "< REP 1 METER_RATE 01000 >"


class TestProtocolInvalidCommands:
    """Tests for invalid command handling."""

    def test_empty_command(self, protocol: MockSlxdProtocol) -> None:
        """Test empty command returns None."""
        response = protocol.handle_command("")
        assert response is None

    def test_no_brackets(self, protocol: MockSlxdProtocol) -> None:
        """Test command without brackets returns None."""
        response = protocol.handle_command("GET MODEL")
        assert response is None

    def test_missing_close_bracket(self, protocol: MockSlxdProtocol) -> None:
        """Test command missing close bracket returns None."""
        response = protocol.handle_command("< GET MODEL")
        assert response is None

    def test_empty_brackets(self, protocol: MockSlxdProtocol) -> None:
        """Test empty brackets returns None."""
        response = protocol.handle_command("< >")
        assert response is None

    def test_unknown_command_type(self, protocol: MockSlxdProtocol) -> None:
        """Test unknown command type returns None."""
        response = protocol.handle_command("< UNKNOWN MODEL >")
        assert response is None

    def test_unknown_property(self, protocol: MockSlxdProtocol) -> None:
        """Test unknown property returns None."""
        response = protocol.handle_command("< GET UNKNOWN_PROP >")
        assert response is None


class TestProtocolSampleGeneration:
    """Tests for SAMPLE metering response generation."""

    def test_generate_sample(self, protocol: MockSlxdProtocol, device: MockDevice) -> None:
        """Test SAMPLE generation."""
        device.channels[0].audio_peak_raw = 100
        device.channels[0].audio_rms_raw = 90
        device.channels[0].rssi_a1_raw = 80
        device.channels[0].rssi_a2_raw = 75

        sample = protocol.generate_sample(1)
        assert sample is not None
        assert "SAMPLE 1 ALL" in sample
        assert "100" in sample
        assert "090" in sample
        assert "080" in sample
        assert "075" in sample

    def test_generate_sample_invalid_channel(
        self, protocol: MockSlxdProtocol
    ) -> None:
        """Test SAMPLE generation for invalid channel returns None."""
        sample = protocol.generate_sample(5)
        assert sample is None

    def test_generate_sample_antenna_selection(
        self, protocol: MockSlxdProtocol, device: MockDevice
    ) -> None:
        """Test SAMPLE indicates active antenna (higher RSSI)."""
        device.channels[0].rssi_a1_raw = 80
        device.channels[0].rssi_a2_raw = 90

        sample = protocol.generate_sample(1)
        assert sample is not None
        # Antenna 2 has higher RSSI
        assert sample.endswith("2 >")


class TestProtocolCaseSensitivity:
    """Tests for command case handling."""

    def test_lowercase_command_type(self, protocol: MockSlxdProtocol) -> None:
        """Test lowercase command type is handled."""
        response = protocol.handle_command("< get MODEL >")
        assert response is not None
        assert "REP MODEL" in response

    def test_lowercase_property(self, protocol: MockSlxdProtocol) -> None:
        """Test lowercase property is handled."""
        response = protocol.handle_command("< GET model >")
        assert response is not None
        assert "REP MODEL" in response

    def test_mixed_case(self, protocol: MockSlxdProtocol) -> None:
        """Test mixed case is handled."""
        response = protocol.handle_command("< Get Model >")
        assert response is not None
        assert "REP MODEL" in response
