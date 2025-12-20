"""State models for mock SLX-D server.

These dataclasses represent the internal state of a simulated SLX-D receiver.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class MockTransmitter:
    """Simulated transmitter state.

    Attributes:
        model: Transmitter model (SLXD1, SLXD2, UNKNOWN)
        connected: Whether transmitter is currently connected
        battery_bars: Battery level in bars (0-5), 255=unknown
        battery_minutes: Estimated minutes remaining, 65534=calculating, 65535=unknown
        encryption: Whether encryption is enabled
    """

    model: str = "SLXD2"
    connected: bool = True
    battery_bars: int = 5
    battery_minutes: int = 480
    encryption: bool = False

    def __post_init__(self) -> None:
        """Validate transmitter state."""
        if self.model not in ("SLXD1", "SLXD2", "UNKNOWN"):
            raise ValueError(f"Invalid transmitter model: {self.model}")
        if not (0 <= self.battery_bars <= 5 or self.battery_bars == 255):
            raise ValueError(f"Invalid battery_bars: {self.battery_bars}")


@dataclass
class MockChannel:
    """Simulated channel state.

    Attributes:
        number: Channel number (1-4)
        name: Channel name (up to 8 characters settable, 31 reported with padding)
        frequency_khz: Operating frequency in kHz
        group_channel: Group/channel preset (e.g., "1,1")
        audio_gain_raw: Raw audio gain value (0-60, maps to -18 to +42 dB)
        audio_out_level: Audio output level ("MIC" or "LINE")
        audio_peak_raw: Raw peak audio level (0-120, maps to -120 to 0 dBFS)
        audio_rms_raw: Raw RMS audio level (0-120)
        rssi_a1_raw: Raw RSSI for antenna 1 (0-120, maps to -120 to 0 dBm)
        rssi_a2_raw: Raw RSSI for antenna 2 (0-120)
        transmitter: Linked transmitter or None if not receiving
    """

    number: int
    name: str = ""
    frequency_khz: int = 578350
    group_channel: str = "1,1"
    audio_gain_raw: int = 18  # 0 dB (18 - 18 = 0)
    audio_out_level: str = "MIC"
    audio_peak_raw: int = 0
    audio_rms_raw: int = 0
    rssi_a1_raw: int = 0
    rssi_a2_raw: int = 0
    transmitter: MockTransmitter | None = None

    def __post_init__(self) -> None:
        """Initialize default name and validate state."""
        if not self.name:
            self.name = f"CH {self.number}"
        if not 1 <= self.number <= 4:
            raise ValueError(f"Invalid channel number: {self.number}")
        if not 0 <= self.audio_gain_raw <= 60:
            raise ValueError(f"Invalid audio_gain_raw: {self.audio_gain_raw}")
        if self.audio_out_level not in ("MIC", "LINE"):
            raise ValueError(f"Invalid audio_out_level: {self.audio_out_level}")


@dataclass
class MockDevice:
    """Simulated SLX-D receiver state.

    Attributes:
        model: Device model (SLXD4, SLXD4D, SLXD4Q+)
        device_id: 8-character device identifier
        firmware_version: Firmware version string
        rf_band: RF frequency band (e.g., "G55", "H55", "J52")
        lock_status: Front panel lock status ("OFF", "MENU", "ALL")
        channels: List of channel states
    """

    model: str = "SLXD4D"
    device_id: str = "2C2A3F01"
    firmware_version: str = "2.0.15.2"
    rf_band: str = "G55"
    lock_status: str = "OFF"
    channels: list[MockChannel] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Initialize channels based on model if not provided."""
        if self.lock_status not in ("OFF", "MENU", "ALL"):
            raise ValueError(f"Invalid lock_status: {self.lock_status}")

        if not self.channels:
            num_channels = self._get_channel_count()
            self.channels = [
                MockChannel(
                    number=i + 1,
                    name=f"CH {i + 1}",
                    frequency_khz=578350 + (i * 250),  # Slightly different frequencies
                )
                for i in range(num_channels)
            ]

    def _get_channel_count(self) -> int:
        """Get number of channels based on model."""
        if "Q" in self.model:
            return 4
        if self.model.endswith("D") or "4D" in self.model:
            return 2
        return 1

    def get_channel(self, number: int) -> MockChannel | None:
        """Get channel by number.

        Args:
            number: Channel number (1-based)

        Returns:
            MockChannel if found, None otherwise
        """
        for channel in self.channels:
            if channel.number == number:
                return channel
        return None

    @property
    def channel_count(self) -> int:
        """Get number of channels."""
        return len(self.channels)
