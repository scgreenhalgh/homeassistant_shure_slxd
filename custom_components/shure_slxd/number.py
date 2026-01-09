"""Number platform for Shure SLX-D integration."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .pyslxd.client import AUDIO_GAIN_MAX_DB, AUDIO_GAIN_MIN_DB

from .const import DOMAIN
from .coordinator import SlxdDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Shure SLX-D number entities."""
    coordinator: SlxdDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities: list[NumberEntity] = []

    # Add channel-level gain controls
    if coordinator.data:
        for channel in coordinator.data.channels:
            entities.append(
                SlxdAudioGainNumber(
                    coordinator=coordinator,
                    channel_number=channel.number,
                )
            )

    async_add_entities(entities)


class SlxdAudioGainNumber(CoordinatorEntity[SlxdDataUpdateCoordinator], NumberEntity):
    """Number entity for audio gain control."""

    _attr_has_entity_name = True
    _attr_native_min_value = AUDIO_GAIN_MIN_DB
    _attr_native_max_value = AUDIO_GAIN_MAX_DB
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "dB"
    _attr_mode = NumberMode.SLIDER

    def __init__(
        self,
        coordinator: SlxdDataUpdateCoordinator,
        channel_number: int,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator)
        self._channel_number = channel_number
        self._attr_unique_id = (
            f"{coordinator.config_entry.data['device_id']}_"
            f"channel_{channel_number}_audio_gain"
        )
        self._attr_name = f"Channel {channel_number} Audio Gain"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.config_entry.data["device_id"])},
            name=f"Shure {self.coordinator.config_entry.data['model']}",
            manufacturer="Shure",
            model=self.coordinator.config_entry.data["model"],
            sw_version=self.coordinator.data.firmware_version if self.coordinator.data else None,
        )

    @property
    def native_value(self) -> float | None:
        """Return the current gain value."""
        if self.coordinator.data is None:
            return None
        channel = self.coordinator.data.get_channel(self._channel_number)
        if channel is None:
            return None
        return channel.audio_gain_db

    async def async_set_native_value(self, value: float) -> None:
        """Set the audio gain value."""
        from .pyslxd.client import SlxdClient

        new_gain = int(value)

        # Optimistic update - update coordinator data immediately for instant UI response
        if self.coordinator.data:
            channel = self.coordinator.data.get_channel(self._channel_number)
            if channel:
                channel.audio_gain_db = new_gain
                self.coordinator.async_set_updated_data(self.coordinator.data)

        # Send command to device (don't wait for refresh - optimistic update handles UI)
        host = self.coordinator.config_entry.data["host"]
        port = self.coordinator.config_entry.data.get("port", 2202)

        client = SlxdClient()
        try:
            await client.connect(host, port)
            await client.set_audio_gain(self._channel_number, new_gain)
        finally:
            await client.disconnect()
