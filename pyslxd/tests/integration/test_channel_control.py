"""Integration tests for channel control with mock server."""

from __future__ import annotations

import pytest

from pyslxd.client import SlxdClient
from pyslxd.mock.server import MockSlxdServer


class TestAudioGainControl:
    """Tests for audio gain control."""

    @pytest.mark.asyncio
    async def test_set_and_get_audio_gain(
        self, mock_server: MockSlxdServer, connected_client: SlxdClient
    ) -> None:
        """Test setting audio gain and reading it back."""
        # Set gain to 12 dB
        await connected_client.set_audio_gain(1, 12)

        # Read back
        gain = await connected_client.get_audio_gain(1)
        assert gain == 12

        # Verify server state
        assert mock_server.device.channels[0].audio_gain_raw == 30  # 12 + 18

    @pytest.mark.asyncio
    async def test_set_audio_gain_min_value(
        self, mock_server: MockSlxdServer, connected_client: SlxdClient
    ) -> None:
        """Test setting minimum audio gain (-18 dB)."""
        await connected_client.set_audio_gain(1, -18)

        gain = await connected_client.get_audio_gain(1)
        assert gain == -18
        assert mock_server.device.channels[0].audio_gain_raw == 0

    @pytest.mark.asyncio
    async def test_set_audio_gain_max_value(
        self, mock_server: MockSlxdServer, connected_client: SlxdClient
    ) -> None:
        """Test setting maximum audio gain (+42 dB)."""
        await connected_client.set_audio_gain(1, 42)

        gain = await connected_client.get_audio_gain(1)
        assert gain == 42
        assert mock_server.device.channels[0].audio_gain_raw == 60

    @pytest.mark.asyncio
    async def test_set_audio_gain_invalid_too_high(
        self, connected_client: SlxdClient
    ) -> None:
        """Test that gain above max raises ValueError."""
        with pytest.raises(ValueError):
            await connected_client.set_audio_gain(1, 50)

    @pytest.mark.asyncio
    async def test_set_audio_gain_invalid_too_low(
        self, connected_client: SlxdClient
    ) -> None:
        """Test that gain below min raises ValueError."""
        with pytest.raises(ValueError):
            await connected_client.set_audio_gain(1, -20)

    @pytest.mark.asyncio
    async def test_set_audio_gain_different_channels(
        self, mock_server: MockSlxdServer, connected_client: SlxdClient
    ) -> None:
        """Test setting different gain on different channels."""
        await connected_client.set_audio_gain(1, 10)
        await connected_client.set_audio_gain(2, 20)

        gain1 = await connected_client.get_audio_gain(1)
        gain2 = await connected_client.get_audio_gain(2)

        assert gain1 == 10
        assert gain2 == 20


class TestAudioOutputLevelControl:
    """Tests for audio output level control."""

    @pytest.mark.asyncio
    async def test_set_and_get_audio_out_level_line(
        self, mock_server: MockSlxdServer, connected_client: SlxdClient
    ) -> None:
        """Test setting audio output level to LINE."""
        await connected_client.set_audio_out_level(1, "LINE")

        level = await connected_client.get_audio_out_level(1)
        assert level == "LINE"
        assert mock_server.device.channels[0].audio_out_level == "LINE"

    @pytest.mark.asyncio
    async def test_set_and_get_audio_out_level_mic(
        self, mock_server: MockSlxdServer, connected_client: SlxdClient
    ) -> None:
        """Test setting audio output level to MIC."""
        # First set to LINE
        mock_server.device.channels[0].audio_out_level = "LINE"

        # Then set back to MIC
        await connected_client.set_audio_out_level(1, "MIC")

        level = await connected_client.get_audio_out_level(1)
        assert level == "MIC"

    @pytest.mark.asyncio
    async def test_set_audio_out_level_lowercase(
        self, connected_client: SlxdClient
    ) -> None:
        """Test setting audio output level with lowercase."""
        await connected_client.set_audio_out_level(1, "line")

        level = await connected_client.get_audio_out_level(1)
        assert level == "LINE"

    @pytest.mark.asyncio
    async def test_set_audio_out_level_invalid(
        self, connected_client: SlxdClient
    ) -> None:
        """Test that invalid level raises ValueError."""
        with pytest.raises(ValueError):
            await connected_client.set_audio_out_level(1, "INVALID")


