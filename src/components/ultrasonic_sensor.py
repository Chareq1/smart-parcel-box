import RPi.GPIO as GPIO
import time

"""
src/components/ultrasonic_sensor.py

Ultrasonic Distance Sensor component for a Raspberry Pi GPIO pin.

This module provides the UltrasonicSensor class which encapsulates GPIO setup,
reading and cleanup for a ultrasonic distance sensor connected to a GPIO pin.
"""


# GPIO Pins for Ultrasonic Sensor
TRIGGER_PIN = 23
ECHO_PIN = 24


class UltrasonicSensor:
    """
    Class for an ultrasonic distance sensor connected to a Raspberry Pi GPIO pin.

    Attributes:
        None
    """

    def __init__(self):
        """
        Initialize GPIO for the ultrasonic sensor.
        - Sets GPIO mode to BCM.
        - Sets up 'TRIGGER_PIN' as output and 'ECHO_PIN' as input.
        - Sets 'TRIGGER_PIN' to LOW.
        - Sleeps for 2 seconds to stabilize the sensor.
        """
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(TRIGGER_PIN, GPIO.OUT)
        GPIO.setup(ECHO_PIN, GPIO.IN)
        GPIO.output(TRIGGER_PIN, False)
        time.sleep(2)


    def __del__(self):
        """
        Clean up GPIO resources for the configured pin.
        """
        GPIO.cleanup([TRIGGER_PIN, ECHO_PIN])


    def __send_pulse(self):
        """
        Send a trigger pulse to the ultrasonic sensor.

        Returns:
            None
        """
        GPIO.output(TRIGGER_PIN, True)
        time.sleep(0.00001)  # 10 µs pulse
        GPIO.output(TRIGGER_PIN, False)


    def __measure_pulse(self, timeout=0.03):
        """
        Measure the duration of the echo pulse.

        Args:
            timeout (float): Maximum time to wait for the pulse in seconds.

        Returns:
            float: Duration of the echo pulse in seconds, or None if timeout occurs.
        """
        start_time = time.time()

        while GPIO.input(ECHO_PIN) == 0:
            if time.time() - start_time > timeout:
                return None
        pulse_start = time.time()

        while GPIO.input(ECHO_PIN) == 1:
            if time.time() - pulse_start > timeout:
                return None
        pulse_end = time.time()

        return pulse_end - pulse_start


    def get_distance(self, samples=5):
        """
        Get the average distance measured by the ultrasonic sensor over a number of samples.

        Args:
            samples (int): Number of distance samples to average.

        Returns:
            float: Average distance in centimeters, or None if no valid measurements.
        """
        distances = []

        for _ in range(samples):
            self.__send_pulse()
            duration = self.__measure_pulse()

            if duration is not None:
                distance = (duration * 34300) / 2
                distances.append(distance)

            time.sleep(0.05)

        if len(distances) == 0:
            return None

        avg_distance = sum(distances) / len(distances)
        return round(avg_distance, 2)
