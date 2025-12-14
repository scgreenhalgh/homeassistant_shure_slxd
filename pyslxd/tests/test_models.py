"""Tests for pyslxd data models.

TDD RED PHASE: These tests define the expected behavior of the models module.
Run these tests to see them fail, then implement models.py to make them pass.
"""

import pytest

from pyslxd.models import (
    SlxdDevice,
    SlxdChannel,
    SlxdTransmitter,
    BatteryStatus,
    LockStatus,
    AudioOutputLevel,
    TransmitterModel,
)


class TestSlxdTransmitter:
    """Tests for SlxdTransmitter dataclass."""

    def test_create_transmitter_with_valid_data(self) -> None:
        """Test creating a transmitter with valid data."""
        # Arrange / Act
        tx = SlxdTransmitter(
            model=TransmitterModel.SLXD2,
            battery_bars=4,
            battery_minutes=125,
        )

        # Assert
        assert tx.model == TransmitterModel.SLXD2
        assert tx.battery_bars == 4
        assert tx.battery_minutes == 125

    def test_transmitter_battery_percentage(self) -> None:
        """Test battery percentage calculation."""
        tx = SlxdTransmitter(
            model=TransmitterModel.SLXD2,
            battery_bars=4,
            battery_minutes=125,
        )
        assert tx.battery_percentage == 80  # 4 bars = 80%

    def test_transmitter_battery_percentage_full(self) -> None:
        """Test battery percentage at full."""
        tx = SlxdTransmitter(
            model=TransmitterModel.SLXD2,
            battery_bars=5,
            battery_minutes=300,
        )
        assert tx.battery_percentage == 100

    def test_transmitter_battery_percentage_unknown(self) -> None:
        """Test battery percentage when unknown."""
        tx = SlxdTransmitter(
            model=TransmitterModel.SLXD2,
            battery_bars=None,
            battery_minutes=None,
        )
        assert tx.battery_percentage is None

    def test_transmitter_unknown_model(self) -> None:
        """Test transmitter with unknown model."""
        tx = SlxdTransmitter(
            model=TransmitterModel.UNKNOWN,
            battery_bars=None,
            battery_minutes=None,
        )
        assert tx.model == TransmitterModel.UNKNOWN

    def test_transmitter_battery_status_normal(self) -> None:
        """Test battery status for normal operation."""
        tx = SlxdTransmitter(
            model=TransmitterModel.SLXD1,
            battery_bars=3,
            battery_minutes=90,
        )
        assert tx.battery_status == BatteryStatus.NORMAL

    def test_transmitter_battery_status_low(self) -> None:
        """Test battery status when low (1 bar)."""
        tx = SlxdTransmitter(
            model=TransmitterModel.SLXD1,
            battery_bars=1,
            battery_minutes=20,
        )
        assert tx.battery_status == BatteryStatus.LOW

    def test_transmitter_battery_status_critical(self) -> None:
        """Test battery status when critical (0 bars)."""
        tx = SlxdTransmitter(
            model=TransmitterModel.SLXD1,
            battery_bars=0,
            battery_minutes=5,
        )
        assert tx.battery_status == BatteryStatus.CRITICAL

    def test_transmitter_battery_status_unknown(self) -> None:
        """Test battery status when unknown."""
        tx = SlxdTransmitter(
            model=TransmitterModel.SLXD1,
            battery_bars=None,
            battery_minutes=None,
        )
        assert tx.battery_status == BatteryStatus.UNKNOWN


