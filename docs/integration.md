# Shure SLX-D Integration Documentation

## Overview

The Shure SLX-D integration allows you to monitor Shure SLX-D wireless microphone receivers from Home Assistant. This integration communicates directly with the receiver over your local network using the SLX-D ASCII protocol.

## Supported Hardware

### Receivers

| Model | Description | Channels |
|-------|-------------|----------|
| SLXD4 | Single-channel receiver | 1 |
| SLXD4D | Dual-channel receiver | 2 |
| SLXD4Q+ | Quad-channel receiver | 4 |

### Transmitters (Monitored via Receiver)

| Model | Description |
|-------|-------------|
| SLXD1 | Bodypack transmitter |
| SLXD2 | Handheld transmitter |

### Frequency Bands

The integration supports all SLX-D frequency bands:
- G55, G58, G59, H55, J52, K59, L57, Q58, R55, S50

## Prerequisites

### Network Requirements

1. **Ethernet Connection**: The SLX-D receiver must be connected to your network via Ethernet (RJ-45 port on rear panel)
2. **IP Address**: The receiver must have a valid IP address (DHCP or static)
3. **Port Access**: TCP port 2202 must be accessible between Home Assistant and the receiver

### Finding Your Receiver's IP Address

1. On the receiver front panel, press the **MENU** button
2. Navigate to **Device** > **Network**
3. The IP address will be displayed

## Configuration

### Adding the Integration

1. Go to **Settings** > **Devices & Services**
2. Click **+ Add Integration**
3. Search for "Shure SLX-D"
4. Enter the configuration:

| Field | Description | Default |
|-------|-------------|---------|
| Host | IP address of the receiver | Required |
| Port | TCP port | 2202 |

### Configuration Options

Currently, no additional options are available after initial setup.

## Entities

### Device Information

The integration creates a device in Home Assistant with:

| Property | Description |
|----------|-------------|
| Manufacturer | Shure |
| Model | SLXD4 / SLXD4D / SLXD4Q+ |
| Firmware | Current firmware version |
| Identifiers | Device ID (8-character unique identifier) |

### Sensors

#### Device-Level Sensors

| Sensor | Description | Entity ID Pattern |
|--------|-------------|-------------------|
| Firmware Version | Current firmware version | `sensor.<name>_firmware_version` |
| Model | Device model | `sensor.<name>_model` |

#### Channel-Level Sensors

For each channel on the receiver:

| Sensor | Description | Unit | Entity ID Pattern |
|--------|-------------|------|-------------------|
| Audio Gain | Current audio gain setting | dB | `sensor.<name>_channel_X_audio_gain` |

### Future Entities (Planned)

#### Additional Sensors

| Sensor | Description | Unit |
|--------|-------------|------|
| Audio Peak | Peak audio level | dBFS |
| Audio RMS | RMS audio level | dBFS |
| RSSI Antenna 1 | Signal strength antenna A | dBm |
| RSSI Antenna 2 | Signal strength antenna B | dBm |
| Frequency | Operating frequency | MHz |
| Battery Bars | Transmitter battery (0-5) | bars |
| Battery Minutes | Estimated runtime | minutes |

#### Number Entities

| Entity | Description | Range |
|--------|-------------|-------|
| Audio Gain | Adjustable audio gain | -18 to +42 dB |

#### Button Entities

| Entity | Description |
|--------|-------------|
| Identify Device | Flash all LEDs on receiver |
| Identify Channel | Flash specific channel LED |

## Actions (Services)

Currently, no custom actions are implemented.

### Planned Actions

| Action | Description |
|--------|-------------|
| `shure_slxd.flash_device` | Flash device LEDs for identification |
| `shure_slxd.flash_channel` | Flash specific channel LED |
| `shure_slxd.set_gain` | Set audio gain for a channel |

## Automations

### Example: Low Battery Alert

```yaml
automation:
  - alias: "Wireless Mic Low Battery Alert"
    trigger:
      - platform: numeric_state
        entity_id: sensor.shure_slxd4d_channel_1_battery_bars
        below: 2
    action:
      - service: notify.mobile_app
        data:
          title: "Low Battery Warning"
          message: "Channel 1 wireless mic battery is low"
```

### Example: Monitor Signal Strength

```yaml
automation:
  - alias: "Wireless Mic Signal Warning"
    trigger:
      - platform: numeric_state
        entity_id: sensor.shure_slxd4d_channel_1_rssi
        below: -80
    action:
      - service: notify.mobile_app
        data:
          title: "Signal Warning"
          message: "Channel 1 signal strength is weak"
```

## Technical Details

### Communication Protocol

The integration uses the Shure SLX-D ASCII protocol:

- **Transport**: TCP/IP
- **Port**: 2202 (default)
- **Format**: ASCII text commands
- **Command Types**: GET, SET, REP, SAMPLE

### Command Examples

```
< GET MODEL >                    # Query device model
< REP MODEL {SLXD4D} >          # Response

< GET 1 AUDIO_GAIN >            # Query channel 1 gain
< REP 1 AUDIO_GAIN 030 >        # Response (raw value)

< SET 1 AUDIO_GAIN 040 >        # Set channel 1 gain
< REP 1 AUDIO_GAIN 040 >        # Confirmation
```

### Value Conversions

| Property | Raw Value | Converted Value |
|----------|-----------|-----------------|
| Audio Gain | 0-60 | -18 to +42 dB |
| Audio Level | 0-120 | -120 to 0 dBFS |
| RSSI | 0-120 | -120 to 0 dBm |

### Polling Interval

The integration polls the device every **30 seconds** by default.

### IoT Classification

`local_polling` - The integration communicates directly with the device over the local network using polling.

## Troubleshooting

### Connection Issues

#### "Cannot connect to device"

1. **Verify the receiver is powered on** and connected to the network
2. **Check the IP address** in the receiver's Network menu
3. **Test connectivity** from Home Assistant host:
   ```bash
   nc -zv <receiver-ip> 2202
   ```
4. **Check firewall rules** - ensure port 2202 TCP is allowed

#### "Device not found" during setup

1. The device may not be an SLX-D receiver
2. Check that the network connection is active
3. Try power cycling the receiver

### Entity Issues

#### Sensors show "unavailable"

1. Check the receiver is powered on
2. Verify network connectivity
3. Check Home Assistant logs:
   ```
   Settings > System > Logs
   ```
   Search for "shure_slxd"

#### Wrong number of channels

The integration detects channels based on model:
- SLXD4 → 1 channel
- SLXD4D → 2 channels
- SLXD4Q+ → 4 channels

If incorrect, check the MODEL response from the device.

### Debug Logging

Enable debug logging to troubleshoot issues:

```yaml
logger:
  default: info
  logs:
    custom_components.shure_slxd: debug
    pyslxd: debug
```

## Known Limitations

1. **No mDNS/Zeroconf discovery** - SLX-D devices don't advertise on the network
2. **Polling only** - Real-time updates require SAMPLE commands (future enhancement)
3. **Single connection** - Only one client can connect at a time

## References

- [Shure SLX-D Command Strings Documentation](https://pubs.shure.com/view/software-firmware/SLXD_COMMAND/en-US/index.htm)
- [Shure SLX-D User Guide](https://pubs.shure.com/guide/SLXD)
