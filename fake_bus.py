import json

import trio
from sys import stderr
from trio_websocket import open_websocket_url

from load_routes import load_routes


async def main():
    url = 'ws://127.0.0.1:8080'

    async with trio.open_nursery() as nursery:
        for route in load_routes():
            nursery.start_soon(run_bus, url, route['name'], route)


async def run_bus(url, bus_id, route):
    bus_msg = {"busId": bus_id, "lat": 55.747629944737, "lng": 37.641726387317, "route": bus_id}
    try:
        async with open_websocket_url(url) as ws:
            for coord in route['coordinates']:
                lat, lng = coord
                bus_msg['lat'] = lat
                bus_msg['lng'] = lng
                await ws.send_message(json.dumps(bus_msg, ensure_ascii=False))
                await trio.sleep(1)

    except OSError as ose:
        print('Connection attempt failed: %s' % ose, file=stderr)


if __name__ == '__main__':
    trio.run(main)
