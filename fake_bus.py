import itertools
import json
import random

import trio
from sys import stderr
from trio_websocket import open_websocket_url

from load_routes import load_routes

PAUSE = 0.1


async def main():
    url = 'ws://127.0.0.1:8080'

    async with trio.open_nursery() as nursery:
        for route in load_routes():
            for index in range(1, 10):
                nursery.start_soon(run_bus, url, generate_bus_id(route['name'], index), route)


def generate_bus_id(route_id, bus_index):
    return f"{route_id}-{bus_index}"


async def run_bus(url, bus_id, route):
    while True:
        try:
            async with open_websocket_url(url) as ws:
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
                    await ws.send_message(json.dumps(bus_msg, ensure_ascii=False))
                    await trio.sleep(PAUSE)

        except OSError as ose:
            print('Connection attempt failed: %s' % ose, file=stderr)


if __name__ == '__main__':
    trio.run(main)
