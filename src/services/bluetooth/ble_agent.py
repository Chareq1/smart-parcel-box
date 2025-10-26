import dbus
import dbus.mainloop.glib
import dbus.service

"""
src/services/bluetooth/ble_agent.py

BLEAgent implements a Bluetooth Low Energy agent for handling pairing requests using
the "Just Works" method (NoInputNoOutput).

This module provides the BLEAgent class which registers itself with BlueZ to
automatically accept pairing requests without user interaction.
"""


# --- BLE Agent Implementation ---
AGENT_PATH = "/org/bluez/SmartParcelAgent"


class BLEAgent(dbus.service.Object):
    """
    Class for handling BLE pairing requests using "Just Works" method.

    Attributes:
        AGENT_INTERFACE (str): D-Bus interface for the BLE agent.
    """

    AGENT_INTERFACE = "org.bluez.Agent1"


    def __init__(self, bus):
        """
        Initialize the BLEAgent and register it on the D-Bus.

        Args:
            bus: D-Bus system bus instance.
        """
        super().__init__(bus, AGENT_PATH)


    @dbus.service.method(AGENT_INTERFACE, in_signature="", out_signature="")
    def Release(self):
        """
        Handle agent release request.

        Returns:
            None
        """
        pass


    @dbus.service.method(AGENT_INTERFACE, in_signature="o", out_signature="")
    def RequestAuthorization(self, device):
        """
        Handle device authorization request.

        Args:
            device: D-Bus object path of the device requesting authorization.

        Returns:
            None
        """
        print(f"[BLEAgent] Authorizing device {device} -> accepted")
        return


    @dbus.service.method(AGENT_INTERFACE, in_signature="os", out_signature="")
    def AuthorizeService(self, device, uuid):
        """
        Handle service authorization request.

        Args:
            device: D-Bus object path of the device requesting service authorization.
            uuid: UUID of the service being authorized.

        Returns:
            None
        """
        print(f"[BLEAgent] Authorizing service {uuid} for {device} -> accepted")
        return


    @dbus.service.method(AGENT_INTERFACE, in_signature="o", out_signature="")
    def RequestConfirmation(self, device):
        """
        Handle pairing confirmation request.

        Args:
            device: D-Bus object path of the device requesting confirmation.

        Returns:
            None
        """
        print(f"[BLEAgent] Just Works -> auto-confirming pairing for {device}")
        return


    @dbus.service.method(AGENT_INTERFACE, in_signature="o", out_signature="u")
    def RequestPasskey(self, device):
        """
        Handle passkey request.

        Args:
            device: D-Bus object path of the device requesting a passkey.

        Returns:
            dbus.UInt32: Always returns 0 for Just Works pairing.
        """
        print(f"[BLEAgent] Ignoring passkey request for {device}, returning 0")
        return dbus.UInt32(0)


    @dbus.service.method(AGENT_INTERFACE, in_signature="o", out_signature="s")
    def RequestPinCode(self, device):
        """
        Handle PIN code request.

        Args:
            device: D-Bus object path of the device requesting a PIN code.

        Returns:
            str: Always returns an empty string for Just Works pairing.
        """
        print(f"[BLEAgent] Ignoring PIN request for {device}, returning empty string")
        return ""


    @staticmethod
    def register(logger=None):
        """
        Register the BLEAgent with BlueZ to handle pairing requests.

        Args:
            logger: Optional logger instance for logging messages.

        Returns:
            BLEAgent: Instance of the registered BLEAgent, or None on failure.
        """
        try:
            dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
            bus = dbus.SystemBus()

            agent = BLEAgent(bus)
            manager = dbus.Interface(bus.get_object("org.bluez", "/org/bluez"), "org.bluez.AgentManager1")

            manager.RegisterAgent(AGENT_PATH, "NoInputNoOutput")
            manager.RequestDefaultAgent(AGENT_PATH)

            adapter_path = "/org/bluez/hci0"
            props = dbus.Interface(bus.get_object("org.bluez", adapter_path), "org.freedesktop.DBus.Properties")
            props.Set("org.bluez.Adapter1", "Discoverable", dbus.Boolean(True))
            props.Set("org.bluez.Adapter1", "Pairable", dbus.Boolean(True))
            props.Set("org.bluez.Adapter1", "DiscoverableTimeout", dbus.UInt32(0))
            props.Set("org.bluez.Adapter1", "PairableTimeout", dbus.UInt32(0))

            if logger:
                logger.info("BLE Agent registered (Just Works / NoInputNoOutput)")
            else:
                print("BLE Agent registered (Just Works / NoInputNoOutput)")

            return agent

        except Exception as e:
            if logger:
                logger.error(f"Failed to register BLE Agent: {e}")
            else:
                print(f"Failed to register BLE Agent: {e}")
            return None
