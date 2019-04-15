# sonoff-lan-mode-homeassistant
Home Assistant platform to control Sonoff switches running the latest Itead firmware, locally (LAN mode).

**This will only work for Sonoff devices running a recent version of the stock (Itead / eWeLink) firmware, which have been blocked from accessing the internet (to put them in LAN Mode).**

This is a simple platform to control switch devices which can normally only be controlled using the Itead cloud app (eWeLink). It may be useful to you if you've bought a Sonoff device and want to control it locally, but cannot flash firmware such as [Tasmota](https://github.com/arendst/Sonoff-Tasmota/) for whatever reason (e.g. lack of tools or confidence soldering).

## Supported devices (running firmware 1.8.0 or later) *:
- Sonoff S20 **
- Sonoff S26
- Sonoff S85
- Sonoff T1 UK/US/EU 1 Gang
- Sonoff S30
- Sonoff S31 Lite
- Sonoff Basic
- Sonoff RF
- Sonoff Slampher
- Sonoff SV
- Sonoff Touch EU/US
- Any other Sonoff / eWeLink device running firmware version 1.8.0 or later

\* I currently only own a Sonoff Basic so haven't actually tested with these devices. However, I am very confident that if your device works with the eWeLink app in LAN Mode, we can get it working with this component - we might need a bit of joint investigation (e.g. `tcpdump` of communication from app) first to get it working!

\*\* Some Sonoff devices seem to not boot directly into LAN mode despite internet access being blocked; there is an ongoing issue open to investigate this and attempt to automate the process of forcing a Sonoff into LAN mode.
Until this is implemented / resolved, for some devices you may need to let it first boot with internet access, then block it's connectivity to get it into LAN mode (which is quite inconvenient if your device cannot be permanently powered).

## What is LAN Mode?
Since mid 2018, the firmware Itead have shipped with Sonoff devices has provided a feature called "LAN Mode" which allows the device to be controlled directly on the local network using a WebSocket connection on port 8081.

The feature is designed to only be used when there is no connection to the Itead cloud servers (e.g. if your internet connection is down, or their servers are down). As such, it is only enabled when the device is connected to your WiFi network, but unable to reach the Itead servers. You can find out more about the feature in the [Itead FAQ page](https://help.ewelink.cc/hc/en-us/articles/360007134171-LAN-Mode-Tutorial).

Here's a video demonstration of a Sonoff Basic being controlled in LAN mode: [https://www.youtube.com/watch?v=sxtt2cNm8g8](https://www.youtube.com/watch?v=sxtt2cNm8g8)

## Setup
Before you can use this platform to control your Sonoff from Home Assistant, you should perform the following setup steps:
1. Initialise the Sonoff device normally using the eWeLink app, connecting it to your home WiFi network etc.
2. Check you can switch the device on/off "normally" (via the Itead cloud) using the eWeLink app.
3. Find out the IP address of the device, and make that IP address static on your router so this doesn't change in future.
    - You can usually do this from the admin page of most home broadband routers (look for "DHCP").
4. Block the Sonoff from accessing the internet at all, but ensure it can still talk to other devices in your home network.
    - I used the "IP Filtering" page in my home broadband router again, blocking all IP ranges except 192.168.0.0/24 for the Sonoff's IP address.
5. Wait a couple of minutes for the Sonoff LED to start flashing (two flashes every 2 seconds).
    - This means it has given up trying to connect to Itead servers, and is now in "LAN mode".

Congrats, you can now uninstall the eWeLink app - you'll won't need it again as your Sonoff can now be controlled directly via WebSocket messages on port 8081!

## Installation
To use this platform, copy switch.py to "<home assistant config dir>/custom_components/sonoff_lan_mode/switch.py" and add the config below to configuration.yaml

```
switch:
  - platform: sonoff_lan_mode
    name: // Switch Name
    host: // Local IP address of device
    icon: // [Optional] Custom icon for device
```

Example:
```
switch:
  - platform: sonoff_lan_mode
    name: Kitchen Ceiling
    host: 192.168.0.72
    icon: mdi:bulb
```

## Future

I'm aware this platform is very primitive at the moment, with no error handling, caching or even status checking implemented yet. I'll probably try and improve it a bit myself, but I'm new to Home Assistant so contributions are very much welcome!

For anyone else who is interested in debugging / reverse engineering the Sonoff "LAN mode" protocol, here's a packet capture I made showing the whole interaction between my internet-access-blocked Sonoff and the eWeLink app, enabling LAN mode, finding the Sonoff and switching it on/off a couple of times:
https://www.dropbox.com/s/qwmkcjnvkdf8a8u/30-12-2018-12.10-filtered-sonoff.pcap?dl=0


