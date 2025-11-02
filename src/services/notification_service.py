from services.firebase_service import FirebaseService
import json

"""
src/services/notification_service.py

Notification service for sending and scheduling notifications.

This module provides the NotificationService class which handles sending
notifications via Firebase and scheduling repeating notifications.
"""

class NotificationService:
    """
    Class for managing notifications.

    Attributes:
        logger: Logger instance for logging messages.
        firebase_service: Instance of FirebaseService for sending notifications.
        all_notifications (list): List of all notification templates loaded from JSON.
        active_repeating_notifications (list): List of keys for currently active repeating notifications.
        scheduler: Scheduler instance for scheduling repeating notifications.
    """

    def __init__(self, scheduler=None, logger=None):
        """
        Initialize the NotificationService with a logger and load notifications.

        Args:
            scheduler: Scheduler instance for scheduling repeating notifications.
            logger: Logger instance for logging messages.
        """
        self.logger = logger
        self.firebase_service = FirebaseService(self.logger)
        self.active_repeating_notifications = []
        try:
            with open("src/json/notifications.json", "r") as f:
                self.all_notifications = json.load(f)
        except FileNotFoundError:
            if self.logger:
                self.logger.warning("Notifications file not found. Starting with an empty list.")
            self.all_notifications = []
        except json.JSONDecodeError as e:
            if self.logger:
                self.logger.error(f"Error while loading notifications: {e}. Starting with an empty list.")
            self.all_notifications = []
        self.scheduler = scheduler


    def send_notification(self, key: str, name: str, uid: str = None):
        """
        Send a notification based on the provided key and name.
        - If the notification is repeatable and not already active, schedule it to repeat after some time.
        - Replace "%name%" in the title and body with the provided name.
        - Log the notification sending process.
        - Handle any exceptions that occur during sending.

        Args:
            key (str): The key identifying the notification template.
            name (str): The name to replace in the notification title and body.
            uid (str): Optional NFC tag UID to replace in the notification body.

        Returns:
            None
        """
        for notification in self.all_notifications:
            if notification["key"] == key:
                try:
                    notification["title"] = notification["title"].replace("%name%", name)
                    notification["body"] = notification["body"].replace("%name%", name)

                    if uid:
                        notification["body"] = notification["body"].replace("%uid%", uid)


                    self.firebase_service.send_notification(notification["title"], notification["body"])
                    self.logger.info(f"Notification sent: {notification['title']} - {notification['body']}")
                    if notification["isRepeatable"] and key not in self.active_repeating_notifications:
                        self.logger.info(f"Scheduling repeating notification: {key}")
                        self.active_repeating_notifications.append(notification["key"])
                        self.scheduler.add_job(self.send_notification, 'interval', minutes=60, args=[key, name], id=key, coalesce=True, misfire_grace_time=10)
                    break
                except Exception as e:
                    if self.logger:
                        self.logger.error(f"Error while sending notification: {e}")
                    break
    
    
    def clear_notification(self, key: str):
        """
        Clear a repeating notification based on the provided key.

        Args:
            key (str): The key identifying the notification to clear.

        Returns:
            None
        """
        if key in self.active_repeating_notifications:
            self.logger.info(f"Clearing repeating notification: {key}")
            self.scheduler.remove_job(key)
            self.active_repeating_notifications.remove(key)


    def check_if_active_repeating(self, key: str) -> bool:
        """
        Check if a repeating notification with the given key is currently active.

        Args:
            key (str): The key identifying the notification to check.

        Returns:
            bool: True if the notification is active, False otherwise.
        """
        return self.scheduler.get_job(key) is not None
