import firebase_admin
from firebase_admin import credentials, firestore, messaging

"""
src/services/firebase_service.py

FirebaseService handles interactions with Firebase services such as Firestore and Cloud Messaging.

This module provides the FirebaseService class which initializes the Firebase app,
connects to Firestore, and sends notifications via Firebase Cloud Messaging.
"""

class FirebaseService:
    """
    Class for interacting with Firebase services.

    Attributes:
        logger: Logger instance for logging messages.
        db: Firestore client instance.
    """

    def __init__(self, logger):
        """
        Initialize Firebase app and Firestore client.

        Args:
            logger: Logger instance for logging messages.
        """
        cred = credentials.Certificate("src/secrets/smart-parcel-box-firebase.json")
        firebase_admin.initialize_app(cred)
        self.logger = logger
        try:
            self.db = firestore.client()
            self.logger.info("Connected to Firestore database.")
        except Exception as e:
            self.logger.error(f"Error connecting to Firestore database: {e}")


    def send_notification(self, title: str, body: str):
        """
        Send a notification via Firebase Cloud Messaging.

        Args:
            title (str): Title of the notification.
            body (str): Body of the notification.
        """
        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body
                ),
                topic="all_users"
            )
            messaging.send(message)
            self.logger.info(f"Notification sent: {title} - {body}")
        except Exception as e:
            self.logger.error(f"Error while sending notification: {e}")
    
    