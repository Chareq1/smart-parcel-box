import dbus
import dbus.exceptions

"""
src/services/bluetooth/bluetooth_constants.py

Bluetooth-related constants and exception classes.

This module defines constants for D-Bus interfaces and UUIDs used in the Bluetooth service, 
as well as custom exception classes for handling Bluetooth-related errors.
"""


# --- Bluetooth Constants ---
BLUEZ_SERVICE_NAME = 'org.bluez'
DBUS_OM_IFACE = 'org.freedesktop.DBus.ObjectManager'
ADAPTER_IFACE = 'org.bluez.Adapter1'
GATT_MANAGER_IFACE = 'org.bluez.GattManager1'
LE_ADVERTISING_MANAGER_IFACE = 'org.bluez.LEAdvertisingManager1'
LE_ADVERTISEMENT_IFACE = 'org.bluez.LEAdvertisement1'


# --- UUIDs ---
PARCEL_SERVICE_UUID = 'de305d54-75b4-431b-adb2-eb6b9e546014'
PARCEL_SETTINGS_CHAR_UUID = 'de305d54-75b4-431b-adb2-eb6b9e546015'


# --- Custom Exceptions ---
class InvalidArgsException(dbus.exceptions.DBusException):
    _dbus_error_name = 'org.freedesktop.DBus.Error.InvalidArgs'

class NotSupportedException(dbus.exceptions.DBusException):
    _dbus_error_name = 'org.bluez.Error.NotSupported'