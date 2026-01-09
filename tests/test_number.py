"""Tests for Shure SLX-D number entities.

TDD RED PHASE: These tests define the expected behavior of the number entities.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.components.number import ATTR_VALUE, SERVICE_SET_VALUE
from homeassistant.const import ATTR_ENTITY_ID
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


async def test_number_entity_created(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test that number entity is created for audio gain."""
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
            "number.shure_slxd4d_channel_1_audio_gain"
        )
        assert entity is not None


async def test_number_entity_state(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test that number entity reports correct state."""
    with patch(
        "custom_components.shure_slxd.coordinator.SlxdClient"
    ) as mock_client_class:
        mock_client = create_mock_slxd_client()
        mock_client_class.return_value = mock_client

        mock_config_entry.add_to_hass(hass)
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        state = hass.states.get("number.shure_slxd4d_channel_1_audio_gain")
        assert state is not None
        assert state.state == "12"


async def test_number_entity_min_max(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test that number entity has correct min/max values."""
    with patch(
        "custom_components.shure_slxd.coordinator.SlxdClient"
    ) as mock_client_class:
        mock_client = create_mock_slxd_client()
        mock_client_class.return_value = mock_client

        mock_config_entry.add_to_hass(hass)
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        state = hass.states.get("number.shure_slxd4d_channel_1_audio_gain")
        assert state is not None
        assert state.attributes.get("min") == -18
        assert state.attributes.get("max") == 42
        assert state.attributes.get("step") == 1


async def test_number_entity_set_value(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test that number entity can set gain value."""
    with patch(
        "custom_components.shure_slxd.coordinator.SlxdClient"
    ) as mock_coordinator_client_class, patch(
        "custom_components.shure_slxd.pyslxd.client.SlxdClient"
    ) as mock_number_client_class:
        # Mock for coordinator
        mock_coordinator_client = create_mock_slxd_client()
        mock_coordinator_client_class.return_value = mock_coordinator_client

        # Mock for number entity set_value (imported inside the method)
        mock_number_client = create_mock_slxd_client()
        mock_number_client_class.return_value = mock_number_client

        mock_config_entry.add_to_hass(hass)
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        # Call the set_value service
        await hass.services.async_call(
            "number",
            SERVICE_SET_VALUE,
            {
                ATTR_ENTITY_ID: "number.shure_slxd4d_channel_1_audio_gain",
                ATTR_VALUE: 20,
            },
            blocking=True,
        )

        # Verify set_audio_gain was called with correct value
        mock_number_client.set_audio_gain.assert_called_with(1, 20)


async def test_number_entity_unique_id(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test that number entity has correct unique ID."""
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
            "number.shure_slxd4d_channel_1_audio_gain"
        )
        assert entity is not None
        assert entity.unique_id == "SLXD4D01_channel_1_audio_gain"
