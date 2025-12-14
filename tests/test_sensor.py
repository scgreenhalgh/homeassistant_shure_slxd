"""Tests for Shure SLX-D sensor entities.

TDD RED PHASE: These tests define the expected behavior of the sensor entities.
Run these tests to see them fail, then implement sensor.py to make them pass.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.const import (
    PERCENTAGE,
    UnitOfFrequency,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.shure_slxd.const import DOMAIN

from pyslxd.models import (
    AudioOutputLevel,
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
def mock_device_data() -> SlxdDevice:
    """Create mock device data."""
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


async def test_sensor_setup_creates_device_sensors(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_device_data: SlxdDevice,
) -> None:
    """Test that sensor setup creates device-level sensors."""
    with patch(
        "custom_components.shure_slxd.coordinator.SlxdClient"
    ) as mock_client_class:
        mock_client = create_mock_slxd_client()
        mock_client_class.return_value = mock_client

        mock_config_entry.add_to_hass(hass)
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        # Check device-level sensors exist
        entity_registry = er.async_get(hass)

        # Firmware version sensor
        fw_entity = entity_registry.async_get(
            "sensor.shure_slxd4d_firmware_version"
        )
        assert fw_entity is not None


async def test_sensor_setup_creates_channel_sensors(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_device_data: SlxdDevice,
) -> None:
    """Test that sensor setup creates channel-level sensors."""
    with patch(
        "custom_components.shure_slxd.coordinator.SlxdClient"
    ) as mock_client_class:
        mock_client = create_mock_slxd_client()
        mock_client_class.return_value = mock_client

        mock_config_entry.add_to_hass(hass)
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        entity_registry = er.async_get(hass)

        # Check channel 1 audio gain sensor exists
        gain_entity = entity_registry.async_get(
            "sensor.shure_slxd4d_channel_1_audio_gain"
        )
        assert gain_entity is not None

        # Check new sensors exist
        peak_entity = entity_registry.async_get(
            "sensor.shure_slxd4d_channel_1_audio_peak"
        )
        assert peak_entity is not None

        rssi_entity = entity_registry.async_get(
            "sensor.shure_slxd4d_channel_1_rssi_antenna_a"
        )
        assert rssi_entity is not None


async def test_firmware_sensor_state(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_device_data: SlxdDevice,
) -> None:
    """Test firmware sensor reports correct state."""
    with patch(
        "custom_components.shure_slxd.coordinator.SlxdClient"
    ) as mock_client_class:
        mock_client = create_mock_slxd_client()
        mock_client_class.return_value = mock_client

        mock_config_entry.add_to_hass(hass)
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        state = hass.states.get("sensor.shure_slxd4d_firmware_version")
        assert state is not None
        assert state.state == "2.0.15.2"


async def test_channel_audio_gain_sensor_state(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_device_data: SlxdDevice,
) -> None:
    """Test channel audio gain sensor reports correct state."""
    with patch(
        "custom_components.shure_slxd.coordinator.SlxdClient"
    ) as mock_client_class:
        mock_client = create_mock_slxd_client()
        mock_client_class.return_value = mock_client

        mock_config_entry.add_to_hass(hass)
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        state = hass.states.get("sensor.shure_slxd4d_channel_1_audio_gain")
        assert state is not None
        assert state.state == "12"


async def test_sensor_unique_id(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_device_data: SlxdDevice,
) -> None:
    """Test sensors have correct unique IDs."""
    with patch(
        "custom_components.shure_slxd.coordinator.SlxdClient"
    ) as mock_client_class:
        mock_client = create_mock_slxd_client()
        mock_client_class.return_value = mock_client

        mock_config_entry.add_to_hass(hass)
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        entity_registry = er.async_get(hass)
        fw_entity = entity_registry.async_get(
            "sensor.shure_slxd4d_firmware_version"
        )
        assert fw_entity is not None
        assert fw_entity.unique_id == "SLXD4D01_firmware_version"


async def test_sensors_unavailable_on_update_failed(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test sensors become unavailable when update fails."""
    from pyslxd.exceptions import SlxdConnectionError

    with patch(
        "custom_components.shure_slxd.coordinator.SlxdClient"
    ) as mock_client_class:
        mock_client = MagicMock()
        mock_client.connect = AsyncMock(
            side_effect=SlxdConnectionError("Connection failed")
        )
        mock_client.disconnect = AsyncMock()
        mock_client_class.return_value = mock_client

        mock_config_entry.add_to_hass(hass)
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        # Sensors should be unavailable if setup failed due to connection error
        state = hass.states.get("sensor.shure_slxd4d_firmware_version")
        # State might be None or unavailable depending on how setup handles errors
        if state is not None:
            assert state.state == "unavailable"
