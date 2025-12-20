"""Integration tests for transmitter simulation with mock server."""

from __future__ import annotations

import pytest

from pyslxd.client import SlxdClient
from pyslxd.mock.server import MockSlxdServer


class TestTransmitterConnection:
    """Tests for transmitter connection/disconnection simulation."""

    @pytest.mark.asyncio
    async def test_transmitter_not_connected_initially(
        self, connected_client: SlxdClient
    ) -> None:
        """Test that no transmitter is connected by default."""
        model = await connected_client.get_tx_model(1)
        assert model == "UNKNOWN"

    @pytest.mark.asyncio
    async def test_connect_transmitter_slxd2(
        self, mock_server: MockSlxdServer, connected_client: SlxdClient
    ) -> None:
        """Test connecting SLXD2 transmitter."""
        mock_server.connect_transmitter(1, model="SLXD2")

        model = await connected_client.get_tx_model(1)
        assert model == "SLXD2"

    @pytest.mark.asyncio
    async def test_connect_transmitter_slxd1(
        self, mock_server: MockSlxdServer, connected_client: SlxdClient
    ) -> None:
        """Test connecting SLXD1 transmitter."""
        mock_server.connect_transmitter(1, model="SLXD1")

        model = await connected_client.get_tx_model(1)
        assert model == "SLXD1"

    @pytest.mark.asyncio
    async def test_disconnect_transmitter(
        self, mock_server: MockSlxdServer, connected_client: SlxdClient
    ) -> None:
        """Test disconnecting transmitter."""
        # Connect first
        mock_server.connect_transmitter(1, model="SLXD2")
        model_before = await connected_client.get_tx_model(1)
        assert model_before == "SLXD2"

        # Disconnect
        mock_server.disconnect_transmitter(1)
        model_after = await connected_client.get_tx_model(1)
        assert model_after == "UNKNOWN"

    @pytest.mark.asyncio
    async def test_rssi_changes_on_connect(
        self, mock_server: MockSlxdServer, connected_client: SlxdClient
    ) -> None:
        """Test that RSSI values appear when transmitter connects."""
        # Before connection
        rssi_before = await connected_client.get_rssi(1, antenna=1)
        assert rssi_before == -120  # No signal

        # Connect transmitter
        mock_server.connect_transmitter(1)

        # After connection
        rssi_after = await connected_client.get_rssi(1, antenna=1)
        assert rssi_after > -120  # Has signal

    @pytest.mark.asyncio
    async def test_rssi_clears_on_disconnect(
        self, mock_server: MockSlxdServer, connected_client: SlxdClient
    ) -> None:
        """Test that RSSI values clear when transmitter disconnects."""
        # Connect
        mock_server.connect_transmitter(1)
        rssi_connected = await connected_client.get_rssi(1, antenna=1)
        assert rssi_connected > -120

        # Disconnect
        mock_server.disconnect_transmitter(1)
        rssi_disconnected = await connected_client.get_rssi(1, antenna=1)
        assert rssi_disconnected == -120


class TestBatteryLevel:
    """Tests for battery level simulation."""

    @pytest.mark.asyncio
    async def test_battery_bars_with_transmitter(
        self, mock_server: MockSlxdServer, connected_client: SlxdClient
    ) -> None:
        """Test reading battery bars from transmitter."""
        mock_server.connect_transmitter(1, battery_bars=4)

        bars = await connected_client.get_tx_batt_bars(1)
        assert bars == 4

    @pytest.mark.asyncio
    async def test_battery_minutes_with_transmitter(
        self, mock_server: MockSlxdServer, connected_client: SlxdClient
    ) -> None:
        """Test reading battery minutes from transmitter."""
        mock_server.connect_transmitter(1, battery_minutes=240)

        mins = await connected_client.get_tx_batt_mins(1)
        assert mins == 240

    @pytest.mark.asyncio
    async def test_battery_level_changes(
        self, mock_server: MockSlxdServer, connected_client: SlxdClient
    ) -> None:
        """Test simulating battery level changes."""
        mock_server.connect_transmitter(1, battery_bars=5, battery_minutes=480)

        # Initial level
        bars1 = await connected_client.get_tx_batt_bars(1)
        mins1 = await connected_client.get_tx_batt_mins(1)
        assert bars1 == 5
        assert mins1 == 480

        # Simulate battery drain
        mock_server.set_battery_level(1, bars=3, minutes=240)

        bars2 = await connected_client.get_tx_batt_bars(1)
        mins2 = await connected_client.get_tx_batt_mins(1)
        assert bars2 == 3
        assert mins2 == 240

    @pytest.mark.asyncio
    async def test_battery_level_low(
        self, mock_server: MockSlxdServer, connected_client: SlxdClient
    ) -> None:
        """Test low battery simulation."""
        mock_server.connect_transmitter(1)
        mock_server.set_battery_level(1, bars=1, minutes=60)

        bars = await connected_client.get_tx_batt_bars(1)
        mins = await connected_client.get_tx_batt_mins(1)

        assert bars == 1
        assert mins == 60

    @pytest.mark.asyncio
    async def test_battery_level_critical(
        self, mock_server: MockSlxdServer, connected_client: SlxdClient
    ) -> None:
        """Test critical battery simulation."""
        mock_server.connect_transmitter(1)
        mock_server.set_battery_level(1, bars=0, minutes=10)

        bars = await connected_client.get_tx_batt_bars(1)
        assert bars == 0


