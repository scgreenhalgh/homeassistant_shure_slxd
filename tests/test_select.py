"""Tests for Shure SLX-D select entities.

TDD RED PHASE: These tests define the expected behavior of the select entities.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from homeassistant.components.select import ATTR_OPTION, SERVICE_SELECT_OPTION
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


async def test_audio_output_level_select_created(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test that audio output level select is created."""
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
            "select.shure_slxd4d_channel_1_audio_output_level"
        )
        assert entity is not None


async def test_audio_output_level_select_state(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test that audio output level select reports correct state."""
    with patch(
        "custom_components.shure_slxd.coordinator.SlxdClient"
    ) as mock_client_class:
        mock_client = create_mock_slxd_client()
        mock_client_class.return_value = mock_client

        mock_config_entry.add_to_hass(hass)
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        state = hass.states.get("select.shure_slxd4d_channel_1_audio_output_level")
        assert state is not None
        assert state.state == "MIC"


async def test_audio_output_level_select_options(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test that audio output level select has correct options."""
    with patch(
        "custom_components.shure_slxd.coordinator.SlxdClient"
    ) as mock_client_class:
        mock_client = create_mock_slxd_client()
        mock_client_class.return_value = mock_client

        mock_config_entry.add_to_hass(hass)
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        state = hass.states.get("select.shure_slxd4d_channel_1_audio_output_level")
        assert state is not None
        options = state.attributes.get("options")
        assert options is not None
        assert "MIC" in options
        assert "LINE" in options


async def test_audio_output_level_select_set_option(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test that audio output level select can change value."""
    with patch(
        "custom_components.shure_slxd.coordinator.SlxdClient"
    ) as mock_coordinator_client_class, patch(
        "pyslxd.client.SlxdClient"
    ) as mock_select_client_class:
        # Mock for coordinator
        mock_coordinator_client = create_mock_slxd_client()
        mock_coordinator_client_class.return_value = mock_coordinator_client

        # Mock for select entity
        mock_select_client = create_mock_slxd_client()
        mock_select_client_class.return_value = mock_select_client

        mock_config_entry.add_to_hass(hass)
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        # Change the option
        await hass.services.async_call(
            "select",
            SERVICE_SELECT_OPTION,
            {
                ATTR_ENTITY_ID: "select.shure_slxd4d_channel_1_audio_output_level",
                ATTR_OPTION: "LINE",
            },
            blocking=True,
        )

        # Verify set_audio_out_level was called with correct value
        mock_select_client.set_audio_out_level.assert_called_with(1, "LINE")


async def test_audio_output_level_select_unique_id(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test that audio output level select has correct unique ID."""
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
            "select.shure_slxd4d_channel_1_audio_output_level"
        )
        assert entity is not None
        assert entity.unique_id == "SLXD4D01_channel_1_audio_output_level"