class TestSlxdChannel:
    """Tests for SlxdChannel dataclass."""

    def test_create_channel_with_valid_data(self) -> None:
        """Test creating a channel with valid data."""
        # Arrange
        tx = SlxdTransmitter(
            model=TransmitterModel.SLXD2,
            battery_bars=4,
            battery_minutes=125,
        )

        # Act
        channel = SlxdChannel(
            number=1,
            name="Lead Vox",
            frequency_khz=578350,
            group_channel="1,1",
            audio_gain_db=12,
            audio_out_level=AudioOutputLevel.MIC,
            audio_peak_dbfs=-18.0,
            audio_rms_dbfs=-25.0,
            rssi_antenna_1_dbm=-37,
            rssi_antenna_2_dbm=-42,
            transmitter=tx,
        )

        # Assert
        assert channel.number == 1
        assert channel.name == "Lead Vox"
        assert channel.frequency_khz == 578350
        assert channel.audio_gain_db == 12
        assert channel.transmitter.model == TransmitterModel.SLXD2

    def test_channel_frequency_mhz(self) -> None:
        """Test frequency conversion to MHz."""
        channel = SlxdChannel(
            number=1,
            name="Test",
            frequency_khz=578350,
            group_channel="1,1",
            audio_gain_db=0,
            audio_out_level=AudioOutputLevel.MIC,
            audio_peak_dbfs=-20.0,
            audio_rms_dbfs=-25.0,
            rssi_antenna_1_dbm=-40,
            rssi_antenna_2_dbm=-45,
            transmitter=None,
        )
        assert channel.frequency_mhz == 578.350

    def test_channel_without_transmitter(self) -> None:
        """Test channel when no transmitter is linked."""
        channel = SlxdChannel(
            number=2,
            name="Backup",
            frequency_khz=600000,
            group_channel="2,1",
            audio_gain_db=0,
            audio_out_level=AudioOutputLevel.LINE,
            audio_peak_dbfs=-120.0,
            audio_rms_dbfs=-120.0,
            rssi_antenna_1_dbm=-120,
            rssi_antenna_2_dbm=-120,
            transmitter=None,
        )
        assert channel.transmitter is None
        assert channel.is_active is False

    def test_channel_is_active_when_transmitter_linked(self) -> None:
        """Test is_active when transmitter is linked."""
        tx = SlxdTransmitter(
            model=TransmitterModel.SLXD2,
            battery_bars=4,
            battery_minutes=125,
        )
        channel = SlxdChannel(
            number=1,
            name="Active",
            frequency_khz=578350,
            group_channel="1,1",
            audio_gain_db=12,
            audio_out_level=AudioOutputLevel.MIC,
            audio_peak_dbfs=-18.0,
            audio_rms_dbfs=-25.0,
            rssi_antenna_1_dbm=-37,
            rssi_antenna_2_dbm=-42,
            transmitter=tx,
        )
        assert channel.is_active is True

    def test_channel_best_rssi(self) -> None:
        """Test best_rssi returns the stronger signal."""
        channel = SlxdChannel(
            number=1,
            name="Test",
            frequency_khz=578350,
            group_channel="1,1",
            audio_gain_db=0,
            audio_out_level=AudioOutputLevel.MIC,
            audio_peak_dbfs=-20.0,
            audio_rms_dbfs=-25.0,
            rssi_antenna_1_dbm=-37,  # Stronger
            rssi_antenna_2_dbm=-42,  # Weaker
            transmitter=None,
        )
        assert channel.best_rssi == -37


