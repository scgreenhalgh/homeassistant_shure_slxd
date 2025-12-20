"""Integration tests for protocol compliance with mock server."""

from __future__ import annotations

import pytest

from pyslxd.client import SlxdClient
from pyslxd.mock.server import MockSlxdServer


class TestDeviceInfoRetrieval:
    """Tests for retrieving device information."""

    @pytest.mark.asyncio
    async def test_get_model(self, connected_client: SlxdClient) -> None:
        """Test getting device model."""
        model = await connected_client.get_model()
        assert model == "SLXD4D"

    @pytest.mark.asyncio
    async def test_get_model_slxd4(self, connected_client_slxd4: SlxdClient) -> None:
        """Test getting SLXD4 model."""
        model = await connected_client_slxd4.get_model()
        assert model == "SLXD4"

    @pytest.mark.asyncio
    async def test_get_model_slxd4q(self, connected_client_slxd4q: SlxdClient) -> None:
        """Test getting SLXD4Q+ model."""
        model = await connected_client_slxd4q.get_model()
        assert model == "SLXD4Q+"

    @pytest.mark.asyncio
    async def test_get_device_id(self, connected_client: SlxdClient) -> None:
        """Test getting device ID."""
        device_id = await connected_client.get_device_id()
        assert device_id == "2C2A3F01"

    @pytest.mark.asyncio
    async def test_get_firmware_version(self, connected_client: SlxdClient) -> None:
        """Test getting firmware version."""
        fw_ver = await connected_client.get_firmware_version()
        assert fw_ver == "2.0.15.2"

    @pytest.mark.asyncio
    async def test_get_rf_band(self, connected_client: SlxdClient) -> None:
        """Test getting RF band."""
        rf_band = await connected_client.get_rf_band()
        assert rf_band == "G55"

    @pytest.mark.asyncio
    async def test_get_lock_status(self, connected_client: SlxdClient) -> None:
        """Test getting lock status."""
        lock_status = await connected_client.get_lock_status()
        assert lock_status == "OFF"


class TestChannelInfoRetrieval:
    """Tests for retrieving channel information."""

    @pytest.mark.asyncio
    async def test_get_channel_name(self, connected_client: SlxdClient) -> None:
        """Test getting channel name."""
        name = await connected_client.get_channel_name(1)
        assert name == "CH 1"

    @pytest.mark.asyncio
    async def test_get_channel_name_channel_2(
        self, connected_client: SlxdClient
    ) -> None:
        """Test getting channel 2 name."""
        name = await connected_client.get_channel_name(2)
        assert name == "CH 2"

    @pytest.mark.asyncio
    async def test_get_audio_gain(self, connected_client: SlxdClient) -> None:
        """Test getting audio gain (converted from raw)."""
        gain = await connected_client.get_audio_gain(1)
        # Default raw is 18, converted = 18 - 18 = 0 dB
        assert gain == 0

    @pytest.mark.asyncio
    async def test_get_frequency(self, connected_client: SlxdClient) -> None:
        """Test getting frequency in kHz."""
        freq = await connected_client.get_frequency(1)
        assert freq == 578350

    @pytest.mark.asyncio
    async def test_get_group_channel(self, connected_client: SlxdClient) -> None:
        """Test getting group/channel preset."""
        group_chan = await connected_client.get_group_channel(1)
        assert group_chan == "1,1"

    @pytest.mark.asyncio
    async def test_get_audio_level_peak(self, connected_client: SlxdClient) -> None:
        """Test getting peak audio level in dBFS."""
        # Default raw is 0, converted = 0 - 120 = -120 dBFS
        level = await connected_client.get_audio_level_peak(1)
        assert level == -120

    @pytest.mark.asyncio
    async def test_get_audio_level_rms(self, connected_client: SlxdClient) -> None:
        """Test getting RMS audio level in dBFS."""
        level = await connected_client.get_audio_level_rms(1)
        assert level == -120

    @pytest.mark.asyncio
    async def test_get_rssi_antenna_1(self, connected_client: SlxdClient) -> None:
        """Test getting RSSI for antenna 1 in dBm."""
        # Default raw is 0, converted = 0 - 120 = -120 dBm
        rssi = await connected_client.get_rssi(1, antenna=1)
        assert rssi == -120

    @pytest.mark.asyncio
    async def test_get_rssi_antenna_2(self, connected_client: SlxdClient) -> None:
        """Test getting RSSI for antenna 2 in dBm."""
        rssi = await connected_client.get_rssi(1, antenna=2)
        assert rssi == -120

    @pytest.mark.asyncio
    async def test_get_audio_out_level(self, connected_client: SlxdClient) -> None:
        """Test getting audio output level."""
        level = await connected_client.get_audio_out_level(1)
        assert level == "MIC"


