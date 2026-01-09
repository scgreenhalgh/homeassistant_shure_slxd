"""Sensor platform for Shure SLX-D integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfFrequency, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .pyslxd.models import SlxdChannel, SlxdDevice

from .const import DOMAIN
from .coordinator import SlxdDataUpdateCoordinator


@dataclass(frozen=True, kw_only=True)
class SlxdSensorEntityDescription(SensorEntityDescription):
    """Describes a Shure SLX-D sensor entity."""

    value_fn: Callable[[SlxdDevice], Any]


@dataclass(frozen=True, kw_only=True)
class SlxdChannelSensorEntityDescription(SensorEntityDescription):
    """Describes a Shure SLX-D channel sensor entity."""

    value_fn: Callable[[SlxdChannel], Any]


DEVICE_SENSORS: tuple[SlxdSensorEntityDescription, ...] = (
    SlxdSensorEntityDescription(
        key="firmware_version",
        translation_key="firmware_version",
        name="Firmware Version",
        value_fn=lambda device: device.firmware_version,
    ),
    SlxdSensorEntityDescription(
        key="model",
        translation_key="model",
        name="Model",
        value_fn=lambda device: device.model,
    ),
    SlxdSensorEntityDescription(
        key="rf_band",
        translation_key="rf_band",
        name="RF Band",
        value_fn=lambda device: device.rf_band,
    ),
    SlxdSensorEntityDescription(
        key="lock_status",
        translation_key="lock_status",
        name="Lock Status",
        value_fn=lambda device: device.lock_status.value,
    ),
)

CHANNEL_SENSORS: tuple[SlxdChannelSensorEntityDescription, ...] = (
    SlxdChannelSensorEntityDescription(
        key="audio_gain",
        translation_key="audio_gain",
        name="Audio Gain",
        native_unit_of_measurement="dB",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda channel: channel.audio_gain_db,
    ),
    SlxdChannelSensorEntityDescription(
        key="audio_peak",
        translation_key="audio_peak",
        name="Audio Peak",
        native_unit_of_measurement="dBFS",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda channel: channel.audio_peak_dbfs,
    ),
    SlxdChannelSensorEntityDescription(
        key="audio_rms",
        translation_key="audio_rms",
        name="Audio RMS",
        native_unit_of_measurement="dBFS",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda channel: channel.audio_rms_dbfs,
    ),
    SlxdChannelSensorEntityDescription(
        key="rssi_antenna_1",
        translation_key="rssi_antenna_1",
        name="RSSI Antenna A",
        native_unit_of_measurement="dBm",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda channel: channel.rssi_antenna_1_dbm,
    ),
    SlxdChannelSensorEntityDescription(
        key="rssi_antenna_2",
        translation_key="rssi_antenna_2",
        name="RSSI Antenna B",
        native_unit_of_measurement="dBm",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda channel: channel.rssi_antenna_2_dbm,
    ),
    SlxdChannelSensorEntityDescription(
        key="frequency",
        translation_key="frequency",
        name="Frequency",
        native_unit_of_measurement=UnitOfFrequency.MEGAHERTZ,
        device_class=SensorDeviceClass.FREQUENCY,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda channel: channel.frequency_mhz,
    ),
    SlxdChannelSensorEntityDescription(
        key="battery_bars",
        translation_key="battery_bars",
        name="Battery Bars",
        native_unit_of_measurement="bars",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda channel: (
            channel.transmitter.battery_bars if channel.transmitter else None
        ),
    ),
    SlxdChannelSensorEntityDescription(
        key="battery_minutes",
        translation_key="battery_minutes",
        name="Battery Time",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda channel: (
            channel.transmitter.battery_minutes if channel.transmitter else None
        ),
    ),
    SlxdChannelSensorEntityDescription(
        key="channel_name",
        translation_key="channel_name",
        name="Name",
        value_fn=lambda channel: channel.name,
    ),
    SlxdChannelSensorEntityDescription(
        key="group_channel",
        translation_key="group_channel",
        name="Group/Channel",
        value_fn=lambda channel: channel.group_channel,
    ),
    SlxdChannelSensorEntityDescription(
        key="transmitter_model",
        translation_key="transmitter_model",
        name="Transmitter Model",
        value_fn=lambda channel: (
            channel.transmitter.model.value if channel.transmitter else None
        ),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Shure SLX-D sensor entities."""
    coordinator: SlxdDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities: list[SensorEntity] = []

    # Add device-level sensors
    for description in DEVICE_SENSORS:
        entities.append(
            SlxdDeviceSensor(
                coordinator=coordinator,
                description=description,
            )
        )

    # Add channel-level sensors
    if coordinator.data:
        for channel in coordinator.data.channels:
            for description in CHANNEL_SENSORS:
                entities.append(
                    SlxdChannelSensor(
                        coordinator=coordinator,
                        description=description,
                        channel_number=channel.number,
                    )
                )

    async_add_entities(entities)


class SlxdDeviceSensor(CoordinatorEntity[SlxdDataUpdateCoordinator], SensorEntity):
    """Sensor for device-level data."""

    entity_description: SlxdSensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: SlxdDataUpdateCoordinator,
        description: SlxdSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.config_entry.data['device_id']}_{description.key}"

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
    def native_value(self) -> Any:
        """Return the sensor value."""
        if self.coordinator.data is None:
            return None
        return self.entity_description.value_fn(self.coordinator.data)


class SlxdChannelSensor(CoordinatorEntity[SlxdDataUpdateCoordinator], SensorEntity):
    """Sensor for channel-level data."""

    entity_description: SlxdChannelSensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: SlxdDataUpdateCoordinator,
        description: SlxdChannelSensorEntityDescription,
        channel_number: int,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._channel_number = channel_number
        self._attr_unique_id = (
            f"{coordinator.config_entry.data['device_id']}_"
            f"channel_{channel_number}_{description.key}"
        )
        self._attr_name = f"Channel {channel_number} {description.name}"

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
    def native_value(self) -> Any:
        """Return the sensor value."""
        if self.coordinator.data is None:
            return None
        channel = self.coordinator.data.get_channel(self._channel_number)
        if channel is None:
            return None
        return self.entity_description.value_fn(channel)
