"""Binary sensor platform for Shure SLX-D integration."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
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
    """Set up Shure SLX-D binary sensor entities."""
    coordinator: SlxdDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities: list[BinarySensorEntity] = []

    # Add channel-level transmitter connected sensors
    if coordinator.data:
        for channel in coordinator.data.channels:
            entities.append(
                SlxdTransmitterConnectedBinarySensor(
                    coordinator=coordinator,
                    channel_number=channel.number,
                )
            )

    async_add_entities(entities)


class SlxdTransmitterConnectedBinarySensor(
    CoordinatorEntity[SlxdDataUpdateCoordinator], BinarySensorEntity
):
    """Binary sensor for transmitter connection status."""

    _attr_has_entity_name = True
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(
        self,
        coordinator: SlxdDataUpdateCoordinator,
        channel_number: int,
    ) -> None:
        """Initialize the binary sensor entity."""
        super().__init__(coordinator)
        self._channel_number = channel_number
        self._attr_unique_id = (
            f"{coordinator.config_entry.data['device_id']}_"
            f"channel_{channel_number}_transmitter_connected"
        )
        self._attr_name = f"Channel {channel_number} Transmitter Connected"

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

    @property
    def is_on(self) -> bool | None:
        """Return True if transmitter is connected."""
        if self.coordinator.data is None:
            return None
        channel = self.coordinator.data.get_channel(self._channel_number)
        if channel is None:
            return None
        return channel.transmitter is not None