class TestSlxdDevice:
    """Tests for SlxdDevice dataclass."""

    def test_create_device_with_valid_data(self) -> None:
        """Test creating a device with valid data."""
        # Arrange / Act
        device = SlxdDevice(
            model="SLXD4D",
            device_id="SLXD4D01",
            firmware_version="2.0.15.2",
            rf_band="G55",
            lock_status=LockStatus.ALL,
            channels=[],
        )

        # Assert
        assert device.model == "SLXD4D"
        assert device.device_id == "SLXD4D01"
        assert device.firmware_version == "2.0.15.2"
        assert device.rf_band == "G55"
        assert device.lock_status == LockStatus.ALL

    def test_device_channel_count_single(self) -> None:
        """Test channel_count for single-channel receiver."""
        device = SlxdDevice(
            model="SLXD4",
            device_id="SLXD4001",
            firmware_version="2.0.15.2",
            rf_band="G55",
            lock_status=LockStatus.OFF,
            channels=[],
        )
        assert device.channel_count == 1

    def test_device_channel_count_dual(self) -> None:
        """Test channel_count for dual-channel receiver."""
        device = SlxdDevice(
            model="SLXD4D",
            device_id="SLXD4D01",
            firmware_version="2.0.15.2",
            rf_band="G55",
            lock_status=LockStatus.OFF,
            channels=[],
        )
        assert device.channel_count == 2

    def test_device_channel_count_quad(self) -> None:
        """Test channel_count for quad-channel receiver."""
        device = SlxdDevice(
            model="SLXD4Q+",
            device_id="SLXD4Q01",
            firmware_version="2.0.15.2",
            rf_band="G55",
            lock_status=LockStatus.OFF,
            channels=[],
        )
        assert device.channel_count == 4

    def test_device_is_dual_channel(self) -> None:
        """Test is_dual_channel property."""
        device = SlxdDevice(
            model="SLXD4D",
            device_id="SLXD4D01",
            firmware_version="2.0.15.2",
            rf_band="G55",
            lock_status=LockStatus.OFF,
            channels=[],
        )
        assert device.is_dual_channel is True

    def test_device_is_quad_channel(self) -> None:
        """Test is_quad_channel property."""
        device = SlxdDevice(
            model="SLXD4Q+",
            device_id="SLXD4Q01",
            firmware_version="2.0.15.2",
            rf_band="G55",
            lock_status=LockStatus.OFF,
            channels=[],
        )
        assert device.is_quad_channel is True

    def test_device_with_channels(self) -> None:
        """Test device with populated channels list."""
        tx1 = SlxdTransmitter(
            model=TransmitterModel.SLXD2,
            battery_bars=4,
            battery_minutes=125,
        )
        ch1 = SlxdChannel(
            number=1,
            name="Lead",
            frequency_khz=578350,
            group_channel="1,1",
            audio_gain_db=12,
            audio_out_level=AudioOutputLevel.MIC,
            audio_peak_dbfs=-18.0,
            audio_rms_dbfs=-25.0,
            rssi_antenna_1_dbm=-37,
            rssi_antenna_2_dbm=-42,
            transmitter=tx1,
        )
        ch2 = SlxdChannel(
            number=2,
            name="Backup",
            frequency_khz=580000,
            group_channel="1,2",
            audio_gain_db=0,
            audio_out_level=AudioOutputLevel.MIC,
            audio_peak_dbfs=-120.0,
            audio_rms_dbfs=-120.0,
            rssi_antenna_1_dbm=-120,
            rssi_antenna_2_dbm=-120,
            transmitter=None,
        )

        device = SlxdDevice(
            model="SLXD4D",
            device_id="SLXD4D01",
            firmware_version="2.0.15.2",
            rf_band="G55",
            lock_status=LockStatus.ALL,
            channels=[ch1, ch2],
        )

        assert len(device.channels) == 2
        assert device.channels[0].name == "Lead"
        assert device.channels[1].transmitter is None

    def test_device_get_channel_by_number(self) -> None:
        """Test getting a channel by number."""
        ch1 = SlxdChannel(
            number=1,
            name="Lead",
            frequency_khz=578350,
            group_channel="1,1",
            audio_gain_db=12,
            audio_out_level=AudioOutputLevel.MIC,
            audio_peak_dbfs=-18.0,
            audio_rms_dbfs=-25.0,
            rssi_antenna_1_dbm=-37,
            rssi_antenna_2_dbm=-42,
            transmitter=None,
        )

        device = SlxdDevice(
            model="SLXD4D",
            device_id="SLXD4D01",
            firmware_version="2.0.15.2",
            rf_band="G55",
            lock_status=LockStatus.ALL,
            channels=[ch1],
        )

        assert device.get_channel(1) == ch1
        assert device.get_channel(2) is None


class TestEnums:
    """Tests for enum classes."""

    def test_lock_status_values(self) -> None:
        """Test LockStatus enum values."""
        assert LockStatus.OFF.value == "OFF"
        assert LockStatus.MENU.value == "MENU"
        assert LockStatus.ALL.value == "ALL"

    def test_audio_output_level_values(self) -> None:
        """Test AudioOutputLevel enum values."""
        assert AudioOutputLevel.MIC.value == "MIC"
        assert AudioOutputLevel.LINE.value == "LINE"

    def test_transmitter_model_values(self) -> None:
        """Test TransmitterModel enum values."""
        assert TransmitterModel.SLXD1.value == "SLXD1"
        assert TransmitterModel.SLXD2.value == "SLXD2"
        assert TransmitterModel.UNKNOWN.value == "UNKNOWN"

    def test_battery_status_values(self) -> None:
        """Test BatteryStatus enum values."""
        assert BatteryStatus.NORMAL.value == "normal"
        assert BatteryStatus.LOW.value == "low"
        assert BatteryStatus.CRITICAL.value == "critical"
        assert BatteryStatus.UNKNOWN.value == "unknown"
