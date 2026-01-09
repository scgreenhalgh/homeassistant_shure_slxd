"""Tests for Shure SLX-D coordinator.

TDD RED PHASE: These tests define the expected behavior of the coordinator.
Run these tests to see them fail, then implement coordinator.py to make them pass.
"""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.shure_slxd.const import DOMAIN
from custom_components.shure_slxd.coordinator import SlxdDataUpdateCoordinator
from custom_components.shure_slxd.pyslxd.exceptions import SlxdConnectionError, SlxdTimeoutError
from custom_components.shure_slxd.pyslxd.models import (
    AudioOutputLevel,
    BatteryStatus,
    LockStatus,
    SlxdChannel,
    SlxdDevice,
    SlxdTransmitter,
    TransmitterModel,
)

from tests.test_utils import create_mock_slxd_client


@pytest.fixture
def mock_config_entry(hass: HomeAssistant) -> MockConfigEntry:
    """Create a mock config entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "host": "192.168.1.100",
            "port": 2202,
            "device_id": "SLXD4D01",
            "model": "SLXD4D",
        },
        title="Shure SLXD4D",
        unique_id="SLXD4D01",
    )
    entry.add_to_hass(hass)
    return entry


@pytest.fixture
def mock_device() -> SlxdDevice:
    """Create a mock SlxdDevice."""
    tx1 = SlxdTransmitter(
        model=TransmitterModel.SLXD2,
        battery_bars=4,
        battery_minutes=125,
    )
    ch1 = SlxdChannel(
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
    return SlxdDevice(
        model="SLXD4D",
        device_id="SLXD4D01",
        firmware_version="2.0.15.2",
        rf_band="G55",
        lock_status=LockStatus.ALL,
        channels=[ch1, ch2],
    )


async def test_coordinator_creation(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    """Test that coordinator can be created."""
    coordinator = SlxdDataUpdateCoordinator(
        hass,
        config_entry=mock_config_entry,
    )
    assert coordinator is not None
    assert coordinator.name == "Shure SLX-D"


async def test_coordinator_update_success(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_device: SlxdDevice,
) -> None:
    """Test successful data update."""
    with patch(
        "custom_components.shure_slxd.coordinator.SlxdClient"
    ) as mock_client_class:
        mock_client = create_mock_slxd_client()
        mock_client_class.return_value = mock_client

        coordinator = SlxdDataUpdateCoordinator(
            hass,
            config_entry=mock_config_entry,
        )

        # Perform update
        data = await coordinator._async_update_data()

        assert data is not None
        assert data.model == "SLXD4D"
        assert data.device_id == "SLXD4D01"


async def test_coordinator_update_connection_error(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    """Test that connection error raises UpdateFailed."""
    with patch(
        "custom_components.shure_slxd.coordinator.SlxdClient"
    ) as mock_client_class:
        mock_client = MagicMock()
        mock_client.connect = AsyncMock(
            side_effect=SlxdConnectionError("Connection refused")
        )
        mock_client.disconnect = AsyncMock()
        mock_client_class.return_value = mock_client

        coordinator = SlxdDataUpdateCoordinator(
            hass,
            config_entry=mock_config_entry,
        )

        with pytest.raises(UpdateFailed):
            await coordinator._async_update_data()


async def test_coordinator_update_timeout_error(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    """Test that timeout error raises UpdateFailed."""
    with patch(
        "custom_components.shure_slxd.coordinator.SlxdClient"
    ) as mock_client_class:
        mock_client = MagicMock()
        mock_client.connect = AsyncMock()
        mock_client.disconnect = AsyncMock()
        mock_client.get_model = AsyncMock(side_effect=SlxdTimeoutError("Timeout"))
        mock_client_class.return_value = mock_client

        coordinator = SlxdDataUpdateCoordinator(
            hass,
            config_entry=mock_config_entry,
        )

        with pytest.raises(UpdateFailed):
            await coordinator._async_update_data()


async def test_coordinator_disconnects_on_error(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    """Test that client is disconnected even on error."""
    with patch(
        "custom_components.shure_slxd.coordinator.SlxdClient"
    ) as mock_client_class:
        mock_client = MagicMock()
        mock_client.connect = AsyncMock()
        mock_client.disconnect = AsyncMock()
        mock_client.get_model = AsyncMock(side_effect=SlxdTimeoutError("Timeout"))
        mock_client_class.return_value = mock_client

        coordinator = SlxdDataUpdateCoordinator(
            hass,
            config_entry=mock_config_entry,
        )

        try:
            await coordinator._async_update_data()
        except UpdateFailed:
            pass

        # Verify disconnect was called
        mock_client.disconnect.assert_called_once()


async def test_coordinator_update_interval(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    """Test that coordinator uses correct update interval."""
    coordinator = SlxdDataUpdateCoordinator(
        hass,
        config_entry=mock_config_entry,
    )

    # Default update interval should be 10 seconds
    assert coordinator.update_interval == timedelta(seconds=10)


async def test_coordinator_data_contains_channels(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    """Test that coordinator data includes channel information."""
    with patch(
        "custom_components.shure_slxd.coordinator.SlxdClient"
    ) as mock_client_class:
        mock_client = create_mock_slxd_client()
        mock_client_class.return_value = mock_client

        coordinator = SlxdDataUpdateCoordinator(
            hass,
            config_entry=mock_config_entry,
        )

        data = await coordinator._async_update_data()

        # Should have channel data
        assert hasattr(data, "channels")
        assert len(data.channels) >= 1

        # Verify channel data is populated
        channel = data.channels[0]
        assert channel.audio_gain_db == 12
        assert channel.frequency_khz == 578350
        assert channel.audio_peak_dbfs == -18.0
        assert channel.rssi_antenna_1_dbm == -37
