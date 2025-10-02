import RPi.GPIO as GPIO

'''!
  @file  ir_break_sensor.py
  @brief  Component for ir beam break sensor
  @details  This file contains all .
  @date  2025-07-08
'''

# GPIO Pin Number 
IR_BEAM_BREAK_SENSOR_PIN = 13

class IRBreakSensor:
    def __init__(self, count=0):
        self.count = count
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(IR_BEAM_BREAK_SENSOR_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(IR_BEAM_BREAK_SENSOR_PIN, GPIO.BOTH, callback=self.break_beam_callback)

    def __del__(self):
        GPIO.cleanup(IR_BEAM_BREAK_SENSOR_PIN)
        
    def is_beam_broken(self):
        return GPIO.input(IR_BEAM_BREAK_SENSOR_PIN) == GPIO.LOW
    
    def get_beam_state(self):
        return GPIO.input(IR_BEAM_BREAK_SENSOR_PIN)
    
    def break_beam_callback(self, channel):
        if self.get_beam_state() == GPIO.LOW:
            self.count += 1