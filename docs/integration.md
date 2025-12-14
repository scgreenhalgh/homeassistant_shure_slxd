# Shure SLX-D Integration for Home Assistant

Complete documentation for monitoring and controlling Shure SLX-D wireless microphone receivers from Home Assistant.

---

## Table of Contents

1. [Overview](#overview)
2. [Supported Hardware](#supported-hardware)
3. [Prerequisites](#prerequisites)
4. [Installation](#installation)
5. [Configuration](#configuration)
6. [Entities Reference](#entities-reference)
7. [Dashboard Examples](#dashboard-examples)
8. [Automation Examples](#automation-examples)
9. [Troubleshooting](#troubleshooting)
10. [Technical Reference](#technical-reference)

---

## Overview

The Shure SLX-D integration provides full monitoring and control of Shure SLX-D wireless microphone receivers directly from Home Assistant. Monitor battery levels, signal strength, audio levels, and control gain settings - all from your smart home dashboard.

### Key Features

- **Real-time monitoring** of audio levels, signal strength, and battery status
- **Remote control** of audio gain and output level settings
- **Device identification** via LED flashing
- **Multi-channel support** for dual and quad receivers
- **Local network communication** - no cloud required

---

## Supported Hardware

### Receivers

| Model | Description | Channels | Status |
|-------|-------------|----------|--------|
| SLXD4 | Single-channel receiver | 1 | Supported |
| SLXD4D | Dual-channel receiver | 2 | Supported |
| SLXD4Q+ | Quad-channel receiver | 4 | Supported |

### Transmitters (Monitored via Receiver)

| Model | Description |
|-------|-------------|
| SLXD1 | Bodypack transmitter |
| SLXD2 | Handheld transmitter |

### Tested Firmware Versions

- 2.0.15.2

### Frequency Bands

All SLX-D frequency bands are supported:
- G55, G58, G59, H55, J52, K59, L57, Q58, R55, S50

---

## Prerequisites

### Network Requirements

1. **Ethernet Connection**: Your SLX-D receiver must be connected to your network via the RJ-45 Ethernet port on the rear panel
2. **IP Address**: The receiver needs a valid IP address (DHCP or static)
3. **Port Access**: TCP port 2202 must be accessible between Home Assistant and the receiver
4. **Same Network**: Home Assistant and the receiver should be on the same network or have routing configured

### Finding Your Receiver's IP Address

**Method 1: Front Panel Menu**
1. Press the **MENU** button on the receiver front panel
2. Navigate to **Device** → **Network**
3. The current IP address will be displayed

**Method 2: Shure Wireless Workbench**
1. Open Shure Wireless Workbench software
2. Your receiver will appear in the device list with its IP address

**Method 3: Router/DHCP Server**
1. Check your router's DHCP client list
2. Look for a device with manufacturer "Shure" or MAC address starting with `00:0E:`

### Firewall Configuration

If you have a firewall between Home Assistant and the receiver, ensure:
- **TCP port 2202** is open (inbound to receiver)
- Allow established connections back to Home Assistant

---

## Installation

### Method 1: HACS (Recommended)

[HACS](https://hacs.xyz/) (Home Assistant Community Store) is the recommended installation method.

1. **Install HACS** if you haven't already: [HACS Installation Guide](https://hacs.xyz/docs/setup/download)

2. **Add the custom repository**:
   - Open HACS in Home Assistant
   - Click the three-dot menu (⋮) in the top right
   - Select **Custom repositories**
   - Add: `https://github.com/scgreenhalgh/homeassistant_shure_slxd`
   - Category: **Integration**
   - Click **Add**

3. **Install the integration**:
   - In HACS, click **+ Explore & Download Repositories**
   - Search for "Shure SLX-D"
   - Click on the integration
   - Click **Download**
   - Select the latest version
   - Click **Download**

4. **Restart Home Assistant**:
   - Go to **Settings** → **System** → **Restart**
   - Click **Restart**

### Method 2: Manual Installation

1. **Download the integration**:
   - Go to the [GitHub releases page](https://github.com/scgreenhalgh/homeassistant_shure_slxd/releases)
   - Download the latest release ZIP file

2. **Extract and copy files**:
   ```bash
   # Navigate to your Home Assistant config directory
   cd /config

   # Create custom_components if it doesn't exist
   mkdir -p custom_components

   # Copy the shure_slxd folder
   cp -r /path/to/extracted/custom_components/shure_slxd custom_components/
   ```

3. **Copy the pyslxd library**:
   ```bash
   # Copy the pyslxd library to custom_components
   cp -r /path/to/extracted/pyslxd/src/pyslxd custom_components/shure_slxd/
   ```

4. **Restart Home Assistant**

---

## Configuration

### Adding a Device

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration** (bottom right)
3. Search for "**Shure SLX-D**"
4. Enter the configuration:

| Field | Description | Required | Default |
|-------|-------------|----------|---------|
| IP Address | The receiver's IP address | Yes | - |
| Port | TCP port for communication | No | 2202 |

5. Click **Submit**

The integration will:
- Connect to the receiver
- Verify it's a Shure SLX-D device
- Detect the model and number of channels
- Create all sensor and control entities

### Adding Multiple Receivers

Repeat the configuration process for each receiver. Each receiver will appear as a separate device in Home Assistant.

### Reconfiguring a Device

Currently, to change the IP address or port:
1. Remove the integration from **Settings** → **Devices & Services**
2. Re-add it with the new configuration

---

## Entities Reference

### Device Information

Each receiver appears as a device with:

| Property | Description |
|----------|-------------|
| Manufacturer | Shure |
| Model | SLXD4 / SLXD4D / SLXD4Q+ |
| Firmware | Current firmware version |
| Identifier | 8-character device ID |

### Sensors

#### Device-Level Sensors

| Sensor | Description | Entity ID |
|--------|-------------|-----------|
| Firmware Version | Current firmware | `sensor.<name>_firmware_version` |
| Model | Device model name | `sensor.<name>_model` |
| RF Band | Frequency band (e.g., G55) | `sensor.<name>_rf_band` |
| Lock Status | Front panel lock state | `sensor.<name>_lock_status` |

#### Channel-Level Sensors

For each channel (X = 1, 2, 3, or 4):

| Sensor | Description | Unit | Entity ID |
|--------|-------------|------|-----------|
| Audio Gain | Current gain setting | dB | `sensor.<name>_channel_X_audio_gain` |
| Audio Peak | Peak audio level | dBFS | `sensor.<name>_channel_X_audio_peak` |
| Audio RMS | Average audio level | dBFS | `sensor.<name>_channel_X_audio_rms` |
| RSSI Antenna A | Signal strength (antenna A) | dBm | `sensor.<name>_channel_X_rssi_antenna_a` |
| RSSI Antenna B | Signal strength (antenna B) | dBm | `sensor.<name>_channel_X_rssi_antenna_b` |
| Frequency | Operating frequency | MHz | `sensor.<name>_channel_X_frequency` |
| Name | Channel name | - | `sensor.<name>_channel_X_name` |
| Group/Channel | Group and channel preset | - | `sensor.<name>_channel_X_group_channel` |
| Battery Bars | Battery indicator (0-5) | bars | `sensor.<name>_channel_X_battery_bars` |
| Battery Time | Estimated remaining time | min | `sensor.<name>_channel_X_battery_time` |
| Transmitter Model | Connected transmitter type | - | `sensor.<name>_channel_X_transmitter_model` |

### Binary Sensors

| Sensor | Description | Entity ID |
|--------|-------------|-----------|
| Transmitter Connected | Whether a transmitter is linked | `binary_sensor.<name>_channel_X_transmitter_connected` |

### Controls

#### Number Entities (Sliders)

| Control | Description | Range | Entity ID |
|---------|-------------|-------|-----------|
| Audio Gain | Adjustable gain | -18 to +42 dB | `number.<name>_channel_X_audio_gain` |

#### Select Entities (Dropdowns)

| Control | Description | Options | Entity ID |
|---------|-------------|---------|-----------|
| Audio Output Level | Output level mode | MIC, LINE | `select.<name>_channel_X_audio_output_level` |

#### Button Entities

| Control | Description | Entity ID |
|---------|-------------|-----------|
| Identify Device | Flash all LEDs | `button.<name>_identify` |
| Identify Channel | Flash channel LED | `button.<name>_channel_X_identify` |

---

## Dashboard Examples

### Basic Wireless Mic Card

Create a simple card showing key information for a wireless microphone:

```yaml
type: entities
title: Lead Vocal Mic
entities:
  - entity: binary_sensor.shure_slxd4d_channel_1_transmitter_connected
    name: Connected
  - entity: sensor.shure_slxd4d_channel_1_battery_bars
    name: Battery
  - entity: sensor.shure_slxd4d_channel_1_rssi_antenna_a
    name: Signal A
  - entity: sensor.shure_slxd4d_channel_1_rssi_antenna_b
    name: Signal B
  - entity: number.shure_slxd4d_channel_1_audio_gain
    name: Gain
```

### Compact Battery Overview

Show battery status for multiple microphones:

```yaml
type: glance
title: Wireless Mic Batteries
entities:
  - entity: sensor.shure_slxd4d_channel_1_battery_bars
    name: Lead Vox
  - entity: sensor.shure_slxd4d_channel_2_battery_bars
    name: Backup Vox
  - entity: sensor.shure_slxd4q_channel_1_battery_bars
    name: Pastor
  - entity: sensor.shure_slxd4q_channel_2_battery_bars
    name: Worship Lead
```

### Audio Levels Gauge Card

Display audio levels with gauge cards (requires custom card):

```yaml
type: horizontal-stack
cards:
  - type: gauge
    entity: sensor.shure_slxd4d_channel_1_audio_peak
    name: Ch1 Peak
    min: -120
    max: 0
    severity:
      green: -60
      yellow: -20
      red: -6
  - type: gauge
    entity: sensor.shure_slxd4d_channel_2_audio_peak
    name: Ch2 Peak
    min: -120
    max: 0
    severity:
      green: -60
      yellow: -20
      red: -6
```

### Full Channel Control Card

Complete control panel for a single channel:

```yaml
type: vertical-stack
cards:
  - type: markdown
    content: "## Channel 1 - Lead Vocal"
  - type: horizontal-stack
    cards:
      - type: entity
        entity: binary_sensor.shure_slxd4d_channel_1_transmitter_connected
        name: Status
      - type: entity
        entity: sensor.shure_slxd4d_channel_1_transmitter_model
        name: Transmitter
  - type: entities
    entities:
      - entity: sensor.shure_slxd4d_channel_1_frequency
        name: Frequency
      - entity: sensor.shure_slxd4d_channel_1_battery_bars
        name: Battery
      - entity: sensor.shure_slxd4d_channel_1_battery_time
        name: Time Remaining
  - type: horizontal-stack
    cards:
      - type: entity
        entity: sensor.shure_slxd4d_channel_1_rssi_antenna_a
        name: RSSI A
      - type: entity
        entity: sensor.shure_slxd4d_channel_1_rssi_antenna_b
        name: RSSI B
  - type: entities
    entities:
      - entity: number.shure_slxd4d_channel_1_audio_gain
        name: Audio Gain
      - entity: select.shure_slxd4d_channel_1_audio_output_level
        name: Output Level
      - entity: button.shure_slxd4d_channel_1_identify
        name: Identify
```

### Conditional Card (Show Only When Active)

Only show microphone info when transmitter is connected:

```yaml
type: conditional
conditions:
  - condition: state
    entity: binary_sensor.shure_slxd4d_channel_1_transmitter_connected
    state: "on"
card:
  type: entities
  title: Channel 1 Active
  entities:
    - sensor.shure_slxd4d_channel_1_battery_bars
    - sensor.shure_slxd4d_channel_1_audio_peak
```

---

## Automation Examples

### Low Battery Alert

Send a notification when battery drops below 2 bars:

```yaml
automation:
  - alias: "Wireless Mic Low Battery Alert"
    description: "Alert when any wireless mic battery is low"
    trigger:
      - platform: numeric_state
        entity_id:
          - sensor.shure_slxd4d_channel_1_battery_bars
          - sensor.shure_slxd4d_channel_2_battery_bars
        below: 2
    condition:
      - condition: state
        entity_id: binary_sensor.shure_slxd4d_channel_1_transmitter_connected
        state: "on"
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "Low Battery Warning"
          message: >
            {{ trigger.to_state.attributes.friendly_name }}
            battery is at {{ trigger.to_state.state }} bars
          data:
            priority: high
```

### Critical Battery Alert (Under 30 Minutes)

Alert when battery time remaining is critical:

```yaml
automation:
  - alias: "Wireless Mic Critical Battery"
    trigger:
      - platform: numeric_state
        entity_id: sensor.shure_slxd4d_channel_1_battery_time
        below: 30
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "CRITICAL: Replace Battery Now"
          message: "Channel 1 has only {{ states('sensor.shure_slxd4d_channel_1_battery_time') }} minutes remaining!"
          data:
            priority: critical
```

### Weak Signal Warning

Alert when signal strength drops too low:

```yaml
automation:
  - alias: "Wireless Mic Weak Signal"
    trigger:
      - platform: numeric_state
        entity_id:
          - sensor.shure_slxd4d_channel_1_rssi_antenna_a
          - sensor.shure_slxd4d_channel_1_rssi_antenna_b
        below: -85
        for:
          seconds: 10
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "Weak Signal Warning"
          message: "{{ trigger.to_state.attributes.friendly_name }} signal is weak ({{ trigger.to_state.state }} dBm)"
```

### Transmitter Connected/Disconnected Log

Log when transmitters connect or disconnect:

```yaml
automation:
  - alias: "Log Transmitter Status Changes"
    trigger:
      - platform: state
        entity_id:
          - binary_sensor.shure_slxd4d_channel_1_transmitter_connected
          - binary_sensor.shure_slxd4d_channel_2_transmitter_connected
    action:
      - service: logbook.log
        data:
          name: "Wireless Mic"
          message: >
            {{ trigger.to_state.attributes.friendly_name }}
            {% if trigger.to_state.state == 'on' %}connected{% else %}disconnected{% endif %}
```

### Pre-Event Battery Check

30 minutes before an event, check all batteries and report status:

```yaml
automation:
  - alias: "Pre-Event Mic Check"
    trigger:
      - platform: calendar
        event: start
        entity_id: calendar.church_services
        offset: "-00:30:00"
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "Pre-Event Mic Check"
          message: >
            Channel 1: {{ states('sensor.shure_slxd4d_channel_1_battery_bars') }} bars
            ({{ states('sensor.shure_slxd4d_channel_1_battery_time') }} min)

            Channel 2: {{ states('sensor.shure_slxd4d_channel_2_battery_bars') }} bars
            ({{ states('sensor.shure_slxd4d_channel_2_battery_time') }} min)
```

### Flash LEDs When Transmitter Disconnects

Automatically flash the channel LED when a transmitter disconnects:

```yaml
automation:
  - alias: "Flash LED on Disconnect"
    trigger:
      - platform: state
        entity_id: binary_sensor.shure_slxd4d_channel_1_transmitter_connected
        from: "on"
        to: "off"
    action:
      - service: button.press
        target:
          entity_id: button.shure_slxd4d_channel_1_identify
```

### Set Gain Based on Time of Day

Adjust gain for different services/events:

```yaml
automation:
  - alias: "Morning Service Gain"
    trigger:
      - platform: time
        at: "08:00:00"
    condition:
      - condition: time
        weekday:
          - sun
    action:
      - service: number.set_value
        target:
          entity_id: number.shure_slxd4d_channel_1_audio_gain
        data:
          value: 12
```

---

## Troubleshooting

### Connection Issues

#### "Cannot connect to device"

1. **Verify power**: Ensure the receiver is powered on (front panel lit)

2. **Check IP address**: Confirm the IP on the receiver matches your configuration
   - Menu → Device → Network → IP Address

3. **Test network connectivity** from your Home Assistant host:
   ```bash
   # Test if port is reachable
   nc -zv <receiver-ip> 2202

   # Or with telnet
   telnet <receiver-ip> 2202
   ```

4. **Check firewall rules**: Ensure TCP 2202 is not blocked

5. **Try power cycling**: Turn the receiver off and on again

#### "Device already configured"

The device ID is already registered. To reconfigure:
1. Go to **Settings** → **Devices & Services**
2. Find the Shure SLX-D integration
3. Click the three-dot menu → **Delete**
4. Re-add the integration

### Entity Issues

#### Sensors show "unavailable"

1. Check receiver is powered on
2. Verify network connectivity
3. Check Home Assistant logs for errors:
   - **Settings** → **System** → **Logs**
   - Filter for "shure_slxd"

#### Battery shows "255" or "unknown"

This indicates:
- No transmitter is connected, OR
- Transmitter battery type is not supported (non-Shure batteries)

#### Audio levels stuck at -120 dBFS

- This is normal when no audio is present
- Check that the transmitter is unmuted
- Verify audio is being transmitted

#### Wrong number of channels displayed

Channel count is based on model detection:
- SLXD4 → 1 channel
- SLXD4D → 2 channels
- SLXD4Q+ → 4 channels

If incorrect, check the MODEL response from the device.

### Control Issues

#### Gain changes don't take effect

1. Ensure the front panel is not locked (check lock_status sensor)
2. Verify network connectivity
3. Check that another application isn't also connected to the receiver

#### Button press does nothing

The identify (flash) function may not be visible if:
- The receiver is in a dark room (LEDs flash but no ambient light)
- The flash duration is very brief

### Debug Logging

Enable detailed logging to troubleshoot issues:

```yaml
# configuration.yaml
logger:
  default: info
  logs:
    custom_components.shure_slxd: debug
    pyslxd: debug
```

After enabling, check logs at **Settings** → **System** → **Logs**.

---

## Technical Reference

### Communication Protocol

The integration uses the Shure SLX-D ASCII protocol:

| Property | Value |
|----------|-------|
| Transport | TCP/IP |
| Default Port | 2202 |
| Format | ASCII text |
| Command Types | GET, SET, REP |

### Command Format

```
< GET [channel] PROPERTY >       # Query a value
< SET [channel] PROPERTY value > # Set a value
< REP [channel] PROPERTY value > # Response from device
```

### Example Commands

```
< GET MODEL >                    # Query device model
< REP MODEL {SLXD4D} >          # Response

< GET 1 AUDIO_GAIN >            # Query channel 1 gain
< REP 1 AUDIO_GAIN 030 >        # Response (raw value 30 = 12 dB)

< SET 1 AUDIO_GAIN 040 >        # Set channel 1 gain to 22 dB
< REP 1 AUDIO_GAIN 040 >        # Confirmation
```

### Value Conversions

| Property | Raw Range | Converted | Formula |
|----------|-----------|-----------|---------|
| Audio Gain | 0-60 | -18 to +42 dB | `dB = raw - 18` |
| Audio Level | 0-120 | -120 to 0 dBFS | `dBFS = raw - 120` |
| RSSI | 0-120 | -120 to 0 dBm | `dBm = raw - 120` |
| Frequency | kHz | MHz | `MHz = kHz / 1000` |

### Polling Interval

The integration polls the device every **30 seconds**.

### IoT Classification

`local_polling` - Direct local network communication using polling.

### Known Limitations

1. **No auto-discovery**: SLX-D devices don't support mDNS/Zeroconf
2. **Polling only**: Real-time push updates not yet implemented
3. **Single connection**: Only one client can connect at a time
4. **No encryption**: Communication is plain text over TCP

---

## References

- [Shure SLX-D Command Strings](https://pubs.shure.com/view/software-firmware/SLXD_COMMAND/en-US/index.htm) - Official protocol documentation
- [Shure SLX-D User Guide](https://pubs.shure.com/guide/SLXD) - Hardware documentation
- [Home Assistant Developer Docs](https://developers.home-assistant.io/) - Integration development
- [GitHub Repository](https://github.com/scgreenhalgh/homeassistant_shure_slxd) - Source code and issues

---

## Support

- **Bug Reports**: [GitHub Issues](https://github.com/scgreenhalgh/homeassistant_shure_slxd/issues)
- **Feature Requests**: [GitHub Issues](https://github.com/scgreenhalgh/homeassistant_shure_slxd/issues)
- **Discussions**: [GitHub Discussions](https://github.com/scgreenhalgh/homeassistant_shure_slxd/discussions)
