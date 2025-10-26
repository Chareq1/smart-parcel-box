import threading
import json
import logging
import dbus
import dbus.exceptions
import dbus.mainloop.glib
import dbus.service
from gi.repository import GLib

from services.bluetooth.bluetooth_basics import Application, Service, Advertisement
from services.bluetooth.bluetooth_characteristics import SettingsCharacteristic
from services.bluetooth.bluetooth_constants import (
    BLUEZ_SERVICE_NAME,
    DBUS_OM_IFACE,
    ADAPTER_IFACE,
    GATT_MANAGER_IFACE,
    LE_ADVERTISING_MANAGER_IFACE,
    PARCEL_SERVICE_UUID
)

"""
src/services/bluetooth/bluetooth_service.py

Bluetooth service for the Smart Parcel Box.

This module defines the BluetoothService class which orchestrates Bluetooth advertising
and GATT server functionality.
"""

class BluetoothService:
    """
    Bluetooth service for advertising and GATT server functionality.

    Attributes:
        settings: SettingsManager instance for persisting settings.
        logger: Logger instance for logging messages.
        adapter_name: Name of the Bluetooth adapter (e.g., 'hci0').
        device_name: Advertised Bluetooth device name.
        command_cb: Optional callback for handling commands.
        on_settings_update: Optional callback invoked after settings are updated.
    """

    def __init__(self, settings_manager, logger=None, adapter_name='hci0', device_name='SmartParcelBox', command_cb=None, on_settings_update=None):
        """
        Initialize the BluetoothService.

        Args:
            settings_manager: SettingsManager instance for persisting settings.
            logger: Logger instance for logging messages.
            adapter_name (str): Name of the Bluetooth adapter (e.g., 'hci0').
            device_name (str): Advertised Bluetooth device name.
            command_cb: Optional callback for handling commands.
            on_settings_update: Optional callback invoked after settings are updated.
        """
        self.settings = settings_manager
        self.logger = logger or logging.getLogger(__name__)
        self.adapter_name = adapter_name
        self.device_name = device_name
        self.command_cb = command_cb

        self.mainloop = None
        self.mainloop_thread = None
        self.bus = None
        self.app = None

        self.ad_manager = None
        self.advertisement = None

        self.on_settings_update = on_settings_update


    def _find_adapter_path(self):
        """
        Find the D-Bus object path of the specified Bluetooth adapter.

        Returns:
            str or None: The D-Bus object path of the adapter, or None if not found.
        """
        obj = self.bus.get_object(BLUEZ_SERVICE_NAME, "/")
        om = dbus.Interface(obj, DBUS_OM_IFACE)
        managed = om.GetManagedObjects()
        for path, interfaces in managed.items():
            if ADAPTER_IFACE in interfaces:
                if path.endswith(self.adapter_name) or self.adapter_name in path:
                    return path
        return None


    def start(self):
        """
        Start the Bluetooth service: initialize D-Bus, set up advertising and GATT server.

        Raises:
            RuntimeError: If the Bluetooth adapter is not found.

        Returns:
            None
        """
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        self.bus = dbus.SystemBus()

        adapter_path = self._find_adapter_path()
        if adapter_path is None:
            raise RuntimeError("[BLE] Bluetooth adapter not found")

        try:
            adapter_props = dbus.Interface(self.bus.get_object(BLUEZ_SERVICE_NAME, adapter_path), 'org.freedesktop.DBus.Properties')
            adapter_props.Set(ADAPTER_IFACE, "Powered", dbus.Boolean(1))
            adapter_props.Set(ADAPTER_IFACE, "Discoverable", dbus.Boolean(1))
            adapter_props.Set(ADAPTER_IFACE, "Pairable", dbus.Boolean(1))
            adapter_props.Set(ADAPTER_IFACE, "DiscoverableTimeout", dbus.UInt32(0))
        except Exception as e:
            self.logger.warning("[BLE] Failed to power on adapter: %s", e)

        self.app = Application(self.bus)
        service = Service(self.bus, 0, PARCEL_SERVICE_UUID, True)
        self.app.add_service(service)

        settings_ch = SettingsCharacteristic(self.bus, 0, service, self.settings, self.logger, self.on_settings_update)

        service.add_characteristic(settings_ch)

        try:
            adapter_obj = self.bus.get_object(BLUEZ_SERVICE_NAME, adapter_path)
            self.ad_manager = dbus.Interface(adapter_obj, LE_ADVERTISING_MANAGER_IFACE)

            self.advertisement = Advertisement(self.bus, 0, self.device_name, [PARCEL_SERVICE_UUID])
            self.ad_manager.RegisterAdvertisement(self.advertisement.get_path(), {},
                reply_handler=lambda: self.logger.info("[BLE] Advertising as %s", self.device_name),
                error_handler=lambda err: self.logger.error("[BLE] Failed to advertise: %s", err))
        except Exception as e:
            self.logger.exception("[BLE] Failed to start BLE advertising: %s", e)

        try:
            adapter_obj = self.bus.get_object(BLUEZ_SERVICE_NAME, adapter_path)
            gatt_manager = dbus.Interface(adapter_obj, GATT_MANAGER_IFACE)
        except Exception as e:
            self.logger.exception("[BLE] Failed to get GATT manager interface: %s", e)
            raise

        def run_mainloop():
            self.mainloop = GLib.MainLoop()
            try:
                gatt_manager.RegisterApplication(self.app.get_path(), {},
                                                 reply_handler=self._register_app_cb,
                                                 error_handler=self._register_app_error_cb)
            except Exception as ex:
                self.logger.exception("[BLE]Failed to register GATT application: %s", ex)
                return
            self.logger.info("[BLE] GLib mainloop starting for BLE")
            try:
                self.mainloop.run()
            except Exception as ex:
                self.logger.exception("[BLE] Mainloop exception: %s", ex)

        self.mainloop_thread = threading.Thread(target=run_mainloop, daemon=True)
        self.mainloop_thread.start()


    def _register_app_cb(self):
        """
        Callback for successful GATT application registration.

        Returns:
            None
        """
        self.logger.info("[BLE] GATT application registered")


    def _register_app_error_cb(self, error):
        """
        Callback for failed GATT application registration.

        Args:
            error: The error encountered during registration.

        Returns:
            None
        """
        self.logger.error("[BLE] Failed to register application: %s", error)


    def _unregister_advertisement(self):
        """
        Unregister the BLE advertisement.

        Returns:
            None
        """
        if not self.ad_manager or not self.advertisement:
            return
        try:
            self.ad_manager.UnregisterAdvertisement(self.advertisement.get_path())
            self.logger.info("[BLE] Unregistered BLE advertisement")
        except Exception as e:
            self.logger.debug("[BLE] UnregisterAdvertisement failed or unnecessary: %s", e)
        finally:
            try:
                self.advertisement.remove_from_connection(self.bus, self.advertisement.get_path())
            except Exception:
                pass
            self.advertisement = None
            self.ad_manager = None


    def stop(self):
        """
        Stop the Bluetooth service: unregister advertisement and stop mainloop.

        Returns:
            None
        """
        try:
            self._unregister_advertisement()
        except Exception as e:
            self.logger.debug("[BLE] Error while unregistering advertisement: %s", e)

        if self.mainloop:
            try:
                self.mainloop.quit()
            except Exception as e:
                self.logger.debug("[BLE] Error quitting mainloop: %s", e)
        if self.mainloop_thread and self.mainloop_thread.is_alive():
            self.mainloop_thread.join(timeout=2)
        self.logger.info("[BLE] Bluetooth service stopped")