"""Data models for Shure SLX-D devices.

This module contains dataclasses representing the state of SLX-D receivers,
channels, and transmitters.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class LockStatus(Enum):
    """Transmitter lock status."""

    OFF = "OFF"
    MENU = "MENU"
    ALL = "ALL"


class AudioOutputLevel(Enum):
    """Audio output level setting."""

    MIC = "MIC"
    LINE = "LINE"


class TransmitterModel(Enum):
    """Transmitter model types."""

    SLXD1 = "SLXD1"  # Bodypack transmitter
    SLXD2 = "SLXD2"  # Handheld transmitter
    UNKNOWN = "UNKNOWN"


class BatteryStatus(Enum):
    """Battery status levels."""

    NORMAL = "normal"
    LOW = "low"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class SlxdTransmitter:
    """Transmitter data model.

    Represents the state of a wireless transmitter (bodypack or handheld)
    linked to a receiver channel.

    Attributes:
        model: Transmitter model type (SLXD1, SLXD2, or UNKNOWN)
        battery_bars: Battery level in bars (0-5) or None if unknown
        battery_minutes: Estimated minutes remaining or None if unknown
    """

    model: TransmitterModel
    battery_bars: int | None
    battery_minutes: int | None

    @property
    def battery_percentage(self) -> int | None:
        """Calculate battery percentage from bars.

        Returns:
            Percentage (0-100) or None if battery_bars is unknown
        """
        if self.battery_bars is None:
            return None
        return self.battery_bars * 20  # 0=0%, 1=20%, ..., 5=100%

    @property
    def battery_status(self) -> BatteryStatus:
        """Get battery status based on bars.

        Returns:
            BatteryStatus enum value indicating current battery state
        """
        if self.battery_bars is None:
            return BatteryStatus.UNKNOWN
        if self.battery_bars == 0:
            return BatteryStatus.CRITICAL
        if self.battery_bars == 1:
            return BatteryStatus.LOW
        return BatteryStatus.NORMAL


@dataclass
class SlxdChannel:
    """Channel data model.

    Represents a single receiver channel with its current state including
    audio levels, RF signal, and linked transmitter.

    Attributes:
        number: Channel number (1-4)
        name: Channel name (up to 8 characters settable, 31 reported)
        frequency_khz: Operating frequency in kHz
        group_channel: Group/channel preset (e.g., "1,1")
        audio_gain_db: Audio gain in dB (-18 to +42)
        audio_out_level: Audio output level (MIC or LINE)
        audio_peak_dbfs: Peak audio level in dBFS (-120 to 0)
        audio_rms_dbfs: RMS audio level in dBFS (-120 to 0)
        rssi_antenna_1_dbm: RSSI for antenna 1 in dBm (-120 to 0)
        rssi_antenna_2_dbm: RSSI for antenna 2 in dBm (-120 to 0)
        transmitter: Linked transmitter or None if not receiving
    """

    number: int
    name: str
    frequency_khz: int
    group_channel: str
    audio_gain_db: int
    audio_out_level: AudioOutputLevel
    audio_peak_dbfs: float
    audio_rms_dbfs: float
    rssi_antenna_1_dbm: int
    rssi_antenna_2_dbm: int
    transmitter: SlxdTransmitter | None

    @property
    def frequency_mhz(self) -> float:
        """Get frequency in MHz.

        Returns:
            Frequency converted from kHz to MHz
        """
        return self.frequency_khz / 1000.0

    @property
    def is_active(self) -> bool:
        """Check if channel has active transmitter.

        Returns:
            True if a transmitter is linked to this channel
        """
        return self.transmitter is not None

    @property
    def best_rssi(self) -> int:
        """Get the best (strongest) RSSI value.

        The SLX-D uses diversity reception with two antennas.
        This returns the stronger signal (less negative = stronger).

        Returns:
            The higher (less negative) RSSI value in dBm
        """
        return max(self.rssi_antenna_1_dbm, self.rssi_antenna_2_dbm)


@dataclass
class SlxdDevice:
    """Device data model.

    Represents an SLX-D receiver with its current state and channels.

    Attributes:
        model: Device model (SLXD4, SLXD4D, SLXD4Q+)
        device_id: 8-character device identifier
        firmware_version: Firmware version string
        rf_band: RF frequency band (e.g., "G55")
        lock_status: Transmitter lock setting
        channels: List of channel states
    """

    model: str
    device_id: str
    firmware_version: str
    rf_band: str
    lock_status: LockStatus
    channels: list[SlxdChannel]

    @property
    def channel_count(self) -> int:
        """Get number of channels based on model.

        Returns:
            1 for SLXD4, 2 for SLXD4D, 4 for SLXD4Q+
        """
        if "Q" in self.model:
            return 4
        # Check for "4D" suffix to distinguish SLXD4D from SLXD4
        if self.model.endswith("D") or "4D" in self.model:
            return 2
        return 1

    @property
    def is_dual_channel(self) -> bool:
        """Check if device is dual-channel.

        Returns:
            True if device is SLXD4D
        """
        return self.channel_count == 2

    @property
    def is_quad_channel(self) -> bool:
        """Check if device is quad-channel.

        Returns:
            True if device is SLXD4Q+
        """
        return self.channel_count == 4

    def get_channel(self, number: int) -> SlxdChannel | None:
        """Get channel by number.

        Args:
            number: Channel number (1-based)

        Returns:
            SlxdChannel if found, None otherwise
        """
        for channel in self.channels:
            if channel.number == number:
                return channel
        return None
