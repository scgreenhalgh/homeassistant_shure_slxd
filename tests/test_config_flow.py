"""Tests for Shure SLX-D config flow.

TDD RED PHASE: These tests define the expected behavior of the config flow.
Run these tests to see them fail, then implement config_flow.py to make them pass.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.shure_slxd.const import DOMAIN


async def test_flow_user_init_shows_form(hass: HomeAssistant) -> None:
    """Test that user init shows the configuration form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}


async def test_flow_user_success(
    hass: HomeAssistant, mock_slxd_client: MagicMock
) -> None:
    """Test successful user configuration."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"host": "192.168.1.100"},
    )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "Shure SLXD4D"
    assert result["data"] == {
        "host": "192.168.1.100",
        "port": 2202,
        "device_id": "SLXD4D01",
        "model": "SLXD4D",
    }
    assert result["result"].unique_id == "SLXD4D01"


async def test_flow_user_with_custom_port(
    hass: HomeAssistant, mock_slxd_client: MagicMock
) -> None:
    """Test user configuration with custom port."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"host": "192.168.1.100", "port": 2203},
    )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"]["port"] == 2203


async def test_flow_user_cannot_connect(
    hass: HomeAssistant, mock_slxd_client_cannot_connect: MagicMock
) -> None:
    """Test handling connection failure."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"host": "192.168.1.100"},
    )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_flow_user_already_configured(
    hass: HomeAssistant, mock_slxd_client: MagicMock
) -> None:
    """Test that flow aborts if device already configured."""
    # First, create an existing entry using MockConfigEntry
    from pytest_homeassistant_custom_component.common import MockConfigEntry

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

    # Now try to configure the same device
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"host": "192.168.1.200"},  # Different IP, same device_id
    )

    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_flow_user_unknown_error(hass: HomeAssistant) -> None:
    """Test handling of unknown errors."""
    with patch(
        "custom_components.shure_slxd.config_flow.SlxdClient"
    ) as mock_client_class:
        mock_client = MagicMock()
        mock_client.connect = AsyncMock(side_effect=Exception("Unknown error"))
        mock_client.disconnect = AsyncMock()
        mock_client_class.return_value = mock_client

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"host": "192.168.1.100"},
        )

        assert result["type"] == FlowResultType.FORM
        assert result["errors"] == {"base": "unknown"}


async def test_flow_validates_host_format(hass: HomeAssistant) -> None:
    """Test that invalid host format is rejected."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    # Empty host should be caught by voluptuous schema
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"host": ""},
    )

    # Should show form with errors or remain on form
    assert result["type"] == FlowResultType.FORM


async def test_flow_default_port_when_omitted(
    hass: HomeAssistant, mock_slxd_client: MagicMock
) -> None:
    """Test that default port 2202 is used when not specified."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"host": "192.168.1.100"},
    )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"]["port"] == 2202

    # Verify the client was called with the default port
    mock_slxd_client.connect.assert_called_once_with("192.168.1.100", 2202)
