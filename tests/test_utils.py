"""Shared test utilities for Shure SLX-D integration tests."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock


def create_mock_slxd_client() -> MagicMock:
    """Create a fully-mocked SlxdClient with all methods."""
    mock_client = MagicMock()
    mock_client.connect = AsyncMock()
    mock_client.disconnect = AsyncMock()
    mock_client.get_model = AsyncMock(return_value="SLXD4D")
    mock_client.get_device_id = AsyncMock(return_value="SLXD4D01")
    mock_client.get_firmware_version = AsyncMock(return_value="2.0.15.2")
    mock_client.get_audio_gain = AsyncMock(return_value=12)
    mock_client.get_frequency = AsyncMock(return_value=578350)
    mock_client.get_channel_name = AsyncMock(return_value="Lead Vox")
    mock_client.get_audio_level_peak = AsyncMock(return_value=-18)
    mock_client.get_audio_level_rms = AsyncMock(return_value=-25)
    mock_client.get_rssi = AsyncMock(return_value=-37)
    mock_client.get_tx_model = AsyncMock(return_value="SLXD2")
    mock_client.get_tx_batt_bars = AsyncMock(return_value=4)
    mock_client.get_tx_batt_mins = AsyncMock(return_value=125)
    mock_client.get_audio_out_level = AsyncMock(return_value="MIC")
    # Control methods
    mock_client.set_audio_gain = AsyncMock()
    mock_client.flash_device = AsyncMock()
    mock_client.flash_channel = AsyncMock()
    mock_client.set_audio_out_level = AsyncMock()
    return mock_client
