"""DataUpdateCoordinator for Shure SLX-D integration."""

from __future__ import annotations

import inspect
import logging
from datetime import timedelta

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

_LOGGER = logging.getLogger(__name__)

# Check if DataUpdateCoordinator supports config_entry parameter (HA 2024.11+)
_COORDINATOR_SUPPORTS_CONFIG_ENTRY = "config_entry" in inspect.signature(
    DataUpdateCoordinator.__init__
).parameters


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
        # Build kwargs for compatibility with different HA versions
        kwargs: dict = {
            "name": "Shure SLX-D",
            "update_interval": timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        }
        if _COORDINATOR_SUPPORTS_CONFIG_ENTRY:
            kwargs["config_entry"] = config_entry

        super().__init__(hass, _LOGGER, **kwargs)

        # Store config_entry for older HA versions
        if not _COORDINATOR_SUPPORTS_CONFIG_ENTRY:
            self.config_entry = config_entry

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
            rf_band = await client.get_rf_band()
            lock_status_str = await client.get_lock_status()
            try:
                lock_status = LockStatus(lock_status_str)
            except ValueError:
                lock_status = LockStatus.OFF

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
                # Fetch all channel properties
                gain_db = await client.get_audio_gain(ch_num)
                frequency_khz = await client.get_frequency(ch_num)
                channel_name = await client.get_channel_name(ch_num)
                group_channel = await client.get_group_channel(ch_num)
                audio_out_level_str = await client.get_audio_out_level(ch_num)
                audio_peak = await client.get_audio_level_peak(ch_num)
                audio_rms = await client.get_audio_level_rms(ch_num)
                rssi_1 = await client.get_rssi(ch_num, antenna=1)
                rssi_2 = await client.get_rssi(ch_num, antenna=2)

                # Parse audio output level
                try:
                    audio_out_level = AudioOutputLevel(audio_out_level_str)
                except ValueError:
                    audio_out_level = AudioOutputLevel.MIC

                # Fetch transmitter info
                tx_model_str = await client.get_tx_model(ch_num)
                tx_batt_bars = await client.get_tx_batt_bars(ch_num)
                tx_batt_mins = await client.get_tx_batt_mins(ch_num)

                # Create transmitter object if we have valid data
                transmitter = None
                if tx_model_str and tx_model_str != "UNKNOWN":
                    try:
                        tx_model = TransmitterModel(tx_model_str)
                    except ValueError:
                        tx_model = TransmitterModel.UNKNOWN
                    transmitter = SlxdTransmitter(
                        model=tx_model,
                        battery_bars=tx_batt_bars,
                        battery_minutes=tx_batt_mins,
                    )

                channel = SlxdChannel(
                    number=ch_num,
                    name=channel_name or f"Channel {ch_num}",
                    frequency_khz=frequency_khz,
                    group_channel=group_channel,
                    audio_gain_db=gain_db,
                    audio_out_level=audio_out_level,
                    audio_peak_dbfs=float(audio_peak),
                    audio_rms_dbfs=float(audio_rms),
                    rssi_antenna_1_dbm=rssi_1,
                    rssi_antenna_2_dbm=rssi_2,
                    transmitter=transmitter,
                )
                channels.append(channel)

            return SlxdDevice(
                model=model,
                device_id=device_id,
                firmware_version=firmware_version,
                rf_band=rf_band,
                lock_status=lock_status,
                channels=channels,
            )

        except SlxdConnectionError as err:
            raise UpdateFailed(f"Connection error: {err}") from err
        except SlxdTimeoutError as err:
            raise UpdateFailed(f"Timeout error: {err}") from err
        finally:
            await client.disconnect()
