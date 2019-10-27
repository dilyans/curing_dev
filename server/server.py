import asyncio, aiohttp, json, logging, os, weakref
from aiohttp import web
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
today = datetime.today().date()

def create_json_response(cmd, payload):
    data = {
        'cmd': cmd,
        'payload': payload
    }
    return data


async def handle_sensor_data(data):
    min_t = config['conditions']['temperature']['min']
    max_t = config['conditions']['temperature']['max']
    min_h = config['conditions']['humidity']['min']
    max_h = config['conditions']['humidity']['max']
    fridge = devices['fridge']
    humidifier = devices['humidifier']
    dehumidifier = devices['dehumidifier']
    msg = create_json_response("DEVICE_UPDATE", {})
    is_fridge_changed = False
    is_humid_changed = False
    is_dedumid_changed = False
    if data['t'] > max_t:
        is_fridge_changed = fridge.set_state("ON")
    elif data['t'] < min_t:
        is_fridge_changed = fridge.set_state("OFF")
    if data['h'] >= max_h:
        is_humid_changed = humidifier.set_state("OFF")
        is_dedumid_changed = dehumidifier.set_state("ON")
    elif data['h'] <= min_h:
        is_humid_changed = humidifier.set_state("ON")
        is_dedumid_changed = dehumidifier.set_state("OFF")
    else:
        is_humid_changed = humidifier.set_state("OFF")
        is_dedumid_changed = dehumidifier.set_state("OFF")
    if is_fridge_changed:
        msg['payload'][fridge.name] = fridge.get_state().name
    if is_humid_changed:
        msg['payload'][humidifier.name] = humidifier.get_state().name
    if is_dedumid_changed:
        msg['payload'][dehumidifier.name] = dehumidifier.get_state().name
    #msg = create_json_response("SENSOR_UPDATE", current_sensor_data)

    if msg['payload']:
        await queue.put(msg)
    return


def write_sensor_data(data):
    global today
    now = datetime.today()
    if today != now.date():
        os.rename(config['datafile'], config['datafile']+"."+today)
        today = now.date()
    to_write = now.strftime("%H:%M:%S") + " " + data + "\n"
    with open(config['datafile'], "a") as f:
        f.write(to_write)
        f.flush()

async def curing_control_loop(app):
    while True:
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
            sensor_data = F'{humidity_in:.2f}:{temperature_in:.2f}:{humidity_out:.2f}:{temperature_out:.2f}'
            log.info(F'current sensor data: {sensor_data}')
            write_sensor_data(sensor_data)
            await handle_sensor_data(current_sensor_data)
            msg = create_json_response("SENSOR_UPDATE", current_sensor_data)
            #msg['payload'] = current_sensor_data
            await queue.put(msg)
        await asyncio.sleep(config["sensor_update_interval"])


async def sensor_data_push(app):
    log.info('starting sensor monitoring')
    msg = create_json_response("SENSOR_UPDATE",{"t":"1","h":"1"})
    while True:
        item = await queue.get()
        #msg['payload'] = item
        data = json.dumps(item)
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
            # TODO send previous sensor data
            if cmd == 'HISTORY':
                resp = create_json_response(cmd, json.dumps({}))
                await ws.send_str(json.dumps(resp, indent=1))
            # todo - this is not working
            elif cmd == 'SENSOR_UPDATE':
                resp = create_json_response(cmd, data['payload'])
                await ws.send_str(json.dumps(resp, indent=1))
            elif cmd == 'DEVICE_UPDATE':
                for device_name, state in data['payload'].items():
                    device = devices[device_name]
                    device.set_state(state)
                msg = create_json_response("DEVICE_UPDATE", {})
                for name, device in devices.items():
                    #device = Device(name=key, pin=value['pin'], state=value['initial_state'])
                    #print("key: {} | value: {}".format(key, value))
                    msg['payload'][name] = device.get_state().name
                    await queue.put(msg)


        elif msg.type == aiohttp.WSMsgType.CLOSE\
                or msg.type == aiohttp.WSMsgType.CLOSED\
                or msg.type == aiohttp.WSMsgType.ERROR:
            request.app['websocets'].remove(ws)
            break;
    log.info('websocket connection closed')
    return ws


async def init_web_server():
    app = web.Application()
    app['websockets'] = weakref.WeakSet()
    app.add_routes([web.get('/ws', websocket_handler)])
    app.router.add_static('/', path=str('../html/build'))
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
        log.info("key: {} | value: {}".format(key, value))
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