class TestTransmitterInfoRetrieval:
    """Tests for retrieving transmitter information."""

    @pytest.mark.asyncio
    async def test_get_tx_model_no_transmitter(
        self, connected_client: SlxdClient
    ) -> None:
        """Test getting TX model when no transmitter connected."""
        model = await connected_client.get_tx_model(1)
        assert model == "UNKNOWN"

    @pytest.mark.asyncio
    async def test_get_tx_model_with_transmitter(
        self, connected_client_with_transmitter: SlxdClient
    ) -> None:
        """Test getting TX model with transmitter connected."""
        model = await connected_client_with_transmitter.get_tx_model(1)
        assert model == "SLXD2"

    @pytest.mark.asyncio
    async def test_get_tx_batt_bars_no_transmitter(
        self, connected_client: SlxdClient
    ) -> None:
        """Test getting battery bars when no transmitter."""
        bars = await connected_client.get_tx_batt_bars(1)
        assert bars is None  # 255 converts to None

    @pytest.mark.asyncio
    async def test_get_tx_batt_bars_with_transmitter(
        self, connected_client_with_transmitter: SlxdClient
    ) -> None:
        """Test getting battery bars with transmitter."""
        bars = await connected_client_with_transmitter.get_tx_batt_bars(1)
        assert bars == 4

    @pytest.mark.asyncio
    async def test_get_tx_batt_mins_no_transmitter(
        self, connected_client: SlxdClient
    ) -> None:
        """Test getting battery minutes when no transmitter."""
        mins = await connected_client.get_tx_batt_mins(1)
        assert mins is None  # 65535 converts to None

    @pytest.mark.asyncio
    async def test_get_tx_batt_mins_with_transmitter(
        self, connected_client_with_transmitter: SlxdClient
    ) -> None:
        """Test getting battery minutes with transmitter."""
        mins = await connected_client_with_transmitter.get_tx_batt_mins(1)
        assert mins == 240


class TestPaddedStringHandling:
    """Tests for proper handling of padded string responses."""

    @pytest.mark.asyncio
    async def test_model_strips_padding(self, connected_client: SlxdClient) -> None:
        """Test that model response strips padding."""
        model = await connected_client.get_model()
        assert model == "SLXD4D"
        assert " " not in model  # No trailing spaces

    @pytest.mark.asyncio
    async def test_channel_name_strips_padding(
        self, connected_client: SlxdClient
    ) -> None:
        """Test that channel name strips padding."""
        name = await connected_client.get_channel_name(1)
        assert name == "CH 1"
        assert not name.endswith(" ")

    @pytest.mark.asyncio
    async def test_firmware_version_strips_padding(
        self, connected_client: SlxdClient
    ) -> None:
        """Test that firmware version strips padding."""
        fw_ver = await connected_client.get_firmware_version()
        assert fw_ver == "2.0.15.2"
        assert not fw_ver.endswith(" ")


class TestNumericValueConversion:
    """Tests for correct numeric value conversion."""

    @pytest.mark.asyncio
    async def test_audio_gain_conversion(
        self, mock_server: MockSlxdServer, connected_client: SlxdClient
    ) -> None:
        """Test audio gain is correctly converted from raw."""
        # Set raw gain to 40 (should be 40 - 18 = 22 dB)
        mock_server.device.channels[0].audio_gain_raw = 40

        gain = await connected_client.get_audio_gain(1)
        assert gain == 22

    @pytest.mark.asyncio
    async def test_audio_level_conversion(
        self, mock_server: MockSlxdServer, connected_client: SlxdClient
    ) -> None:
        """Test audio level is correctly converted from raw."""
        # Set raw peak to 100 (should be 100 - 120 = -20 dBFS)
        mock_server.set_audio_level(1, peak=100, rms=90)

        peak = await connected_client.get_audio_level_peak(1)
        rms = await connected_client.get_audio_level_rms(1)

        assert peak == -20
        assert rms == -30

    @pytest.mark.asyncio
    async def test_rssi_conversion(
        self, mock_server: MockSlxdServer, connected_client: SlxdClient
    ) -> None:
        """Test RSSI is correctly converted from raw."""
        # Set raw RSSI to 80 (should be 80 - 120 = -40 dBm)
        mock_server.set_rssi(1, antenna1=80, antenna2=75)

        rssi1 = await connected_client.get_rssi(1, antenna=1)
        rssi2 = await connected_client.get_rssi(1, antenna=2)

        assert rssi1 == -40
        assert rssi2 == -45
