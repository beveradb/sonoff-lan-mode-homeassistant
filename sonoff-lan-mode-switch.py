# name = data.get('name', 'world')
# logger.info("Hello {}".format(name))
# hass.bus.fire(name, { "wow": "from a Python script!" })
import json
from websocket import create_connection

sonoff_ipaddress = "192.168.0.72"

ws = create_connection("ws://" + sonoff_ipaddress + ":8081/")

initiate_session_message_json = json.dumps(
    {
        "action": "userOnline",
        "ts": "1546208633",
        "version": 6,
        "apikey": "nonce",
        "sequence": "1546208633",
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
            "switch": "on"
        },
        "sequence": "1546208633",
        "userAgent": "app"
    }
)

print("Updating state: " + update_state_message_json)
ws.send(update_state_message_json)

response_message = ws.recv()
print("Response: '%s'" % response_message)

print("Closing WebSocket")
ws.close()
