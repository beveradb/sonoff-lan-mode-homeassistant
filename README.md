# sonoff-lan-mode-homeassistant
Home Assistant platform to control Sonoff switches running the V3+ Itead firmware, locally (LAN mode).

**This will only work for Sonoff devices running V3+ of the stock (Itead / eWeLink) firmware. For users of V1.8.0 - V2.6.1, please see previous code on the depracted [V2 Firmware branch](https://github.com/mattsaxon/sonoff-lan-mode-homeassistant/tree/V2-Firmware)**

This is a simple platform to control switch devices which can normally only be controlled using the Itead cloud app (eWeLink). It may be useful to you if you've bought a Sonoff device and want to control it locally, but cannot flash firmware such as [Tasmota](https://github.com/arendst/Sonoff-Tasmota/) for whatever reason (e.g. lack of tools or confidence soldering).

## Tested Devices
 - Sonoff Basic
 - Sonoff RF
 - Sonoff S26
 - Sonoff T1 UK

## Expected Supported devices:
- Sonoff S20 
- Sonoff S85
- Sonoff T1 UK/US/EU 1 Gang
- Sonoff S30
- Sonoff S31 Lite
- Sonoff Slampher
- Sonoff SV
- Sonoff Touch EU/US
- Any other Sonoff / eWeLink single channel device

## Unsupported Devices*
 - Multi outlets devices

However, I am very confident that if your device works with the eWeLink app in LAN Mode, we can get it working with this component - we might need a bit of joint investigation (e.g. `tcpdump` of communication from app) first to get it working!

## What is LAN Mode?
Since mid 2018, the firmware Itead have shipped with Sonoff devices has provided a feature called "LAN Mode" which allows the device to be controlled directly on the local network using a WebSocket or HTTP REST connection on port 8081.

Whilst older devices only dropped into LAN moe when the internet was unavailabel, the latest V3 firmware are designed to be used in LAN mode predominantly. Note: the eWeLink app doesn't show this very well and when you turn it to LAN mode, it doesn't report that it connect to V3 devices in this mode, so many users are unaware of this and believe the device to be connected via internet, however there is an icon against the device showing a LAN icon when using LAN mode.

Here's a video demonstration of a Sonoff Basic being controlled in LAN mode: [https://www.youtube.com/watch?v=sxtt2cNm8g8](https://www.youtube.com/watch?v=sxtt2cNm8g8)

## Setup
Before you can use this platform to control your Sonoff from Home Assistant, you should perform the following setup steps:
1. Find the "Device ID" of you switch in the eWeLink app, it is under settings
2. For normal devices (i.e. those not branded DIY and some branded DIY too), you need to find the api key (which is used for encryption). DIY branded devices I was told don't have encryption turned on by an Itead employee, but the only device I've seen does actually have it on.

2a. Capture with V2 firmware: If you have V2 firmware and are using the earlier version of this component, the apikey is visible in the HA logs at startup (part of the "user online response") when debug is turned on (see below)
2b. Capture during pairing: You can use the method described [here](https://blog.ipsumdomus.com/sonoff-switch-complete-hack-without-firmware-upgrade-1b2d6632c01). Despite this guide being quite old and for older firmware, the early part where the api_key is uncovered still works. Unfortunately this is only visible this way during pairing

## Installation
To use this platform, copy switch.py to "<home assistant config dir>/custom_components/sonoff_lan_mode/switch.py" and add the config below to configuration.yaml

```
switch:
  - platform: sonoff_lan_mode
    name: // Switch Name
    device_id: // Local IP address of device
    api_key: // [Optional] Custom icon for device
```

Example:
```
switch:
  - platform: sonoff_lan_mode
    name: Kitchen Ceiling
    device_id: 1000111111
    api_key: 12345678-90AB-CDEF-1234-567890ABCDEF
    icon: mdi:lightbulb
```

## Debugging

If raising issues with this component, please consider capturing the appropriate part of the HA log when debug is enabled as below in configuration.yaml

```
logger:
  default: warn
  logs:
    homeassistant.components.switch.sonoff_lan_mode: debug
```

## Future

It would be easier for users if the api key was reported by the eWeLink app, an issue has been raised. I will post it here once it has undergone the Itead forum moderation process.