class TestFlashControl:
    """Tests for flash/identify functionality."""

    @pytest.mark.asyncio
    async def test_flash_device(self, connected_client: SlxdClient) -> None:
        """Test flashing device LEDs."""
        # Should not raise
        await connected_client.flash_device()

    @pytest.mark.asyncio
    async def test_flash_channel(self, connected_client: SlxdClient) -> None:
        """Test flashing specific channel LED."""
        await connected_client.flash_channel(1)
        await connected_client.flash_channel(2)

    @pytest.mark.asyncio
    async def test_flash_channel_invalid(self, connected_client: SlxdClient) -> None:
        """Test flashing invalid channel raises ValueError."""
        with pytest.raises(ValueError):
            await connected_client.flash_channel(5)


class TestMeteringControl:
    """Tests for metering control."""

    @pytest.mark.asyncio
    async def test_start_metering(self, connected_client: SlxdClient) -> None:
        """Test starting metering on a channel."""
        # Should not raise
        await connected_client.start_metering(1, rate_ms=1000)

    @pytest.mark.asyncio
    async def test_stop_metering(self, connected_client: SlxdClient) -> None:
        """Test stopping metering on a channel."""
        await connected_client.start_metering(1, rate_ms=1000)
        await connected_client.stop_metering(1)

    @pytest.mark.asyncio
    async def test_start_metering_different_rates(
        self, connected_client: SlxdClient
    ) -> None:
        """Test starting metering with different rates."""
        await connected_client.start_metering(1, rate_ms=100)
        await connected_client.start_metering(2, rate_ms=500)
        await connected_client.stop_metering(1)
        await connected_client.stop_metering(2)


class TestChannelValidation:
    """Tests for channel number validation."""

    @pytest.mark.asyncio
    async def test_get_audio_gain_invalid_channel_0(
        self, connected_client: SlxdClient
    ) -> None:
        """Test that channel 0 raises ValueError."""
        with pytest.raises(ValueError, match="Channel must be 1-4"):
            await connected_client.get_audio_gain(0)

    @pytest.mark.asyncio
    async def test_get_audio_gain_invalid_channel_5(
        self, connected_client: SlxdClient
    ) -> None:
        """Test that channel 5 raises ValueError."""
        with pytest.raises(ValueError, match="Channel must be 1-4"):
            await connected_client.get_audio_gain(5)

    @pytest.mark.asyncio
    async def test_set_audio_gain_invalid_channel(
        self, connected_client: SlxdClient
    ) -> None:
        """Test that invalid channel in set raises ValueError."""
        with pytest.raises(ValueError):
            await connected_client.set_audio_gain(0, 10)

    @pytest.mark.asyncio
    async def test_rssi_invalid_antenna(self, connected_client: SlxdClient) -> None:
        """Test that invalid antenna raises ValueError."""
        with pytest.raises(ValueError, match="Antenna must be 1 or 2"):
            await connected_client.get_rssi(1, antenna=3)


class TestMultiChannelDevices:
    """Tests for multi-channel device control."""

    @pytest.mark.asyncio
    async def test_slxd4_single_channel(
        self, connected_client_slxd4: SlxdClient
    ) -> None:
        """Test single-channel SLXD4 only has channel 1."""
        # Channel 1 should work
        gain = await connected_client_slxd4.get_audio_gain(1)
        assert gain == 0

    @pytest.mark.asyncio
    async def test_slxd4q_all_channels(
        self, mock_server_slxd4q: MockSlxdServer, connected_client_slxd4q: SlxdClient
    ) -> None:
        """Test quad-channel SLXD4Q+ has all 4 channels."""
        for ch in range(1, 5):
            await connected_client_slxd4q.set_audio_gain(ch, ch * 5)

        for ch in range(1, 5):
            gain = await connected_client_slxd4q.get_audio_gain(ch)
            assert gain == ch * 5

    @pytest.mark.asyncio
    async def test_slxd4d_two_channels(
        self, mock_server: MockSlxdServer, connected_client: SlxdClient
    ) -> None:
        """Test dual-channel SLXD4D has channels 1 and 2."""
        await connected_client.set_audio_gain(1, 5)
        await connected_client.set_audio_gain(2, 10)

        gain1 = await connected_client.get_audio_gain(1)
        gain2 = await connected_client.get_audio_gain(2)

        assert gain1 == 5
        assert gain2 == 10
