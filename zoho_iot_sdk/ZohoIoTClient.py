#!/usr/bin/env python3
import logging

from zoho_iot_sdk.MqttConstants import TransactionStatus, ClientStatus, CommandAckResponseCodes, ConfigAckResponseCodes
from os.path import exists
import paho.mqtt.client as MqttClient
import json
import threading
import yaml


class ZohoIoTClient:
    def __init__(self, secureConnection=False, useClientCertificates=False):
        self.mqttUserName = None
        self.mqttPassword = None
        self.hostname = None
        self.clientID = None
        self.port = None

        self.caCertificate = None
        self.clientCertificate = None
        self.privateKey = None
        self.privateKeyPassword = None
        self.secureConnection = secureConnection
        self.useClientCertificates = useClientCertificates

        self.dataTopic = None
        self.eventTopic = None
        self.commandsTopic = None
        self.commandsAckTopic = None
        self.configTopic = None
        self.configAckTopic = None

        self.disconnectResponseCode = -1
        self.connectResponseCode = -1
        self.clientStatus = ClientStatus.NOT_INITIALIZED
        self.subscriptionTopicsList = []
        self.connectionEvent = threading.Event()
        self.subscribeEvent = threading.Event()
        self.callBackList = {}

        self.pahoClient = None
        self.payloadJSON = {}

        self.logger = logging.getLogger(self.__module__ + "." + self.__class__.__name__)
        self.logger.setLevel(logging.DEBUG)
        self.logger.handlers = []
        c_handler = logging.StreamHandler()
        c_format = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
        c_handler.setFormatter(c_format)
        self.logger.addHandler(c_handler)

    def is_blank(self, Input):
        if Input is not None and Input.strip() != "":
            return False
        return True

    def setLogger(self, loglevel=None, filename=None):
        if not self.is_blank(loglevel):
            if loglevel == "INFO":
                self.logger.setLevel(logging.INFO)
            elif loglevel == "DEBUG":
                self.logger.setLevel(logging.DEBUG)
            elif loglevel == "ERROR":
                self.logger.setLevel(logging.ERROR)
            else:
                self.logger.error("Loglevel: %s invalid, Please use INFO or DEBUG or ERROR")
        if not self.is_blank(filename):
            for handler in self.logger.handlers:
                if isinstance(handler, logging.FileHandler):
                    self.logger.removeHandler(handler)
            f_handler = logging.FileHandler(filename)
            f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            f_handler.setFormatter(f_format)
            self.logger.addHandler(f_handler)

    def _onConnect(self, client, userdata, flags, rc):
        self.connectResponseCode = rc
        if self.connectResponseCode == 0:
            if self.clientStatus == ClientStatus.DISCONNECTED:
                self.logger.info("Client reconnected")
                threading.Thread(target=self.resubscribe, args=()).start()
        self.clientStatus = ClientStatus.CONNECTED
        self.connectionEvent.set()

    def _onPublish(self, client, userdata, mid):
        self.connectionEvent.set()

    def _onDisconnect(self, client, userdata, rc):
        self.logger.info("Client disconnected")
        self.clientStatus = ClientStatus.DISCONNECTED
        self.disconnectResponseCode = rc
        self.connectionEvent.set()

    def _onSubscribe(self, client, userdata, mid, granted_qos):
        self.subscribeEvent.set()

    def _onMessage(self, client, userdata, msg):
        self.logger.info("Message Received")
        self.logger.debug("Message:%s ,Topic:%s ", msg.payload, msg.topic)
        if msg.topic == self.commandsTopic:
            threading.Thread(target=self.handleCommand, args=(msg,)).start()
        elif msg.topic == self.configTopic:
            threading.Thread(target=self.handleConfig, args=(msg,)).start()
        else:
            if msg.topic in self.callBackList:
                threading.Thread(target=self.callBackList[msg.topic], args=(self, msg,)).start()
            else:
                self.logger.error("Invalid topic")

    def isConnected(self):
        return self.pahoClient.is_connected()

    def handleCommand(self, message):
        self.sendFirstAck(message=message.payload, topic=self.commandsAckTopic,
                          ackCode=CommandAckResponseCodes.COMMAND_RECEIVED_ACK_CODE)
        if self.commandsTopic in self.callBackList:
            threading.Thread(target=self.callBackList[self.commandsTopic], args=(self, message,)).start()

    def handleConfig(self, message):
        self.sendFirstAck(message=message.payload, topic=self.configAckTopic,
                          ackCode=ConfigAckResponseCodes.CONFIG_RECEIVED_ACK_CODE)
        if self.configTopic in self.callBackList:
            threading.Thread(target=self.callBackList[self.configTopic], args=(self, message,)).start()


    def sendFirstAck(self, message, topic, ackCode):  # --
        commands_list = json.loads(message)
        ack_payload = {}
        for i in range(len(commands_list)):
            correlationId = commands_list[i]["correlation_id"]
            ack_payload[correlationId] = {"status_code": ackCode.value,
                                          "response": ""}
        return self.publishWithTopic(topic=topic, message=json.dumps(ack_payload))

    def publishCommandAckList(self, payloadJSON):
        self.publishAckLst(topic=self.commandsAckTopic, payload=payloadJSON)

    def publishConfigAckList(self, payloadJSON):
        self.publishAckLst(topic=self.configAckTopic, payload=payloadJSON)

    def publishAckLst(self, topic, payload):
        continue_flag = True
        try:
            ack_payload_object = json.loads(payload)
            for i in range(len(ack_payload_object)):
                key = list(ack_payload_object.keys())[i]
                correlation_id = ack_payload_object[key]
                status_code = correlation_id["status_code"]
                if key is None:
                    self.logger.error("Correlation_id is empty or null")
                    continue_flag = False
                    break
                if status_code is None or type(status_code) != int:
                    self.logger.error("Status_code key is either missing or not valid")
                    continue_flag = False
                    break
                if correlation_id["response"] is None:
                    self.logger.error("Response string is missing")
                    continue_flag = False
                    break
                if len(correlation_id) > 2:
                    self.logger.error("Correlation object has additional keys other than status_code and response")
                    continue_flag = False
                    break
        except ValueError as err:
            self.logger.error("Command Ack message is an invalid JSON, Error message:%s", err)
            continue_flag = False

        if not continue_flag:
            self.logger.error("Cannot publish with improper Command ACK structure :\n" + payload)
            return TransactionStatus.FAILURE.value

        return self.publishWithTopic(topic=topic, message=payload)

    def publishCommandAck(self, correlation_id, status_code, responseMessage):
        if status_code not in CommandAckResponseCodes:
            self.logger.error("Invalid status code")
            return TransactionStatus.FAILURE.value
        self.publishAck(topic=self.commandsAckTopic, correlation_id=correlation_id, status_code=status_code,
                        responseMessage=responseMessage)

    def publishConfigAck(self, correlation_id, status_code, responseMessage):
        if status_code not in ConfigAckResponseCodes:
            self.logger.error("Invalid status code")
            return TransactionStatus.FAILURE.value
        self.publishAck(topic=self.configAckTopic, correlation_id=correlation_id, status_code=status_code,
                        responseMessage=responseMessage)

    def publishAck(self, topic, correlation_id, status_code, responseMessage):
        if self.is_blank(correlation_id) or responseMessage is None:
            self.logger.error("Correlation ID or response Message can't be NULL or empty")
            return TransactionStatus.FAILURE.value
        ack_payload = {correlation_id: {"status_code": status_code.value, "response": responseMessage}}
        return self.publishWithTopic(topic=topic, message=json.dumps(ack_payload))

    def validateClientState(self):
        if self.clientStatus == ClientStatus.NOT_INITIALIZED:
            self.logger.error("Client must be initialized")
            return TransactionStatus.FAILURE.value
        elif ClientStatus == ClientStatus.DISCONNECTED:
            self.logger.debug("Connection to server is disconnected")
            return TransactionStatus.CONNECTION_ERROR.value
        elif ClientStatus == ClientStatus.INITIALIZED:
            self.logger.debug("Client must be connected to HUB ")
            return TransactionStatus.FAILURE.value
        else:
            if self.isConnected():
                return TransactionStatus.SUCCESS.value
            else:
                return TransactionStatus.FAILURE.value

    def extractHostNameAndClientId(self, mqttUserName):
        mqttUserNameArray = mqttUserName.split("/")
        if len(mqttUserNameArray) != 6:
            self.logger.error("Wrong MQTTUserName format.")
            return False
        else:
            self.hostname = mqttUserNameArray[1]
            self.clientID = mqttUserNameArray[4]
            return True

    def initYamlConfiguration(self, file):
        if self.is_blank(file) and not exists(file.strip()):
            self.logger.error("Location is blank or yaml file missing in the location")
            return TransactionStatus.FAILURE.value
        with open(file) as file:
            configuration = yaml.full_load(file)
        if configuration["ENABLE_TLS"]:
            self.secureConnection = True
        if configuration["USE_CLIENT_CERTS"]:
            self.useClientCertificates = True
        if configuration["LOG_LEVEL"] is not None:
            self.setLogger(loglevel=configuration["LOG_LEVEL"])
        if configuration["LOG_FILENAME"] is not None:
            self.setLogger(filename=configuration["LOG_FILENAME"])
        self.logger.debug("Configuration data:%s", configuration)
        return self.init(mqttUserName=configuration['MQTT_USERNAME'], mqttPassword=configuration['MQTT_PASSWORD'],
                         caCertificate=configuration['CA_CRT'], clientCertificate=configuration['CLIENT_CRT'],
                         privateKey=configuration['CLIENT_KEY'])

    def init(self, mqttUserName, mqttPassword='', caCertificate=None, clientCertificate=None, privateKey=None,
             privateKeyPassword=None):
        if self.is_blank(mqttUserName):
            self.logger.error("MQTTUserName cannot be empty")
            return TransactionStatus.FAILURE.value

        self.mqttUserName = str(mqttUserName).strip()
        self.mqttPassword = str(mqttPassword).strip()
        if not self.extractHostNameAndClientId(self.mqttUserName):
            self.clientStatus = ClientStatus.NOT_INITIALIZED
            return False
        topicPrefix = "/devices/" + str(self.clientID)
        self.dataTopic = topicPrefix + "/telemetry"
        self.eventTopic = topicPrefix + "/events"
        self.commandsTopic = topicPrefix + "/commands"
        self.commandsAckTopic = str(self.commandsTopic) + "/ack"
        self.configTopic = topicPrefix + "/configsettings"
        self.configAckTopic = str(self.configTopic) + "/ack"
        self.subscriptionTopicsList.append(self.commandsTopic)
        self.subscriptionTopicsList.append(self.configTopic)

        if self.secureConnection:
            if self.is_blank(caCertificate) or not exists(caCertificate.strip()):
                self.logger.error("CAFile file is not found/ empty or can't be accessed.")
                return TransactionStatus.FAILURE.value

            self.caCertificate = caCertificate.strip()

            if self.useClientCertificates:
                if ((self.is_blank(clientCertificate) or not exists(clientCertificate.strip())) or (
                        self.is_blank(privateKey) or not exists(privateKey.strip()))):
                    self.logger.error("ClientCertificate / PrivateKey file is not found or empty or can't be accessed.")
                    return TransactionStatus.FAILURE.value
                self.clientCertificate = clientCertificate.strip()
                self.privateKey = privateKey.strip()
                self.privateKeyPassword = privateKeyPassword if self.is_blank(
                    privateKeyPassword) else privateKeyPassword.strip()
            else:
                # MQTTPassword is not applicable for Server TLS mode.
                if self.is_blank(self.mqttPassword):
                    self.logger.error("MQTTPassword cannot be empty.")
                    return TransactionStatus.FAILURE.value
            self.port = 8883

        else:
            if self.is_blank(mqttPassword):
                self.logger.error("MQTTPassword cannot be empty.")
                return TransactionStatus.FAILURE.value
            self.port = 1883

        self.clientStatus = ClientStatus.INITIALIZED
        self.logger.debug("Client is Initialized")
        return TransactionStatus.SUCCESS.value

    def connect(self):
        self.logger.debug("trying to  connect..")
        if self.clientStatus == ClientStatus.NOT_INITIALIZED:
            self.logger.error("Client must be initialized")
            return TransactionStatus.FAILURE.value

        if self.clientStatus == ClientStatus.CONNECTED and self.isConnected():
            self.logger.debug("already connected!")
            return MqttClient.CONNACK_ACCEPTED

        try:
            if self.pahoClient is None:
                self.pahoClient = MqttClient.Client(client_id=self.clientID, clean_session=True, protocol=4)

            # self.pahoClient.enable_logger(logging.DEBUG)
            self.pahoClient.username_pw_set(self.mqttUserName, self.mqttPassword)
            self.pahoClient.reconnect_delay_set(min_delay=1, max_delay=1800)
            self.pahoClient._connect_timeout = 10

            if self.secureConnection:
                self.pahoClient.tls_set(ca_certs=self.caCertificate, certfile=self.clientCertificate,
                                        keyfile=self.privateKey)

            self.pahoClient.on_connect = self._onConnect
            self.pahoClient.on_publish = self._onPublish
            self.pahoClient.on_disconnect = self._onDisconnect
            self.pahoClient.on_subscribe = self._onSubscribe
            self.pahoClient.on_message = self._onMessage

            self.logger.debug("Connecting..")
            self.connectionEvent.clear()
            self.pahoClient.connect(self.hostname, self.port, keepalive=60)
            self.pahoClient.loop_start()

            if not self.connectionEvent.wait(timeout=60):
                self.logger.error("Connection timeout, unable to connect to client: %s", self.hostname)
                self.pahoClient.loop_stop()
                return TransactionStatus.FAILURE.value

            if self.connectResponseCode == 0:
                self.logger.info("Client connected to MQTT Broker! " + self.hostname)
            else:
                self.logger.error("Error code: %d Reason: %s", self.connectResponseCode,
                                  MqttClient.connack_string(self.connectResponseCode))
                self.pahoClient.loop_stop()
                return self.connectResponseCode

            self.subscribe(topicList=self.subscriptionTopicsList)

            return self.connectResponseCode

        except Exception as e:
            self.logger.error("Exception :", e)
            return TransactionStatus.FAILURE.value

    def addDataPoint(self, key, value, assetName=None):
        if self.is_blank(key):
            self.logger.error("Can't add empty key")
            return TransactionStatus.FAILURE.value

        if self.is_blank(assetName):
            self.payloadJSON[key] = value
        else:
            if assetName in self.payloadJSON.keys():
                self.payloadJSON[assetName][key] = value
            else:
                valueObject = {key: value}
                self.payloadJSON[assetName] = valueObject
        return TransactionStatus.SUCCESS.value

    def addJson(self, json_data):
        if self.is_blank(json_data):
            logging.error("Can't add empty json")
            return TransactionStatus.FAILURE.value
        try:
            parsed_data = json.loads(json_data)
            self.JsonData = parsed_data
            return TransactionStatus.SUCCESS.value
        except json.JSONDecodeError as e:
            logging.error("Invalid json ")
        return TransactionStatus.FAILURE.value

    def markDataPointAsError(self, key, assetName=None):
        return self.addDataPoint(key=key, value="<ERROR>", assetName=assetName)

    def dispatch(self):
        rc = self.publishWithTopic(topic=self.dataTopic, message=json.dumps(self.payloadJSON))
        if rc == 0:
            self.payloadJSON = {}
        return rc

    def publish(self, messageString):
        rc = self.publishWithTopic(topic=self.dataTopic, message=json.dumps(messageString))
        if rc == 0:
            self.payloadJSON = {}
        return rc

    def dispatchEvent(self, eventType=None, eventDescription=None, eventDataKeymap=None, assetName=None):
        if self.is_blank(eventType) or self.is_blank(eventDescription) or eventDataKeymap is None:
            self.logger.error("Can't append NULL arguments to Event.")
            return TransactionStatus.FAILURE
        payload = {}
        if not self.is_blank(eventType):
            payload["eventType"] = eventType
        if not self.is_blank(eventDescription):
            payload["eventDescription"] = eventDescription
        if eventDataKeymap is not None:
            payload["eventData"] = eventDataKeymap
        if self.is_blank(assetName):
            return self.publishWithTopic(topic=self.dataTopic, message=json.dumps(payload))
        else:
            return self.dispatchAsset(assetName)

    def dispatchAsset(self, assetName):
        if self.is_blank(assetName):
            self.logger.error("Asset Name can't be null")
            return TransactionStatus.FAILURE
        payload = {assetName: self.payloadJSON}
        rc = self.publishWithTopic(topic=self.dataTopic, message=json.dumps(payload))
        if rc == 0:
            self.payloadJSON = {}
        return rc

    def publishWithTopic(self, topic, message):
        if self.is_blank(topic):
            self.logger.error("Topic can't be blank")
            return TransactionStatus.FAILURE
        if self.is_blank(message):
            self.logger.error("Message can't be blank")
            return TransactionStatus.FAILURE
        self.connectionEvent.clear()
        rc = self.pahoClient.publish(topic=topic, payload=message, qos=0, retain=False)
        if not self.connectionEvent.wait(timeout=10):
            self.logger.error("Publish timeout, unable to publish message")
            return TransactionStatus.FAILURE

        if rc[0] == 0:
            self.logger.info("Message published successfully")
            self.logger.debug("Message :%s , topic :%s", message, topic)
        else:
            self.logger.error("Message publish Error code : %d Reason : %s", rc[0], MqttClient.error_string(rc[0]))
        return rc[0]

    def disconnect(self):
        if self.clientStatus == ClientStatus.NOT_INITIALIZED:
            self.logger.error("Client must be initialized")
            return TransactionStatus.FAILURE.value
        elif self.clientStatus == ClientStatus.INITIALIZED:
            self.logger.debug("Client must be connected to HUB ")
            return TransactionStatus.FAILURE.value
        elif self.clientStatus == ClientStatus.DISCONNECTED:
            self.logger.debug("Client already Disconnected")
            return TransactionStatus.SUCCESS.value

        if self.isConnected():
            self.connectionEvent.clear()
            self.pahoClient.loop_stop()
            self.pahoClient.disconnect()
            if not self.connectionEvent.wait(timeout=10):
                self.logger.error("Disconnect timeout, unable to disconnect Client:%s", self.hostname)
                return TransactionStatus.FAILURE.value
        self.connectionEvent.clear()

        if self.disconnectResponseCode != 0:
            self.logger.error("Unable to Disconnect paho client , with rc = %d", self.disconnectResponseCode)
            return TransactionStatus.FAILURE.value

        self.clientStatus = ClientStatus.DISCONNECTED
        return TransactionStatus.SUCCESS.value

    def resubscribe(self):
        self.subscribe(topicList=self.subscriptionTopicsList)

    def subscribe(self, topicList=None):
        if topicList is None:
            self.logger.error("List of topic is mandatory")
            return TransactionStatus.FAILURE.value
        elif len(topicList) == 0:
            self.logger.error("ListTopic can't be empty")
            return TransactionStatus.FAILURE.value

        clientState = self.validateClientState()
        if clientState != 0 or not self.isConnected():
            return TransactionStatus.FAILURE.value

        isFailed = False
        if topicList is not None:
            for Topic in topicList:
                if Topic in self.subscriptionTopicsList:
                    self.subscribeEvent.clear()
                    rc = self.pahoClient.subscribe(Topic)
                    if not self.subscribeEvent.wait(timeout=20):
                        self.logger.error("Subscribe timeout, unable to subscribe to topic: %s", Topic)
                        isFailed = True
                    if rc[0] == 0:
                        self.logger.debug("Subscribed to topic:%s", Topic)
                    else:
                        isFailed = True
                else:
                    isFailed = True
                    self.logger.error("Invalid topic:%s", Topic)

        return TransactionStatus.SUCCESS.value if isFailed else TransactionStatus.FAILURE.value

    def subscribeCommandCallback(self, function):
        self.callBackList[self.commandsTopic] = function

    def subscribeConfigCallback(self, function):
        self.callBackList[self.configTopic] = function
