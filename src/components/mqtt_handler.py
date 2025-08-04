import paho.mqtt.client as mqtt
import json

class MQTTHandler:
    def __init__(self, broker_ip, subscribeTopics, publishTopics, on_message):
        self.broker_ip = broker_ip
        self.subscribeTopics = subscribeTopics
        self.publishTopics = publishTopics
        
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = on_message
    
    def connect(self):
        self.client.connect(self.broker_ip)
        self.client.loop_start()
        
    def publish(self, topic, message):
        if topic in self.publishTopics:
            payload = json.dumps(message)
            self.client.publish(topic, payload)
        else:
            print(f"Topic {topic} not allowed for publishing.")
    
    def on_connect(self, client, userdata, flags, rc):
        print(f"Connected to MQTT broker at {self.broker_ip} with result code {rc}")
        for topic in self.subscribeTopics:
            client.subscribe(topic)
            print(f"Subscribed to topic: {topic}")
    
    def disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()