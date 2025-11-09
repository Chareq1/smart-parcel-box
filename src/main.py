import datetime
import time
import signal
import sys
import logging

from components.nfc_reader import NFCReader
from components.rgb_button import RGBButton
from components.door_sensor import DoorSensor
from components.ir_break_sensor import IRBreakSensor
from components.electromagnetic_lock import ElectromagneticLock
from components.ultrasonic_sensor import UltrasonicSensor
from components.dht_sensor import DHTSensor
from components.step_motor_lock import StepMotorLock

from services.mqtt_handler import MQTTHandler
from services.notification_service import NotificationService
from services.settings_manager import SettingsManager
from services.bluetooth.bluetooth_service import BluetoothService

from apscheduler.schedulers.background import BackgroundScheduler
from services.event_handler import EventHandler
from services.bluetooth.ble_agent import BLEAgent
from services.data_manager import DataManager


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("smart_parcel_box.log"),
        logging.StreamHandler()
    ]
)


# METHODS
def publish_status():
    mqtt_handler.publish('smart-parcel-box/status', {
        'online': True,
        'name': name,
        'description': description,
    })
    logger.info("Status published: online")


def on_message(self, client, msg):
    topic = msg.topic

    if topic == 'smart-parcel-box/cmd/check-status':
        mqtt_handler.publish('smart-parcel-box/status', {
            'online': True,
            'name': name,
            'description': description,
        })
        logger.info("Status published: online")

    elif topic == 'smart-parcel-box/cmd/get-settings':
        mqtt_handler.publish('smart-parcel-box/settings', {
            'minimal_temperature': settings.get("minimal_temperature", 0),
            'maximal_temperature': settings.get("maximal_temperature", 50),
            'minimal_humidity': settings.get("minimal_humidity", 20),
            'maximal_humidity': settings.get("maximal_humidity", 80)
        })

    elif topic == 'smart-parcel-box/cmd/unlock-main-door':
        electromagnetic_lock.unlock()

        if event_handler.is_courier_waiting:
            event_handler.reset_courier_button()
            if scheduler.get_job("reset_courier_button"):
                scheduler.remove_job("reset_courier_button")

        if not scheduler.get_job("autolock_main_door"):
            scheduler.add_job(event_handler.autolock_main_door, 'date',run_date=datetime.datetime.now() + datetime.timedelta(seconds=autolock_main_door_seconds), args=[electromagnetic_lock], id='autolock_main_door', coalesce=True, misfire_grace_time=10)

        if not scheduler.get_job("check_if_door_opened"):
            scheduler.add_job(event_handler.check_if_door_open, 'date', run_date=datetime.datetime.now() + datetime.timedelta(seconds=open_main_door_duration_seconds), args=[door_sensor, electromagnetic_lock], id='check_if_door_opened', coalesce=True, misfire_grace_time=10)

        logger.info("Electromagnetic Lock Unlocked")
        notification_service.send_notification("mainDoorOpened", name)

    elif topic == 'smart-parcel-box/cmd/lock-main-door':
        electromagnetic_lock.lock()
        if scheduler.get_job("autolock_main_door"):
            scheduler.remove_job("autolock_main_door")
        logger.info("Electromagnetic Lock Locked")

    elif topic == 'smart-parcel-box/cmd/lock-parcel-door':
        step_motor_lock.lock_door()
        if scheduler.get_job("autolock_slide_parcel_door"):
            scheduler.remove_job("autolock_slide_parcel_door")
        logger.info("Slide parcel Door Locked")

    elif topic == 'smart-parcel-box/cmd/unlock-parcel-door':
        step_motor_lock.unlock_door()

        if event_handler.is_courier_waiting:
            event_handler.reset_courier_button()
            if scheduler.get_job("reset_courier_button"):
                scheduler.remove_job("reset_courier_button")

        if not scheduler.get_job("autolock_slide_parcel_door"):
            scheduler.add_job(event_handler.autolock_slide_door, 'date', run_date=datetime.datetime.now() + datetime.timedelta(seconds=autolock_slide_parcel_door_seconds), args=[step_motor_lock], id='autolock_slide_parcel_door', coalesce=True, misfire_grace_time=10)

        logger.info("Slide parcel Door Unlocked")
        notification_service.send_notification("slideParcelDoorOpened", name)

    elif topic == 'smart-parcel-box/cmd/add-parcels':
        try:
            count = int(msg.payload.decode())
            if count > 0:
                ir_break_sensor.count += count
                logger.info(f"Added {count} parcels. New count: {ir_break_sensor.count}")
                notification_service.send_notification("newPackagesDelivered", name, amount=count)
            else:
                logger.warning("Received non-positive parcel count to add.")
        except ValueError:
            logger.error("Invalid parcel count received.")

    elif topic == 'smart-parcel-box/cmd/unload-box':
        ir_break_sensor.count = 0
        logger.info("Parcel box unloaded. Parcel count reset to 0.")


