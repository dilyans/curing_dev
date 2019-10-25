import logging
import aiohttp
from aiohttp import web
import json
import asyncio
from collections import defaultdict
import weakref
#from aio_timers import Timer

log = logging.getLogger(__name__)

sockets = set()

async def callback(ws):
    print("Hello {}!")
    await ws.send_str("test");

# timer is scheduled here


def create_json_response(cmd, payload):
    data = {
        'cmd': cmd,
        'payload': payload
    }
    json_d = json.dumps(data, indent=1)
    return json_d


async def timer(app):
    print('hello')
    msg = {
        "cmd": "SENSOR_UPDATE",
        "payload": {
            "t": "1",
            "h": "1"
        }
    }
    count = 0
    while True:
        await asyncio.sleep(3)
        for ws in set(app['websockets']):
            msg['payload']['t'] = count
            msg['payload']['h'] = count
            count += 1
            print('world')
            data = json.dumps(msg)
            await ws.send_str(data)


async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    request.app['websockets'].add(ws)
    async for msg in ws:
        if msg.type == aiohttp.WSMsgType.TEXT:
            log.info("got %s on socket: %s", msg.data, request.rel_url)
            data = json.loads(msg.data)
            cmd = data['cmd']
            if cmd == 'HISTORY':
                resp = create_json_response(cmd, json.dumps({}))
                await ws.send_str(resp)
            elif cmd == 'SENSOR_UPDATE':
                resp = create_json_response(cmd, data['payload'])
                await ws.send_str(resp)
            elif cmd == 'DEVICE_UPDATE':
                resp = create_json_response(cmd, data['payload'])
                await ws.send_str(resp)

    print('websocket connection closed')
    return ws


async def init_app():
    app = web.Application()
    app['websockets'] = weakref.WeakSet()
    app.add_routes([web.get('/ws', websocket_handler)])
    app.router.add_static('/', path=str('../static'))
    app.on_startup.append(start_background_tasks)
    app.on_cleanup.append(cleanup_background_tasks)
    return app


async def start_background_tasks(app):
    app['websoct_listener'] = asyncio.create_task(timer(app))


async def cleanup_background_tasks(app):
    app['websoct_listener'].cancel()
    await app['websoct_listener']

def main():
    logging.basicConfig(level=logging.DEBUG)

    app = init_app()
    web.run_app(app)


if __name__ == '__main__':
    main()
