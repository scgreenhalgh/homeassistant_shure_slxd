"""Button platform for Shure SLX-D integration."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SlxdDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Shure SLX-D button entities."""
    coordinator: SlxdDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities: list[ButtonEntity] = []

    # Add device-level identify button
    entities.append(SlxdIdentifyDeviceButton(coordinator=coordinator))

    # Add channel-level identify buttons
    if coordinator.data:
        for channel in coordinator.data.channels:
            entities.append(
                SlxdIdentifyChannelButton(
                    coordinator=coordinator,
                    channel_number=channel.number,
                )
            )

    async_add_entities(entities)


class SlxdIdentifyDeviceButton(
    CoordinatorEntity[SlxdDataUpdateCoordinator], ButtonEntity
):
    """Button entity for device identification (flash all LEDs)."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: SlxdDataUpdateCoordinator,
    ) -> None:
        """Initialize the button entity."""
        super().__init__(coordinator)
        self._attr_unique_id = (
            f"{coordinator.config_entry.data['device_id']}_identify"
        )
        self._attr_name = "Identify"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.config_entry.data["device_id"])},
            name=f"Shure {self.coordinator.config_entry.data['model']}",
            manufacturer="Shure",
            model=self.coordinator.config_entry.data["model"],
            sw_version=self.coordinator.data.firmware_version
            if self.coordinator.data
            else None,
        )

    async def async_press(self) -> None:
        """Handle the button press."""
        from pyslxd.client import SlxdClient

        host = self.coordinator.config_entry.data["host"]
        port = self.coordinator.config_entry.data.get("port", 2202)

        client = SlxdClient()
        try:
            await client.connect(host, port)
            await client.flash_device()
        finally:
            await client.disconnect()


class SlxdIdentifyChannelButton(
    CoordinatorEntity[SlxdDataUpdateCoordinator], ButtonEntity
):
    """Button entity for channel identification (flash channel LED)."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: SlxdDataUpdateCoordinator,
        channel_number: int,
    ) -> None:
        """Initialize the button entity."""
        super().__init__(coordinator)
        self._channel_number = channel_number
        self._attr_unique_id = (
            f"{coordinator.config_entry.data['device_id']}_"
            f"channel_{channel_number}_identify"
        )
        self._attr_name = f"Channel {channel_number} Identify"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.config_entry.data["device_id"])},
            name=f"Shure {self.coordinator.config_entry.data['model']}",
            manufacturer="Shure",
            model=self.coordinator.config_entry.data["model"],
            sw_version=self.coordinator.data.firmware_version
            if self.coordinator.data
            else None,
        )

    async def async_press(self) -> None:
        """Handle the button press."""
        from pyslxd.client import SlxdClient

        host = self.coordinator.config_entry.data["host"]
        port = self.coordinator.config_entry.data.get("port", 2202)

        client = SlxdClient()
        try:
            await client.connect(host, port)
            await client.flash_channel(self._channel_number)
        finally:
            await client.disconnect()
