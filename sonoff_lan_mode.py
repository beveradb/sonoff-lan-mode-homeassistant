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

REQUIREMENTS = ['websocket-client==0.54.0']

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


def set_sonoff_state(sonoff_device, state):
    timestamp = str(time()).replace('.', '')
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
    sonoff_device.get_ws.send(update_state_message_json)

    response_message = sonoff_device.get_ws.recv()
    print("Response: '%s'" % response_message)


class SonoffDevice(SwitchDevice):
    """Representation of a Sonoff switch."""

    def __init__(self, host, port, name, icon):
        """Initialize the Sonoff switch."""
        self._host = host
        self._port = port
        self._name = name
        self._icon = icon
        self._state = False
        self._ws = None
        self.init_ws_connection()

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

    @property
    def get_ws(self):
        return self._ws

    def turn_on(self, **kwargs):
        """Turn Sonoff switch on."""
        set_sonoff_state(self, "on")
        self._state = True

    def turn_off(self, **kwargs):
        """Turn Sonoff switch off."""
        set_sonoff_state(self, "off")
        self._state = False

    def init_ws_connection(self):
        from websocket import create_connection
        timestamp = str(time()).replace('.', '')

        ws_address = "ws://" + self._host + ":8081/"
        self._ws = create_connection("ws://" + self._host + ":8081/")
        logger.info("connecting to " + ws_address)
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
        self._ws.send(initiate_session_message_json)

        response_message = self._ws.recv()
        print("Response: '%s'" % response_message)


def setup_platform(hass, config, add_devices, discovery_info=None):
    devices = config.get(CONF_SWITCHES)
    switches = []

    for object_id, device_config in devices.items():
        add_sonoff_device(config, 8081, device_config.get(CONF_FRIENDLY_NAME, object_id))

    name = config.get(CONF_NAME)

    if name:
        switches.append(add_sonoff_device(config, 8081, name))

    add_devices(switches)


def add_sonoff_device(config, port, name):
    return SonoffDevice(
        config.get(CONF_HOST),
        port,
        name,
        config.get(CONF_ICON)
    )
