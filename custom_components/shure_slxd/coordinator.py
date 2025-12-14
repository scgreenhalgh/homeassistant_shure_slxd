"""DataUpdateCoordinator for Shure SLX-D integration."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import TYPE_CHECKING

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from pyslxd.client import SlxdClient
from pyslxd.exceptions import SlxdConnectionError, SlxdTimeoutError
from pyslxd.models import (
    AudioOutputLevel,
    LockStatus,
    SlxdChannel,
    SlxdDevice,
    SlxdTransmitter,
    TransmitterModel,
)

from .const import DEFAULT_SCAN_INTERVAL

if TYPE_CHECKING:
    pass

_LOGGER = logging.getLogger(__name__)


class SlxdDataUpdateCoordinator(DataUpdateCoordinator[SlxdDevice]):
    """Coordinator for SLX-D device data updates."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the coordinator.

        Args:
            hass: Home Assistant instance
            config_entry: Config entry for this integration
        """
        super().__init__(
            hass,
            _LOGGER,
            name="Shure SLX-D",
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
            config_entry=config_entry,
        )
        self._host = config_entry.data[CONF_HOST]
        self._port = config_entry.data.get(CONF_PORT, 2202)

    async def _async_update_data(self) -> SlxdDevice:
        """Fetch data from the SLX-D device.

        Returns:
            SlxdDevice with current state

        Raises:
            UpdateFailed: If unable to fetch data
        """
        client = SlxdClient()
        try:
            await client.connect(self._host, self._port)

            # Fetch device info
            model = await client.get_model()
            device_id = await client.get_device_id()
            firmware_version = await client.get_firmware_version()

            # Determine channel count based on model
            if "Q" in model:
                channel_count = 4
            elif model.endswith("D") or "4D" in model:
                channel_count = 2
            else:
                channel_count = 1

            # Fetch channel data
            channels = []
            for ch_num in range(1, channel_count + 1):
                gain_db = await client.get_audio_gain(ch_num)
                channel = SlxdChannel(
                    number=ch_num,
                    name=f"Channel {ch_num}",
                    frequency_khz=0,  # Would need additional API calls
                    group_channel="",
                    audio_gain_db=gain_db,
                    audio_out_level=AudioOutputLevel.MIC,
                    audio_peak_dbfs=-120.0,
                    audio_rms_dbfs=-120.0,
                    rssi_antenna_1_dbm=-120,
                    rssi_antenna_2_dbm=-120,
                    transmitter=None,
                )
                channels.append(channel)

            return SlxdDevice(
                model=model,
                device_id=device_id,
                firmware_version=firmware_version,
                rf_band="",  # Would need additional API call
                lock_status=LockStatus.OFF,
                channels=channels,
            )

        except SlxdConnectionError as err:
            raise UpdateFailed(f"Connection error: {err}") from err
        except SlxdTimeoutError as err:
            raise UpdateFailed(f"Timeout error: {err}") from err
        finally:
            await client.disconnect()
