from components.rgb_button import RGBButton
from components.door_sensor import DoorSensor
from components.ir_break_sensor import IRBreakSensor
from components.electromagnetic_lock import ElectromagneticLock
from components.ultrasonic_sensor import UltrasonicSensor
from components.dht_sensor import DHTSensor
from components.step_motor_lock import StepMotorLock

from services.mqtt_handler import MQTTHandler
from services.firebase_service import FirebaseService
from services.settings_manager import SettingsManager

from apscheduler.schedulers.background import BackgroundScheduler

import RPi.GPIO as GPIO
import time
import json


# SETTINGS
settings = SettingsManager()
name = settings.get("name", "Parcel 1")
description = settings.get("description", "Smart Parcel Box")
mqtt_broker = settings.get("mqtt_broker", "192.168.1.215")
data_publish_interval = settings.get("data_publish_interval", 3)
status_publish_interval = settings.get("status_publish_interval", 5)
minimal_temperature = settings.get("minimal_temperature", 0)
maximal_temperature = settings.get("maximal_temperature", 50)
minimal_humidity = settings.get("minimal_humidity", 20)
maximal_humidity = settings.get("maximal_humidity", 80)
ultrasonic_threshold = settings.get("ultrasonic_threshold", 10)


# METHODS
def on_message(self, client, msg):
    topic = msg.topic

    if topic == 'smart-parcel-box/cmd/check-status':
        mqtt_handler.publish('smart-parcel-box/status', {
            'online': True,
            'name': name,
            'description': description,
        })

    elif topic == 'smart-parcel-box/cmd/unlock-main-door':
        electromagnetic_lock.unlock()
        print("Electromagnetic Lock Unlocked")

    elif topic == 'smart-parcel-box/cmd/lock-main-door':
        electromagnetic_lock.lock()
        print("Electromagnetic Lock Locked")

    elif topic == 'smart-parcel-box/cmd/lock-parcel-door':
        step_motor_lock.lock_door()
        print("Parcel Door Locked")

    elif topic == 'smart-parcel-box/cmd/unlock-parcel-door':
        step_motor_lock.unlock_door()
        print("Parcel Door Unlocked")


# SENSORS
dht_sensor = DHTSensor()
door_sensor = DoorSensor()
ir_break_sensor = IRBreakSensor()
ultrasonic_sensor = UltrasonicSensor()
electromagnetic_lock = ElectromagneticLock()
step_motor_lock = StepMotorLock()
step_motor_lock.unlock_door()
rgb_button = RGBButton()


# STATE
is_space_available = True
is_minimal_temperature_alert_sent = False
is_maximal_temperature_alert_sent = False
is_minimal_humidity_alert_sent = False
is_maximal_humidity_alert_sent = False
is_someone_waiting_alert_sent = False


# FIREBASE
firebase_service = FirebaseService()


# MQTT
subscribe_topics = ['smart-parcel-box/cmd/unlock-main-door', 'smart-parcel-box/cmd/lock-main-door', 'smart-parcel-box/cmd/check-status', 'smart-parcel-box/cmd/lock-parcel-door', 'smart-parcel-box/cmd/unlock-parcel-door']
publish_topics = ['smart-parcel-box/data', 'smart-parcel-box/status']
mqtt_handler = MQTTHandler(mqtt_broker, subscribe_topics, publish_topics, on_message)
mqtt_handler.connect()


# SCHEDULER AND METHOD SCHEDULERS
def get_sensor_data():
    global is_space_available, was_space_available_alert_sent
     
    dht_sensor.safe_read()
    
    if (ultrasonic_sensor.get_distance() > ultrasonic_threshold):
        rgb_button.set_RGB_color(0, 255, 0)
        is_space_available = True
        was_space_available_alert_sent = False
    elif (ultrasonic_sensor.get_distance() <= ultrasonic_threshold):
        rgb_button.set_RGB_color(255, 0, 0)
        if not was_space_available_alert_sent:
            firebase_service.send_notification("Parcel Box Full", "The parcel box is full. Please empty it.")
            was_space_available_alert_sent = True
        is_space_available = False

    print(f"Door Open: {door_sensor.is_door_open()}")
    print(f"IR Break Sensor packages: {ir_break_sensor.count}")
    print(f"Ultrasonic Sensor Distance: {ultrasonic_sensor.get_distance()} cm")
    print(f"Step Motor Lock State: {'Locked' if step_motor_lock.is_parcel_door_locked else 'Unlocked'}")
    print(f"Electromagnetic Lock State: {'Locked' if electromagnetic_lock.is_locked() else 'Unlocked'}")
    print(f"RGB Button State: {rgb_button.get_status()}")
    print(f"Temperature: {dht_sensor.temperature} °C, Humidity: {dht_sensor.humidity} %\n")
    mqtt_handler.publish('smart-parcel-box/data', {
        'door_state': door_sensor.is_door_open(),
        'parcel_count': ir_break_sensor.count,
        'is_space_available': is_space_available,
        'parcel_door_step_motor_lock_state': step_motor_lock.is_parcel_door_locked,
        'main_door_electromagnetic_lock_state': electromagnetic_lock.is_locked(),
        'rgb_button_state': rgb_button.get_status(),
        'temperature': dht_sensor.temperature,
        'humidity': dht_sensor.humidity
    })

scheduler = BackgroundScheduler()
scheduler.add_job(get_sensor_data, 'interval', seconds=data_publish_interval, max_instances=1, coalesce=True, misfire_grace_time=10)
scheduler.start()

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    scheduler.shutdown()