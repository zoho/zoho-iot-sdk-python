#!/usr/bin/env python3
import logging

from zoho_iot_sdk.MqttConstants import TransactionStatus, ClientStatus, MqttCodes, ConnectionStatus, \
    CommandAckResponseCodes
from zoho_iot_sdk.Utils import Utils, connectionStatusMessage, publishStatusMessage
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
        self.disconnected = False #TODO: remove this unwanted state.
        self.connectResponseCode = -1
        self.clientStatus = ClientStatus.NOT_INITIALIZED
        self.subscriptionTopicsList = []
        self.connectionEvent = threading.Event()
        self.subscribeEvent = threading.Event()
        self.callBackList = {}

        self.pahoClient = None
        self.payloadJSON = {}

        self.logger = logging.getLogger(self.__module__ + "." + self.__class__.__name__)
        self.logger.setLevel(logging.INFO)
        self.logger.handlers = []
        c_handler = logging.StreamHandler()
        c_format = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
        c_handler.setFormatter(c_format)
        self.logger.addHandler(c_handler)

    # -->
    def setLogger(self, loglevel=None, filename=None):
        if not Utils.is_blank(loglevel):
            if loglevel == "INFO":
                self.logger.setLevel(logging.INFO)
            elif loglevel == "DEBUG":
                self.logger.setLevel(logging.DEBUG)
            elif loglevel == "ERROR":
                self.logger.setLevel(logging.ERROR)
            else:
                self.logger.error("Loglevel: %s invalid, Please use INFO or DEBUG or ERROR")
        if not Utils.is_blank(filename):
            for handler in self.logger.handlers:
                if isinstance(handler, logging.FileHandler):
                    self.logger.removeHandler(handler)
            f_handler = logging.FileHandler(filename)
            f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            f_handler.setFormatter(f_format)
            self.logger.addHandler(f_handler)

    def _onConnect(self, client, userdata, flags, rc):
        if self.connectResponseCode == 0 and self.disconnected:
            self.disconnected = False
            self.clientStatus = ClientStatus.CONNECTED
            self.logger.info("Client reconnected")
            threading.Thread(target=self.resubscribe, args=()).start()

        self.connectResponseCode = rc
        self.connectionEvent.set()

    def _onPublish(self, client, userdata, mid):
        self.connectionEvent.set()

    def _onDisconnect(self, client, userdata, rc):
        self.logger.info("Client disconnected")
        self.disconnected = True #--
        self.clientStatus = ClientStatus.DISCONNECTED
        self.disconnectResponseCode = rc
        self.connectionEvent.set()

    def _onSubscribe(self, client, userdata, mid, granted_qos):
        self.subscribeEvent.set()

    def _onMessage(self, client, userdata, msg):
        self.logger.debug("Message:%s ,Received on Topic:%s ", msg.payload, msg.topic)
        if msg.topic == self.commandsTopic:
            threading.Thread(target=self.handleCommand, args=(msg,)).start()
        elif msg.topic == self.configTopic:
            configAck = threading.Thread(target=self.handleConfig, args=(msg,))
            configAck.start() #TODO: Remove all unsued thread referernces
        else: #TODO: invalid topic log error and do nothig..
            if msg.topic in self.callBackList:
                callback = threading.Thread(target=self.callBackList[msg.topic], args=(self, msg,))
                callback.start()

    def isConnected(self):
        return self.pahoClient.is_connected()

    def handleCommand(self, message):
        self.sendFirstAck(message=message.payload, topic=self.commandsAckTopic)
        if self.commandsTopic in self.callBackList:
            secondAck = threading.Thread(target=self.callBackList[self.commandsTopic], args=(self, message,))
            secondAck.start()

    def handleConfig(self, message):
        self.sendFirstAck(message=message.payload, topic=self.configAckTopic)
        if self.configTopic in self.callBackList:
            secondAck = threading.Thread(target=self.callBackList[self.configTopic], args=(self, message,))
            secondAck.start()

    '''
    @staticmethod
    def getCorrelationId(message):
        array = json.loads(message)
        return array[0]["correlation_id"]
    '''

    def sendFirstAck(self, message, topic): #--
        commands_list = json.loads(message)
        ack_payload = {}
        for i in range(len(commands_list)):
            correlationId = commands_list[i]["correlation_id"]
            ack_payload[correlationId] = {"status_code": CommandAckResponseCodes.COMMAND_RECEIVED_ACK_CODE.value, "response" : ""}
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
            self.logger.error("Command Ack message is an invalid JSON ")
            continue_flag = False

        if not continue_flag:
            self.logger.error("Cannot publish with improper Command ACK structure :\n" + payload)
            return TransactionStatus.FAILURE.value

        return self.publishWithTopic(topic=topic, message=payload)

    def publishCommandAck(self, correlation_id, status_code, responseMessage):
        self.publishAck(topic=self.commandsAckTopic, correlation_id=correlation_id, status_code=status_code,
                        responseMessage=responseMessage)

    def publishConfigAck(self, correlation_id, status_code, responseMessage):
        self.publishAck(topic=self.configAckTopic, correlation_id=correlation_id, status_code=status_code,
                        responseMessage=responseMessage)

    def publishAck(self, topic, correlation_id, status_code, responseMessage):
        if Utils.is_blank(correlation_id) or responseMessage is None:
            self.logger.error("Correlation ID or response Message can't be NULL or empty")
            return TransactionStatus.FAILURE.value
        if status_code not in CommandAckResponseCodes:
            self.logger.error("Invalid status code")
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
        elif ClientStatus == ClientStatus.RETRYING:
            self.logger.debug("Connection to Server is lost, trying to reconnect")
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
        if Utils.is_blank(file) and not exists(file.strip()):
            self.logger.error("Location is blank or yaml file missing in the location")
            return TransactionStatus.FAILURE.value
        with open(file) as file:
            configuration = yaml.full_load(file) #TODO: need to verify the scope of configuration
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
        if Utils.is_blank(mqttUserName):
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
            if Utils.is_blank(caCertificate) or not exists(caCertificate.strip()):
                self.logger.error("CAFile file is not found/ empty or can't be accessed.")
                return TransactionStatus.FAILURE.value

            self.caCertificate = caCertificate.strip()

            if self.useClientCertificates:
                if ((Utils.is_blank(clientCertificate) or not exists(clientCertificate.strip())) or (
                        Utils.is_blank(privateKey) or not exists(privateKey.strip()))):
                    self.logger.error("ClientCertificate / PrivateKey file is not found or empty or can't be accessed.")
                    return TransactionStatus.FAILURE.value
                self.clientCertificate = clientCertificate.strip()
                self.privateKey = privateKey.strip()
                self.privateKeyPassword = privateKeyPassword if Utils.is_blank(
                    privateKeyPassword) else privateKeyPassword.strip()
            else:
                # MQTTPassword is not applicable for Server TLS mode.
                if Utils.is_blank(self.mqttPassword):
                    self.logger.error("MQTTPassword cannot be empty.")
                    return TransactionStatus.FAILURE.value
            self.port = 8883

        else:
            if Utils.is_blank(mqttPassword):
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
            return ConnectionStatus.FAILURE.value

        if self.clientStatus == ClientStatus.CONNECTED and self.isConnected():
            self.logger.debug("already connected!")
            return ConnectionStatus.SUCCESS.value

        try:
            if self.pahoClient is None:
                self.pahoClient = MqttClient.Client(client_id=self.clientID, clean_session=True, protocol=4)

            # self.pahoClient.enable_logger(logging.DEBUG)
            self.pahoClient.username_pw_set(self.mqttUserName, self.mqttPassword)
            self.pahoClient.reconnect_delay_set(min_delay=1, max_delay=1800000) #TODO: set max retry interval to 30 mins

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
            self.pahoClient.connect(self.hostname, self.port, keepalive=60, bind_address="") #TODO: remove bindaddress
            #TODO: try to set connection Timeout as 10 seconds.
            self.pahoClient.loop_start()

            if not self.connectionEvent.wait(timeout=60):
                self.logger.error("Connection timeout, unable to connect to client: %s", self.hostname)
                self.pahoClient.loop_stop()
                return ConnectionStatus.FAILURE.value

            if self.connectResponseCode == 0:
                logging.info("Client connected to MQTT Broker! " + self.hostname)
            else:
                logging.error("Error code: %d Reason: %s", self.connectResponseCode, connectionStatusMessage(self.connectResponseCode))
                self.pahoClient.loop_stop()
                return ConnectionStatus.FAILURE.value

            if len(self.subscriptionTopicsList) != 0:
                for topic in self.subscriptionTopicsList:
                    self.subscribeEvent.clear()
                    self.pahoClient.subscribe(topic)
                    if not self.subscribeEvent.wait(timeout=10):
                        self.logger.error("Subscribe timeout, unable to subscribe to topic: %s", topic)
                        return ConnectionStatus.FAILURE.value

            return ConnectionStatus.SUCCESS.value

        except Exception as e:
            self.logger.error("Exception :", e)
            return ConnectionStatus.FAILURE.value

    def addDataPoint(self, key, value, assetName=None):
        if Utils.is_blank(key):
            self.logger.error("Can't add empty key")
            return TransactionStatus.FAILURE.value

        if Utils.is_blank(assetName):
            self.payloadJSON[key] = value
        else:
            if assetName in self.payloadJSON.keys():
                self.payloadJSON[assetName][key] = value
            else:
                valueObject = {key: value}
                self.payloadJSON[assetName] = valueObject
        return TransactionStatus.SUCCESS.value

    def markDataPointAsError(self, key, assetName=None):
        return self.addDataPoint(key=key, value="<ERROR>", assetName=assetName)

    def dispatch(self):
        return self.publishWithTopic(topic=self.dataTopic, message=json.dumps(self.payloadJSON))

    def publish(self, messageString):
        return self.publishWithTopic(topic=self.dataTopic, message=json.dumps(messageString))

    def dispatchEvent(self, eventType=None, eventDescription=None, eventDataKeymap=None, assetName=None):
        if Utils.is_blank(eventType) or Utils.is_blank(eventDescription) or eventDataKeymap is None:
            self.logger.error("Can't append NULL arguments to Event.")
            return MqttCodes.MQTT_ERR_AGAIN.value
        if not Utils.is_blank(eventType):
            self.payloadJSON["eventType"] = eventType #TODO: use local scopped payloadJSON
        if not Utils.is_blank(eventDescription):
            self.payloadJSON["eventDescription"] = eventDescription
        if eventDataKeymap is not None:
            self.payloadJSON["eventData"] = eventDataKeymap
        if Utils.is_blank(assetName):
            return self.publishWithTopic(topic=self.dataTopic, message=json.dumps(self.payloadJSON))
        else:
            return self.dispatchAsset(assetName)

    def dispatchAsset(self, assetName):
        if Utils.is_blank(assetName):
            self.logger.error("Asset Name can't be null")
            return MqttCodes.MQTT_ERR_AGAIN.value
        payload = {assetName: self.payloadJSON}
        return self.publishWithTopic(topic=self.dataTopic, message=json.dumps(payload))

    def publishWithTopic(self, topic, message):
        if Utils.is_blank(topic):
            self.logger.error("Topic can't be blank")
            return MqttCodes.MQTT_ERR_AGAIN.value
        if Utils.is_blank(message):
            self.logger.error("Message can't be blank")
            return MqttCodes.MQTT_ERR_AGAIN.value
        self.connectionEvent.clear()
        rc = self.pahoClient.publish(topic=topic, payload=message, qos=0, retain=False)
        if not self.connectionEvent.wait(timeout=10):
            self.logger.error("Publish timeout, unable to publish message")
            return MqttCodes.MQTT_ERR_AGAIN.value

        if rc[0] == 0:
            self.logger.info("Message published successfully")
            self.logger.debug("Message :%s , topic :%s", message, topic)
            self.payloadJSON = None
        else:
            self.logger.error("Message publish Error code : %d Reason : %s", rc[0], publishStatusMessage(rc[0]))
        return rc[0]

    def disconnect(self):
        if self.clientStatus == ClientStatus.NOT_INITIALIZED:
            self.logger.error("Client must be initialized")
            return TransactionStatus.FAILURE.value
        elif self.clientStatus == ClientStatus.INITIALIZED:
            self.logger.debug("Client must be connected to HUB ")
            return TransactionStatus.FAILURE.value

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
        connectionState = self.validateClientState()
        if connectionState != 0 or not self.isConnected():
            return connectionState
        isFailed = False
        if len(self.subscriptionTopicsList) != 0:
            for topic in self.subscriptionTopicsList:
                self.subscribeEvent.clear()
                self.pahoClient.subscribe(topic)
                if not self.subscribeEvent.wait(timeout=10):
                    self.logger.error("Subscribe timeout, unable to subscribe to topic: %s", topic)
                    isFailed = True
        return TransactionStatus.SUCCESS.value if isFailed else TransactionStatus.FAILURE.value

    def subscribe(self, topic=None, topicList=None):
        if topic is None and topicList is None:
            self.logger.error("Topic or list of topic is mandatory")
            return TransactionStatus.FAILURE.value
        elif topicList is not None and topic is None:
            if len(topicList) == 0:
                self.logger.error("ListTopic can't be empty")
                return TransactionStatus.FAILURE.value
        elif Utils.is_blank(topic):
            self.logger.error("Topic can't not be blank ,invalid topic")
            return TransactionStatus.FAILURE.value

