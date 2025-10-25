import json
import os

"""
src/services/settings_manager.py

Settings manager service for loading and saving application settings.

This module provides the SettingsManager class which handles loading and saving
application settings to and from a JSON file.
"""

class SettingsManager:
    """
    Class for managing application settings in a JSON file.

    Attributes:
        settings_path (str): Path to the JSON file for saving/loading settings.
        logger: Logger instance for logging messages.
        default_settings (dict): Dictionary holding the default settings.
        settings (dict): Dictionary holding the current settings.
    """

    def __init__(self, settings_path='src/json/settings.json', logger=None):
        """
        Initialize the SettingsManager with a logger and default settings.

        Args:
            settings_path (str): Path to the JSON file for saving/loading settings.
            logger: Logger instance for logging messages.
        """
        self.settings_path = settings_path
        self.logger = logger
        self.default_settings = {
            "name": "Parcel 1",
            "description": "Smart Parcel Box",
            "mqtt_broker": "192.168.1.215",
            "data_publish_interval": 3,
            "status_publish_interval": 5,
            "minimal_temperature": 0,
            "maximal_temperature": 50,
            "minimal_humidity": 20,
            "maximal_humidity": 80,
            "ultrasonic_threshold": 10,
            "autolock_slide_parcel_door_seconds": 60,
            "autolock_main_door_seconds": 60,
            "open_main_door_duration_seconds": 60
        }
        self.settings = self.load_settings()


    def load_settings(self):
        """
        Load settings from JSON file if it exists.
        - If the file does not exist, create it with default settings.
        - If the file is corrupted, revert to default settings.
        - If an error occurs during loading, it will be logged.

        Returns:
            dict: Loaded settings dictionary.
        """
        try:
            if not os.path.exists(self.settings_path):
                if self.logger:
                    self.logger.warning(f"Settings file not found. Creating default settings at {self.settings_path}.")
                self.save_settings(self.default_settings)
                return self.default_settings.copy()
            with open(self.settings_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            if self.logger:
                self.logger.error(f"Error while loading settings: {e}. Reverting to default settings.")


    def save_settings(self, settings=None):
        """
        Save the given settings to the JSON file.
        - If the file does not exist, it will be created.
        - If an error occurs during saving, it will be logged.

        Args:
            settings (dict): Settings to be saved. If None, saves current settings.

        Returns:
            None
        """
        try:
            if settings is None:
                settings = self.settings
            with open(self.settings_path, 'w') as f:
                json.dump(settings, f, indent=4)
        except IOError as e:
            if self.logger:
                self.logger.error(f"Error while saving settings: {e}.")


    def get(self, key, default=None):
        """
        Get a setting value by key.

        Args:
            key (str): The key of the setting to retrieve.
            default: The default value to return if the key is not found.

        Returns:
            The value of the setting if found, otherwise the default value.
        """
        return self.settings.get(key, default)


    def set(self, key, value):
        """
        Set a setting value by key and save the settings.

        Args:
            key (str): The key of the setting to set.
            value: The value to set for the setting.

        Returns:
            None
        """
        self.settings[key] = value
        self.save_settings()