import json

import trio
from sys import stderr
from trio_websocket import open_websocket_url

from load_routes import load_routes

PAUSE = 0.1


async def main():
    url = 'ws://127.0.0.1:8080'

    async with trio.open_nursery() as nursery:
        for route in load_routes():
            nursery.start_soon(run_bus, url, route['name'], route)


async def run_bus(url, bus_id, route):
    while True:
        try:
            async with open_websocket_url(url) as ws:
                for coord in route['coordinates']:
                    lat, lng = coord
                    bus_msg = {
                        "busId": bus_id,
                        "lat": lat,
                        "lng": lng,
                        "route": bus_id
                    }
                    await ws.send_message(json.dumps(bus_msg, ensure_ascii=False))
                    await trio.sleep(PAUSE)

        except OSError as ose:
            print('Connection attempt failed: %s' % ose, file=stderr)


if __name__ == '__main__':
    trio.run(main)