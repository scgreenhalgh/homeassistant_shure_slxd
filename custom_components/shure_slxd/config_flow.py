"""Config flow for Shure SLX-D integration.

TDD RED phase - tests are written, implementation pending.
"""

from __future__ import annotations

from homeassistant import config_entries

from .const import DOMAIN


class ShureSlxdConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Shure SLX-D."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        raise NotImplementedError("TDD RED phase")
