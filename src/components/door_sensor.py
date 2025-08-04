import RPi.GPIO as GPIO

'''!
  @file  door_sensor.py
  @brief  Component for magnetic door sensor
  @details  This file contains all .
  @date  2025-07-05
'''

# GPIO Pin Number 
DOOR_SENSOR_PIN = 25

# GPIO.HIGH == Door Open
# GPIO.LOW == Door Closed

class DoorSensor:
    def __init__(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(DOOR_SENSOR_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        self.door_state = GPIO.input(DOOR_SENSOR_PIN)
        
    def __del__(self):
        GPIO.cleanup(DOOR_SENSOR_PIN)
        
    def is_door_open(self):
        self.get_door_state()
        if(self.door_state == GPIO.HIGH):
          return True
        else:
          return False    
    
    def get_door_state(self):
        self.door_state = GPIO.input(DOOR_SENSOR_PIN)