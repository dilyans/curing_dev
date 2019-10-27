
class Adafruit_DHT:
    count = 0
    DHT22 = "dht22"

    def read_retry(sensor_type, pin):
        Adafruit_DHT.count += 1
        return [Adafruit_DHT.count, Adafruit_DHT.count]