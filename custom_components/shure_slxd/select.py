"""Select platform for Shure SLX-D integration."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SlxdDataUpdateCoordinator

AUDIO_OUTPUT_LEVELS = ["MIC", "LINE"]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Shure SLX-D select entities."""
    coordinator: SlxdDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities: list[SelectEntity] = []

    # Add channel-level audio output level selects
    if coordinator.data:
        for channel in coordinator.data.channels:
            entities.append(
                SlxdAudioOutputLevelSelect(
                    coordinator=coordinator,
                    channel_number=channel.number,
                )
            )

    async_add_entities(entities)


class SlxdAudioOutputLevelSelect(
    CoordinatorEntity[SlxdDataUpdateCoordinator], SelectEntity
):
    """Select entity for audio output level."""

    _attr_has_entity_name = True
    _attr_options = AUDIO_OUTPUT_LEVELS

    def __init__(
        self,
        coordinator: SlxdDataUpdateCoordinator,
        channel_number: int,
    ) -> None:
        """Initialize the select entity."""
        super().__init__(coordinator)
        self._channel_number = channel_number
        self._attr_unique_id = (
            f"{coordinator.config_entry.data['device_id']}_"
            f"channel_{channel_number}_audio_output_level"
        )
        self._attr_name = f"Channel {channel_number} Audio Output Level"

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
    def current_option(self) -> str | None:
        """Return the current audio output level."""
        if self.coordinator.data is None:
            return None
        channel = self.coordinator.data.get_channel(self._channel_number)
        if channel is None:
            return None
        return channel.audio_out_level.value

    async def async_select_option(self, option: str) -> None:
        """Set the audio output level."""
        from .pyslxd.client import SlxdClient

        host = self.coordinator.config_entry.data["host"]
        port = self.coordinator.config_entry.data.get("port", 2202)

        client = SlxdClient()
        try:
            await client.connect(host, port)
            await client.set_audio_out_level(self._channel_number, option)
        finally:
            await client.disconnect()

        # Request a coordinator refresh to update the state
        await self.coordinator.async_request_refresh()
