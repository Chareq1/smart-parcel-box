# -*- coding: utf-8 -*

'''!
  @file  DFRobot_RGBButton.py
  @brief  Define infrastructure of DFRobot_RGBButton class
  @details  This file contains the implementation of the DFRobot_RGBButton class, which provides methods to interact with the RGB button hardware using the I2C protocol.
  @copyright  Copyright (c) 2010 DFRobot Co.Ltd (http://www.dfrobot.com)
  @licensecd ense (MIT)
  @version  V1.0
  @date  2022-05-17
  @url  https://github.com/DFRobot/DFRobot_RGBButton
'''

import smbus
from ctypes import *

# Default I2C address for the RGB button
RGBBUTTON_DEFAULT_I2C_ADDR  = 0x2A
# Expected chip ID for the RGB button
RGBBUTTON_PART_ID           = 0x43DF

# Register addresses for the RGB button
RGBBUTTON_I2C_ADDR_REG      = 0x00  # I2C address register
RGBBUTTON_RED_REG           = 0x01  # Red color register
RGBBUTTON_GREEN_REG         = 0x02  # Green color register
RGBBUTTON_BLUE_REG          = 0x03  # Blue color register
RGBBUTTON_BUTTON_SIGNAL_REG = 0x04  # Button signal register
RGBBUTTON_PID_MSB_REG       = 0x09  # Chip ID MSB register
RGBBUTTON_PID_LSB_REG       = 0x0A  # Chip ID LSB register

class dfrobot_rgb_button(object):
    ''' 
      @brief  Constructor of DFRobot_RGBButton class
      @param i2c_addr: I2C address of the RGBButton, default is 0x2A
      @param bus: I2C bus number, default is 1
      @note The RGBButton uses the I2C protocol for communication. 
    '''
    def __init__(self, i2c_addr=RGBBUTTON_DEFAULT_I2C_ADDR, bus=1):
        self._addr = i2c_addr
        self._i2c = smbus.SMBus(bus)

    '''
      @brief  Initialize the RGBButton and verify its chip ID
      @return True if the RGBButton is initialized successfully, False otherwise
      @note This method must be called before using other methods of the class.
    '''
    def begin(self):
        ret = True
        chip_id = self._read_reg(RGBBUTTON_PID_MSB_REG, 2)
        if RGBBUTTON_PART_ID != ((chip_id[0] << 8) | chip_id[1]):
            ret = False
        return ret

    '''
      @brief  Set the RGB color of the button
      @param args: Either a single integer representing the RGB color or three integers for red, green, and blue values
      @note The RGB values should be in the range 0-255.
    '''
    def set_RGB_color(self, *args):
        rgb_buf = [0] * 3
        if 1 == len(args):
          rgb_buf[0] = (args[0] >> 16) & 0xFF
          rgb_buf[1] = (args[0] >> 8) & 0xFF
          rgb_buf[2] = args[0] & 0xFF
        elif 3 == len(args):
          rgb_buf[0] = args[0]
          rgb_buf[1] = args[1]
          rgb_buf[2] = args[2]
        self._write_reg(RGBBUTTON_RED_REG, rgb_buf)

    '''
      @brief Get the current status of the button
      @return True if the button is pressed, False otherwise
    '''
    def get_button_status(self):
        button_status = False
        if 1 == self._read_reg(RGBBUTTON_BUTTON_SIGNAL_REG, 1)[0]:
          button_status = True
        return button_status

    '''
      @brief Write data to a specific register over I2C
      @param reg: The register address to write to
      @param data: The data to write (can be a single integer or a list of integers)
      @note Handles I/O errors gracefully by printing an error message.
    '''
    def _write_reg(self, reg, data):
        if isinstance(data, int):
            data = [data]
        try:
          self._i2c.write_i2c_block_data(self._addr, reg, data)
        except IOError:
          print("Remote I/O error!")

    '''
      @brief Read data from a specific register over I2C
      @param reg: The register address to read from
      @param length: The number of bytes to read
      @return A list of integers representing the data read from the register
      @note Handles I/O errors gracefully by returning a list of zeros.
    '''
    def _read_reg(self, reg, length):
        try:
          return self._i2c.read_i2c_block_data(self._addr, reg, length)
        except IOError:
          print("Remote I/O error!")
          return [0] * length
