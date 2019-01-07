"""
Simple platform to control Sonoff switch devices in LAN Mode

For more details about this platform, please refer to the documentation at
https://github.com/beveradb/sonoff-lan-mode-homeassistant
"""
import voluptuous as vol
from homeassistant.components.switch import SwitchDevice, PLATFORM_SCHEMA
from homeassistant.const import (CONF_NAME, CONF_HOST, CONF_ID, CONF_SWITCHES, CONF_FRIENDLY_NAME, CONF_ICON)
import homeassistant.helpers.config_validation as cv
from time import time
import json
from venv import logger

REQUIREMENTS = ['websocket-client=0.54.0']

SWITCH_SCHEMA = vol.Schema({
    vol.Optional(CONF_ID, default=1): cv.string,
    vol.Optional(CONF_FRIENDLY_NAME): cv.string,
})

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_NAME): cv.string,
    vol.Optional(CONF_ICON): cv.icon,
    vol.Required(CONF_HOST): cv.string,
    vol.Optional(CONF_ID, default=1): cv.string,
    vol.Optional(CONF_SWITCHES, default={}):
        vol.Schema({cv.slug: SWITCH_SCHEMA}),
})


def set_sonoff_state(host, state):
    from websocket import create_connection
    timestamp = str(time()).replace('.', '')
    ws = create_connection("ws://" + host + ":8081/")

    initiate_session_message_json = json.dumps(
        {
            "action": "userOnline",
            "ts": timestamp,
            "version": 6,
            "apikey": "nonce",
            "sequence": timestamp,
            "userAgent": "app"
        }
    )

    print("Initiating session: " + initiate_session_message_json)
    ws.send(initiate_session_message_json)

    response_message = ws.recv()
    print("Response: '%s'" % response_message)

    update_state_message_json = json.dumps(
        {
            "action": "update",
            "deviceid": "nonce",
            "apikey": "nonce",
            "selfApikey": "nonce",
            "params": {
                "switch": state
            },
            "sequence": timestamp,
            "userAgent": "app"
        }
    )

    print("Updating state: " + update_state_message_json)
    ws.send(update_state_message_json)

    response_message = ws.recv()
    print("Response: '%s'" % response_message)

    print("Closing WebSocket")
    ws.close()


class SonoffDevice(SwitchDevice):
    """Representation of a Sonoff switch."""

    def __init__(self, host, name, icon):
        """Initialize the Sonoff switch."""
        self._host = host
        self._name = name
        self._icon = icon
        self._state = False

    @property
    def name(self):
        """Get name of Sonoff switch."""
        return self._name

    @property
    def is_on(self):
        """Check if Sonoff switch is on."""
        return self._state

    @property
    def icon(self):
        """Return the icon."""
        return self._icon

    def turn_on(self, **kwargs):
        """Turn Sonoff switch on."""
        set_sonoff_state(self._host, "on")
        self._state = True

    def turn_off(self, **kwargs):
        """Turn Sonoff switch off."""
        set_sonoff_state(self._host, "off")
        self._state = False


def setup_platform(hass, config, add_devices, discovery_info=None):
    devices = config.get(CONF_SWITCHES)
    switches = []

    for object_id, device_config in devices.items():
        switches.append(
            SonoffDevice(
                config.get(CONF_HOST),
                device_config.get(CONF_FRIENDLY_NAME, object_id),
                device_config.get(CONF_ICON)
            )
        )

    name = config.get(CONF_NAME)
    if name:
        switches.append(
            SonoffDevice(
                config.get(CONF_HOST),
                name,
                config.get(CONF_ICON)
            )
        )

    add_devices(switches)
