"""Tests for mock server state models."""

from __future__ import annotations

import pytest

from pyslxd.mock.state import MockChannel, MockDevice, MockTransmitter


class TestMockTransmitter:
    """Tests for MockTransmitter dataclass."""

    def test_default_values(self) -> None:
        """Test default transmitter values."""
        tx = MockTransmitter()
        assert tx.model == "SLXD2"
        assert tx.connected is True
        assert tx.battery_bars == 5
        assert tx.battery_minutes == 480
        assert tx.encryption is False

    def test_custom_values(self) -> None:
        """Test custom transmitter values."""
        tx = MockTransmitter(
            model="SLXD1",
            connected=False,
            battery_bars=3,
            battery_minutes=240,
            encryption=True,
        )
        assert tx.model == "SLXD1"
        assert tx.connected is False
        assert tx.battery_bars == 3
        assert tx.battery_minutes == 240
        assert tx.encryption is True

    def test_invalid_model_raises_error(self) -> None:
        """Test that invalid model raises ValueError."""
        with pytest.raises(ValueError, match="Invalid transmitter model"):
            MockTransmitter(model="INVALID")

    def test_valid_models(self) -> None:
        """Test all valid model types."""
        for model in ("SLXD1", "SLXD2", "UNKNOWN"):
            tx = MockTransmitter(model=model)
            assert tx.model == model

    def test_invalid_battery_bars_raises_error(self) -> None:
        """Test that invalid battery_bars raises ValueError."""
        with pytest.raises(ValueError, match="Invalid battery_bars"):
            MockTransmitter(battery_bars=10)

    def test_battery_bars_unknown_value(self) -> None:
        """Test that 255 is valid for unknown battery."""
        tx = MockTransmitter(battery_bars=255)
        assert tx.battery_bars == 255


class TestMockChannel:
    """Tests for MockChannel dataclass."""

    def test_default_values(self) -> None:
        """Test default channel values."""
        ch = MockChannel(number=1)
        assert ch.number == 1
        assert ch.name == "CH 1"
        assert ch.frequency_khz == 578350
        assert ch.group_channel == "1,1"
        assert ch.audio_gain_raw == 18
        assert ch.audio_out_level == "MIC"
        assert ch.audio_peak_raw == 0
        assert ch.audio_rms_raw == 0
        assert ch.rssi_a1_raw == 0
        assert ch.rssi_a2_raw == 0
        assert ch.transmitter is None

    def test_custom_name(self) -> None:
        """Test custom channel name."""
        ch = MockChannel(number=2, name="Lead Vox")
        assert ch.name == "Lead Vox"

    def test_default_name_based_on_number(self) -> None:
        """Test default name is based on channel number."""
        ch = MockChannel(number=3)
        assert ch.name == "CH 3"

    def test_with_transmitter(self) -> None:
        """Test channel with transmitter attached."""
        tx = MockTransmitter(model="SLXD1", battery_bars=4)
        ch = MockChannel(number=1, transmitter=tx)
        assert ch.transmitter is not None
        assert ch.transmitter.model == "SLXD1"
        assert ch.transmitter.battery_bars == 4

    def test_invalid_channel_number_too_low(self) -> None:
        """Test that channel number 0 raises ValueError."""
        with pytest.raises(ValueError, match="Invalid channel number"):
            MockChannel(number=0)

    def test_invalid_channel_number_too_high(self) -> None:
        """Test that channel number 5 raises ValueError."""
        with pytest.raises(ValueError, match="Invalid channel number"):
            MockChannel(number=5)

    def test_invalid_audio_gain_raw(self) -> None:
        """Test that invalid audio_gain_raw raises ValueError."""
        with pytest.raises(ValueError, match="Invalid audio_gain_raw"):
            MockChannel(number=1, audio_gain_raw=100)

    def test_invalid_audio_out_level(self) -> None:
        """Test that invalid audio_out_level raises ValueError."""
        with pytest.raises(ValueError, match="Invalid audio_out_level"):
            MockChannel(number=1, audio_out_level="INVALID")


class TestMockDevice:
    """Tests for MockDevice dataclass."""

    def test_default_values(self) -> None:
        """Test default device values."""
        device = MockDevice()
        assert device.model == "SLXD4D"
        assert device.device_id == "2C2A3F01"
        assert device.firmware_version == "2.0.15.2"
        assert device.rf_band == "G55"
        assert device.lock_status == "OFF"
        assert len(device.channels) == 2  # SLXD4D has 2 channels

    def test_slxd4_single_channel(self) -> None:
        """Test SLXD4 creates 1 channel."""
        device = MockDevice(model="SLXD4")
        assert device.channel_count == 1
        assert len(device.channels) == 1
        assert device.channels[0].number == 1

    def test_slxd4d_dual_channel(self) -> None:
        """Test SLXD4D creates 2 channels."""
        device = MockDevice(model="SLXD4D")
        assert device.channel_count == 2
        assert len(device.channels) == 2
        assert device.channels[0].number == 1
        assert device.channels[1].number == 2

    def test_slxd4q_quad_channel(self) -> None:
        """Test SLXD4Q+ creates 4 channels."""
        device = MockDevice(model="SLXD4Q+")
        assert device.channel_count == 4
        assert len(device.channels) == 4
        for i in range(4):
            assert device.channels[i].number == i + 1

    def test_custom_channels(self) -> None:
        """Test providing custom channels."""
        channels = [
            MockChannel(number=1, name="Custom1"),
            MockChannel(number=2, name="Custom2"),
        ]
        device = MockDevice(channels=channels)
        assert device.channels[0].name == "Custom1"
        assert device.channels[1].name == "Custom2"

    def test_get_channel_exists(self) -> None:
        """Test get_channel returns channel when exists."""
        device = MockDevice()
        ch = device.get_channel(1)
        assert ch is not None
        assert ch.number == 1

    def test_get_channel_not_exists(self) -> None:
        """Test get_channel returns None when not exists."""
        device = MockDevice(model="SLXD4")  # Single channel
        ch = device.get_channel(2)
        assert ch is None

    def test_invalid_lock_status_raises_error(self) -> None:
        """Test that invalid lock_status raises ValueError."""
        with pytest.raises(ValueError, match="Invalid lock_status"):
            MockDevice(lock_status="INVALID")

    def test_valid_lock_statuses(self) -> None:
        """Test all valid lock status values."""
        for status in ("OFF", "MENU", "ALL"):
            device = MockDevice(lock_status=status)
            assert device.lock_status == status

    def test_channels_have_different_frequencies(self) -> None:
        """Test that auto-created channels have different frequencies."""
        device = MockDevice(model="SLXD4D")
        assert device.channels[0].frequency_khz != device.channels[1].frequency_khz
