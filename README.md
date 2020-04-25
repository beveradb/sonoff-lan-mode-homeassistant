[![Latest PyPi Release](https://img.shields.io/pypi/v/pysonofflanr3.svg)](https://pypi.python.org/pypi/pysonofflanr3) [![Updates](https://pyup.io/repos/github/mattsaxon/sonoff-lan-mode-homeassistant/shield.svg)](https://pyup.io/repos/github/mattsaxon/sonoff-lan-mode-homeassistant/) [![Python 3](https://pyup.io/repos/github/mattsaxon/sonoff-lan-mode-homeassistant/python-3-shield.svg)](https://pyup.io/repos/github/mattsaxon/sonoff-lan-mode-homeassistant/pysonofflan/) [![Buy Me A Coffee](https://www.buymeacoffee.com/assets/img/guidelines/download-assets-sm-2.svg)](https://www.buymeacoffee.com/XTOsBAc)

# sonoff-lan-mode-homeassistant
Home Assistant platform to control Sonoff switches running the V3+ Itead firmware (tested on 3.0, 3.0.1, 3.1.0, 3.3.0, 3.4.0, 3.5.0), locally (LAN mode).

**This will only work for Sonoff devices running V3+ of the stock (Itead / eWeLink) firmware. For users of V1.8.0 - V2.6.1, please see the code in this repository https://github.com/beveradb/sonoff-lan-mode-homeassistant**

This is a simple platform to control switch devices which can normally only be controlled using the Itead cloud app (eWeLink). It may be useful to you if you've bought a Sonoff device and want to control it locally, but cannot flash firmware such as [Tasmota](https://github.com/arendst/Sonoff-Tasmota/) for whatever reason (e.g. its already in the wall, lack of tools or confidence soldering or you don't want to forgoe using eWeLink also).

## Tested Devices
 - Sonoff Basic R2
 - Sonoff Basic R3 (both DIY and eWebLink modes)
 - Sonoff RF
 - Sonoff RF R3 (both DIY and eWebLink modes)
 - Sonoff S20 
 - Sonoff S26
 - Sonoff T1 UK 1 Gang
 - Sonoff R2 POW
 - Sonoff S31
 - Sonoff 4CH Pro
 - Sonoff iFan02
 - Sonoff TH16
 
## Expected Supported devices:

- Sonoff Mini
- Sonoff S85
- Sonoff T1 US/EU 1 Gang
- Sonoff S30
- Sonoff S31 Lite
- Sonoff Slampher
- Sonoff SV
- Sonoff Touch EU/US

## Unsupported Devices
 - Sonoff iFan03
 - Any that can't run V3+ firmware

However, I am very confident that if your device works with the eWeLink app in LAN Mode, we can get it working with this component - we might need a bit of joint investigation (e.g. `tcpdump` of communication from app) first to get it working!

## What is LAN Mode?
Since mid 2018, the firmware Itead have shipped with Sonoff devices has provided a feature called "LAN Mode" which allows the device to be controlled directly on the local network using a WebSocket or HTTP REST connection on port 8081.

Whilst older devices only dropped into LAN mode when the internet was unavailable, the latest V3 firmware are designed to be used in LAN mode predominantly. Note: the eWeLink app doesn't show this very well and when you turn it to LAN mode, it doesn't report that it has connected to V3 devices in this mode. Many users are therefore unaware of this and believe the device to be connected via internet, however there is an icon against the device showing a LAN icon when using LAN mode.

Here's a video demonstration of a Sonoff Basic being controlled in LAN mode: [https://www.youtube.com/watch?v=sxtt2cNm8g8](https://www.youtube.com/watch?v=sxtt2cNm8g8)

## Setup
Before you can use this platform to control your Sonoff from Home Assistant, you should perform the following setup steps:
1. Find the "Device ID" of you switch in the eWeLink app, it is under the device settings.
2. For non DIY devices, you need to find the api key (which is used for encryption). DIY branded devices, when configured using the jumper switch do not need the api key configured as they run without encryption.

See https://pysonofflanr3.readthedocs.io/encryption.html

## Installation
To use this platform, copy the folder 'custom_components/sonoff_lan_mode_r3' into your "<home assistant config dir>/custom_components/ directory and add the config below to configuration.yaml

You will also need to be on Home Assistant v94.0 or newer (to pick up the more recent zeroconf dependency).

```
switch:
  - platform: sonoff_lan_mode_r3
    name: // Switch Name
    device_id: // device id (e.g. obtained from eWeLink app)
    api_key: // [Required unless in DIY mode] api_key obtained during pairing or from V2 firmware trace
    icon: // [Optional] Custom icon for device
    outlet: // [Optional] Outlet number, numbered form 0 to 3 on a 4CH as opposed to 1-4 as in the eWeLink interface
```

Example:
```
switch:
  - platform: sonoff_lan_mode_r3
    name: Kitchen
    device_id: 1000111111
    api_key: 12345678-90AB-CDEF-1234-567890ABCDEF # not needed for devices in DIY mode
    icon: mdi:lightbulb
    outlet: 0
```

## Debugging

If raising issues with this component, please consider capturing the appropriate part of the HA log when debug is enabled as below in configuration.yaml

```
logger:
  default: warn
  logs:
    custom_components.sonoff_lan_mode_r3: debug
```

## Future

It would be easier for users if the api key was reported by the eWeLink app. Here is a feature request I've raised with Itead https://support.itead.cc/support/discussions/topics/11000026824

At the moment, there is no discovery, but that would be fairly easy to implement.

## See Also

There is a thread on the Home Assistant Community here discussing this component https://community.home-assistant.io/t/new-custom-component-sonoff-lan-mode-local-with-stock-firmware/88132/66
