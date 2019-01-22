import logging, time, hmac, hashlib, random, base64, json, socket, requests, re, threading, websocket

_LOGGER = logging.getLogger(__name__)


class Sonoff:
    def __init__(self):
        self._wshost = "echo.websocket.org"  # Replace with local LAN IP, e.g. 192.168.0.112
        self._wsport = "80"  # Replace with "8081" to connect to LAN mode Sonoff

        self._wsendpoint = "/"
        self._ws = None
        self._devices = []

        self.thread = threading.Thread(target=self.init_websocket)
        self.thread.daemon = True
        self.thread.start()

    # Listen for state updates from HASS and update the device accordingly
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

        if outlet is not None:
            params = {'switches': device['params']['switches']}
            params['switches'][outlet]['switch'] = new_state

        else:
            params = {'switch': new_state}

        payload = {
            'action': 'update',
            'userAgent': 'app',
            'params': params,
            'apikey': 'apikey',  # No apikey needed in LAN mode
            'deviceid': str(device['deviceid']),
            'sequence': str(time.time()).replace('.', ''),
            'controlType': device['params']['controlType'] if 'controlType' in device['params'] else 4,
            'ts': 0
        }

        self.get_ws().send(json.dumps(payload))

        # set also the pseudo-internal state of the device until the real refresh kicks in
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
        data = args[-1]  # to accommodate the weird behaviour where the function receives 2 or 3 args

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
        error = args[-1]  # to accommodate the case when the function receives 2 or 3 args
        _LOGGER.error('websocket error: %s' % str(error))

    def set_entity_state(self, deviceid, state, outlet=None):
        entity_id = 'switch.%s%s' % (deviceid, '_' + str(outlet + 1) if outlet is not None else '')
        _LOGGER.debug("(Not yet implemented!) Updating HASS state for entity: `%s` to state: %s", entity_id, state)

    def update_devices(self):
        return self._devices

    def get_devices(self, force_update=False):
        if force_update:
            return self.update_devices()

        return self._devices

    def get_device(self, deviceid):
        for device in self.get_devices():
            if 'deviceid' in device and device['deviceid'] == deviceid:
                return device

    def get_ws(self):
        return self._ws

    def get_wshost(self):
        return self._wshost

    def get_wsport(self):
        return self._wsport

    def get_wsendpoint(self):
        return self._wsendpoint


class WebsocketListener(threading.Thread, websocket.WebSocketApp):
    def __init__(self, sonoff, on_message=None, on_error=None):
        self._sonoff = sonoff

        threading.Thread.__init__(self)
        websocket.WebSocketApp.__init__(self, 'ws://{}:{}{}'.format(self._sonoff.get_wshost(),
                                                                    self._sonoff.get_wsport(),
                                                                    self._sonoff.get_wsendpoint()),
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
            'at': 'at',  # No bearer token needed in LAN mode
            'apikey': 'apikey',  # No apikey needed in LAN mode
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
