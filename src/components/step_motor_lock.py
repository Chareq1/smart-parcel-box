#!/usr/bin/python3
import RPi.GPIO as GPIO
import time

IN1_PIN = 17
IN2_PIN = 18
IN3_PIN = 27
IN4_PIN = 22

STEP_SLEEP = 0.002
STEP_COUNT = 1024

STEP_SEQUENCE = [[1,0,0,1], [1,0,0,0], [1,1,0,0], [0,1,0,0], [0,1,1,0], [0,0,1,0], [0,0,1,1], [0,0,0,1]]

class StepMotorLock:
    def __init__(self):
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
    
    def __del__(self):
        GPIO.cleanup([IN1_PIN, IN2_PIN, IN3_PIN, IN4_PIN])

    def move_motor(self, steps, direction):
        global MOTOR_STEP_COUNTER
        for i in range(steps):
            for pin in range(0, len(self.MOTOR_PINS)):
                GPIO.output(self.MOTOR_PINS[pin], STEP_SEQUENCE[self.MOTOR_STEP_COUNTER][pin])
            if direction:
                self.MOTOR_STEP_COUNTER = (self.MOTOR_STEP_COUNTER - 1) % 8
            else:
                self.MOTOR_STEP_COUNTER = (self.MOTOR_STEP_COUNTER + 1) % 8
            time.sleep(STEP_SLEEP)
    
    def lock_door(self):
        self.move_motor(STEP_COUNT, False)
        self.is_parcel_door_locked = True
    
    def unlock_door(self):
        self.move_motor(STEP_COUNT, True)
        self.is_parcel_door_locked = False
