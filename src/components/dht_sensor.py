import RPi.GPIO as GPIO
import datetime
import time

# GPIO Pin Number 
DHT_SENSOR_PIN = 4

class DHTSensor:
    def __init__(self):
        GPIO.setmode(GPIO.BCM)
        self.humidity = None
        self.temperature_celsius = None
        self.temperature_fahrenheit = None

    def read(self):
        data = []
        GPIO.setup(DHT_SENSOR_PIN, GPIO.OUT)
        GPIO.output(DHT_SENSOR_PIN, GPIO.LOW)
        time.sleep(0.019)
        GPIO.setup(DHT_SENSOR_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        count = 0
        while GPIO.input(DHT_SENSOR_PIN) == GPIO.HIGH:
            count += 1
            if count > 10000:
                return None

        while GPIO.input(DHT_SENSOR_PIN) == GPIO.LOW:
            pass
        while GPIO.input(DHT_SENSOR_PIN) == GPIO.HIGH:
            pass

        for _ in range(40):
            while GPIO.input(DHT_SENSOR_PIN) == GPIO.LOW:
                pass
            t_start = time.time()
            while GPIO.input(DHT_SENSOR_PIN) == GPIO.HIGH:
                pass
            t_duration = time.time() - t_start
            data.append(1 if t_duration > 0.00005 else 0)

        bytes_data = []
        for i in range(0, 40, 8):
            byte = 0
            for j in range(8):
                byte <<= 1
                byte |= data[i + j]
            bytes_data.append(byte)

        checksum = sum(bytes_data[0:4]) & 0xFF
        if bytes_data[4] != checksum:
            print("Checksum error")
            return None

        humidity = ((bytes_data[0] << 8) + bytes_data[1]) / 10.0
        temperature = (((bytes_data[2] & 0x7F) << 8) + bytes_data[3]) / 10.0
        if bytes_data[2] & 0x80:
            temperature = -temperature

        self.temperature_celsius = round(temperature, 1)
        self.temperature_fahrenheit = round(((temperature * 9.0 / 5.0) + 32.0), 1)
        self.humidity = humidity

    def cleanup(self):
        GPIO.cleanup()