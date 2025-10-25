from libraries.dfrobot_rgb_button import dfrobot_rgb_button
import smbus

"""
src/components/rgb_button.py

I2C RGB Button component for a Raspberry Pi GPIO pin.

This module provides the RGBButton class which encapsulates I2C setup and
reading for a DFRobot RGB Button connected to a I2C1 pins.

It uses the DFRobot RGB Button library to control the RGB button.
"""

class RGBButton:
    """
    Class for an RGB Button connected to a Raspberry Pi I2C pins.

    Attributes:
        rgb_button: Instance of the DFRobot RGB Button class.
        is_courier_waiting (bool): Status of courier waiting.
    """

    # Predefined RGB color values
    e_red    = 0xFF0000
    e_orange = 0xFF7F00
    e_yellow = 0xFFFF00
    e_green  = 0x00FF00 
    e_cyan   = 0x00FFFF 
    e_blue   = 0x0000FF 
    e_purple = 0x8B00FF 
    e_white  = 0xFFFFFF 
    e_black  = 0x000000 


    def __init__(self, i2c_addr=0x2A, bus=1):
        """
        Initialize I2C and DFRobot RGB Button.
        - Creates instance of DFRobot RGB Button.
        - Checks if RGB Button initializes correctly, raises RuntimeError if not.
        - Sets initial RGB color to black.

        Args:
            i2c_addr (int): I2C address of the RGB Button.
            bus (int): I2C bus number.
        """
        self.rgb_button = dfrobot_rgb_button(i2c_addr, bus)
        if not self.rgb_button.begin():
            raise RuntimeError("Failed to initialize RGB Button!")
        self.rgb_button.set_RGB_color(self.e_black)  # Set initial color to black


    def set_RGB_color(self, red, green, blue):
        """
        Set the RGB color of the button.

        Args:
            red (int): Red component (0-255).
            green (int): Green component (0-255).
            blue (int): Blue component (0-255).
        """
        if isinstance(red, int) and isinstance(green, int) and isinstance(blue, int):
            self.rgb_button.set_RGB_color(red, green, blue)
        else:
            raise ValueError("RGB values must be integers in the range 0-255.")


    def get_status(self):
        """
        Check whether the RGB button is currently pressed or not.

        Returns:
            bool: True if the button is pressed, False otherwise.
        """
        return self.rgb_button.get_button_status()

    
    
        
    
    