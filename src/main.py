from components.rgb_button import RGBButton
from components.door_sensor import DoorSensor
from components.ir_break_sensor import IRBreakSensor
from components.electromagnetic_lock import ElectromagneticLock
from components.ultrasonic_sensor import UltrasonicSensor
from components.dht_sensor import DHTSensor
from components.mqtt_handler import MQTTHandler

import RPi.GPIO as GPIO
import time
import json

def on_message(self, client, msg):
    topic = msg.topic

    if topic == 'smart-parcel-box/cmd/unlock':
        electromagnetic_lock.unlock()
        print("Electromagnetic Lock Unlocked")

    elif topic == 'smart-parcel-box/cmd/lock':
        electromagnetic_lock.lock()
        print("Electromagnetic Lock Locked")

dht_sensor = DHTSensor()
door_sensor = DoorSensor()
ir_break_sensor = IRBreakSensor()
ultrasonic_sensor = UltrasonicSensor()
electromagnetic_lock = ElectromagneticLock()
rgb_button = RGBButton()

mqtt_broker = '192.168.1.247'
subscribe_topics = ['smart-parcel-box/cmd/unlock', 'smart-parcel-box/cmd/lock']
publish_topics = ['smart-parcel-box/data', 'home/status']
mqtt_handler = MQTTHandler(mqtt_broker, subscribe_topics, publish_topics, on_message)
mqtt_handler.connect()

while True:
    '''
    dht_sensor.read()
    mqtt_handler.publish('smart-parcel-box/data', {
        'humidity': dht_sensor.humidity,
        'temperature_celsius': dht_sensor.temperature_celsius,
        'temperature_fahrenheit': dht_sensor.temperature_fahrenheit,
    })
    print(f"Humidity: {dht_sensor.humidity}, Temperature (C): {dht_sensor.temperature_celsius}, Temperature (F): {dht_sensor.temperature_fahrenheit}")
    time.sleep(1)  # Adjust the sleep time as needed
    '''
    dht_sensor.read()
    print(f"Door Open: {door_sensor.is_door_open()}")
    print(f"IR Break Sensor packages: {ir_break_sensor.count}")
    print(f"Ultrasonic Sensor Distance: {ultrasonic_sensor.get_distance()} cm")
    print(f"Electromagnetic Lock State: {'Locked' if electromagnetic_lock.is_locked() else 'Unlocked'}")
    print(f"RGB Button State: {rgb_button.get_status()}")
    print(f"Temperature: {dht_sensor.temperature_celsius} °C, Humidity: {dht_sensor.humidity} %\n")
    mqtt_handler.publish('smart-parcel-box/data', {
        'door_state': door_sensor.is_door_open(),
        'package_count': ir_break_sensor.count,
        'ultrasonic_distance': ultrasonic_sensor.get_distance(),
        'electromagnetic_lock_state': electromagnetic_lock.is_locked(),
        'rgb_button_state': rgb_button.get_status(),
        'temperature_celsius': dht_sensor.temperature_celsius,
        'temperature_fahrenheit': dht_sensor.temperature_fahrenheit,
        'humidity': dht_sensor.humidity
    })
    time.sleep(2)