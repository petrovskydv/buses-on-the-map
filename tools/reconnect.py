import functools

import trio


def relaunch_on_disconnect(exceptions, loger, time_out=2):
    def wrapper(func):
        @functools.wraps(func)
        async def wrapped(*args, **kwargs):
            while True:
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    loger.info('reconnect')
                    await trio.sleep(time_out)

        return wrapped

    return wrapper
