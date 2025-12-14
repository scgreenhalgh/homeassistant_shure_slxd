"""Data models for Shure SLX-D devices.

Stub file for TDD RED phase - tests are written, implementation pending.
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

    SLXD1 = "SLXD1"
    SLXD2 = "SLXD2"
    UNKNOWN = "UNKNOWN"


class BatteryStatus(Enum):
    """Battery status levels."""

    NORMAL = "normal"
    LOW = "low"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class SlxdTransmitter:
    """Transmitter data model - stub for TDD."""

    model: TransmitterModel
    battery_bars: int | None
    battery_minutes: int | None

    @property
    def battery_percentage(self) -> int | None:
        """Calculate battery percentage from bars."""
        raise NotImplementedError("TDD RED phase")

    @property
    def battery_status(self) -> BatteryStatus:
        """Get battery status based on bars."""
        raise NotImplementedError("TDD RED phase")


@dataclass
class SlxdChannel:
    """Channel data model - stub for TDD."""

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
        """Get frequency in MHz."""
        raise NotImplementedError("TDD RED phase")

    @property
    def is_active(self) -> bool:
        """Check if channel has active transmitter."""
        raise NotImplementedError("TDD RED phase")

    @property
    def best_rssi(self) -> int:
        """Get the best (strongest) RSSI value."""
        raise NotImplementedError("TDD RED phase")


@dataclass
class SlxdDevice:
    """Device data model - stub for TDD."""

    model: str
    device_id: str
    firmware_version: str
    rf_band: str
    lock_status: LockStatus
    channels: list[SlxdChannel]

    @property
    def channel_count(self) -> int:
        """Get number of channels based on model."""
        raise NotImplementedError("TDD RED phase")

    @property
    def is_dual_channel(self) -> bool:
        """Check if device is dual-channel."""
        raise NotImplementedError("TDD RED phase")

    @property
    def is_quad_channel(self) -> bool:
        """Check if device is quad-channel."""
        raise NotImplementedError("TDD RED phase")

    def get_channel(self, number: int) -> SlxdChannel | None:
        """Get channel by number."""
        raise NotImplementedError("TDD RED phase")
