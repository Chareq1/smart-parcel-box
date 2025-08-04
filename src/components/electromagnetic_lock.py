import RPi.GPIO as GPIO
'''!
  @file  ir_break_sensor.py
  @brief  Component for ir beam break sensor
  @details  This file contains all .
  @date  2025-07-08
'''
RELAY_PIN = 16

class ElectromagneticLock:
    def __init__(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(RELAY_PIN, GPIO.OUT)

    def __del__(self):
        GPIO.cleanup(RELAY_PIN)

    def lock(self):
        GPIO.output(RELAY_PIN, GPIO.LOW)

    def unlock(self):
        GPIO.output(RELAY_PIN, GPIO.HIGH)

    def is_locked(self):
        return GPIO.input(RELAY_PIN) == GPIO.LOW