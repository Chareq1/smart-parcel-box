import board
import busio
from digitalio import DigitalInOut
from adafruit_pn532.spi import PN532_SPI

"""
src/components/nfc_reader.py

PN532 NFC Reader module for reading and writing data to MIFARE Classic tags.

This module initializes the PN532 NFC reader, reads the UID of NFC tags,
authenticates using common keys, and provides methods to read and write data
from/to the tags.
"""


COMMON_KEYS = [
    b'\xFF\xFF\xFF\xFF\xFF\xFF',
    b'\x00\x00\x00\x00\x00\x00',
    b'\xD3\xF7\xD3\xF7\xD3\xF7',
    b'\xA0\xA1\xA2\xA3\xA4\xA5'
]
MIFARE_AUTH_A = 0x60
DATA_BLOCK = 4


class NFCReader:
    """
    Class for PN532 NFC Reader for MIFARE Classic tags connected
    to a Raspberry Pi SPI0 pins and D5 (for CS).

    Attributes:
        nfc_reader: Instance of PN532_SPI for NFC operations.
        logger: Logger instance for logging messages.
    """

    def __init__(self, logger):
        """
        Initialize the NFCReader with SPI communication and configures the PN532.
        - Creates SPI bus and CS pin.
        - Initializes PN532_SPI instance.
        - Configures the PN532 to read NFC tags.
        - Sets up a logger for logging messages.

        Args:
            logger: Logger instance for logging messages.
        """
        spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
        cs = DigitalInOut(board.D5)
        self.nfc_reader = PN532_SPI(spi, cs, debug=False)
        self.nfc_reader.SAM_configuration()
        self.logger = logger


    def read_uid_tag(self):
        """
        Reads the UID of a passive NFC tag.

        Returns:
            uid (bytes): UID of the NFC tag if found, else None.
        """
        uid = self.nfc_reader.read_passive_target()
        return uid


    def find_authentication_key(self, uid):
        """
        Attempts to find a valid authentication key for the given UID
        by trying common keys.

        Args:
            uid (bytes): UID of the NFC tag.

        Returns:
            found_key (bytes): The found authentication key, or None if not found.
        """
        found_key = None
        if uid:
            for key in COMMON_KEYS:
                success = self.nfc_reader.mifare_classic_authenticate_block(uid, DATA_BLOCK, MIFARE_AUTH_A, key)
                if success:
                    found_key = key
                    break

        return found_key


    def read_data_from_tag(self, uid):
        """
        Reads data from a specific block of the NFC tag after authenticating.

        Args:
            uid (bytes): UID of the NFC tag.

        Returns:
            block_data (list): Data read from the block if successful, else None.
        """
        found_key = self.find_authentication_key(uid)

        if not found_key:
            self.logger.error("No authentication key found. Authentication failed!")
            return None

        success = self.nfc_reader.mifare_classic_authenticate_block(uid, DATA_BLOCK, MIFARE_AUTH_A, found_key)

        if success:
            block_data = self.nfc_reader.mifare_classic_read_block(DATA_BLOCK)

            if block_data:
                self.logger.info(f"Found data in block {DATA_BLOCK}: {[hex(x) for x in block_data]}")
                return block_data
            else:
                self.logger.error(f"Failed to read data from block {DATA_BLOCK}.")
                return None
        else:
            self.logger.error(f"Failed to authenticate block {DATA_BLOCK}.")
            return None


    def write_data_from_tag(self, uid, data):
        """
        Writes data to a specific block of the NFC tag after authenticating.

        Args:
            uid (bytes): UID of the NFC tag.
            data (str): Data to write to the tag (will be encoded to bytes).

        Returns:
            success (bool): True if write was successful, else None.
        """
        found_key = self.find_authentication_key(uid)

        if not found_key:
            self.logger.error("No authentication key found. Authentication failed!")
            return None

        success = self.nfc_reader.mifare_classic_authenticate_block(uid, DATA_BLOCK, MIFARE_AUTH_A, found_key)

        if success:
            data_to_write = data.encode('utf-8').ljust(16, b' ')

            if self.nfc_reader.mifare_classic_write_block(DATA_BLOCK, data_to_write):
                print(f"Wrote generated code to block {DATA_BLOCK}.")
                return True
            else:
                print(f"Failed to write generated code to block {DATA_BLOCK}.")
                return None
        else:
            self.logger.error(f"Failed to authenticate block {DATA_BLOCK}.")
            return None