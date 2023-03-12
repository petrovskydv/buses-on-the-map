import argparse
import contextlib
import functools
import json
import logging
from collections import defaultdict
from dataclasses import asdict

import trio
from pydantic import ValidationError
from trio_websocket import serve_websocket, ConnectionClosed

from tools.models import WindowBounds, Bus, BrowserMsg

loger = logging.getLogger('server')

PAUSE = 0.1
buses = defaultdict()


async def talk_to_browser(request):
    ws = await request.accept()
    loger.info(f'open remote connection on port {ws.remote.port}')

    bounds = WindowBounds(south_lat=0, north_lat=0, west_lng=0, east_lng=0)

    async with trio.open_nursery() as nursery:
        nursery.start_soon(listen_browser, ws, bounds)
        nursery.start_soon(send_buses, ws, bounds)

    loger.info(f'close remote connection')


async def send_buses(ws, bounds):
    while True:

        buses_coords = [
            asdict(bus) for bus_id, bus in buses.items() if bounds.is_inside(bus.lat, bus.lng)
        ]
        if not buses_coords:
            await trio.sleep(PAUSE)
            continue
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
            if not isinstance(bus_msgs, list):
                bus = Bus(**bus_msgs)
                buses[bus.busId] = bus
                await ws.send_message('OK')
                continue
            for bus_msg in bus_msgs:
                bus = Bus(**bus_msg)
                buses[bus.busId] = bus
        except ConnectionClosed:
            break
        except ValidationError as e:
            error_msg = await create_error_msg(e)
            await ws.send_message(json.dumps(error_msg))


async def listen_browser(ws, bounds: WindowBounds):
    while True:
        try:
            message = await ws.get_message()
            loger.debug(f'receive new bounds {message}')
            browser_msg = BrowserMsg.parse_raw(message)

            # получаем координаты окна от браузера для фильтрации автобусов
            bounds.update(browser_msg.data.dict())
            loger.debug(f'set new bounds {bounds}')

            await ws.send_message('OK')
        except ConnectionClosed:
            break
        except ValidationError as e:
            error_msg = await create_error_msg(e)
            await ws.send_message(json.dumps(error_msg))


async def create_error_msg(e):
    error_msg = {'errors': [], 'msgType': 'Errors'}
    for item in e.errors():
        loc = '->'.join(item['loc'])
        error_msg['errors'].append(f'{loc}: {item["msg"]}')
    return error_msg


async def main():
    parser = argparse.ArgumentParser(description='Backend for busses map')
    parser.add_argument('--bus_port', type=int, default=8080, help='port for data about bus')
    parser.add_argument('--browser_port', type=int, default=8000, help='port for frontend')
    parser.add_argument('-v', '--verbose', choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'], default='DEBUG',
                        help='logging level')
    args = parser.parse_args()

    loger.setLevel(args.verbose)

    partial_talk_to_browser = functools.partial(serve_websocket, talk_to_browser, '0.0.0.0', args.browser_port,
                                                ssl_context=None)
    partial_handle_bus_msg = functools.partial(serve_websocket, handle_bus_msg, '0.0.0.0', args.bus_port,
                                               ssl_context=None)

    async with trio.open_nursery() as nursery:
        nursery.start_soon(partial_talk_to_browser)
        nursery.start_soon(partial_handle_bus_msg)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(levelname)s:%(name)s:%(message)s')
    trio_loger = logging.getLogger('trio-websocket')
    trio_loger.setLevel(level=logging.INFO)

    with contextlib.suppress(KeyboardInterrupt):
        trio.run(main)