#TODO: resue resubscribe here..
#TODO: for shahul: reverify the flow after refactoring..
        clientState = self.validateClientState()
        if clientState != 0 or not self.isConnected():
            return clientState
        isFailed = False
        if topicList is not None:
            for Topic in topicList:
                if Topic not in self.subscriptionTopicsList:
                    self.subscriptionTopicsList.append(Topic)
                    self.subscribeEvent.clear()
                    self.pahoClient.subscribe(Topic)
                    if not self.subscribeEvent.wait(timeout=10):
                        self.logger.error("Subscribe timeout, unable to subscribe to topic: %s", Topic)
                        isFailed = True
        if topic is not None:
            if topic not in self.subscriptionTopicsList:
                self.subscriptionTopicsList.append(topic)
                self.subscribeEvent.clear()
                self.pahoClient.subscribe(topic)
                if not self.subscribeEvent.wait(timeout=10):
                    self.logger.error("Subscribe timeout, unable to subscribe to topic: %s", topic)
                    isFailed = True

        return TransactionStatus.SUCCESS.value if isFailed else TransactionStatus.FAILURE.value

    def subscribeCommandCallback(self, topic, function):
        if topic not in self.subscriptionTopicsList:
            self.logger.error("Topic not subscribed")
            return TransactionStatus.FAILURE.value
        self.callBackList[topic] = function

#TODO: include subscribe call back mehod for config settings