import RPi.GPIO as GPIO

"""
src/components/door_sensor.py

Magnetic door sensor component for a Raspberry Pi GPIO pin.

This module provides the DoorSensor class which encapsulates GPIO setup,
reading and cleanup for a magnetic break switch connected to a GPIO pin.

Behavior:
  - GPIO.HIGH -> Door open
  - GPIO.LOW  -> Door closed
"""


# GPIO Pin for Door Sensor
DOOR_SENSOR_PIN = 12


class DoorSensor:
    """
    Class for a magnetic door sensor connected to a Raspberry Pi GPIO pin.

    Attributes:
        door_state (int): Saved raw GPIO input value (GPIO.HIGH or GPIO.LOW).
    """
    def __init__(self):
        """
        Initialize GPIO for the door sensor and read the initial state.

        - Sets GPIO mode to BCM.
        - Configures `DOOR_SENSOR_PIN` as an input with an internal pull-up.
        - Reads and saves the initial door state in `self.door_state`.
        """
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(DOOR_SENSOR_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        self.door_state = GPIO.input(DOOR_SENSOR_PIN)


    def __del__(self):
        """
        Clean up GPIO resources for the configured pin.
        """
        GPIO.cleanup(DOOR_SENSOR_PIN)


    def is_door_open(self):
        """
        Check whether the door is currently open or closed.

        Returns:
          bool: True if the sensor reads `GPIO.HIGH` (door open), False
          otherwise.
        """
        self.get_door_state()
        if self.door_state == GPIO.HIGH:
          return True
        else:
          return False    


    def get_door_state(self):
        """
        Read the current raw GPIO value for the door sensor
        and set it as value of door_state attribute.

        Returns:
           None
        """
        self.door_state = GPIO.input(DOOR_SENSOR_PIN)
