"""Shure SLX-D integration for Home Assistant.

TDD RED phase - tests are written, implementation pending.
"""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN

PLATFORMS: list[str] = []


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Shure SLX-D from a config entry."""
    raise NotImplementedError("TDD RED phase")


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    raise NotImplementedError("TDD RED phase")
