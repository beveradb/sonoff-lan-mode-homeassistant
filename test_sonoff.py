import logging, time, hmac, hashlib, random, base64, json, socket, requests, re, threading, websocket

_LOGGER = logging.getLogger(__name__)


class Sonoff():
    def __init__(self):
        self._wshost = "echo.websocket.org"  # Replace with local LAN IP, e.g. 192.168.0.112
        self._wsport = "80"  # Replace with "8081" to connect to LAN mode Sonoff

        self._ws = None
        self._devices = []

        self.thread = threading.Thread(target=self.init_websocket)
        self.thread.daemon = True
        self.thread.start()

    async def state_listener(self, event):
        if not self.get_ws().connected:
            _LOGGER.error('websocket is not connected')
            return

        _LOGGER.debug('received state event change from: %s' % event.data['deviceid'])

        new_state = event.data['state']

        # convert from True/False to on/off
        if isinstance(new_state, (bool)):
            new_state = 'on' if new_state else 'off'

        device = self.get_device(event.data['deviceid'])
        outlet = event.data['outlet']

        if outlet is not None:
            _LOGGER.debug("Switching `%s - %s` on outlet %d to state: %s", device['deviceid'], device['name'],
                          (outlet + 1), new_state)
        else:
            _LOGGER.debug("Switching `%s` to state: %s", device['deviceid'], new_state)

        if not device:
            _LOGGER.error('unknown device to be updated')
            return False

        """
        the payload rule is like this:
          normal device (non-shared) 
              apikey      = login apikey (= device apikey too)

          shared device
              apikey      = device apikey
              selfApiKey  = login apikey (yes, it's typed corectly selfApikey and not selfApiKey :|)
        """
        if outlet is not None:
            params = {'switches': device['params']['switches']}
            params['switches'][outlet]['switch'] = new_state

        else:
            params = {'switch': new_state}

        payload = {
            'action': 'update',
            'userAgent': 'app',
            'params': params,
            'apikey': device['apikey'],
            'deviceid': str(device['deviceid']),
            'sequence': str(time.time()).replace('.', ''),
            'controlType': device['params']['controlType'] if 'controlType' in device['params'] else 4,
            'ts': 0
        }

        # this key is needed for a shared device
        if device['apikey'] != self.get_user_apikey():
            payload['selfApikey'] = self.get_user_apikey()

        self.get_ws().send(json.dumps(payload))

        # set also te pseudo-internal state of the device until the real refresh kicks in
        for idxd, dev in enumerate(self._devices):
            if dev['deviceid'] == device['deviceid']:
                if outlet is not None:
                    self._devices[idxd]['params']['switches'][outlet]['switch'] = new_state
                else:
                    self._devices[idxd]['params']['switch'] = new_state

    def init_websocket(self):
        # keep websocket open indefinitely
        while True:
            _LOGGER.debug('(re)init websocket')
            self._ws = WebsocketListener(sonoff=self, on_message=self.on_message, on_error=self.on_error)

            try:
                # 145 interval is defined by the first websocket response after login
                self._ws.run_forever(ping_interval=145)
            finally:
                self._ws.close()

    def on_message(self, *args):
        data = args[-1]  # to accomodate the weird behaviour where the function receives 2 or 3 args

        _LOGGER.debug('websocket msg: %s', data)

        data = json.loads(data)
        if 'action' in data and data['action'] == 'update' and 'params' in data:
            if 'switch' in data['params'] or 'switches' in data['params']:
                for idx, device in enumerate(self._devices):
                    if device['deviceid'] == data['deviceid']:
                        self._devices[idx]['params'] = data['params']

                        if 'switches' in data['params']:
                            for switch in data['params']['switches']:
                                self.set_entity_state(data['deviceid'], data['params']['switch'], switch['outlet'])
                        else:
                            self.set_entity_state(data['deviceid'], data['params']['switch'])

                        break  # do not remove

    def on_error(self, *args):
        error = args[-1]  # to accomodate the case when the function receives 2 or 3 args
        _LOGGER.error('websocket error: %s' % str(error))

    def is_grace_period(self):
        grace_time_elapsed = self._skipped_login * int(SCAN_INTERVAL.total_seconds())
        grace_status = grace_time_elapsed < int(self._grace_period.total_seconds())

        if grace_status:
            self._skipped_login += 1

        return grace_status

    def set_entity_state(self, deviceid, state, outlet=None):
        entity_id = 'switch.%s%s' % (deviceid, '_' + str(outlet + 1) if outlet is not None else '')
        attr = self._hass.states.get(entity_id).attributes
        self._hass.states.set(entity_id, state, attr)

    def update_devices(self):
        # we are in the grace period, no updates to the devices
        if self._skipped_login and self.is_grace_period():
            _LOGGER.info("Grace period active")
            return self._devices

        r = requests.get(
            'https://{}-api.coolkit.cc:8080/api/user/device?lang=en&apiKey={}&getTags=1'.format(self._api_region,
                                                                                                self.get_user_apikey()),
            headers=self._headers)

        resp = r.json()
        if 'error' in resp and resp['error'] in [HTTP_BAD_REQUEST, HTTP_UNAUTHORIZED]:
            # @IMPROVE add maybe a service call / switch to deactivate sonoff component
            if self.is_grace_period():
                _LOGGER.warning("Grace period activated!")

                # return the current (and possible old) state of devices
                # in this period any change made with the mobile app (on/off) won't be shown in HA
                return self._devices

            _LOGGER.info("Re-login component")
            self.do_login()

        self._devices = r.json()
        return self._devices

    def get_devices(self, force_update=False):
        if force_update:
            return self.update_devices()

        return self._devices

    def get_device(self, deviceid):
        for device in self.get_devices():
            if 'deviceid' in device and device['deviceid'] == deviceid:
                return device

    def get_bearer_token(self):
        return self._bearer_token

    def get_user_apikey(self):
        return self._user_apikey

    def get_ws(self):
        return self._ws

    def get_wshost(self):
        return self._wshost

    def get_wsport(self):
        return self._wsport

    def get_outlets(self, device):
        # information found in ewelink app source code
        name_to_outlets = {
            'SOCKET': 1,
            'SWITCH_CHANGE': 1,
            'GSM_UNLIMIT_SOCKET': 1,
            'SWITCH': 1,
            'THERMOSTAT': 1,
            'SOCKET_POWER': 1,
            'GSM_SOCKET': 1,
            'POWER_DETECTION_SOCKET': 1,
            'SOCKET_2': 2,
            'GSM_SOCKET_2': 2,
            'SWITCH_2': 2,
            'SOCKET_3': 3,
            'GSM_SOCKET_3': 3,
            'SWITCH_3': 3,
            'SOCKET_4': 4,
            'GSM_SOCKET_4': 4,
            'SWITCH_4': 4,
            'CUN_YOU_DOOR': 4
        }

        uiid_to_name = {
            1: "SOCKET",
            2: "SOCKET_2",
            3: "SOCKET_3",
            4: "SOCKET_4",
            5: "SOCKET_POWER",
            6: "SWITCH",
            7: "SWITCH_2",
            8: "SWITCH_3",
            9: "SWITCH_4",
            10: "OSPF",
            11: "CURTAIN",
            12: "EW-RE",
            13: "FIREPLACE",
            14: "SWITCH_CHANGE",
            15: "THERMOSTAT",
            16: "COLD_WARM_LED",
            17: "THREE_GEAR_FAN",
            18: "SENSORS_CENTER",
            19: "HUMIDIFIER",
            22: "RGB_BALL_LIGHT",
            23: "NEST_THERMOSTAT",
            24: "GSM_SOCKET",
            25: 'AROMATHERAPY',
            26: "RuiMiTeWenKongQi",
            27: "GSM_UNLIMIT_SOCKET",
            28: "RF_BRIDGE",
            29: "GSM_SOCKET_2",
            30: "GSM_SOCKET_3",
            31: "GSM_SOCKET_4",
            32: "POWER_DETECTION_SOCKET",
            33: "LIGHT_BELT",
            34: "FAN_LIGHT",
            35: "EZVIZ_CAMERA",
            36: "SINGLE_CHANNEL_DIMMER_SWITCH",
            38: "HOME_KIT_BRIDGE",
            40: "FUJIN_OPS",
            41: "CUN_YOU_DOOR",
            42: "SMART_BEDSIDE_AND_NEW_RGB_BALL_LIGHT",
            43: "",
            44: "",
            45: "DOWN_CEILING_LIGHT",
            46: "AIR_CLEANER",
            49: "MACHINE_BED",
            51: "COLD_WARM_DESK_LIGHT",
            52: "DOUBLE_COLOR_DEMO_LIGHT",
            53: "ELECTRIC_FAN_WITH_LAMP",
            55: "SWEEPING_ROBOT",
            56: "RGB_BALL_LIGHT_4",
            57: "MONOCHROMATIC_BALL_LIGHT",
            59: "MUSIC_LIGHT_BELT",
            60: "NEW_HUMIDIFIER",
            61: "KAI_WEI_ROUTER",
            62: "MEARICAMERA",
            66: "ZIGBEE_MAIN_DEVICE",
            67: "RollingDoor",
            68: "KOOCHUWAH",
            1001: "BLADELESS_FAN",
            1003: "WARM_AIR_BLOWER",
            1000: "ZIGBEE_SINGLE_SWITCH",
            1770: "ZIGBEE_TEMPERATURE_SENSOR",
            1256: "ZIGBEE_LIGHT"
        }

        if device['uiid'] in uiid_to_name.keys() and \
                uiid_to_name[device['uiid']] in name_to_outlets.keys():
            return name_to_outlets[uiid_to_name[device['uiid']]]

        return None


