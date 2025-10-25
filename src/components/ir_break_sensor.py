import RPi.GPIO as GPIO

"""
src/components/ir_break_sensor.py

IR Beam Break sensor component for a Raspberry Pi GPIO pin.

This module provides the IRBreakSensor class which encapsulates GPIO setup,
reading and cleanup for a IR beam break sensor connected to a GPIO pin.

Behavior:
  - GPIO.HIGH -> IR beam intact
  - GPIO.LOW  -> IR beam broken
"""


# GPIO Pin for IR Beam Break Sensor
IR_BEAM_BREAK_SENSOR_PIN = 13


class IRBreakSensor:
    """
    Class for an IR beam break sensor connected to a Raspberry Pi GPIO pin.

    Attributes:
        count (int): Number of times the beam has been broken.
        notification_service: Service to send notifications.
        name (str): Name identifier for the smart parcel box.
    """

    def __init__(self, count=0, notification_service=None, name=None):
        """
        Initialize GPIO for the IR beam break sensor.
        - Sets value of count to 0.
        - Sets GPIO mode to BCM.
        - Configures `IR_BEAM_BREAK_SENSOR_PIN` as an input with an internal pull-up.
        - Adds event detection on `IR_BEAM_BREAK_SENSOR_PIN` for both rising and falling edges with callback to `break_beam_callback`.
        - Sets notification_service based on given parameter.
        - Sets name based on given parameter.

        Args:
            count (int): Initial count of beam breaks.
            notification_service: Service to send notifications.
            name (str): Name identifier for the smart parcel box.
        """
        self.count = count
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(IR_BEAM_BREAK_SENSOR_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(IR_BEAM_BREAK_SENSOR_PIN, GPIO.BOTH, callback=self.break_beam_callback)
        self.notification_service = notification_service
        self.name = name


    def __del__(self):
        """
        Clean up GPIO resources for the configured pin.
        """
        GPIO.cleanup(IR_BEAM_BREAK_SENSOR_PIN)
        
        
    def is_beam_broken(self):
        """
        Check whether the IR beam is broken.

        Returns:
            bool: True if the IR beam is broken `GPIO.LOW`, False otherwise.
        """
        return GPIO.input(IR_BEAM_BREAK_SENSOR_PIN) == GPIO.LOW
    
    
    def get_beam_state(self):
        """
        Check the state of IR beam.

        Returns:
            bool: True if the IR beam is broken (GPIO.LOW),
            False if the beam is intact (GPIO.HIGH).
        """
        return GPIO.input(IR_BEAM_BREAK_SENSOR_PIN)
    
    
    def break_beam_callback(self, channel):
        """
        Callback methods, that if IR beam is broken, increases package
        count by 1 and sends notification to the app.

        Returns:
            None
        """
        if self.get_beam_state() == GPIO.LOW:
            self.count += 1
            self.notification_service.send_notification("irBeamBroken", self.name)
        