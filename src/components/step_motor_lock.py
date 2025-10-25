#!/usr/bin/python3
import RPi.GPIO as GPIO
import time

"""
src/components/step_motor_lock.py

Step motor lock component for a Raspberry Pi GPIO pin.

This module provides the StepMotorLock class which encapsulates GPIO setup,
reading and cleanup for a step motor connected to a GPIO pin.
"""

# GPIO Pins for step motor
IN1_PIN = 17
IN2_PIN = 18
IN3_PIN = 27
IN4_PIN = 22


# Step motor configuration constants (sleep time and step count)
STEP_SLEEP = 0.002
STEP_COUNT = 1024


# Step sequence for controlling the step motor
STEP_SEQUENCE = [[1,0,0,1], [1,0,0,0], [1,1,0,0], [0,1,0,0], [0,1,1,0], [0,0,1,0], [0,0,1,1], [0,0,0,1]]


class StepMotorLock:
    """
    Class for an step motor parcel door lock connected
    to a Raspberry Pi GPIO pin.

    Attributes:
        is_parcel_door_locked (bool): State of the parcel door step motor lock.
        MOTOR_PINS (list): List of GPIO pins used for the step motor.
        MOTOR_STEP_COUNTER (int): Current step position of the motor.
    """

    def __init__(self):
        """
        Initialize GPIO for the step motor.
        - Sets GPIO mode to BCM.
        - Sets up IN1_PIN, IN2_PIN, IN3_PIN, IN4_PIN as outputs.
        - Initializes all motor pins to LOW.
        - Initializes MOTOR_PINS list and MOTOR_STEP_COUNTER.
        - Initializes is_parcel_door_locked to False.
        - Unlocks the door by default.
        """
        GPIO.setmode(GPIO.BCM)

        GPIO.setup(IN1_PIN, GPIO.OUT)
        GPIO.setup(IN2_PIN, GPIO.OUT)
        GPIO.setup(IN3_PIN, GPIO.OUT)
        GPIO.setup(IN4_PIN, GPIO.OUT)

        GPIO.output(IN1_PIN, GPIO.LOW)
        GPIO.output(IN2_PIN, GPIO.LOW)
        GPIO.output(IN3_PIN, GPIO.LOW)
        GPIO.output(IN4_PIN, GPIO.LOW)

        self.MOTOR_PINS = [IN1_PIN, IN2_PIN, IN3_PIN, IN4_PIN]
        self.MOTOR_STEP_COUNTER = 0
        
        self.is_parcel_door_locked = False
        
        self.unlock_door()


    def __del__(self):
        """
        Clean up GPIO resources for the configured pin.
        """
        GPIO.cleanup([IN1_PIN, IN2_PIN, IN3_PIN, IN4_PIN])


    def move_motor(self, steps, direction):
        """
        Move the step motor a given number of steps in the specified direction.

        Args:
            steps (int): Number of steps to move the motor.
            direction (bool): Direction to move the motor. True for one direction, False for the opposite.

        Returns:
            None
        """
        for i in range(steps):
            for pin in range(0, len(self.MOTOR_PINS)):
                GPIO.output(self.MOTOR_PINS[pin], STEP_SEQUENCE[self.MOTOR_STEP_COUNTER][pin])
            if direction:
                self.MOTOR_STEP_COUNTER = (self.MOTOR_STEP_COUNTER - 1) % 8
            else:
                self.MOTOR_STEP_COUNTER = (self.MOTOR_STEP_COUNTER + 1) % 8
            time.sleep(STEP_SLEEP)


    def lock_door(self):
        """
        Lock parcel door by moving the step motor to locked position.

        Returns:
            None
        """
        self.is_parcel_door_locked = True
        self.move_motor(STEP_COUNT, False)


    def unlock_door(self):
        """
        Unlock parcel door by moving the step motor to unlocked position.

        Returns:
            None
        """
        self.is_parcel_door_locked = False
        self.move_motor(STEP_COUNT, True)