class TestAudioLevelSimulation:
    """Tests for audio level simulation."""

    @pytest.mark.asyncio
    async def test_audio_level_no_signal(
        self, connected_client: SlxdClient
    ) -> None:
        """Test audio levels with no transmitter."""
        peak = await connected_client.get_audio_level_peak(1)
        rms = await connected_client.get_audio_level_rms(1)

        assert peak == -120
        assert rms == -120

    @pytest.mark.asyncio
    async def test_audio_level_with_signal(
        self, mock_server: MockSlxdServer, connected_client: SlxdClient
    ) -> None:
        """Test setting audio levels."""
        mock_server.set_audio_level(1, peak=100, rms=90)

        peak = await connected_client.get_audio_level_peak(1)
        rms = await connected_client.get_audio_level_rms(1)

        assert peak == -20  # 100 - 120
        assert rms == -30   # 90 - 120

    @pytest.mark.asyncio
    async def test_audio_level_hot_signal(
        self, mock_server: MockSlxdServer, connected_client: SlxdClient
    ) -> None:
        """Test near-clipping audio levels."""
        mock_server.set_audio_level(1, peak=118, rms=110)

        peak = await connected_client.get_audio_level_peak(1)
        rms = await connected_client.get_audio_level_rms(1)

        assert peak == -2   # Near 0 dBFS
        assert rms == -10


class TestRSSISimulation:
    """Tests for RSSI simulation."""

    @pytest.mark.asyncio
    async def test_set_rssi_levels(
        self, mock_server: MockSlxdServer, connected_client: SlxdClient
    ) -> None:
        """Test setting RSSI levels for both antennas."""
        mock_server.set_rssi(1, antenna1=85, antenna2=80)

        rssi1 = await connected_client.get_rssi(1, antenna=1)
        rssi2 = await connected_client.get_rssi(1, antenna=2)

        assert rssi1 == -35  # 85 - 120
        assert rssi2 == -40  # 80 - 120

    @pytest.mark.asyncio
    async def test_rssi_diversity(
        self, mock_server: MockSlxdServer, connected_client: SlxdClient
    ) -> None:
        """Test RSSI with antenna diversity."""
        # Antenna 1 stronger
        mock_server.set_rssi(1, antenna1=90, antenna2=70)

        rssi1 = await connected_client.get_rssi(1, antenna=1)
        rssi2 = await connected_client.get_rssi(1, antenna=2)

        assert rssi1 > rssi2


class TestMultipleChannelTransmitters:
    """Tests for transmitters on multiple channels."""

    @pytest.mark.asyncio
    async def test_different_transmitters_on_channels(
        self, mock_server: MockSlxdServer, connected_client: SlxdClient
    ) -> None:
        """Test different transmitters on different channels."""
        mock_server.connect_transmitter(1, model="SLXD2", battery_bars=5)
        mock_server.connect_transmitter(2, model="SLXD1", battery_bars=3)

        model1 = await connected_client.get_tx_model(1)
        model2 = await connected_client.get_tx_model(2)
        bars1 = await connected_client.get_tx_batt_bars(1)
        bars2 = await connected_client.get_tx_batt_bars(2)

        assert model1 == "SLXD2"
        assert model2 == "SLXD1"
        assert bars1 == 5
        assert bars2 == 3

    @pytest.mark.asyncio
    async def test_partial_channel_connection(
        self, mock_server: MockSlxdServer, connected_client: SlxdClient
    ) -> None:
        """Test only some channels have transmitters."""
        mock_server.connect_transmitter(1, model="SLXD2")
        # Channel 2 has no transmitter

        model1 = await connected_client.get_tx_model(1)
        model2 = await connected_client.get_tx_model(2)

        assert model1 == "SLXD2"
        assert model2 == "UNKNOWN"
