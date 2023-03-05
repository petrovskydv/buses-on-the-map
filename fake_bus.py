import argparse
import contextlib
import itertools
import json
import logging
import random
from sys import stderr

import trio
from trio_websocket import open_websocket_url, ConnectionClosed, HandshakeError

from load_routes import load_routes
from reconnect import relaunch_on_disconnect

loger = logging.getLogger(__name__)


async def main():
    parser = argparse.ArgumentParser(description='Create fake coordinates for buses')
    parser.add_argument('--server', default='ws://127.0.0.1:8080', help='server url')
    parser.add_argument('--routes_number', type=int, default=595, help='number of routes')
    parser.add_argument('--buses_per_route', type=int, default=10, help='number of buses per route')
    parser.add_argument('--websockets_number', type=int, default=10, help='number of websockets')
    parser.add_argument('--emulator_id', default='1', help='prefix for busId for many instances of script')
    parser.add_argument('--refresh_timeout', type=float, default=0.1, help='delay for updating server coordinates')
    parser.add_argument('--buffer_size', type=int, default=100, help='buffer size for messages to server')
    parser.add_argument('-v', '--verbose', choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'], default='INFO',
                        help='logging level')
    args = parser.parse_args()

    send_channels, receive_channels = create_channels_pool(args.websockets_number, args.buffer_size)

    async with trio.open_nursery() as nursery:
        for receive_channel in receive_channels:
            nursery.start_soon(send_updates, args.server, receive_channel, args.refresh_timeout, args.buffer_size)

        count = 0
        for route in load_routes():
            count += 1
            if count > args.routes_number:
                break
            for index in range(args.buses_per_route):
                send_channel = random.choice(send_channels)
                bus_id = generate_bus_id(args.emulator_id, route['name'], index)
                nursery.start_soon(run_bus, bus_id, route, send_channel, args.refresh_timeout)


def create_channels_pool(channels_count, buffer_size):
    send_channels = []
    receive_channels = []
    for _ in range(channels_count):
        loger.info(f'Create channel {_}')
        send_channel, receive_channel = trio.open_memory_channel(buffer_size)
        send_channels.append(send_channel)
        receive_channels.append(receive_channel)
    return send_channels, receive_channels


def generate_bus_id(emulator_id, route_id, bus_index):
    return f"{emulator_id}-{route_id}-{bus_index}"


async def run_bus(bus_id, route, send_channel, refresh_timeout):
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
            loger.info(f'send msg to channel: {bus_msg}')
            await trio.sleep(refresh_timeout)


@relaunch_on_disconnect((ConnectionClosed, HandshakeError,), loger)
async def send_updates(server_address, receive_channel, refresh_timeout, buffer_size):
    try:
        async with open_websocket_url(server_address) as ws:
            loger.info(f'open connection on port {ws.local.port}')
            msgs = []
            async for msg in receive_channel:

                loger.info(f'receive msg on port {ws.local.port}: {msg}')
                msgs.append(msg)
                if len(msgs) == buffer_size:
                    loger.info(f'send msg on port {ws.local.port}')
                    encoded_msgs = json.dumps(msgs, ensure_ascii=False)
                    await ws.send_message(encoded_msgs)
                    msgs.clear()
                    await trio.sleep(refresh_timeout)
    except OSError as ose:
        print('Connection attempt failed: %s' % ose, file=stderr)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
    trio_loger = logging.getLogger('trio-websocket')
    trio_loger.setLevel(level=logging.INFO)

    with contextlib.suppress(KeyboardInterrupt):
        trio.run(main)
