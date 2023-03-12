import json
import logging

import trio
from trio_websocket import open_websocket_url


async def main():
    try:
        async with open_websocket_url('ws://localhost:8080') as ws:
            data = {
                "busId": "123",
                "lat": 'vsdvd',
                "lng": 37.52079963684083,
                "route": 1234
            }
            await ws.send_message(json.dumps(data))
            message = await ws.get_message()
            print(f'response: {message}')
    except OSError as ose:
        logging.error('Connection attempt failed: %s', ose)


if __name__ == '__main__':
    trio.run(main)
