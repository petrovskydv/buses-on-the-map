import itertools
import json
import logging
import random

import trio
from sys import stderr
from trio_websocket import open_websocket_url

from load_routes import load_routes

PAUSE = 0.1
CHANNELS_COUNT = 10
ROUTE_BUSSES_COUNT = 3

loger = logging.getLogger(__name__)


async def main():
    url = 'ws://127.0.0.1:8080'
    send_channels, receive_channels = create_channels_pool(CHANNELS_COUNT)

    async with trio.open_nursery() as nursery:
        for receive_channel in receive_channels:
            nursery.start_soon(send_updates, url, receive_channel)

        for route in load_routes():
            for index in range(1, ROUTE_BUSSES_COUNT):
                send_channel = random.choice(send_channels)
                bus_id = generate_bus_id(route['name'], index)
                nursery.start_soon(run_bus, bus_id, route, send_channel)


def create_channels_pool(channels_count):
    send_channels = []
    receive_channels = []
    for _ in range(channels_count):
        loger.info(f'Create channel {_}')
        send_channel, receive_channel = trio.open_memory_channel(0)
        send_channels.append(send_channel)
        receive_channels.append(receive_channel)
    return send_channels, receive_channels


def generate_bus_id(route_id, bus_index):
    return f"{route_id}-{bus_index}"


async def run_bus(bus_id, route, send_channel):
    while True:
        coordinates = itertools.cycle(route['coordinates'])
        start = random.randint(1, len(route['coordinates']))
        for coord in itertools.islice(coordinates, start, None):
            lat, lng = coord
            bus_msg = {
                "busId": bus_id,
                "lat": lat,
                "lng": lng,
                "route": route['name']
            }
            await send_channel.send(bus_msg)
            loger.info(f'send msg: {bus_msg}')
            await trio.sleep(PAUSE)


async def send_updates(server_address, receive_channel):
    # while True:
    try:
        async with open_websocket_url(server_address) as ws:
            loger.info(f'open connection on port {ws.local.port}')

            async for msg in receive_channel:
                loger.info(f'receive msg on port {ws.local.port}: {msg}')
                encoded_msg = json.dumps(msg, ensure_ascii=False)
                loger.info(f'send msg on port {ws.local.port}: {msg}')
                await ws.send_message(encoded_msg)
                await trio.sleep(PAUSE)

            loger.info(f'no more msgs ')
        loger.info(f'close connection')

    except OSError as ose:
        print('Connection attempt failed: %s' % ose, file=stderr)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
    trio.run(main)
