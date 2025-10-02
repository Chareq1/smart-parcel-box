import firebase_admin
from firebase_admin import credentials, firestore, messaging

class FirebaseService:
    def __init__(self):
        cred = credentials.Certificate("src/secrets/smart-parcel-box-firebase.json")
        firebase_admin.initialize_app(cred)
        self.db = firestore.client() 
    
    def send_notification(self, title: str, body: str):
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body
            ),
            topic="all_users"
        )
        messaging.send(message)