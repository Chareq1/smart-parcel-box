import datetime
import json
import os
import hashlib

"""
src/services/event_handler.py

Event handler service for managing events and notifications.

This module provides the EventHandler class which handles various events
related to the smart parcel box, such as space availability, temperature and humidity
thresholds, courier button presses, and door status.
"""

class EventHandler:
    """
    Class for handling events and notifications related to the smart parcel box.

    Attributes:
        notification_service: Service to send notifications.
        name (str): Name identifier for the smart parcel box.
        rgb_button: RGB button component for visual indicators.
        door_sensor: Door sensor component to monitor door status.
        nfc_reader: NFC reader component for reading NFC tags.
        electromagnetic_lock: Electromagnetic lock component for locking/unlocking the main door.
        autolock_main_door_seconds (int): Time in seconds to auto-lock the main door.
        open_main_door_duration_seconds (int): Duration in seconds to keep the main door
        is_courier_waiting (bool): Flag indicating if a courier is waiting.
        is_space_available (bool): Flag indicating if space is available in the parcel box.
        logger: Logger instance for logging messages.
        scheduler: Scheduler for managing timed jobs.
    """

    def __init__(self, notification_service, name, button, door_sensor, scheduler, logger, nfc_reader, electromagnetic_lock, autolock_main_door_seconds, open_main_door_duration_seconds, wait_time=30):
        """
        Initialize the EventHandler with necessary components and state.
        - Sets notification_service, name, rgb_button, door_sensor, logger, and scheduler based on given parameters.
        - Initializes is_courier_waiting to False and is_space_available to True.
        - Schedules periodic job to check courier button status every second.

        Args:
            notification_service: Service to send notifications.
            name (str): Name identifier for the smart parcel box.
            button: RGB button component for visual indicators.
            door_sensor: Door sensor component to monitor door status.
            nfc_reader: NFC reader component for reading NFC tags.
            electromagnetic_lock: Electromagnetic lock component for locking/unlocking the main door.
            autolock_main_door_seconds (int): Time in seconds to auto-lock the main
            open_main_door_duration_seconds (int): Duration in seconds to keep the main door
            scheduler: Scheduler for managing timed jobs.
            logger: Logger instance for logging messages.
            wait_time (int): Time in seconds to wait before resetting the courier button state.
        """
        self.notification_service = notification_service
        self.name = name
        self.rgb_button = button
        self.door_sensor = door_sensor
        self.nfc_reader = nfc_reader
        self.electromagnetic_lock = electromagnetic_lock
        self.autolock_main_door_seconds = autolock_main_door_seconds
        self.open_main_door_duration_seconds = open_main_door_duration_seconds
        self.is_courier_waiting = False
        self.is_space_available = True
        self.logger = logger
        self.scheduler = scheduler

        self.scheduler.add_job(self.unlock_door_using_nfc_tag, 'interval', seconds=1, coalesce=True, max_instances=10, misfire_grace_time=10)
        self.scheduler.add_job(self.check_courier_button, 'interval', args=[wait_time], seconds=1, id='check_courier_button', coalesce=True, misfire_grace_time=10)


    def check_space_availability(self, distance, ultrasonic_threshold):
        """
        Check and update space availability in the parcel box based on ultrasonic sensor distance.
        - If distance is greater than ultrasonic_threshold, sets RGB button to green and clears "no
        space available" notification if active.
        - If distance is less than or equal to ultrasonic_threshold, sets RGB button to red and
        sends "no space available" notification if not already active.
        - Updates is_space_available flag accordingly.

        Args:
            distance (float): Distance reading from the ultrasonic sensor.
            ultrasonic_threshold (float): Threshold distance to determine space availability.

        Returns:
            bool: Current space availability status.
        """
        if distance > ultrasonic_threshold:
            if not self.is_courier_waiting or not self.door_sensor.is_door_open():
                self.rgb_button.set_RGB_color(0, 255, 0)

            if self.notification_service.check_if_active_repeating("noSpaceAvailable"):
                self.logger.info("Space available in parcel box.")
                self.notification_service.clear_notification("noSpaceAvailable")

            self.is_space_available = True
        elif distance <= ultrasonic_threshold:
            if not self.is_courier_waiting or not self.door_sensor.is_door_open():
                self.rgb_button.set_RGB_color(255, 0, 0)

            if not self.notification_service.check_if_active_repeating("noSpaceAvailable"):
                self.logger.info("No space available in parcel box.")
                self.notification_service.send_notification("noSpaceAvailable", self.name)

            self.is_space_available = False
            
        return self.is_space_available


    def change_space_availability_on_start(self):
        """
        Update RGB button and notifications based on current space availability status.
        - If is_space_available is True, sets RGB button to green and clears "no space available"
        notification if active.
        - If is_space_available is False, sets RGB button to red and sends "no space available"
        notification if not already active.

        Returns:
            None
        """
        if self.is_space_available:
            if not self.is_courier_waiting or not self.door_sensor.is_door_open():
                self.rgb_button.set_RGB_color(0, 255, 0)

            if self.notification_service.check_if_active_repeating("noSpaceAvailable"):
                self.logger.info("Space available in parcel box.")
                self.notification_service.clear_notification("noSpaceAvailable")

            self.is_space_available = True
        else:
            if not self.is_courier_waiting or not self.door_sensor.is_door_open():
                self.rgb_button.set_RGB_color(255, 0, 0)

            if not self.notification_service.check_if_active_repeating("noSpaceAvailable"):
                self.logger.info("No space available in parcel box.")
                self.notification_service.send_notification("noSpaceAvailable", self.name)

            self.is_space_available = False

        

    def check_minimal_temperature_threshold(self, temperature, minimal):
        """
        Check minimal temperature threshold and send/clear notifications accordingly.
        - If temperature is below minimal threshold, sends "minimal temperature alert" notification
        if not already active.
        - If temperature is above minimal threshold, clears "minimal temperature alert" notification
        if active.

        Args:
            temperature (float): Current temperature reading.
            minimal (float): Minimal temperature threshold.

        Returns:
            None
        """
        if temperature < minimal:
            if not self.notification_service.check_if_active_repeating("minimalTemperatureAlert"):
                self.logger.info(f"Temperature {temperature}°C is below minimal threshold of {minimal}°C.")
                self.notification_service.send_notification("minimalTemperatureAlert", self.name)
        else:
            if self.notification_service.check_if_active_repeating("minimalTemperatureAlert"):
                self.logger.info(f"Temperature {temperature}°C is above minimal threshold of {minimal}°C.")
                self.notification_service.clear_notification("minimalTemperatureAlert")
                

    def check_maximal_temperature_threshold(self, temperature, maximal):
        """
        Check maximal temperature threshold and send/clear notifications accordingly.
        - If temperature is above maximal threshold, sends "maximal temperature alert" notification
        if not already active.
        - If temperature is below maximal threshold, clears "maximal temperature alert" notification
        if active.

        Args:
            temperature (float): Current temperature reading.
            maximal (float): Maximal temperature threshold.

        Returns:
            None
        """
        if temperature > maximal:
            if not self.notification_service.check_if_active_repeating("maximalTemperatureAlert"):
                self.logger.info(f"Temperature {temperature}°C is above maximal threshold of {maximal}°C.")
                self.notification_service.send_notification("maximalTemperatureAlert", self.name)
        else:
            if self.notification_service.check_if_active_repeating("maximalTemperatureAlert"):
                self.logger.info(f"Temperature {temperature}°C is below maximal threshold of {maximal}°C.")
                self.notification_service.clear_notification("maximalTemperatureAlert")


    def check_maximal_humidity_threshold(self, humidity, maximal):
        """
        Check maximal humidity threshold and send/clear notifications accordingly.
        - If humidity is above maximal threshold, sends "maximal humidity alert" notification
        if not already active.
        - If humidity is below maximal threshold, clears "maximal humidity alert" notification
        if active.

        Args:
            humidity (float): Current humidity reading.
            maximal (float): Maximal humidity threshold.

        Returns:
            None
        """
        if humidity > maximal:
            if not self.notification_service.check_if_active_repeating("maximalHumidityAlert"):
                self.logger.info(f"Humidity {humidity}% is above maximal threshold of {maximal}%.")
                self.notification_service.send_notification("maximalHumidityAlert", self.name)
        else:
            if self.notification_service.check_if_active_repeating("maximalHumidityAlert"):
                self.logger.info(f"Humidity {humidity}% is below maximal threshold of {maximal}%.")
                self.notification_service.clear_notification("maximalHumidityAlert")


    def check_minimal_humidity_threshold(self, humidity, minimal):
        """
        Check minimal humidity threshold and send/clear notifications accordingly.
        - If humidity is below minimal threshold, sends "minimal humidity alert" notification
        if not already active.
        - If humidity is above minimal threshold, clears "minimal humidity alert" notification
        if active.

        Args:
            humidity (float): Current humidity reading.
            minimal (float): Minimal humidity threshold.

        Returns:
            None
        """
        if humidity < minimal:
            if not self.notification_service.check_if_active_repeating("minimalHumidityAlert"):
                self.logger.info(f"Humidity {humidity}% is below minimal threshold of {minimal}%.")
                self.notification_service.send_notification("minimalHumidityAlert", self.name)
        else:
            if self.notification_service.check_if_active_repeating("minimalHumidityAlert"):
                self.logger.info(f"Humidity {humidity}% is above minimal threshold of {minimal}%.")
                self.notification_service.clear_notification("minimalHumidityAlert")


    def check_courier_button(self, wait_time=30):
        """
        Check the status of the courier button and handle courier waiting state.
        - If the courier button is pressed, courier is not already waiting, space is available,
        and the door is not open, sets RGB button to yellow, marks courier as waiting,
        sends "courier waiting" notification, and schedules a job to reset the courier button
        state after some time.

        Args:
            wait_time (int): Time in seconds to wait before resetting the courier button state.

        Returns:
            None
        """
        if self.rgb_button.get_status() and not self.is_courier_waiting and self.is_space_available and not self.door_sensor.is_door_open():
            self.logger.info("Courier button pressed. Courier is waiting.")
            self.rgb_button.set_RGB_color(255, 255, 0)
            self.is_courier_waiting = True
            self.notification_service.send_notification("courierWaiting", self.name)
            self.scheduler.add_job(self.reset_courier_button, 'date', run_date=datetime.datetime.now() + datetime.timedelta(seconds=wait_time), id='reset_courier_button', coalesce=True, misfire_grace_time=10)


    def autolock_slide_door(self, step_motor_lock):
        """
        Auto-lock the slide parcel door using the step motor lock.

        Args:
            step_motor_lock: Step motor lock component for locking the slide parcel door.

        Returns:
            None
        """
        self.logger.info("Auto-locking slide parcel door after selected time.")
        step_motor_lock.lock_door()


    def autolock_main_door(self, electromagnetic_lock):
        """
        Auto-lock the main door using the electromagnetic lock.

        Args:
            electromagnetic_lock: Electromagnetic lock component for locking the main door.

        Returns:
            None
        """
        self.logger.info("Auto-locking main door after selected time.")
        electromagnetic_lock.lock()


    def check_if_door_open(self, door_sensor, electromagnetic_lock):
        """
        Check if the main door is open for too long and handle notifications and locking.
        - If the door is open, sends "main door opened too long" notification if not
        already active, sets RGB button to blue, and schedules periodic checks every 5 seconds.
        - If the door is closed, clears "main door opened too long" notification if active
        and stops periodic checks. If the door is closed but not locked, locks the door.

        Args:
            door_sensor: Door sensor component to monitor door status.
            electromagnetic_lock: Electromagnetic lock component for locking the main door.

        Returns:
            None
        """
        if door_sensor.is_door_open():
            self.logger.info("Main door is opened for a long time. Sending notification.")
            if not self.notification_service.check_if_active_repeating("mainDoorOpenedTooLong"):
                self.notification_service.send_notification("mainDoorOpenedTooLong", self.name)
                self.rgb_button.set_RGB_color(0,0,255)
                self.scheduler.add_job(self.check_if_door_open, 'interval', seconds=5, args=[door_sensor, electromagnetic_lock], id='check_if_door_open', coalesce=True, misfire_grace_time=10)
        elif not door_sensor.is_door_open():
            if self.scheduler.get_job("check_if_door_open"):
                self.logger.info("Main door is closed now. Clearing notification and stopping checks.")
                if self.is_space_available:
                    self.rgb_button.set_RGB_color(0, 255, 0)
                else:
                    self.rgb_button.set_RGB_color(255, 0, 0)
                self.notification_service.clear_notification("mainDoorOpenedTooLong")
                self.scheduler.remove_job("check_if_door_open")
            if not electromagnetic_lock.is_locked():
                self.logger.info("Main door is closed but not locked. Locking the door.")
                electromagnetic_lock.lock()


    def reset_courier_button(self):
        """
        Reset the courier button state after a specified wait time.
        - If the courier is marked as waiting and the door is not open, resets the courier
          waiting state, updates the RGB button color based on space availability, and logs the action.

        Returns:
            None
        """
        if self.is_courier_waiting and not self.door_sensor.is_door_open():
            self.logger.info("Resetting courier button state.")
            self.is_courier_waiting = False
            if self.is_space_available:
                self.rgb_button.set_RGB_color(0, 255, 0)
            else:
                self.rgb_button.set_RGB_color(255, 0, 0)


    def check_door_status(self, door_sensor):
        """
        Check the door status and update RGB button color accordingly.

        Args:
            door_sensor: Door sensor component to monitor door status.

        Returns:
            None
        """
        if door_sensor.is_door_open():
            self.rgb_button.set_RGB_color(0, 0, 255)

        if not door_sensor.is_door_open() and self.scheduler.get_job("check_if_door_opened"):
            self.scheduler.remove_job("check_if_door_opened")


    def unlock_door_using_nfc_tag(self):
        """
        Unlock the main door using an NFC tag.
        - Reads the UID from the NFC tag and checks if it is registered in the system.
        - If registered, reads data from the tag and compares its hash with the stored hash.
        - If hashes match and the door is locked and closed, unlocks the door, resets
        courier button if needed, schedules auto-lock and door open checks, and sends
        a notification about the door being opened by NFC.

        Args:
        """
        uid = self.nfc_reader.read_uid_tag()
        if uid:
            uid_hex = ''.join("{:02X}".format(x) for x in uid)
            try:
                if not os.path.exists('src/secrets/rfid_tags.json'):
                    if self.logger:
                        self.logger.warning(f"File with RFID cards not found. Creating empty file for it.")
                    with open('src/secrets/rfid_tags.json', 'w') as f:
                        json.dump({}, f, indent=4)

                with open('src/secrets/rfid_tags.json', 'r') as f:
                    records = json.load(f)

                nfc_dict = {r["uid_hex"]: r["code"] for r in records}

                if uid_hex in nfc_dict:
                    data = self.nfc_reader.read_data_from_tag(uid)
                    if data:
                        text = bytes(data).decode('utf-8').rstrip(' ')

                        read_hash = hashlib.sha256(text.encode()).hexdigest()
                        stored_hash = hashlib.sha256(nfc_dict[uid_hex].encode()).hexdigest()

                        if read_hash == stored_hash and data:
                            if self.electromagnetic_lock.is_locked() and not self.door_sensor.is_door_open():
                                self.electromagnetic_lock.unlock()

                                if self.is_courier_waiting:
                                    self.reset_courier_button()
                                    if self.scheduler.get_job("reset_courier_button"):
                                        self.scheduler.remove_job("reset_courier_button")

                                if not self.scheduler.get_job("autolock_main_door"):
                                    self.scheduler.add_job(self.autolock_main_door, 'date', run_date=datetime.datetime.now() + datetime.timedelta(seconds=self.autolock_main_door_seconds), args=[self.electromagnetic_lock], id='autolock_main_door', coalesce=True, misfire_grace_time=10)

                                if not self.scheduler.get_job("check_if_door_opened"):
                                    self.scheduler.add_job(self.check_if_door_open, 'date',
                                                      run_date=datetime.datetime.now() + datetime.timedelta(
                                                          seconds=self.open_main_door_duration_seconds),
                                                      args=[self.door_sensor, self.electromagnetic_lock], id='check_if_door_opened',
                                                      coalesce=True, misfire_grace_time=10)

                                self.notification_service.send_notification("mainDoorOpenedByNFC", self.name, uid=uid_hex)
                                self.logger.info(f"Electromagnetic Lock Unlocked using NFC card with uid {uid_hex}")
                        else:
                            self.logger.warning(f"Could not read data from card with uid {uid_hex}.")
                    else:
                        self.logger.warning(f"Card with uid {uid_hex} doesn't have correct data saved on it.")
                else:
                    self.logger.warning(f"Card with uid {uid_hex} not registered in system.")

            except (json.JSONDecodeError, IOError) as e:
                if self.logger:
                    self.logger.error("Error while loading data from file")
