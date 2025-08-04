import RPi.GPIO as GPIO
import time

TRIGGER_PIN = 23
ECHO_PIN = 24

class UltrasonicSensor:
    def __init__(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(TRIGGER_PIN, GPIO.OUT)
        GPIO.setup(ECHO_PIN, GPIO.IN)

    def __del__(self):
        GPIO.cleanup([TRIGGER_PIN, ECHO_PIN])
    
    def get_distance(self):
        GPIO.output(TRIGGER_PIN, True)
        time.sleep(0.00001)
        GPIO.output(TRIGGER_PIN, False)
        
        while GPIO.input(ECHO_PIN) == 0:
            pulse_start = time.time()
            
        while GPIO.input(ECHO_PIN) == 1:
            pulse_end = time.time()
            
        pulse_duration = pulse_end - pulse_start
        distance = pulse_duration * 17150
        distance = round(distance, 2)
        return distance