class WebsocketListener(threading.Thread, websocket.WebSocketApp):
    def __init__(self, sonoff, on_message=None, on_error=None):
        self._sonoff = sonoff

        threading.Thread.__init__(self)
        websocket.WebSocketApp.__init__(self, 'ws://{}:{}/api/ws'.format(self._sonoff.get_wshost(),
                                                                         self._sonoff.get_wsport()),
                                        on_open=self.on_open,
                                        on_error=on_error,
                                        on_message=on_message,
                                        on_close=self.on_close)

        self.connected = False
        self.last_update = time.time()

    def on_open(self, *args):
        self.connected = True
        self.last_update = time.time()

        payload = {
            'action': "userOnline",
            'userAgent': 'app',
            'version': 6,
            'nonce': ''.join([str(random.randint(0, 9)) for i in range(15)]),
            'apkVesrion': "1.8",
            'os': 'ios',
            'at': self._sonoff.get_bearer_token(),
            'apikey': self._sonoff.get_user_apikey(),
            'ts': str(int(time.time())),
            'model': 'iPhone10,6',
            'romVersion': '11.1.2',
            'sequence': str(time.time()).replace('.', '')
        }

        self.send(json.dumps(payload))

    def on_close(self, *args):
        _LOGGER.debug('websocket closed')
        self.connected = False

    def run_forever(self, sockopt=None, sslopt=None, ping_interval=0, ping_timeout=None):
        websocket.WebSocketApp.run_forever(self,
                                           sockopt=sockopt,
                                           sslopt=sslopt,
                                           ping_interval=ping_interval,
                                           ping_timeout=ping_timeout)


