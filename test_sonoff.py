import json
import random
import threading
import time
import websocket
import logging
import logging.config


class Sonoff:
    def __init__(self):
        self.logger = self.configure_logger('default', 'test_sonoff.log')

        self.logger.debug('Sonoff class initialising')

        self._wshost = "localhost"  # Replace with local LAN IP, e.g. 192.168.0.112
        self._wsport = "8081"
        self._wsendpoint = "/"

        self._ws = None
        self._devices = []

        self.thread = threading.Thread(target=self.init_websocket(self.logger))
        self.thread.daemon = False
        self.thread.start()

    # Listen for state updates from HASS and update the device accordingly
    async def state_listener(self, event):
        if not self.get_ws().connected:
            self.logger.error('websocket is not connected')
            return

        self.logger.debug('received state event change from: %s' % event.data['deviceid'])

        new_state = event.data['state']

        # convert from True/False to on/off
        if isinstance(new_state, (bool)):
            new_state = 'on' if new_state else 'off'

        device = self.get_device(event.data['deviceid'])
        outlet = event.data['outlet']

        if outlet is not None:
            self.logger.info("Switching `%s - %s` on outlet %d to state: %s", device['deviceid'], device['name'],
                             (outlet + 1), new_state)
        else:
            self.logger.info("Switching `%s` to state: %s", device['deviceid'], new_state)

        if not device:
            self.logger.error('unknown device to be updated')
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

        self.logger.debug('sending state update websocket msg: %s', json.dumps(payload))

        self.get_ws().send(json.dumps(payload))

        # set also the pseudo-internal state of the device until the real refresh kicks in
        for idxd, dev in enumerate(self._devices):
            if dev['deviceid'] == device['deviceid']:
                if outlet is not None:
                    self._devices[idxd]['params']['switches'][outlet]['switch'] = new_state
                else:
                    self._devices[idxd]['params']['switch'] = new_state

    def init_websocket(self, logger):
        self.logger = logger
        self.logger.debug('initializing websocket')

        self._ws = WebsocketListener(sonoff=self, on_message=self.on_message, on_error=self.on_error)

        try:
            # 145 interval is defined by the first websocket response after login
            self._ws.run_forever(ping_interval=145)
        except:
            self.logger.error('websocket error occurred, shutting down')
        finally:
            self._ws.close()

    def on_message(self, *args):
        data = args[-1]  # to accommodate the weird behaviour where the function receives 2 or 3 args

        self.logger.debug('received websocket msg: %s', data)

        data = json.loads(data)

        if 'action' in data:
            self.logger.info('received action: %s', data['action'])

            if data['action'] == 'update' and 'params' in data:
                self.logger.debug('found update action in websocket update msg')
                if 'switch' in data['params'] or 'switches' in data['params']:
                    self.logger.debug('found switch/switches in websocket update msg')

                    self.logger.debug(
                        'searching for deviceid: {} in known devices {}'.format(self._devices.__str__(),
                                                                                data['deviceid'])
                    )

                    found_device = False
                    for idx, device in enumerate(self._devices):
                        if device['deviceid'] == data['deviceid']:
                            self._devices[idx]['params'] = data['params']
                            found_device = True

                            if 'switches' in data['params']:
                                for switch in data['params']['switches']:
                                    self.set_entity_state(data['deviceid'], data['params']['switch'], switch['outlet'])
                            else:
                                self.set_entity_state(data['deviceid'], data['params']['switch'])

                            break

                    if not found_device:
                        self.logger.debug('device not found in known devices, adding')
                        self.add_device(data)

        elif 'deviceid' in data:
            self.logger.debug('received hello from deviceid: %s, no action required', data['deviceid'])

    def on_error(self, *args):
        error = args[-1]  # to accommodate the case when the function receives 2 or 3 args
        self.logger.error('websocket error: %s' % str(error))

    def set_entity_state(self, deviceid, state, outlet=None):
        entity_id = 'switch.%s%s' % (deviceid, '_' + str(outlet + 1) if outlet is not None else '')
        self.logger.info("Success! TODO: update HASS state for entity: `%s` to state: %s", entity_id, state)

    def add_device(self, device):
        self._devices.append(device)
        return self._devices

    def get_devices(self):
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

    def configure_logger(self, name, log_path):
        logging.config.dictConfig({
            'version': 1,
            'formatters': {
                'default': {'format': '%(asctime)s - %(levelname)s - %(message)s', 'datefmt': '%Y-%m-%d %H:%M:%S'}
            },
            'handlers': {
                'console': {
                    'level': 'DEBUG',
                    'class': 'logging.StreamHandler',
                    'formatter': 'default',
                    'stream': 'ext://sys.stdout'
                },
                'file': {
                    'level': 'DEBUG',
                    'class': 'logging.handlers.RotatingFileHandler',
                    'formatter': 'default',
                    'filename': log_path,
                    'maxBytes': 10000,
                    'backupCount': 3
                }
            },
            'loggers': {
                'default': {
                    'level': 'DEBUG',
                    'handlers': ['console', 'file']
                }
            },
            'disable_existing_loggers': False
        })
        return logging.getLogger(name)


class WebsocketListener(threading.Thread, websocket.WebSocketApp):
    def __init__(self, sonoff, on_message=None, on_error=None):
        self.logger = sonoff.logger
        self.logger.warning('WebsocketListener initialising...')

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
        self.logger.warning('WebsocketListener initialised')

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

        self.logger.debug('sending user online websocket msg: %s', json.dumps(payload))

        self.send(json.dumps(payload))

    def on_close(self, *args):
        self.logger.debug('websocket closed')
        self.connected = False

    def run_forever(self, sockopt=None, sslopt=None, ping_interval=5, ping_timeout=None,
                    http_proxy_host=None, http_proxy_port=None,
                    http_no_proxy=None, http_proxy_auth=None,
                    skip_utf8_validation=False,
                    host=None, origin=None, dispatcher=None,
                    suppress_origin=False, proxy_type=None):
        self.logger.debug('attempting to call WebSocketApp run_forever with ping_interval: {}'.format(ping_interval))

        websocket.WebSocketApp.run_forever(self,
                                           sockopt=sockopt,
                                           sslopt=sslopt,
                                           ping_interval=ping_interval,
                                           ping_timeout=ping_timeout)


if __name__ == '__main__':
    Sonoff()
