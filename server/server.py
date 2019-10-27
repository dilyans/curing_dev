import logging
import aiohttp
from aiohttp import web
import json
import asyncio
import weakref
from datetime import datetime
from device import Device
try: # this is available only on raspberry pi
    import Adafruit_DHT
except ImportError: # use mock if not available
    from mock.adafruit_mock import Adafruit_DHT

log = logging.getLogger(__name__)

sockets = set()
config = None
devices = {}
queue = asyncio.Queue()

def create_json_response(cmd, payload):
    data = {
        'cmd': cmd,
        'payload': payload
    }
    return data


async def curing_control_loop(app):
    while True:
        now = datetime.now()
        dt_string = now.strftime("%d/%m/%Y %HH:%MM:%SS")
        await asyncio.sleep(config["sensor_update_interval"])
        humidity_in, temperature_in = Adafruit_DHT.read_retry(Adafruit_DHT.DHT22,
                        config["sensors"]["dht22_inside_pin"])
        humidity_out, temperature_out = Adafruit_DHT.read_retry(Adafruit_DHT.DHT22,
                        config["sensors"]["dht22_outside_pin"])
        if humidity_in is not None and temperature_in is not None and\
            humidity_out is not None and temperature_out is not None:
            current_sensor_data = {
                "t": temperature_in,
                "h": humidity_in,
                "out_t": temperature_out,
                "out_h": humidity_out
            }
            log.info('current sensor data: {}:{}:{}:{}', temperature_in,\
                    humidity_in, temperature_out, humidity_out)
            await queue.put(current_sensor_data)


async def sensor_data_push(app):
    log.info('starting sensor monitoring')
    msg = create_json_response("SENSOR_UPDATE",{"t":"1","h":"1"})
    while True:
        item = await queue.get()
        msg['payload'] = item
        data = json.dumps(msg)
        for ws in set(app['websockets']):
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
                await ws.send_str(json.dumps(resp, indent=1))
            elif cmd == 'SENSOR_UPDATE':
                resp = create_json_response(cmd, data['payload'])
                await ws.send_str(json.dumps(resp, indent=1))
            elif cmd == 'DEVICE_UPDATE':
                for device_name, state in data['payload'].items():
                    device = devices[device_name]
                    device.set_state(state)
                    resp = create_json_response(cmd, data['payload'])
                    await ws.send_str(json.dumps(resp, indent=1))
        elif msg.type == aiohttp.WSMsgType.CLOSE\
                or msg.type == aiohttp.WSMsgType.CLOSED\
                or msg.type == aiohttp.WSMsgType.ERROR:
            request.app['websocets'].remove(ws)
            break;
    print('websocket connection closed')
    return ws


async def init_web_server():
    app = web.Application()
    app['websockets'] = weakref.WeakSet()
    app.add_routes([web.get('/ws', websocket_handler)])
    app.router.add_static('/', path=str('../static'))
    app.on_startup.append(start_background_tasks)
    app.on_cleanup.append(cleanup_background_tasks)
    return app


async def start_background_tasks(app):
    app['websoct_listener'] = asyncio.create_task(sensor_data_push(app))
    app['temp_control'] = asyncio.create_task(curing_control_loop(app))


async def cleanup_background_tasks(app):
    app['websoct_listener'].cancel()
    app['temp_control'].cancel()
    await app['websoct_listener']
    await app['temp_control']


def init_devices():
    for key, value in config['devices'].items():
        device = Device(name=key, pin=value['pin'], state=value['initial_state'])
        print("key: {} | value: {}".format(key, value))
        devices[key]= device


def load_config():
    global config
    with open('config.json') as config_file:
        config = json.load(config_file)


def main():
    logging.basicConfig(level=logging.DEBUG)
    load_config()
    init_devices()
    app = init_web_server()
    web.run_app(app)


if __name__ == '__main__':
    main()
