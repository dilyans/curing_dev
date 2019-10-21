import logging
import aiohttp
from aiohttp import web
import json

log = logging.getLogger(__name__)

sockets = set()


def create_json_response(cmd, payload):
    data = {
        'cmd': cmd,
        'payload': payload
    }
    json_d = json.dumps(data, indent=1)
    return json_d


async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    sockets.add(ws)
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
    app['websockets'] = {}
    app.add_routes([web.get('/ws', websocket_handler)])
    app.router.add_static('/', path=str('../static'))
    return app


def main():
    logging.basicConfig(level=logging.DEBUG)

    app = init_app()
    web.run_app(app)


if __name__ == '__main__':
    main()
