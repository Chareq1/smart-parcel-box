import RPi.GPIO as GPIO
import time

DHT_SENSOR_PIN = 4

class DHTSensor:
    def __init__(self):
        GPIO.setmode(GPIO.BCM)
        self.humidity = None
        self.temperature = None

    def wait_for_level(self, level, timeout=0.02):
        start_time = time.time()
        while GPIO.input(DHT_SENSOR_PIN) == level:
            if (time.time() - start_time) > timeout:
                return False
        return True
    
    def handshake(self):
        if not self.wait_for_level(GPIO.HIGH):
            print("Timeout waiting for initial HIGH signal.")
            return None
        
        if not self.wait_for_level(GPIO.LOW):
            print("Timeout waiting for initial LOW signal.")
            return None
        
        if not self.wait_for_level(GPIO.HIGH):
            print("Timeout waiting for HIGH before data.")
            return None

    def read(self):
        data = []
        GPIO.setup(DHT_SENSOR_PIN, GPIO.OUT)
        GPIO.output(DHT_SENSOR_PIN, GPIO.LOW)
        time.sleep(0.02)
        GPIO.setup(DHT_SENSOR_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        self.handshake()

        for _ in range(40):
            if not self.wait_for_level(GPIO.LOW):
                print("Timeout waiting for LOW during data.")
                return None
            
            t_start = time.time()
            
            if not self.wait_for_level(GPIO.HIGH):
                print("Timeout waiting for HIGH during data.")
                return None
            
            t_duration = time.time() - t_start
            data.append(1 if t_duration > 0.00005 else 0)

        bytes_data = []
        for i in range(0, 40, 8):
            byte = 0
            for j in range(8):
                byte = (byte << 1) | data[i + j]
            bytes_data.append(byte)

        if bytes_data[4] != (sum(bytes_data[0:4]) & 0xFF):
            print("Checksum error")
            return None

        humidity = ((bytes_data[0] << 8) + bytes_data[1]) / 10.0
        temperature = (((bytes_data[2] & 0x7F) << 8) + bytes_data[3]) / 10.0
        
        if bytes_data[2] & 0x80:
            temperature = -temperature

        self.temperature = temperature
        self.humidity = humidity
        return True

    def safe_read(self, retries=5, delay=2):
        for _ in range(retries):
            if self.read():
                return True
            time.sleep(delay)
        print("Failed to read after retries.")
        return False

    def cleanup(self):
        GPIO.cleanup()
