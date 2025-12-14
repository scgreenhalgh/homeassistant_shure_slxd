"""Pytest configuration for pyslxd tests."""

import pytest


@pytest.fixture
def sample_device_responses() -> dict[str, str]:
    """Sample device responses for testing protocol parsing."""
    return {
        "model": "< REP MODEL {SLXD4D                          } >",
        "device_id": "< REP DEVICE_ID {SLXD4D01} >",
        "fw_ver": "< REP FW_VER {2.0.15.2                } >",
        "rf_band": "< REP RF_BAND {G55     } >",
        "lock_status": "< REP LOCK_STATUS ALL >",
    }


@pytest.fixture
def sample_channel_responses() -> dict[str, str]:
    """Sample channel responses for testing protocol parsing."""
    return {
        "chan_name": "< REP 1 CHAN_NAME {Lead Vox                       } >",
        "audio_gain": "< REP 1 AUDIO_GAIN 030 >",
        "audio_out_lvl": "< REP 1 AUDIO_OUT_LVL_SWITCH MIC >",
        "frequency": "< REP 1 FREQUENCY 0578350 >",
        "group_channel": "< REP 1 GROUP_CHANNEL {1,1  } >",
        "audio_peak": "< REP 1 AUDIO_LEVEL_PEAK 102 >",
        "audio_rms": "< REP 1 AUDIO_LEVEL_RMS 095 >",
        "rssi": "< REP 1 RSSI 1 083 >",
    }


@pytest.fixture
def sample_transmitter_responses() -> dict[str, str]:
    """Sample transmitter responses for testing protocol parsing."""
    return {
        "tx_model": "< REP 1 TX_MODEL SLXD2 >",
        "tx_batt_bars": "< REP 1 TX_BATT_BARS 004 >",
        "tx_batt_mins": "< REP 1 TX_BATT_MINS 00125 >",
    }


@pytest.fixture
def sample_commands() -> dict[str, str]:
    """Sample commands for testing command building."""
    return {
        "get_model": "< GET MODEL >",
        "get_all": "< GET 0 ALL >",
        "get_channel_gain": "< GET 1 AUDIO_GAIN >",
        "set_channel_gain": "< SET 1 AUDIO_GAIN 040 >",
        "set_flash": "< SET FLASH ON >",
        "set_channel_flash": "< SET 1 FLASH ON >",
        "set_meter_rate": "< SET 1 METER_RATE 01000 >",
    }
