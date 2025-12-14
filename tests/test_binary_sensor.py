"""Tests for Shure SLX-D binary sensor entities."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from homeassistant.const import STATE_OFF, STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.shure_slxd.const import DOMAIN

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


async def test_transmitter_connected_binary_sensor_created(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test that transmitter connected binary sensor is created."""
    with patch(
        "custom_components.shure_slxd.coordinator.SlxdClient"
    ) as mock_client_class:
        mock_client = create_mock_slxd_client()
        mock_client_class.return_value = mock_client

        mock_config_entry.add_to_hass(hass)
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        entity_registry = er.async_get(hass)
        entity = entity_registry.async_get(
            "binary_sensor.shure_slxd4d_channel_1_transmitter_connected"
        )
        assert entity is not None


async def test_transmitter_connected_binary_sensor_on(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test that transmitter connected shows ON when transmitter is linked."""
    with patch(
        "custom_components.shure_slxd.coordinator.SlxdClient"
    ) as mock_client_class:
        mock_client = create_mock_slxd_client()
        # Default mock returns SLXD2 for tx_model, so transmitter is connected
        mock_client_class.return_value = mock_client

        mock_config_entry.add_to_hass(hass)
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        state = hass.states.get(
            "binary_sensor.shure_slxd4d_channel_1_transmitter_connected"
        )
        assert state is not None
        assert state.state == STATE_ON


async def test_transmitter_connected_binary_sensor_unique_id(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test that transmitter connected binary sensor has correct unique ID."""
    with patch(
        "custom_components.shure_slxd.coordinator.SlxdClient"
    ) as mock_client_class:
        mock_client = create_mock_slxd_client()
        mock_client_class.return_value = mock_client

        mock_config_entry.add_to_hass(hass)
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        entity_registry = er.async_get(hass)
        entity = entity_registry.async_get(
            "binary_sensor.shure_slxd4d_channel_1_transmitter_connected"
        )
        assert entity is not None
        assert entity.unique_id == "SLXD4D01_channel_1_transmitter_connected"