class SonoffDevice(Entity):
    """Representation of a Sonoff device"""

    def __init__(self, hass, device):
        """Initialize the device."""

        self._outlet = None
        self._sensor = None
        self._state = None

        self._hass = hass
        self._deviceid = device['deviceid']
        self._available = device['online']

        self._attributes = {
            'device_id': self._deviceid,
        }

    def get_device(self):
        for device in self._hass.data[DOMAIN].get_devices():
            if 'deviceid' in device and device['deviceid'] == self._deviceid:
                return device

        return None

    def get_state(self):
        device = self.get_device()

        # Pow & Pow R2:
        if 'power' in device['params']:
            self._attributes['power'] = device['params']['power']

        # Pow R2 only:
        if 'current' in device['params']:
            self._attributes['current'] = device['params']['current']
        if 'voltage' in device['params']:
            self._attributes['voltage'] = device['params']['voltage']

        # TH10/TH16
        if 'currentHumidity' in device['params'] and device['params']['currentHumidity'] != "unavailable":
            self._attributes['humidity'] = device['params']['currentHumidity']
        if 'currentTemperature' in device['params'] and device['params']['currentTemperature'] != "unavailable":
            self._attributes['temperature'] = device['params']['currentTemperature']

        if 'rssi' in device['params']:
            self._attributes['rssi'] = device['params']['rssi']

            # the device has more switches
        if self._outlet is not None:
            return device['params']['switches'][self._outlet]['switch'] == 'on' if device else False

        else:
            return device['params']['switch'] == 'on' if device else False

    def get_available(self):
        device = self.get_device()

        return device['online'] if device else False

    @property
    def should_poll(self):
        """Return the polling state."""
        return True

    @property
    def name(self):
        """Return the name of the switch."""
        return self._name

    @property
    def available(self):
        """Return true if device is online."""
        return self.get_available()

    # @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        """Update device state."""

        # we don't update here because there's 1 single thread that can be active at anytime
        # and the websocket will send the state update messages
        pass

    @property
    def device_state_attributes(self):
        """Return device specific state attributes."""
        return self._attributes
