import dbus
import dbus.exceptions
import dbus.service
import logging
import json

from services.bluetooth.bluetooth_constants import PARCEL_SETTINGS_CHAR_UUID, InvalidArgsException
from services.bluetooth.bluetooth_basics import Characteristic

"""
src/services/bluetooth/bluetooth_characteristics.py

Bluetooth GATT characteristics for the Smart Parcel Box.

This module defines the SettingsCharacteristic class which handles reading and writing
settings via Bluetooth GATT.
"""

class SettingsCharacteristic(Characteristic):
    """
    Characteristic for reading and writing parcel box settings via Bluetooth GATT.

    Attributes:
        settings: SettingsManager instance for persisting settings.
        logger: Logger instance for logging messages.
        on_settings_update: Callback function to invoke after settings are updated.
    """

    def __init__(self, bus, index, service, settings_manager, logger,  on_settings_update):
        """
        Initialize the SettingsCharacteristic.

        Args:
            bus: D-Bus bus instance.
            index: Characteristic index.
            service: Parent service instance.
            settings_manager: SettingsManager instance for persisting settings.
            logger: Logger instance for logging messages.
            on_settings_update: Callback function to invoke after settings are updated.
        """
        super().__init__(bus, index, PARCEL_SETTINGS_CHAR_UUID, ['read', 'write'], service)
        self.settings = settings_manager
        self.logger = logger or logging.getLogger(__name__)
        self.on_settings_update = on_settings_update


    def ReadValue(self, options):
        """
        Read the current settings and return them as a JSON-encoded byte array.

        Args:
            options: Read options (not used).

        Returns:
            dbus.Array: Byte array containing JSON-encoded settings.
        """
        payload = {
            'name': self.settings.get('name', 'Parcel 1'),
            'description': self.settings.get('description', 'Smart Parcel Box'),
            'minimal_temperature': self.settings.get('minimal_temperature', 0),
            'maximal_temperature': self.settings.get('maximal_temperature', 50),
            'minimal_humidity': self.settings.get('minimal_humidity', 20),
            'maximal_humidity': self.settings.get('maximal_humidity', 80),
            'ultrasonic_threshold': self.settings.get('ultrasonic_threshold', 10),
            'autolock_slide_parcel_door_seconds': self.settings.get('autolock_slide_parcel_door_seconds', 60),
            'autolock_main_door_seconds': self.settings.get('autolock_main_door_seconds', 60),
            'open_main_door_duration_seconds': self.settings.get('open_main_door_duration_seconds', 60),
            'data_publish_interval': self.settings.get('data_publish_interval', 3),
            'status_publish_interval': self.settings.get('status_publish_interval', 5)
        }
        data = json.dumps(payload).encode('utf-8')
        self.logger.info("BLE Read: returning settings JSON")
        return dbus.Array([dbus.Byte(b) for b in data], signature='y')


    def WriteValue(self, value, options):
        """
        Write new settings from a JSON-encoded byte array or key=value pairs.

        Args:
            value: Byte array containing the new settings.
            options: Write options (not used).

        Returns:
            None
        """
        b = bytes(value)
        try:
            s = b.decode('utf-8').strip()
        except Exception:
            raise InvalidArgsException("Invalid encoding")

        try:
            if s.startswith('{'):
                payload = json.loads(s)
            else:
                payload = {}
                for line in s.splitlines():
                    if '=' not in line:
                        continue
                    k, v = line.split('=', 1)
                    payload[k.strip()] = v.strip()

            applied = {}
            for k, v in payload.items():
                allowed_keys = [
                    'name', 'description',
                    'minimal_temperature','maximal_temperature',
                    'minimal_humidity','maximal_humidity',
                    'ultrasonic_threshold',
                    'autolock_slide_parcel_door_seconds',
                    'autolock_main_door_seconds',
                    'open_main_door_duration_seconds',
                    'data_publish_interval','status_publish_interval'
                ]
                if k not in allowed_keys:
                    self.logger.warning("Unknown BLE setting key: %s", k)
                    continue

                # Cast numeric values where appropriate
                if k in [
                    'minimal_temperature','maximal_temperature',
                    'minimal_humidity','maximal_humidity',
                    'ultrasonic_threshold',
                    'autolock_slide_parcel_door_seconds',
                    'autolock_main_door_seconds',
                    'open_main_door_duration_seconds',
                    'data_publish_interval','status_publish_interval'
                ]:
                    try:
                        if '.' in str(v):
                            casted = float(v)
                        else:
                            casted = int(v)
                    except Exception:
                        self.logger.warning("Invalid value for %s: %s", k, v)
                        continue
                else:
                    casted = str(v)

                # Bounds checks
                if k == 'minimal_temperature' and (casted < -40 or casted > 100):
                    self.logger.warning("minimal_temperature out of bounds: %s", casted)
                    continue
                if k == 'maximal_temperature' and (casted < -40 or casted > 100):
                    self.logger.warning("maximal_temperature out of bounds: %s", casted)
                    continue

                try:
                    # Persist to SettingsManager (expects .set(key, value) or adjust to your API)
                    self.settings.set(k, casted)
                except Exception as e:
                    self.logger.error("Failed to persist setting %s: %s", k, e)
                    continue
                applied[k] = casted

            self.logger.info("BLE Write: applied settings: %s", applied)

            if self.on_settings_update:
                try:
                    self.on_settings_update(applied)
                except Exception as e:
                    self.logger.error("on_settings_update callback failed: %s", e)
        except json.JSONDecodeError:
            raise InvalidArgsException("Invalid JSON payload")