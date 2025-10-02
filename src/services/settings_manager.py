import json
import os

class SettingsManager:
    def __init__(self, settings_path='src/settings.json'):
        self.settings_path = settings_path
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
        }
        self.settings = self.load_settings()

    def load_settings(self):
        if not os.path.exists(self.settings_path):
            self.save_settings(self.default_settings)
            return self.default_settings.copy()
        with open(self.settings_path, 'r') as f:
            return json.load(f)

    def save_settings(self, settings=None):
        if settings is None:
            settings = self.settings
        with open(self.settings_path, 'w') as f:
            json.dump(settings, f, indent=4)

    def get(self, key, default=None):
        return self.settings.get(key, default)

    def set(self, key, value):
        self.settings[key] = value
        self.save_settings()