def get_sensor_data():
    try:
        dht_sensor.safe_read()

        event_handler.check_minimal_temperature_threshold(dht_sensor.temperature, minimal_temperature)
        event_handler.check_maximal_temperature_threshold(dht_sensor.temperature, maximal_temperature)

        event_handler.check_minimal_humidity_threshold(dht_sensor.humidity, minimal_humidity)
        event_handler.check_maximal_humidity_threshold(dht_sensor.humidity, maximal_humidity)

        is_space_available = event_handler.check_space_availability(ultrasonic_sensor.get_distance(), ultrasonic_threshold)

        event_handler.check_door_status(door_sensor)

        data = {
            'door_state': door_sensor.is_door_open(),
            'parcel_count': ir_break_sensor.count,
            'is_space_available': is_space_available,
            'parcel_door_step_motor_lock_state': step_motor_lock.is_parcel_door_locked,
            'main_door_electromagnetic_lock_state': electromagnetic_lock.is_locked(),
            'rgb_button_state': rgb_button.get_status(),
            'temperature': dht_sensor.temperature,
            'humidity': dht_sensor.humidity
        }

        data_manager.save_data(data)

        mqtt_handler.publish('smart-parcel-box/data', data)

        logger.info(f"Sent data: {data}")
    except Exception as e:
        logger.error(f"Error during getting data from sensors: {e}")


def check_initial_data():
    saved_data = data_manager.data

    if saved_data["door_state"]:
        event_handler.check_door_status(door_sensor)

    if saved_data["parcel_count"]:
        ir_break_sensor.count = saved_data["parcel_count"]

    if saved_data["is_space_available"]:
        event_handler.is_space_available = saved_data["is_space_available"]
        event_handler.change_space_availability_on_start()

    if saved_data["temperature"]:
        event_handler.check_minimal_temperature_threshold(saved_data["temperature"], minimal_temperature)
        event_handler.check_maximal_temperature_threshold(saved_data["temperature"], maximal_temperature)

        dht_sensor.temperature = saved_data["temperature"]

    if saved_data["humidity"]:
        event_handler.check_minimal_humidity_threshold(saved_data["humidity"], minimal_humidity)
        event_handler.check_maximal_humidity_threshold(saved_data["humidity"], maximal_humidity)

        dht_sensor.humidity = saved_data["humidity"]

    if saved_data["parcel_door_step_motor_lock_state"]:
        step_motor_lock.is_parcel_door_locked = saved_data["parcel_door_step_motor_lock_state"]
        if step_motor_lock.is_parcel_door_locked:
            step_motor_lock.lock_door()
            if scheduler.get_job("autolock_slide_parcel_door"):
                scheduler.remove_job("autolock_slide_parcel_door")
        else:
            step_motor_lock.unlock_door()

            if event_handler.is_courier_waiting:
                event_handler.reset_courier_button()
                if scheduler.get_job("reset_courier_button"):
                    scheduler.remove_job("reset_courier_button")

            if scheduler.get_job("autolock_slide_parcel_door"):
                scheduler.add_job(event_handler.autolock_slide_door, 'date',
                                  run_date=datetime.datetime.now() + datetime.timedelta(
                                      seconds=autolock_slide_parcel_door_seconds), args=[step_motor_lock],
                                  id='autolock_slide_parcel_door', coalesce=True, misfire_grace_time=10)

    if saved_data["main_door_electromagnetic_lock_state"]:
        if saved_data["main_door_electromagnetic_lock_state"]:
            electromagnetic_lock.lock()
            if scheduler.get_job("autolock_main_door"):
                scheduler.remove_job("autolock_main_door")
        else:
            electromagnetic_lock.unlock()

            if event_handler.is_courier_waiting:
                event_handler.reset_courier_button()
                if scheduler.get_job("reset_courier_button"):
                    scheduler.remove_job("reset_courier_button")

            if scheduler.get_job("autolock_main_door"):
                scheduler.add_job(event_handler.autolock_main_door, 'date',
                                  run_date=datetime.datetime.now() + datetime.timedelta(seconds=autolock_main_door_seconds),
                                  args=[electromagnetic_lock], id='autolock_main_door', coalesce=True,
                                  misfire_grace_time=10)

            if not scheduler.get_job("check_if_door_opened"):
                scheduler.add_job(event_handler.check_if_door_open, 'date',
                                  run_date=datetime.datetime.now() + datetime.timedelta(
                                      seconds=open_main_door_duration_seconds),
                                  args=[door_sensor, electromagnetic_lock], id='check_if_door_opened', coalesce=True,
                                  misfire_grace_time=10)
            logger.info("Electromagnetic Lock Unlocked")


