import paho.mqtt.client as mqtt
import json

"""
src/services/mqtt_handler.py

MQTT handler service for connecting to an MQTT broker, subscribing to topics,
and publishing messages.

This module provides the MQTTHandler class which encapsulates MQTT client
setup, connection, subscription, publishing, and disconnection.
"""

class MQTTHandler:
    """
    Class for handling MQTT connections, subscriptions, and publishing.

    Attributes:
        broker_ip (str): IP address of the MQTT broker.
        subscribe_topics (list): List of topics to subscribe to.
        publish_topics (list): List of topics allowed for publishing.
        client: MQTT client instance.
        logger: Logger instance for logging messages.
    """

    def __init__(self, broker_ip, subscribe_topics, publish_topics, on_message, logger):
        """
        Initialize the MQTTHandler with broker details and topics.

        Args:
            broker_ip (str): IP address of the MQTT broker.
            subscribe_topics (list): List of topics to subscribe to.
            publish_topics (list): List of topics allowed for publishing.
            on_message (function): Callback function for handling incoming messages.
            logger: Logger instance for logging messages.
        """
        self.broker_ip = broker_ip
        self.subscribe_topics = subscribe_topics
        self.publish_topics = publish_topics
        
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = on_message

        self.logger = logger


    def connect(self):
        """
        Connect to the MQTT broker with TLS and start the network loop.

        Returns:
            None
        """
        try:
            self.client.tls_set()
            self.client.tls_insecure_set(False)

            self.client.connect(self.broker_ip, 8883)
            self.client.loop_start()
        except Exception as e:
            self.logger.error(f"Error connecting to MQTT broker at {self.broker_ip}: {e}")


    def publish(self, topic, message):
        """
        Publish a message to a specified topic if allowed.

        Args:
            topic (str): Topic to publish the message to.
            message (dict): Message payload as a dictionary.

        Returns:
            None
        """
        if topic in self.publish_topics:
            payload = json.dumps(message)
            self.client.publish(topic, payload)
        else:
            self.logger.warning(f"Topic {topic} not allowed for publishing.")


    def on_connect(self, client, userdata, flags, rc):
        """
        Callback function for when the client connects to the broker.

        Args:
            client: The MQTT client instance.
            userdata: The private user data.
            flags: Response flags sent by the broker.
            rc: Connection result code.

        Returns:
            None
        """
        self.logger.info(f"Connected to MQTT broker at {self.broker_ip} with result code {rc}")
        for topic in self.subscribe_topics:
            client.subscribe(topic)
            self.logger.info(f"Subscribed to topic: {topic}")


    def disconnect(self):
        """
        Disconnect from the MQTT broker and stop the network loop.

        Returns:
            None
        """
        try:
            self.client.loop_stop()
            self.client.disconnect()
            self.logger.info("Disconnected from MQTT broker.")
        except Exception as e:
            self.logger.error(f"Error while disconnecting from MQTT broker: {e}")