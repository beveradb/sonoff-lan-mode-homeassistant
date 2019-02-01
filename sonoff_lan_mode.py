"""
Support for Sonoff smart home devices, such as smart switches (e.g. Sonoff
Basic), plugs (e.g. Sonoff S20), and wall switches (e.g. Sonoff Touch),
when these devices are in "LAN Mode", directly over the local network.

For more details about this platform, please refer to the documentation at
https://github.com/beveradb/sonoff-lan-mode-homeassistant
"""
import logging

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.switch import (SwitchDevice, PLATFORM_SCHEMA)
from homeassistant.const import (CONF_HOST, CONF_NAME)

REQUIREMENTS = ['pysonofflan>=0.1.7']

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = 'Sonoff Switch'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_HOST): cv.string,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
})


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Sonoff LAN Mode Switch platform."""
    host = config.get(CONF_HOST)
    name = config.get(CONF_NAME)

    add_entities([HassSonoffSwitch(host, name)], True)


class HassSonoffSwitch(SwitchDevice):
    """Home Assistant representation of a Sonoff LAN Mode device."""

    def __init__(self, host, name):
        from pysonofflan import SonoffSwitch
        self._name = name
        self._state = None
        self._available = True
        self.shared_state = {"hass_self": self}
        self.sonoffdevice = SonoffSwitch(
            host=host,
            callback_after_update=self.device_update_callback,
            shared_state=self.shared_state,
            logger=_LOGGER
        )

    @property
    def name(self):
        return self._name

    @property
    def available(self) -> bool:
        """Return if switch is available."""
        return self._available

    @property
    def is_on(self):
        """Return true if switch is on."""
        return self._state

    async def turn_on(self, **kwargs):
        """Turn the switch on."""
        await self.sonoffdevice.turn_on()

    async def turn_off(self, **kwargs):
        """Turn the switch off."""
        await self.sonoffdevice.turn_off()

    async def device_update_callback(self, callback_self):
        """Handle state updates announced by the device itself."""
        self._state = \
            self.sonoffdevice.state == \
            self.sonoffdevice.SWITCH_STATE_ON

    async def update(self):
        """Update the device state."""
        try:
            self._state = self.sonoffdevice.state == \
                          self.sonoffdevice.SWITCH_STATE_ON
        except (Exception, OSError) as ex:
            if self._available:
                _LOGGER.warning(
                    "Could not read state for %s: %s", self.name, ex)
                self._available = False
