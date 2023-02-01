#!/usr/bin/env python3
import logging
from zoho_iot_sdk.MqttConstants import transactionStatus, clientStatus, connectionStatus
from zoho_iot_sdk.Utils import Utils, connack_string, puback_string
from os.path import exists
import paho.mqtt.client as MqttClient
import time
import json


class ZohoIoTClient():
    def __init__(self):
        self.mqttUserName = None
        self.mqttPassword = None
        self.caCertificate = None
        self.clientCertificate = None
        self.privateKey = None
        self.privateKeyPassword = None

        self.hostname = None
        self.clientID = None
        self.port = None

        self.dataTopic = None
        self.eventTopic = None
        self.commandsTopic = None
        self.commandsAckTopic = None

        self.secureConnection = False
        self.useClientCertificates = False

        self.connectionString = True

        self.clientStatus = clientStatus.NOT_INITIALIZED

        self.pahoClient = None

        self.isAutoRetryEnabled = False

        self.connack = False

        self.ackCode = -1
        self.JsonData = {}

        self.puback = False

        self.disack = False
        self.disAckCode = -1

        self.subscriptionTopicsSet = []
        self.subAck = False
        self.subAckQOS = -1

    def _onConnect(self, client, userdata, flags, rc):
        self.ackCode = rc
        self.connack = True

    def _onPublish(self, client, userdata, mid):
        self.puback = True

    def _onDisconnect(self, client, userdata, rc):
        self.disack = True
        self.disAckCode = rc

    def _onSubscribe(self, client, userdata, mid, granted_qos):
        self.subAck = True
        self.subAckQOS = granted_qos

    def extractHostNameAndClientId(self, mqttUserName):
        mqttUserNameArray = mqttUserName.split("/")
        if (len(mqttUserNameArray) != 6):
            logging.error("Wrong MQTTUserName format.")
            exit()
        else:
            self.hostname = mqttUserNameArray[1]
            self.clientID = mqttUserNameArray[4]

    def init(self, mqttUserName, mqttPassword=None, caCertificate=None, clientCertificate=None, privateKey=None,
             privateKeyPassword=None):
        if (Utils.is_blank(mqttUserName)):
            logging.error("MQTTUserName cannot be empty")
            return transactionStatus.FAILURE.value
        self.mqttUserName = str(mqttUserName).strip()
        self.mqttPassword = str(mqttPassword).strip()
        self.extractHostNameAndClientId(self.mqttUserName)
        self.dataTopic = "/devices/" + str(self.clientID) + "/telemetry"
        self.eventTopic = "/devices/" + str(self.clientID) + "/events"
        self.commandsTopic = "/devices/" + str(self.clientID) + "/commands"
        self.commandsAckTopic = str(self.commandsTopic) + "/ack"
        self.subscriptionTopicsSet.append(self.commandsTopic)
        # messageListener = new MQTTListener(this, commandsTopic);
        if (self.secureConnection):

            if (Utils.is_blank(caCertificate) or not exists(caCertificate.strip())):
                logging.error("CAFile file is not found/ empty or can't be accessed.")
                return transactionStatus.FAILURE.value
            self.caCertificate = caCertificate.strip()

            if (self.useClientCertificates):
                if ((Utils.is_blank(clientCertificate) or not exists(clientCertificate.strip())) or (
                        Utils.is_blank(privateKey) or not exists(privateKey.trim()))):
                    logging.error("ClientCertificate / PrivateKey file is not found or empty or can't be accessed.");
                    return transactionStatus.FAILURE.value
                self.clientCertificate = str(clientCertificate).strip()
                self.privateKey = privateKey.strip()
                self.privateKeyPassword = privateKeyPassword if Utils.is_blank(
                    privateKeyPassword) else privateKeyPassword.strip()
            else:
                # MQTTPassword is not applicable for Server TLS mode.
                if (Utils.is_blank(self.mqttPassword)):
                    logging.error("MQTTPassword cannot be empty.")
                    return transactionStatus.FAILURE.value
            self.port = 8883

        else:

            if (Utils.is_blank(mqttPassword)):
                logging.error("MQTTPassword cannot be empty.")
                return transactionStatus.FAILURE.value
            self.port = 1883

        self.clientStatus = clientStatus.INITIALIZED
        logging.debug("Client is Initialized")
        return transactionStatus.SUCCESS.value

    def connect(self):
        logging.debug("validating connection")

        if (self.clientStatus == clientStatus.NOT_INITIALIZED):
            logging.error("Client must be initialized")
            return connectionStatus.FAILURE

        if (self.clientStatus == clientStatus.CONNECTED and self.pahoClient.is_connected()):
            logging.debug("already connected!")
            return connectionStatus.SUCCESS

        try:
            if (self.pahoClient == None):
                # locks_dir = new File(System.getProperty("user.dir") + "/locks");
                # pahoClient = new MqttClient(connectionString, clientID, new MqttDefaultFilePersistence(locks_dir.getPath()));
                self.pahoClient = MqttClient.Client(client_id=self.clientID, clean_session=True)

            # connectOptions.setMqttVersion(4);

            self.pahoClient.username_pw_set(self.mqttUserName, self.mqttPassword)

            # make automatic reconnect to be true if we want custom reconnect.
            # connectOptions.setAutomaticReconnect(isAutoRetryEnabled);

            if (self.isAutoRetryEnabled):
                self.pahoClient.reconnect_delay_set(min_delay=1, max_delay=1800000)

            # //TODO: verify to enable or disable hostname verification.
            # connectOptions.setHttpsHostnameVerificationEnabled(false);

            if (self.secureConnection):
                self.pahoClient.tls_set(self.caCertificate, self.clientCertificate, self.privateKey)

            # Calling it before connect only can able to get connectComplete() callbacks.
            # pahoClient.setCallback(messageListener);
            # self.pahoClient.on_connect = lambda client, userdata, flags, rc: self.on_connect(client, userdata, flags, rc)
            # self.pahoClient.on_publish = lambda client, userdata, mid: self.on_publish(client, userdata, mid)
            # self.pahoClient.on_disconnect = lambda client, userdata, rc: self.on_disconnect(client,userdata,rc)
            self.pahoClient.on_connect = self._onConnect
            self.pahoClient.on_publish = self._onPublish
            self.pahoClient.on_disconnect = self._onDisconnect
            self.pahoClient.on_subscribe = self._onSubscribe

            logging.debug("Connecting..")
            self.pahoClient.connect(self.hostname, self.port, keepalive=10, bind_address="")
            self.pahoClient.loop_start()
            logging.debug("waiting for CONNACK")

            while (True):
                if (self.connack):
                    t1_stop = time.process_time()
                    self.connack = False
                    break

            if self.ackCode == 0:
                logging.info("Client connected to MQTT Broker! " + self.hostname)
                self.clientStatus = clientStatus.CONNECTED
            else:
                logging.error("Error code: %d Reason: %s", self.ackCode, connack_string(self.ackCode))
                self.pahoClient.loop_stop()

            if (len(self.subscriptionTopicsSet) != 0):
                for topic in self.subscriptionTopicsSet:
                    self.pahoClient.subscribe(topic)
                    while not self.subAck:
                        pass
                    self.subAck = False

            return self.ackCode

        except Exception as e:
            logging.error("Expection :", e)

    def addDataPoint(self, key, value):
        if (Utils.is_blank(key)):
            logging.error("Can't add empty key")
            return transactionStatus.FAILURE.value
        self.JsonData[key] = value
        return transactionStatus.SUCCESS.value

    def dispatchEvent(self, eventType=None, eventDescription=None, eventDataKeymap=None, assetName=None):
        if (not Utils.is_blank(eventType)):
            self.JsonData["eventType"] = eventType
        if (not Utils.is_blank(eventDescription)):
            self.JsonData["eventDescription"] = eventDescription
        if (not Utils.is_blank(eventDataKeymap)):
            self.JsonData["eventData"] = eventDataKeymap

        self.publishWithTopic(assetName)

    def publishWithTopic(self, assetName=None):
        msg = None
        if (Utils.is_blank(assetName)):
            print(json.dumps(self.JsonData))
            msg = json.dumps(self.JsonData)
        else:
            buffer = {}
            buffer[assetName] = self.JsonData
            msg = json.dumps(buffer)
        logging.debug("Message : %s", msg)
        rc = self.pahoClient.publish(topic=self.dataTopic, payload=msg, qos=0, retain=False)
        while not self.puback:
            pass
        self.puback = False
        if (rc[0] == 0):
            logging.info("Message published successfully")
        else:
            logging.error("Message publish Error code : %d Reason : %s", rc[0], puback_string(rc[0]))
        return rc[0]

    def disconnect(self):
        if (self.clientStatus == clientStatus.NOT_INITIALIZED):
            logging.error("Client must be initialized")
            return transactionStatus.FAILURE.value
        elif (self.clientStatus == clientStatus.INITIALIZED):
            logging.debug("Client must be connected to HUB ")
            return transactionStatus.FAILURE.value

        if (self.pahoClient.is_connected()):
            self.pahoClient.disconnect()
            while not self.disack:
                pass
            self.disack = False
        if (self.disAckCode == 0):
            logging.info("Client disconnected sucessfully")
        else:
            logging.error("Unable to Disconnect paho client , with rc = " + self.disAckCode)
            return transactionStatus.FAILURE.value

        self.clientStatus = clientStatus.DISCONNECTED
        return transactionStatus.SUCCESS.value








