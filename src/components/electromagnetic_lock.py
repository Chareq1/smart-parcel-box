import RPi.GPIO as GPIO

"""
src/components/electromagnetic_lock.py

Electromagnetic lock component for a Raspberry Pi GPIO pin.

This module provides the ElectromagneticLock class which encapsulates GPIO setup,
reading and cleanup for a magnetic reed switch connected to a GPIO pin.

Behavior:
  - GPIO.HIGH -> Electromagnetic lock disengaged
  - GPIO.LOW  -> Electromagnetic lock engaged
  (because the relay is normally closed (NC))
"""


# GPIO Pin for relay controlling the electromagnetic lock
RELAY_PIN = 16


class ElectromagneticLock:
    """
    Class for an electromagnetic door lock connected through 5V relay
    to a Raspberry Pi GPIO pin.

    Attributes:
        None
    """

    def __init__(self):
        """
        Initialize GPIO for the electromagnetic lock.

        - Sets GPIO mode to BCM.
        - Configures `RELAY_PIN` as an output.
        """
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(RELAY_PIN, GPIO.OUT)


    def __del__(self):
        """
        Clean up GPIO resources for the configured pin.
        """
        GPIO.cleanup(RELAY_PIN)


    def lock(self):
        """
        Lock main door (electromagnetic lock) by setting value of
        RELAY_PIN on GPIO.LOW.

        Returns:
           None
        """
        GPIO.output(RELAY_PIN, GPIO.LOW)


    def unlock(self):
        """
        Unlock main door (electromagnetic lock) by setting value of
        RELAY_PIN on GPIO.HIGH.

        Returns:
           None
        """
        GPIO.output(RELAY_PIN, GPIO.HIGH)


    def is_locked(self):
        """
        Check whether the door is currently locked or unlocked.

        Returns:
          bool: True if the main door is locked (GPIO.LOW), False
          otherwise.
        """
        return GPIO.input(RELAY_PIN) == GPIO.LOW