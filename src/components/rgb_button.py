from libraries.dfrobot_rgb_button import dfrobot_rgb_button
import smbus

'''!
  @file  rgb_button.py
  @brief  Component for RGB Button
  @details  This file contains all .
  @date  2025-07-05
'''
class RGBButton:
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
        self.rgb_button = dfrobot_rgb_button(i2c_addr, bus)
        if not self.rgb_button.begin():
            raise RuntimeError("Failed to initialize RGB Button!")
        self.rgb_button.set_RGB_color(self.e_black)  # Set initial color to black
    
    def set_RGB_color(self, red, green, blue):
        if isinstance(red, int) and isinstance(green, int) and isinstance(blue, int):
            self.rgb_button.set_RGB_color(red, green, blue)
        else:
            raise ValueError("RGB values must be integers in the range 0-255.")

    def get_status(self):
        return self.rgb_button.get_button_status()
    
    
        
    
    