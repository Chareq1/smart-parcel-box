import RPi.GPIO as GPIO
import time

"""
src/components/dht_sensor.py

DHT Humidity and Temperature sensor component for a Raspberry Pi GPIO pin.

This module provides the DHTSensor class which encapsulates GPIO setup,
reading and cleanup for a humidity and temperature sensor connected to a GPIO pin.
"""


# GPIO Pin for DHT Sensor
DHT_SENSOR_PIN = 4


class DHTSensor:
    """
    Class for a DHT sensor connected to a Raspberry Pi GPIO pin.

    Attributes:
        logger: Logger instance for logging messages.
        temperature (float): Last read temperature value in Celsius.
        humidity (float): Last read humidity value in percentage.
    """

    def __init__(self, logger):
        """
        Initialize GPIO for the DHT sensor and set initial state.
        - Sets logger based on argument.
        - Initializes temperature and humidity to None.
        - Sets GPIO mode to BCM.
        - Configures `DHT_SENSOR_PIN` as an output with an initial HIGH state.
        - Sets sleep for 0.1.

        Args:
            logger: Logger instance for logging messages.
        """
        self.logger = logger
        self.temperature = None
        self.humidity = None
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(DHT_SENSOR_PIN, GPIO.OUT, initial=GPIO.HIGH)
        time.sleep(0.1)


    def _wait_for_level(self, level, timeout=0.1):
        """
        Wait for the GPIO pin to reach the specified level within the timeout.

        Args:
            level: GPIO.HIGH or GPIO.LOW to wait for.
            timeout: Maximum time to wait in seconds.

        Returns:
            bool: True if the level was reached, False if timeout occurred.
        """
        start_time = time.time()
        while GPIO.input(DHT_SENSOR_PIN) == level:
            if time.time() - start_time > timeout:
                return False
        return True


    def _handshake(self):
        """
        Perform the initial handshake with the DHT sensor.

        Returns:
            bool: True if handshake was successful, False otherwise.
        """
        GPIO.setup(DHT_SENSOR_PIN, GPIO.OUT)
        GPIO.output(DHT_SENSOR_PIN, GPIO.LOW)
        time.sleep(0.018)
        GPIO.output(DHT_SENSOR_PIN, GPIO.HIGH)
        time.sleep(0.00004)  # 40us

        GPIO.setup(DHT_SENSOR_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        if not self._wait_for_level(GPIO.HIGH):
            self.logger.warning("Timeout: waiting for sensor response HIGH.")
            return False
        if not self._wait_for_level(GPIO.LOW):
            self.logger.warning("Timeout: waiting for sensor response LOW.")
            return False
        return True


    def _read_data_bits(self):
        """
        Read 40 bits of data from the DHT sensor.

        Returns:
            bits (list): List of 40 bits read from the sensor,
            or None on timeout.
        """
        bits = []
        for _ in range(40):
            if not self._wait_for_level(GPIO.LOW, timeout=0.02):
                self.logger.warning("Timeout: waiting for LOW during bit read.")
                return None

            start_time = time.time()
            if not self._wait_for_level(GPIO.HIGH, timeout=0.02):
                self.logger.warning("Timeout: waiting for HIGH during bit read.")
                return None

            pulse_length = time.time() - start_time
            bits.append(1 if pulse_length > 0.00005 else 0)
        return bits


    def read(self):
        """
        Read temperature and humidity from the DHT sensor with
        checking bits and checksum.

        Returns:
            bool: True if read was successful, None otherwise.
        """
        if not self._handshake():
            return None

        bits = self._read_data_bits()
        if bits is None:
            return None

        data = []
        for i in range(0, 40, 8):
            byte = 0
            for j in range(8):
                byte = (byte << 1) | bits[i + j]
            data.append(byte)

        checksum = sum(data[0:4]) & 0xFF
        if data[4] != checksum:
            self.logger.warning(f"Checksum error: got {data[4]}, expected {checksum}")
            return None

        self.humidity = ((data[0] << 8) + data[1]) / 10.0
        temp_raw = ((data[2] & 0x7F) << 8) + data[3]
        self.temperature = -temp_raw / 10.0 if data[2] & 0x80 else temp_raw / 10.0

        return True


    def safe_read(self, retries=5, delay=1):
        """
        Attempt to read from the DHT sensor with retries.

        Args:
            retries (int): Number of read attempts.
            delay (int): Delay between attempts in seconds.
        """
        for attempt in range(retries):
            if self.read():
                return True
            self.logger.warning(f"Read attempt {attempt + 1}/{retries} failed, retrying...")
            time.sleep(delay)
        self.logger.error("Failed to read from DHT sensor after retries.")
        return False


    def cleanup(self):
        """
        Clean up GPIO resources for the configured pin.
        """
        GPIO.cleanup()
