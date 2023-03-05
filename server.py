import contextlib
import functools
import json
import logging
from collections import defaultdict

import trio
from trio_websocket import serve_websocket, ConnectionClosed

loger = logging.getLogger('server')

PAUSE = 0.1
buses = defaultdict()


async def talk_to_browser(request):
    ws = await request.accept()

    while True:
        await listen_browser(ws)

        buses_coords = [
            {"busId": bus_id, "lat": bus['lat'], "lng": bus['lng'], "route": bus['route']}
            for bus_id, bus in buses.items()
        ]

        buses_msg = {
            "msgType": "Buses",
            "buses": buses_coords
        }
        try:
            await ws.send_message(json.dumps(buses_msg))
            await trio.sleep(PAUSE)
        except ConnectionClosed:
            break


async def handle_bus_msg(request):
    ws = await request.accept()
    while True:
        try:
            message = await ws.get_message()
            bus_msgs = json.loads(message)
            for bus_msg in bus_msgs:
                buses[bus_msg['busId']] = bus_msg
        except ConnectionClosed:
            break


async def listen_browser(ws):
    with contextlib.suppress(ConnectionClosed):
        message = await ws.get_message()
        loger.debug(message)
        bounds = json.loads(message)['data']
        return bounds


def is_inside(bounds, lat, lng):
    is_lat_in_bounds = bounds['north_lat'] > lat > bounds['south_lat']
    is_lng_in_bounds = bounds['east_lng'] > lng > bounds['west_lng']
    return all((is_lat_in_bounds, is_lng_in_bounds))


async def main():
    partial_talk_to_browser = functools.partial(serve_websocket, talk_to_browser, '127.0.0.1', 8000, ssl_context=None)
    partial_handle_bus_msg = functools.partial(serve_websocket, handle_bus_msg, '127.0.0.1', 8080, ssl_context=None)

    async with trio.open_nursery() as nursery:
        nursery.start_soon(partial_talk_to_browser)
        nursery.start_soon(partial_handle_bus_msg)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(levelname)s:%(name)s:%(message)s')
    trio_loger = logging.getLogger('trio-websocket')
    trio_loger.setLevel(level=logging.INFO)

    trio.run(main)
