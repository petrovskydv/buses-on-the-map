import functools
import json
from collections import defaultdict

import trio
from trio_websocket import serve_websocket, ConnectionClosed

buses = defaultdict()


async def talk_to_browser(request):
    ws = await request.accept()
    buses_msg = {
        "msgType": "Buses",
        "buses": [
            {"busId": "c790сс", "lat": 55.7500, "lng": 37.600, "route": "156"},
        ]
    }

    while True:
        try:
            buses_msgs = []
            for bus_id, bus in buses.items():
                buses_msgs.append(
                    {"busId": bus_id, "lat": bus['lat'], "lng": bus['lng'], "route": bus_id},
                )

            buses_msg['buses'] = buses_msgs
            await ws.send_message(json.dumps(buses_msg))
            await trio.sleep(2)
        except ConnectionClosed:
            break


async def handle_bus_msg(request):
    ws = await request.accept()
    while True:
        try:
            message = await ws.get_message()
            bus_msg = json.loads(message)
            buses[bus_msg['busId']] = bus_msg
        except ConnectionClosed:
            break


async def main():
    partial_talk_to_browser = functools.partial(serve_websocket, talk_to_browser, '127.0.0.1', 8000, ssl_context=None)
    partial_handle_bus_msg = functools.partial(serve_websocket, handle_bus_msg, '127.0.0.1', 8080, ssl_context=None)

    async with trio.open_nursery() as nursery:
        nursery.start_soon(partial_talk_to_browser)
        nursery.start_soon(partial_handle_bus_msg)


trio.run(main)