def settings_update():
    global name, description, mqtt_broker
    global data_publish_interval, status_publish_interval
    global minimal_temperature, maximal_temperature
    global minimal_humidity, maximal_humidity
    global ultrasonic_threshold
    global courier_button_wait_time_seconds
    global autolock_slide_parcel_door_seconds
    global autolock_main_door_seconds
    global open_main_door_duration_seconds
    global event_handler, ir_break_sensor

    name = settings.get("name", "Parcel 1")
    description = settings.get("description", "Smart Parcel Box")
    mqtt_broker = settings.get("mqtt_broker", "mqtt.smaartparcelbox.app")
    data_publish_interval = settings.get("data_publish_interval", 3)
    status_publish_interval = settings.get("status_publish_interval", 5)
    minimal_temperature = settings.get("minimal_temperature", 0)
    maximal_temperature = settings.get("maximal_temperature", 50)
    minimal_humidity = settings.get("minimal_humidity", 20)
    maximal_humidity = settings.get("maximal_humidity", 80)
    ultrasonic_threshold = settings.get("ultrasonic_threshold", 10)
    courier_button_wait_time_seconds = settings.get("courier_button_wait_time_seconds", 30)
    autolock_slide_parcel_door_seconds = settings.get("autolock_slide_parcel_door_seconds", 60)
    autolock_main_door_seconds = settings.get("autolock_main_door_seconds", 60)
    open_main_door_duration_seconds = settings.get("open_main_door_duration_seconds", 60)

    try:
        event_handler.courier_button_wait_time_seconds = courier_button_wait_time_seconds
        event_handler.name = name
        ir_break_sensor.name = name
    except Exception:
        pass


def on_settings_update(*args, **kwargs):
    settings.save_settings()
    settings.load_settings()

    settings_update()

    mqtt_handler.publish('smart-parcel-box/status', {
        'online': True,
        'name': settings.get("name", "Parcel 1"),
        'description': settings.get("description", "Smart Parcel Box"),
    })

    mqtt_handler.publish('smart-parcel-box/settings', {
        'minimal_temperature': settings.get("minimal_temperature", 0),
        'maximal_temperature': settings.get("maximal_temperature", 50),
        'minimal_humidity': settings.get("minimal_humidity", 20),
        'maximal_humidity': settings.get("maximal_humidity", 80)
    })



