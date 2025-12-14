"""Tests for Shure SLX-D button entities.

TDD RED PHASE: These tests define the expected behavior of the button entities.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from homeassistant.components.button import SERVICE_PRESS
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


async def test_identify_device_button_created(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test that identify device button is created."""
    with patch(
        "custom_components.shure_slxd.coordinator.SlxdClient"
    ) as mock_client_class:
        mock_client = create_mock_slxd_client()
        mock_client_class.return_value = mock_client

        mock_config_entry.add_to_hass(hass)
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        entity_registry = er.async_get(hass)
        entity = entity_registry.async_get("button.shure_slxd4d_identify")
        assert entity is not None


async def test_identify_channel_button_created(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test that identify channel buttons are created."""
    with patch(
        "custom_components.shure_slxd.coordinator.SlxdClient"
    ) as mock_client_class:
        mock_client = create_mock_slxd_client()
        mock_client_class.return_value = mock_client

        mock_config_entry.add_to_hass(hass)
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        entity_registry = er.async_get(hass)
        # Should have identify buttons for each channel
        entity = entity_registry.async_get(
            "button.shure_slxd4d_channel_1_identify"
        )
        assert entity is not None


async def test_identify_device_button_press(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test that identify device button calls flash_device."""
    with patch(
        "custom_components.shure_slxd.coordinator.SlxdClient"
    ) as mock_coordinator_client_class, patch(
        "pyslxd.client.SlxdClient"
    ) as mock_button_client_class:
        # Mock for coordinator
        mock_coordinator_client = create_mock_slxd_client()
        mock_coordinator_client_class.return_value = mock_coordinator_client

        # Mock for button entity
        mock_button_client = create_mock_slxd_client()
        mock_button_client_class.return_value = mock_button_client

        mock_config_entry.add_to_hass(hass)
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        # Press the button
        await hass.services.async_call(
            "button",
            SERVICE_PRESS,
            {ATTR_ENTITY_ID: "button.shure_slxd4d_identify"},
            blocking=True,
        )

        # Verify flash_device was called
        mock_button_client.flash_device.assert_called_once()


async def test_identify_channel_button_press(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test that identify channel button calls flash_channel."""
    with patch(
        "custom_components.shure_slxd.coordinator.SlxdClient"
    ) as mock_coordinator_client_class, patch(
        "pyslxd.client.SlxdClient"
    ) as mock_button_client_class:
        # Mock for coordinator
        mock_coordinator_client = create_mock_slxd_client()
        mock_coordinator_client_class.return_value = mock_coordinator_client

        # Mock for button entity
        mock_button_client = create_mock_slxd_client()
        mock_button_client_class.return_value = mock_button_client

        mock_config_entry.add_to_hass(hass)
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        # Press the channel 1 identify button
        await hass.services.async_call(
            "button",
            SERVICE_PRESS,
            {ATTR_ENTITY_ID: "button.shure_slxd4d_channel_1_identify"},
            blocking=True,
        )

        # Verify flash_channel was called with channel 1
        mock_button_client.flash_channel.assert_called_with(1)


async def test_identify_device_button_unique_id(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test that identify device button has correct unique ID."""
    with patch(
        "custom_components.shure_slxd.coordinator.SlxdClient"
    ) as mock_client_class:
        mock_client = create_mock_slxd_client()
        mock_client_class.return_value = mock_client

        mock_config_entry.add_to_hass(hass)
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        entity_registry = er.async_get(hass)
        entity = entity_registry.async_get("button.shure_slxd4d_identify")
        assert entity is not None
        assert entity.unique_id == "SLXD4D01_identify"


async def test_identify_channel_button_unique_id(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test that identify channel button has correct unique ID."""
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
            "button.shure_slxd4d_channel_1_identify"
        )
        assert entity is not None
        assert entity.unique_id == "SLXD4D01_channel_1_identify"
