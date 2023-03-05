import contextlib
import functools
import json
import logging
from collections import defaultdict
from dataclasses import asdict

import trio
from trio_websocket import serve_websocket, ConnectionClosed

from models import WindowBounds, Bus

loger = logging.getLogger('server')

PAUSE = 0.1
buses = defaultdict()


async def talk_to_browser(request):
    ws = await request.accept()
    loger.info(f'open remote connection on port {ws.remote.port}')

    bounds = WindowBounds()

    async with trio.open_nursery() as nursery:
        nursery.start_soon(listen_browser, ws, bounds)
        nursery.start_soon(send_buses, ws, bounds)

    loger.info(f'close remote connection')


async def send_buses(ws, bounds):
    while True:

        buses_coords = [
            asdict(bus) for bus_id, bus in buses.items() if bounds.is_inside(bus.lat, bus.lng)
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
                bus = Bus(**bus_msg)
                buses[bus.busId] = bus
        except ConnectionClosed:
            break


async def listen_browser(ws, bounds: WindowBounds):
    while True:
        try:
            message = await ws.get_message()
            loger.debug(f'receive new bounds {message}')
            new_bounds = json.loads(message)['data']
            bounds.update(new_bounds)
            loger.debug(f'set new bounds {bounds}')
        except ConnectionClosed:
            break


async def main():
    partial_talk_to_browser = functools.partial(serve_websocket, talk_to_browser, '0.0.0.0', 8000, ssl_context=None)
    partial_handle_bus_msg = functools.partial(serve_websocket, handle_bus_msg, '0.0.0.0', 8080, ssl_context=None)

    async with trio.open_nursery() as nursery:
        nursery.start_soon(partial_talk_to_browser)
        nursery.start_soon(partial_handle_bus_msg)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(levelname)s:%(name)s:%(message)s')
    trio_loger = logging.getLogger('trio-websocket')
    trio_loger.setLevel(level=logging.INFO)

    with contextlib.suppress(KeyboardInterrupt):
        trio.run(main)
