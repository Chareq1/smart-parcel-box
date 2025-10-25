import json
import os
import datetime

"""
src/services/data_manager.py

Data manager service for saving and loading application state.

This module provides the DataManager class which handles saving and loading
application state to and from a JSON file.
"""

class DataManager:
    """
    Class for managing saved data in a JSON file.

    Attributes:
        logger: Logger instance for logging messages.
        file_path (str): Path to the JSON file for saving/loading data.
        data (dict): Dictionary holding the saved data.
    """

    def __init__(self, logger):
        """
        Initialize the DataManager with a logger and default data.

        Args:
            logger: Logger instance for logging messages.
        """
        self.logger = logger
        self.file_path = "src/json/saved_data.json"
        self.data = {
            "door_state": False,
            "parcel_count": 0,
            "is_space_available": True,
            "parcel_door_step_motor_lock_state": False,
            "main_door_electromagnetic_lock_state": True,
            "temperature": 22.0,
            "humidity": 50.0,
            "updated_at": str(datetime.datetime.now())
        }


    def load_data(self):
        """
        Load saved data from JSON file if it exists.
        If the file does not exist or is corrupted, use default data.
        If an error occurs during loading, it will be logged.

        Returns:
            None
        """
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r') as f:
                    self.data = json.load(f)
                self.logger.info("Loaded saved data successfully.")
            except (json.JSONDecodeError, IOError) as e:
                self.logger.error(f"Error loading saved data: {e}. Using default data.")
        else:
            self.logger.info("No saved data file found. Using default data.")


    def save_data(self, data):
        """
        Save the given data to the JSON file.
        If the file does not exist, it will be created.
        If an error occurs during saving, it will be logged.

        Args:
            data (dict): Data to be saved.

        Returns:
            None
        """
        self.data.update(data)
        self.data["updated_at"] = str(datetime.datetime.now())
        try:
            with open(self.file_path, 'w') as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving data: {e}.")