def handle_shutdown(signum, frame):
    try:
        logger.info("System shutting down, saving state...")
        data_manager.save_data({
            'door_state': door_sensor.is_door_open(),
            'parcel_count': ir_break_sensor.count,
            'is_space_available': event_handler.is_space_available,
            'parcel_door_step_motor_lock_state': step_motor_lock.is_parcel_door_locked,
            'main_door_electromagnetic_lock_state': electromagnetic_lock.is_locked(),
            'rgb_button_state': rgb_button.get_status(),
            'temperature': dht_sensor.temperature,
            'humidity': dht_sensor.humidity
        })

        mqtt_handler.publish("smart-parcel-box/status", {
            "online": False,
            "name": name,
            "description": description
        })

        try:
            bluetooth_service.stop()
        except Exception:
            pass

        scheduler.shutdown(wait=False)
        mqtt_handler.disconnect()
        rgb_button.set_RGB_color(0, 0, 0)
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")
        sys.exit(1)


def main():
    logger.info("Starting Smart Parcel Box...")
    notification_service.send_notification("machineIsOnline", name)

    check_initial_data()
    signal.signal(signal.SIGTERM, handle_shutdown)
    signal.signal(signal.SIGINT, handle_shutdown)

    scheduler.add_job(get_sensor_data, 'interval', seconds=data_publish_interval, max_instances=1, coalesce=True, misfire_grace_time=10)
    scheduler.add_job(publish_status, 'interval', seconds=status_publish_interval, max_instances=1, coalesce=True, misfire_grace_time=10)
    scheduler.start()

    BLEAgent.register(logger)

    try:
        bluetooth_service.start()
        logger.info("Bluetooth service started")
    except Exception as e:
        logger.error(f"Failed to start Bluetooth service: {e}")

    try:
        while True:
            if not mqtt_handler.client.is_connected():
                logger.warning("MQTT disconnected. Attempting to reconnect...")
                try:
                    mqtt_handler.connect()
                    logger.info("MQTT connected")
                except Exception as e:
                    logger.error(f"MQTT reconnection failed: {e}")
            time.sleep(1)
    except KeyboardInterrupt:
        handle_shutdown(None, None)


# COMPONENTS
# LOGGER
logger = logging.getLogger(__name__)
logging.getLogger("apscheduler").setLevel(logging.WARNING)

# SETTINGS
settings = SettingsManager(logger=logger)
settings_update()

# SCHEDULER
scheduler = BackgroundScheduler()

# NOTIFICATIONS
notification_service = NotificationService(scheduler=scheduler, logger=logger)

# SENSORS
dht_sensor = DHTSensor(logger=logger)
door_sensor = DoorSensor()
ir_break_sensor = IRBreakSensor(notification_service=notification_service, name=name)
ultrasonic_sensor = UltrasonicSensor()
electromagnetic_lock = ElectromagneticLock()
step_motor_lock = StepMotorLock()
rgb_button = RGBButton()
nfc_reader = NFCReader(logger=logger)

# DATA MANAGER
data_manager = DataManager(logger=logger)
data_manager.load_data()

# EVENT HANDLER
event_handler = EventHandler(notification_service, name, rgb_button, door_sensor, scheduler, logger, nfc_reader, electromagnetic_lock, autolock_main_door_seconds, open_main_door_duration_seconds, courier_button_wait_time_seconds)

# MQTT
subscribe_topics = ['smart-parcel-box/cmd/unlock-main-door', 'smart-parcel-box/cmd/lock-main-door',
                    'smart-parcel-box/cmd/check-status', 'smart-parcel-box/cmd/lock-parcel-door',
                    'smart-parcel-box/cmd/unlock-parcel-door', 'smart-parcel-box/cmd/get-settings',
                    'smart-parcel-box/cmd/add-parcels', 'smart-parcel-box/cmd/unload-box']
publish_topics = ['smart-parcel-box/data', 'smart-parcel-box/status', 'smart-parcel-box/settings']
mqtt_handler = MQTTHandler(mqtt_broker, subscribe_topics, publish_topics, on_message, logger)
mqtt_handler.connect()

bluetooth_service = BluetoothService(settings_manager=settings, logger=logger, device_name="SmartParcelBox", on_settings_update=on_settings_update)


# MAIN
if __name__ == "__main__":
    main()