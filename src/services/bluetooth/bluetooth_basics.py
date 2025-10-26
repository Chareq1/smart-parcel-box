import dbus
import dbus.exceptions
import dbus.mainloop.glib
import dbus.service

from services.bluetooth.bluetooth_constants import DBUS_OM_IFACE, LE_ADVERTISEMENT_IFACE, LE_ADVERTISING_MANAGER_IFACE, NotSupportedException

"""
src/services/bluetooth/bluetooth_basics.py

Basic Bluetooth GATT and Advertisement classes.

This module provides foundational classes for creating Bluetooth GATT services,
characteristics, and advertisements using D-Bus.
"""


class Application(dbus.service.Object):
    """
    Class representing the GATT application.

    Attributes:
        PATH_BASE (str): Base D-Bus path for the application.
        services (list): List of GATT services in the application.
    """
    PATH_BASE = '/org/bluez/smartparcelbox'


    def __init__(self, bus):
        """
        Initialize the GATT application.

        Args:
            bus: D-Bus bus instance.
        """
        self.path = self.PATH_BASE
        self.services = []
        dbus.service.Object.__init__(self, bus, self.path)


    def get_path(self):
        """
        Get the D-Bus object path of the application.

        Returns:
            dbus.ObjectPath: The D-Bus object path.
        """
        return dbus.ObjectPath(self.path)


    def add_service(self, service):
        """
        Add a GATT service to the application.

        Args:
            service: Service instance to add.

        Returns:
            None
        """
        self.services.append(service)


    @dbus.service.method(DBUS_OM_IFACE, out_signature='a{oa{sa{sv}}}')
    def GetManagedObjects(self):
        """
        Get all managed objects (services and characteristics) in the application.

        Returns:
            dict: Dictionary of object paths to their properties.
        """
        response = {}
        for service in self.services:
            response[service.get_path()] = service.get_properties()
            for ch in service.get_characteristics():
                response[ch.get_path()] = ch.get_properties()
        return response



class Service(dbus.service.Object):
    """
    Class representing a GATT service.

    Attributes:
        path (str): D-Bus object path of the service.
        bus: D-Bus bus instance.
        uuid (str): UUID of the service.
        primary (bool): Indicates if the service is primary.
        characteristics (list): List of characteristics in the service.
    """

    def __init__(self, bus, index, uuid, primary):
        """
        Initialize the GATT service.

        Args:
            bus: D-Bus bus instance.
            index (int): Index of the service.
            uuid (str): UUID of the service.
            primary (bool): Indicates if the service is primary.
        """
        self.path = Application.PATH_BASE + f"/service{index}"
        self.bus = bus
        self.uuid = uuid
        self.primary = primary
        self.characteristics = []
        dbus.service.Object.__init__(self, bus, self.path)


    def get_path(self):
        """
        Get the D-Bus object path of the service.

        Returns:
            dbus.ObjectPath: The D-Bus object path.
        """
        return dbus.ObjectPath(self.path)


    def add_characteristic(self, chrc):
        """
        Add a characteristic to the service.

        Args:
            chrc: Characteristic instance to add.

        Returns:
            None
        """
        self.characteristics.append(chrc)


    def get_characteristics(self):
        """
        Get the list of characteristics in the service.

        Returns:
            list: List of characteristics.
        """
        return self.characteristics


    def get_properties(self):
        """
        Get the properties of the service.

        Returns:
            dict: Dictionary of service properties.
        """
        return {
            'org.bluez.GattService1': {
                'UUID': self.uuid,
                'Primary': self.primary,
                'Characteristics': [ch.get_path() for ch in self.characteristics]
            }
        }



class Characteristic(dbus.service.Object):
    """
    Class representing a GATT characteristic.

    Attributes:
        path (str): D-Bus object path of the characteristic.
        bus: D-Bus bus instance.
        uuid (str): UUID of the characteristic.
        flags (list): List of flags for the characteristic.
        service: Service instance the characteristic belongs to.
    """

    def __init__(self, bus, index, uuid, flags, service):
        """
        Initialize the GATT characteristic.

        Args:
            bus: D-Bus bus instance.
            index (int): Index of the characteristic.
            uuid (str): UUID of the characteristic.
            flags (list): List of flags for the characteristic.
            service: Service instance the characteristic belongs to.
        """
        self.path = service.get_path() + '/char' + str(index)
        self.bus = bus
        self.uuid = uuid
        self.flags = flags
        self.service = service
        dbus.service.Object.__init__(self, bus, self.path)


    def get_path(self):
        """
        Get the D-Bus object path of the characteristic.

        Returns:
            dbus.ObjectPath: The D-Bus object path.
        """
        return dbus.ObjectPath(self.path)


    def get_properties(self):
        """
        Get the properties of the characteristic.

        Returns:
            dict: Dictionary of characteristic properties.
        """
        return {
            'org.bluez.GattCharacteristic1': {
                'Service': self.service.get_path(),
                'UUID': self.uuid,
                'Flags': self.flags,
            }
        }


    @dbus.service.method('org.bluez.GattCharacteristic1', in_signature='a{sv}', out_signature='ay')
    def ReadValue(self, options):
        """
        Raise NotSupportedException for ReadValue.

        Args:
            options: Options for reading the value.

        Returns:
            None
        """
        raise NotSupportedException()

    @dbus.service.method('org.bluez.GattCharacteristic1', in_signature='aya{sv}')
    def WriteValue(self, value, options):
        """
        Raise NotSupportedException for WriteValue.

        Args:
            value: Value to write.
            options: Options for writing the value.

        Returns:
            None
        """
        raise NotSupportedException()



class Advertisement(dbus.service.Object):
    """
    Class representing a Bluetooth LE advertisement.

    Attributes:
        PATH_BASE (str): Base D-Bus path for the advertisement.
        path (str): D-Bus object path of the advertisement.
        bus: D-Bus bus instance.
        name (str): Local name of the advertised device.
        service_uuids (list): List of service UUIDs advertised.
    """

    PATH_BASE = '/org/bluez/smartparcelbox/advertisement'


    def __init__(self, bus, index, name, service_uuids):
        """
        Initialize the LE advertisement.

        Args:
            bus: D-Bus bus instance.
            index (int): Index of the advertisement.
            name (str): Local name of the advertised device.
            service_uuids (list): List of service UUIDs advertised.
        """
        self.path = self.PATH_BASE + str(index)
        self.bus = bus
        self.name = name
        self.service_uuids = service_uuids or []
        dbus.service.Object.__init__(self, bus, self.path)


    def get_path(self):
        """
        Get the D-Bus object path of the advertisement.

        Returns:
            dbus.ObjectPath: The D-Bus object path.
        """
        return dbus.ObjectPath(self.path)


    def get_properties(self):
        """
        Get the properties of the advertisement.

        Returns:
            dict: Dictionary of advertisement properties.
        """
        return {
            LE_ADVERTISEMENT_IFACE: {
                'Type': 'peripheral',
                'LocalName': self.name,
                'ServiceUUIDs': dbus.Array(self.service_uuids, signature='s'),
                'IncludeTxPower': dbus.Boolean(True)
            }
        }


    @dbus.service.method(LE_ADVERTISEMENT_IFACE, in_signature='', out_signature='')
    def Release(self):
        """
        Handle the Release method call for the advertisement.

        Returns:
            None
        """
        pass
