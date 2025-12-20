#!/usr/bin/env python3
"""Entrypoint for the Mock SLX-D Server container.

This script starts a mock SLX-D receiver that can be configured via
environment variables for testing Home Assistant integration.
"""

from __future__ import annotations

import asyncio
import os
import signal
import sys

from pyslxd.mock.server import MockSlxdServer
from pyslxd.mock.state import MockDevice, MockTransmitter


def get_env(name: str, default: str) -> str:
    """Get environment variable with default."""
    return os.environ.get(name, default)


def get_env_int(name: str, default: int) -> int:
    """Get integer environment variable with default."""
    try:
        return int(os.environ.get(name, str(default)))
    except ValueError:
        return default


def get_env_bool(name: str, default: bool = False) -> bool:
    """Get boolean environment variable with default."""
    value = os.environ.get(name, "").lower()
    if value in ("true", "1", "yes", "on"):
        return True
    if value in ("false", "0", "no", "off"):
        return False
    return default


def create_device() -> MockDevice:
    """Create a MockDevice configured from environment variables."""
    model = get_env("MOCK_MODEL", "SLXD4D")
    device_id = get_env("MOCK_DEVICE_ID", "TEST0001")
    firmware = get_env("MOCK_FIRMWARE", "2.0.15.2")
    rf_band = get_env("MOCK_RF_BAND", "G55")

    device = MockDevice(
        model=model,
        device_id=device_id,
        firmware_version=firmware,
        rf_band=rf_band,
    )

    # Configure transmitters if requested
    for i, channel in enumerate(device.channels, start=1):
        tx_connected = get_env_bool(f"MOCK_CH{i}_TX_CONNECTED", False)
        if tx_connected:
            tx_model = get_env(f"MOCK_CH{i}_TX_MODEL", "SLXD2")
            battery_bars = get_env_int(f"MOCK_CH{i}_BATTERY_BARS", 5)
            battery_mins = get_env_int(f"MOCK_CH{i}_BATTERY_MINS", 480)

            channel.transmitter = MockTransmitter(
                model=tx_model,
                connected=True,
                battery_bars=battery_bars,
                battery_minutes=battery_mins,
            )
            # Set some default RSSI for connected transmitter
            channel.rssi_a1_raw = 80
            channel.rssi_a2_raw = 75

        # Configure channel name if provided
        name = get_env(f"MOCK_CH{i}_NAME", "")
        if name:
            channel.name = name

    return device


async def main() -> None:
    """Run the mock server."""
    host = get_env("MOCK_HOST", "0.0.0.0")
    port = get_env_int("MOCK_PORT", 2202)

    device = create_device()

    print("=" * 60)
    print("Mock SLX-D Server")
    print("=" * 60)
    print(f"Model:      {device.model}")
    print(f"Device ID:  {device.device_id}")
    print(f"Firmware:   {device.firmware_version}")
    print(f"RF Band:    {device.rf_band}")
    print(f"Channels:   {len(device.channels)}")
    print("-" * 60)

    for channel in device.channels:
        tx_status = "Connected" if channel.transmitter and channel.transmitter.connected else "Not connected"
        print(f"Channel {channel.number}: {channel.name} - TX: {tx_status}")

    print("-" * 60)
    print(f"Listening on {host}:{port}")
    print("=" * 60)
    sys.stdout.flush()

    server = MockSlxdServer(host=host, port=port, device=device)

    # Handle graceful shutdown
    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    def signal_handler() -> None:
        print("\nShutdown signal received...")
        stop_event.set()

    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, signal_handler)

    await server.start()
    print(f"Server started on port {server.port}")
    sys.stdout.flush()

    # Wait for shutdown signal
    await stop_event.wait()

    print("Stopping server...")
    await server.stop()
    print("Server stopped")


if __name__ == "__main__":
    asyncio.run(main())
