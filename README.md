# Shure SLX-D Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

Home Assistant integration for Shure SLX-D wireless microphone receivers. Monitor your wireless microphone systems directly from Home Assistant.

## Supported Devices

| Model | Channels | Status |
|-------|----------|--------|
| SLXD4 | 1 | Supported |
| SLXD4D | 2 | Supported |
| SLXD4Q+ | 4 | Supported |

### Tested Firmware Versions

- 2.0.15.2

## Features

### Sensors

**Device-level:**
- Firmware Version
- Model

**Channel-level (per channel):**
- Audio Gain (dB)

### Planned Features

- Audio level metering (peak/RMS)
- RSSI signal strength
- Transmitter battery status
- Frequency display
- Gain control (number entity)
- Flash/Identify buttons

## Prerequisites

Before setting up the integration:

1. **Network Connection**: Your SLX-D receiver must be connected to your network via Ethernet
2. **IP Address**: Note the IP address of your receiver (found in the device menu under Network settings)
3. **Port Access**: Ensure port 2202 (TCP) is accessible from your Home Assistant instance

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click the three dots in the top right corner
3. Select "Custom repositories"
4. Add this repository URL: `https://github.com/seangreenhalgh/homeassistant_sennheiser_slxd`
5. Select "Integration" as the category
6. Click "Add"
7. Search for "Shure SLX-D" and install
8. Restart Home Assistant

### Manual Installation

1. Download the latest release
2. Copy the `custom_components/shure_slxd` folder to your Home Assistant's `custom_components` directory
3. Restart Home Assistant

## Configuration

1. Go to **Settings** > **Devices & Services**
2. Click **+ Add Integration**
3. Search for "Shure SLX-D"
4. Enter the IP address of your receiver
5. (Optional) Change the port if not using the default 2202

The integration will automatically:
- Connect to your receiver
- Detect the model and number of channels
- Create sensor entities for each channel

## Entities

After setup, the following entities are created:

### Device Sensors

| Entity | Description |
|--------|-------------|
| `sensor.<device>_firmware_version` | Current firmware version |
| `sensor.<device>_model` | Device model (SLXD4, SLXD4D, SLXD4Q+) |

### Channel Sensors

For each channel (1-4 depending on model):

| Entity | Description | Unit |
|--------|-------------|------|
| `sensor.<device>_channel_X_audio_gain` | Audio gain setting | dB |

## Technical Details

### Communication Protocol

The integration communicates with SLX-D receivers using:
- **Protocol**: ASCII over TCP
- **Port**: 2202 (default)
- **Commands**: GET/SET/REP format per Shure specification

### Polling Interval

- Device state is polled every **30 seconds**
- Future versions may support push updates via SAMPLE commands

### IoT Class

`local_polling` - The integration polls the device over the local network.

## Troubleshooting

### Cannot Connect to Device

1. **Verify network connectivity**: Ensure your receiver is connected via Ethernet and has an IP address
2. **Check IP address**: Confirm the IP address in your receiver's Network menu matches what you entered
3. **Firewall**: Ensure port 2202 TCP is not blocked between Home Assistant and the receiver
4. **Power cycle**: Try restarting the receiver

### Entity Shows "Unavailable"

1. Check if the receiver is powered on
2. Verify network connectivity
3. Check Home Assistant logs for connection errors

### Wrong Channel Count

The integration detects channels based on the model name:
- SLXD4 = 1 channel
- SLXD4D = 2 channels
- SLXD4Q+ = 4 channels

If detection fails, check that the model is reporting correctly.

## Development

This project follows **strict Test-Driven Development (TDD)**. See [CLAUDE.md](CLAUDE.md) for development guidelines.

### Project Structure

```
homeassistant_sennheiser_slxd/
├── pyslxd/                          # PyPI library for SLX-D communication
│   ├── src/pyslxd/
│   │   ├── client.py                # Async TCP client
│   │   ├── protocol.py              # Command/response parsing
│   │   ├── models.py                # Data models
│   │   └── exceptions.py            # Custom exceptions
│   └── tests/                       # Library tests (85 tests)
│
├── custom_components/shure_slxd/    # HA Integration
│   ├── __init__.py                  # Integration setup
│   ├── config_flow.py               # UI configuration
│   ├── coordinator.py               # Data update coordinator
│   ├── sensor.py                    # Sensor entities
│   └── const.py                     # Constants
│
└── tests/                           # Integration tests (21 tests)
```

### Running Tests

```bash
# Install dependencies
python -m venv .venv
source .venv/bin/activate
pip install pytest pytest-asyncio pytest-homeassistant-custom-component

# Run pyslxd library tests
PYTHONPATH="pyslxd/src:." pytest pyslxd/tests/ -v

# Run HA integration tests
PYTHONPATH="pyslxd/src:." pytest tests/ -v
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- Shure for the [SLX-D Command Strings documentation](https://pubs.shure.com/view/software-firmware/SLXD_COMMAND/en-US/index.htm)
- Home Assistant community for the integration framework

## Contributing

Contributions are welcome! Please:

1. Follow TDD methodology (write tests first)
2. Ensure all tests pass
3. Follow the code style in CLAUDE.md
4. Submit a pull request with a clear description
