"""Config flow for Shure SLX-D integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.data_entry_flow import FlowResult

from pyslxd.client import SlxdClient
from pyslxd.exceptions import SlxdConnectionError

from .const import DEFAULT_PORT, DOMAIN

_LOGGER = logging.getLogger(__name__)


class ShureSlxdConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Shure SLX-D."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input.get(CONF_HOST, "").strip()
            port = user_input.get(CONF_PORT, DEFAULT_PORT)

            # Validate host is not empty
            if not host:
                errors["base"] = "cannot_connect"
                return self.async_show_form(
                    step_id="user",
                    data_schema=self._get_schema(),
                    errors=errors,
                )

            # Try to connect to the device
            client = SlxdClient()
            try:
                await client.connect(host, port)
                model = await client.get_model()
                device_id = await client.get_device_id()
            except SlxdConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Unexpected error during config flow")
                errors["base"] = "unknown"
            else:
                # Check if device is already configured
                await self.async_set_unique_id(device_id)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=f"Shure {model}",
                    data={
                        CONF_HOST: host,
                        CONF_PORT: port,
                        "device_id": device_id,
                        "model": model,
                    },
                )
            finally:
                await client.disconnect()

        return self.async_show_form(
            step_id="user",
            data_schema=self._get_schema(),
            errors=errors,
        )

    def _get_schema(self) -> vol.Schema:
        """Get the data schema for user input."""
        return vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
            }
        )
