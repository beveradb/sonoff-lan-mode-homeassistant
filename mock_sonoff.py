import json
import logging
import logging.config
import threading
import time

from websocket_server import WebsocketServer


class MockSonoff:
    def __init__(self):
        self.logger = self.configure_logger('default', 'mock_sonoff.log')
        self.logger.debug('MockSonoff class initialising')

        self.server = None
        websocket_thread = threading.Thread(target=self.init_websocket)
        websocket_thread.daemon = True
        websocket_thread.start()

        while True:
            time.sleep(1)

    def init_websocket(self):
        self.logger.debug('Running websocket server on port 8081 to simulate Sonoff')

        self.server = WebsocketServer(8081, '127.0.0.1', logging.ERROR)
        self.server.set_fn_new_client(self.new_client)
        self.server.set_fn_client_left(self.client_left)
        self.server.set_fn_message_received(self.on_message)
        self.server.run_forever()

    def new_client(self, client, server):
        self.logger.debug("New client connected and was given id %d" % client['id'])

    def client_left(self, client, server):
        self.logger.debug("Client(%d) disconnected" % client['id'])

    def on_message(self, client, server, data):
        self.logger.debug('Received websocket msg: %s' % data)

        data = json.loads(data)
        self.logger.debug('Action: %s' % data['action'])

        if 'action' in data and data['action'] == 'userOnline':
            self.logger.debug('Found userOnline action, sending simulated hello response')
            self.server.send_message_to_all(json.dumps({
                "error": 0,
                "apikey": "09a15816-c289-4333-bf7b-aa52ffafdf96",
                "sequence": "1548124045842",
                "deviceid": "100060af40"
            }))

            self.logger.debug('Waiting 1 second, then sending simulated initial switch state')
            time.sleep(1)

            self.server.send_message_to_all(json.dumps({
                "userAgent": "device",
                "apikey": "09a15816-c289-4333-bf7b-aa52ffafdf96",
                "deviceid": "100060af40",
                "action": "update",
                "params": {
                    "switch": "off"
                }
            }))

            # WIP: This mocks the multi-outlet device provided by user PlayedIn in issue #6
            # self.server.send_message_to_all(json.dumps({
            #     "userAgent": "device",
            #     "apikey": "nonce",
            #     "deviceid": "100040e943",
            #     "action": "update",
            #     "params": {
            #         "switches": [{"switch": "off", "outlet": 0}, {"switch": "off", "outlet": 1},
            #                      {"switch": "off", "outlet": 2}, {"switch": "off", "outlet": 3}]
            #     }
            # }))

            self.logger.debug('Now waiting 10 seconds before simulating manual switch ON')
            time.sleep(10)

            self.logger.debug("Sending simulated switch ON message to client %d" % client['id'])
            self.server.send_message_to_all(json.dumps({
                "userAgent": "device",
                "apikey": "09a15816-c289-4333-bf7b-aa52ffafdf96",
                "deviceid": "100060af40",
                "action": "update",
                "params": {
                    "switch": "on"
                }
            }))

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


if __name__ == '__main__':
    MockSonoff()
