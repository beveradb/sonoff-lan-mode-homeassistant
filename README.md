# sonoff-lan-mode-homeassistant
Home Assistant platform to control Sonoff switches running the latest Itead firmware, locally (LAN mode).

**This will only work for Sonoff devices running a recent version of the stock (Itead / eWeLink) firmware.**

This is a simple platform to control switch devices which can normally only be controlled using the Itead cloud app (eWeLink). It may be useful to you if you've bought a Sonoff device and want to control it locally, but cannot flash firmware such as Tasmota for whatever reason (e.g. lack of tools or confidence soldering).

## Supported devices (running firmware 1.8.0 or later):
- Sonoff S20
- Sonoff S26
- Sonoff S85
- Sonoff T1 UK/US/EU 1 Gang
- S30
- Sonoff Basic
- Sonoff RF 
- Slampher
- Sonoff SV
- Sonoff Touch EU/US
- S31 Lite
- 1 Channel Inching/Self-locking Mode Wifi wireless Switch 5V/12V
- Inching/Self-locking Wifi Wireless Switch 5V
- Any other eWeLink-compatible device running firmware version 1.8.0 or later

## What is LAN Mode?
Since mid 2018, the firmware Itead have shipped with Sonoff devices has provided a feature called "LAN Mode" which allows the device to be controlled directly on the local network using a WebSocket connection on port 8081.

The feature is designed to only be used when there is no connection to the Itead cloud servers (e.g. if your internet connection is down, or their servers are down). As such, it is only enabled when the device is connected to your WiFi network, but unable to reach the Itead servers. You can find out more about the feature in the [Itead FAQ page](https://help.ewelink.cc/hc/en-us/articles/360007134171-LAN-Mode-Tutorial).

## Setup
Before you can use this platform to control your Sonoff from Home Assistant, you should perform the following setup steps:
- First, add/initialise the Sonoff device normally using the eWeLink app, including connecting it to your home WiFi network etc.
- Check you can switch the device on/off "normally" (via the Itead cloud) using the eWeLink app.
- Find out the IP address of the device, and give it a static local IP address so it can't get a different IP address from your router's DHCP server. You can usually do this from the admin page of most home broadband routers (look for "DHCP").
- Now, block it from accessing the internet at all. There are several ways you can do this, but I used the "IP Filtering" page in my home broadband router again, blocking all IP ranges except 192.168.0.0/24 for the Sonoff's IP address.
- Wait a couple of minutes for the Sonoff LED to start flashing (two flashes every 2 seconds) - this means it has given up trying to connect to Itead servers and is now in "LAN mode".

Congrats, you can now uninstall the eWeLink app - you'll won't need it again as your Sonoff can now be controlled directly via WebSocket messages on port 8081!

## Installation
To use this platform, copy sonoff_lan_mode.py to "<home assistant config dir>/custom_components/switch" and add the config below to configuration.yaml

```
switch:
  - platform: sonoff_lan_mode
    name: // Switch Name
    host: // Local IP address of device
```
