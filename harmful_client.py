import json
import logging

import trio
from trio_websocket import open_websocket_url


async def main():
    try:
        async with open_websocket_url('ws://localhost:8000') as ws:
            data = {
                "msgType": "newBounds11",
                "data": {"south_lat11": 55.72633672900146, "north_lat": 55.77367652953477,
                         "west_lng": 37.52079963684083, "east_lng": 37.67924308776856}
            }
            await ws.send_message(json.dumps(data))
            message = await ws.get_message()
            print(f'response: {message}')
    except OSError as ose:
        logging.error('Connection attempt failed: %s', ose)


if __name__ == '__main__':
    trio.run(main)
