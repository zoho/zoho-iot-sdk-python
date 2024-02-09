#!/usr/bin/env python3
import logging

from zoho_iot_sdk.MqttConstants import TransactionStatus, ClientStatus, CommandAckResponseCodes, ConfigAckResponseCodes, DEFAULT_PAYLOAD_SIZE, MAXIMUM_PAYLOAD_SIZE, MIN_RETRY_DELAY, MAX_RETRY_DELAY
from os.path import exists
import paho.mqtt.client as mqtt_client
import json
import threading



class ZohoIoTClient:
    def __init__(self, secure_connection=False, use_client_certificates=False):
        self.mqttUserName = None
        self.mqttPassword = None
        self.hostname = None
        self.clientID = None
        self.port = None
        self.payload_size = None

        self.caCertificate = None
        self.clientCertificate = None
        self.privateKey = None
        self.privateKeyPassword = None
        self.secureConnection = secure_connection
        self.useClientCertificates = use_client_certificates

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
        self.autoreconnect=None

        self.pahoClient = None
        self.payloadJSON = {}
        self.failedAck = {}

        self.logger = logging.getLogger(self.__module__ + "." + self.__class__.__name__)
        self.logger.setLevel(logging.DEBUG)
        self.logger.handlers = []
        c_handler = logging.StreamHandler()
        c_format = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
        c_handler.setFormatter(c_format)
        self.logger.addHandler(c_handler)

    @staticmethod
    def is_blank(data):
        if data is not None and data.strip() != "":
            return False
        return True

    def set_logger(self, loglevel=None, filename=None):
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

    def _on_connect(self, client, userdata, flags, rc):
        self.connectResponseCode = rc
        if self.connectResponseCode == 0:
            if self.clientStatus == ClientStatus.DISCONNECTED:
                self.logger.info("Client reconnected")
                threading.Thread(target=self.resubscribe, args=()).start()
        self.clientStatus = ClientStatus.CONNECTED
        self.connectionEvent.set()
        temp_dict = self.failedAck.copy()
        for topic, ack_payload in self.failedAck:
            rc = self.publish_with_topic(topic= topic, message=json.dumps(ack_payload))
            if rc == 0:
                self.logger.debug("Ack sent successfully in the topic %s",topic)
                temp_dict.pop(topic)
        self.failedAck = temp_dict.copy()

    def _on_publish(self, client, userdata, mid):
        self.connectionEvent.set()

    def _on_disconnect(self, client, userdata, rc):
        self.logger.info("Client disconnected")
        self.clientStatus = ClientStatus.DISCONNECTED
        self.disconnectResponseCode = rc
        self.connectionEvent.set()

    def _on_subscribe(self, client, userdata, mid, granted_qos):
        self.subscribeEvent.set()

    def _on_message(self, client, userdata, msg):
        self.logger.info("Message Received")
        self.logger.debug("Message:%s ,Topic:%s ", msg.payload, msg.topic)
        if msg.topic == self.commandsTopic:
            threading.Thread(target=self.handle_command, args=(msg,)).start()
        elif msg.topic == self.configTopic:
            threading.Thread(target=self.handle_config, args=(msg,)).start()
        else:
            if msg.topic in self.callBackList:
                threading.Thread(target=self.callBackList[msg.topic], args=(self, msg,)).start()
            else:
                self.logger.error("Invalid topic")

    def is_connected(self):
        return self.pahoClient.is_connected()

    def handle_command(self, message):
        self.send_first_ack(message=message.payload, topic=self.commandsAckTopic,
                            ack_code=CommandAckResponseCodes.COMMAND_RECEIVED_ACK_CODE)
        if self.commandsTopic in self.callBackList:
            threading.Thread(target=self.callBackList[self.commandsTopic], args=(self, message,)).start()

    def handle_config(self, message):
        self.send_first_ack(message=message.payload, topic=self.configAckTopic,
                            ack_code=ConfigAckResponseCodes.CONFIG_RECEIVED_ACK_CODE)
        if self.configTopic in self.callBackList:
            threading.Thread(target=self.callBackList[self.configTopic], args=(self, message,)).start()

    def send_first_ack(self, message, topic, ack_code):
        commands_list = json.loads(message)
        ack_payload = {}
        for i in range(len(commands_list)):
            correlation_id = commands_list[i]["correlation_id"]
            ack_payload[correlation_id] = {"status_code": ack_code.value,
                                           "response": ""}
        return self.publish_with_topic(topic=topic, message=json.dumps(ack_payload))

    def publish_command_ack_list(self, payload_json):
        self.publish_ack_lst(topic=self.commandsAckTopic, payload=payload_json)

    def publish_config_ack_list(self, payload_json):
        self.publish_ack_lst(topic=self.configAckTopic, payload=payload_json)

    def publish_ack_lst(self, topic, payload):
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

        return self.publish_with_topic(topic=topic, message=payload)

    def publish_command_ack(self, correlation_id, status_code, response_message):
        if status_code not in CommandAckResponseCodes:
            self.logger.error("Invalid status code")
            return TransactionStatus.FAILURE.value
        self.publish_ack(topic=self.commandsAckTopic, correlation_id=correlation_id, status_code=status_code,
                         response_message=response_message)

    def publish_config_ack(self, correlation_id, status_code, response_message):
        if status_code not in ConfigAckResponseCodes:
            self.logger.error("Invalid status code")
            return TransactionStatus.FAILURE.value
        self.publish_ack(topic=self.configAckTopic, correlation_id=correlation_id, status_code=status_code,
                         response_message=response_message)

    def publish_ack(self, topic, correlation_id, status_code, response_message):
        if self.is_blank(correlation_id) or response_message is None:
            self.logger.error("Correlation ID or response Message can't be NULL or empty")
            return TransactionStatus.FAILURE.value
        ack_payload = {correlation_id: {"status_code": status_code.value, "response": response_message}}

        rc = self.publish_with_topic(topic=topic, message=json.dumps(ack_payload))
        if rc == 0:
            return rc
        if self.is_connected() == False:
            self.logger.error("Error in publish ack due to lost connection")
            self.clientStatus =  ClientStatus.DISCONNECTED
            self.failedAck[topic] = ack_payload

    def validate_client_state(self):
        if self.clientStatus == ClientStatus.NOT_INITIALIZED:
            self.logger.error("Client must be initialized")
            return TransactionStatus.FAILURE.value
        elif self.clientStatus == ClientStatus.DISCONNECTED:
            self.logger.debug("Connection to server is disconnected")
            return TransactionStatus.CONNECTION_ERROR.value
        elif self.clientStatus == ClientStatus.INITIALIZED:
            self.logger.debug("Client must be connected to HUB ")
            return TransactionStatus.FAILURE.value
        else:
            if self.is_connected():
                return TransactionStatus.SUCCESS.value
            else:
                return TransactionStatus.FAILURE.value

    def extract_host_name_and_client_id(self, mqtt_user_name):
        mqtt_user_name_array = mqtt_user_name.split("/")
        if len(mqtt_user_name_array) != 6:
            self.logger.error("Wrong MQTTUserName format.")
            return False
        else:
            self.hostname = mqtt_user_name_array[1]
            self.clientID = mqtt_user_name_array[4]
            return True

    def init(self, mqtt_user_name, mqtt_password='', ca_certificate=None, client_certificate=None, private_key=None,
             private_key_password=None):
        if self.is_blank(mqtt_user_name):
            self.logger.error("MQTTUserName cannot be empty")
            return TransactionStatus.FAILURE.value

        self.mqttUserName = str(mqtt_user_name).strip()
        self.mqttPassword = str(mqtt_password).strip()
        if not self.extract_host_name_and_client_id(self.mqttUserName):
            self.clientStatus = ClientStatus.NOT_INITIALIZED
            return False
        topic_prefix = "/devices/" + str(self.clientID)
        self.dataTopic = topic_prefix + "/telemetry"
        self.eventTopic = topic_prefix + "/events"
        self.commandsTopic = topic_prefix + "/commands"
        self.commandsAckTopic = str(self.commandsTopic) + "/ack"
        self.configTopic = topic_prefix + "/configsettings"
        self.configAckTopic = str(self.configTopic) + "/ack"
        self.subscriptionTopicsList.append(self.commandsTopic)
        self.subscriptionTopicsList.append(self.configTopic)
        self.payload_size = DEFAULT_PAYLOAD_SIZE

        if self.secureConnection:
            if self.is_blank(ca_certificate) or not exists(ca_certificate.strip()):
                self.logger.error("CAFile file is not found/ empty or can't be accessed.")
                return TransactionStatus.FAILURE.value

            self.caCertificate = ca_certificate.strip()

            if self.useClientCertificates:
                if ((self.is_blank(client_certificate) or not exists(client_certificate.strip())) or (
                        self.is_blank(private_key) or not exists(private_key.strip()))):
                    self.logger.error("ClientCertificate / PrivateKey file is not found or empty or can't be accessed.")
                    return TransactionStatus.FAILURE.value
                self.clientCertificate = client_certificate.strip()
                self.privateKey = private_key.strip()
                self.privateKeyPassword = private_key_password if self.is_blank(
                    private_key_password) else private_key_password.strip()
            else:
                # MQTTPassword is not applicable for Server TLS mode.
                if self.is_blank(self.mqttPassword):
                    self.logger.error("MQTTPassword cannot be empty.")
                    return TransactionStatus.FAILURE.value
            self.port = 8883

        else:
            if self.is_blank(mqtt_password):
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

        if self.clientStatus == ClientStatus.CONNECTED and self.is_connected():
            self.logger.debug("already connected!")
            return mqtt_client.CONNACK_ACCEPTED.value

        try:
            if self.pahoClient is None:
                self.pahoClient = mqtt_client.Client(client_id=self.clientID, clean_session=True, protocol=4)

            # self.pahoClient.enable_logger(logging.DEBUG)
            self.pahoClient.username_pw_set(self.mqttUserName, self.mqttPassword)
            if self.autoreconnect == True:
                self.pahoClient.reconnect_delay_set(min_delay=MIN_RETRY_DELAY, max_delay=MAX_RETRY_DELAY)
            self.pahoClient._connect_timeout = 10

            if self.secureConnection:
                self.pahoClient.tls_set(ca_certs=self.caCertificate, certfile=self.clientCertificate,
                                        keyfile=self.privateKey)

            self.pahoClient.on_connect = self._on_connect
            self.pahoClient.on_publish = self._on_publish
            self.pahoClient.on_disconnect = self._on_disconnect
            self.pahoClient.on_subscribe = self._on_subscribe
            self.pahoClient.on_message = self._on_message

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
                                  mqtt_client.connack_string(self.connectResponseCode))
                self.pahoClient.loop_stop()
                return self.connectResponseCode

            self.subscribe(topic_list=self.subscriptionTopicsList)

            return self.connectResponseCode

        except Exception as e:
            self.logger.error("Exception :", e)
            return TransactionStatus.FAILURE.value

    def reconnect(self):
        if self.autoreconnect == True:
            self.logger.error("Auto reconnect is enabled so not able to reconnect manaly")
            return -1
        rc = self.connect()
        if rc != 0:
            self.logger.error("reconnection is failure")
            return rc
        self.logger.debug("reconnection is success")
        temp_dict = self.failedAck.copy()
        for topic, ack_payload in self.failedAck:
            rc = self.publish_with_topic(topic= topic, message=json.dumps(ack_payload))
            if rc == 0:
                self.logger.debug("Ack sent successfully in the topic %s",topic)
                temp_dict.pop(topic)
        self.failedAck = temp_dict.copy()
        return 0

    def add_data_point(self, key, value, asset_name=None):
        if self.is_blank(key):
            self.logger.error("Can't add empty key")
            return TransactionStatus.FAILURE.value

        if self.is_blank(asset_name):
            self.payloadJSON[key] = value
        else:
            if asset_name in self.payloadJSON.keys():
                self.payloadJSON[asset_name][key] = value
            else:
                value_object = {key: value}
                self.payloadJSON[asset_name] = value_object
        return TransactionStatus.SUCCESS.value

    def add_json(self, key, json_data):
        if self.is_blank(key):
            self.logger.error("Can't add empty key")
            return TransactionStatus.FAILURE.value

        if self.is_blank(json_data):
            logging.error("Can't add empty json")
            return TransactionStatus.FAILURE.value
        try:
            self.payloadJSON[key] = json_data
            return TransactionStatus.SUCCESS.value
        except json.JSONDecodeError:
            logging.error("Invalid json ")
        return TransactionStatus.FAILURE.value

    def mark_data_point_as_error(self, key, asset_name=None):
        return self.add_data_point(key=key, value="<ERROR>", asset_name=asset_name)

    def dispatch(self):
        rc = self.publish_with_topic(topic=self.dataTopic, message=json.dumps(self.payloadJSON))
        if rc == 0:
            self.payloadJSON = {}
        return rc

    def publish(self, message_string):
        rc = self.publish_with_topic(topic=self.dataTopic, message=json.dumps(message_string))
        if rc == 0:
            self.payloadJSON = {}
        return rc

    def dispatch_event(self, event_type=None, event_description=None, event_data_keymap=None, asset_name=None):
        if self.is_blank(event_type) or self.is_blank(event_description) or event_data_keymap is None:
            self.logger.error("Can't append NULL arguments to Event.")
            return TransactionStatus.FAILURE
        payload = {}
        if not self.is_blank(event_type):
            payload["eventType"] = event_type
        if not self.is_blank(event_description):
            payload["eventDescription"] = event_description
        if event_data_keymap is not None:
            payload["eventData"] = event_data_keymap
        if self.is_blank(asset_name):
            return self.publish_with_topic(topic=self.dataTopic, message=json.dumps(payload))
        else:
            return self.dispatch_asset(asset_name)

    def dispatch_asset(self, asset_name):
        if self.is_blank(asset_name):
            self.logger.error("Asset Name can't be null")
            return TransactionStatus.FAILURE
        payload = {asset_name: self.payloadJSON}
        rc = self.publish_with_topic(topic=self.dataTopic, message=json.dumps(payload))
        if rc == 0:
            self.payloadJSON = {}
        return rc

    def publish_with_topic(self, topic, message):
        if self.is_blank(topic):
            self.logger.error("Topic can't be blank")
            return TransactionStatus.FAILURE
        if self.is_blank(message):
            self.logger.error("Message can't be blank")
            return TransactionStatus.FAILURE
        if len(message)> self.payload_size:
            self.logger.error("client payload size is greater than maximum payload size. The payload size is %d",len(message))
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
            self.logger.error("Message publish Error code : %d Reason : %s", rc[0], mqtt_client.error_string(rc[0]))
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

        if self.is_connected():
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
        self.subscribe(topic_list=self.subscriptionTopicsList)

    def subscribe(self, topic_list=None):
        if topic_list is None:
            self.logger.error("List of topic is mandatory")
            return TransactionStatus.FAILURE.value
        elif len(topic_list) == 0:
            self.logger.error("ListTopic can't be empty")
            return TransactionStatus.FAILURE.value

        client_state = self.validate_client_state()
        if client_state != 0 or not self.is_connected():
            return TransactionStatus.FAILURE.value

        is_failed = False
        if topic_list is not None:
            for Topic in topic_list:
                if Topic in self.subscriptionTopicsList:
                    self.subscribeEvent.clear()
                    rc = self.pahoClient.subscribe(Topic)
                    if not self.subscribeEvent.wait(timeout=20):
                        self.logger.error("Subscribe timeout, unable to subscribe to topic: %s", Topic)
                        is_failed = True
                    if rc[0] == 0:
                        self.logger.debug("Subscribed to topic:%s", Topic)
                    else:
                        is_failed = True
                else:
                    is_failed = True
                    self.logger.error("Invalid topic:%s", Topic)

        return TransactionStatus.SUCCESS.value if is_failed else TransactionStatus.FAILURE.value

    def subscribe_command_callback(self, function):
        self.callBackList[self.commandsTopic] = function

    def subscribe_config_callback(self, function):
        self.callBackList[self.configTopic] = function

    def set_maximum_payload_size(self,size):
        if size>MAXIMUM_PAYLOAD_SIZE:
            self.logger.error("message payload size %d is greater than maximum payload size %d continues on maximum payload size",size,MAXIMUM_PAYLOAD_SIZE)
            self.payload_size = MAXIMUM_PAYLOAD_SIZE
            return TransactionStatus.FAILURE.value
        elif size < DEFAULT_PAYLOAD_SIZE:
            self.logger.error("message payload size %d is lesser than default payload size %d continues on default payload size",size,DEFAULT_PAYLOAD_SIZE)
            self.payload_size = DEFAULT_PAYLOAD_SIZE
            return TransactionStatus.FAILURE.value
        else:
            self.logger.debug("Message payload size is updated to the %d",size)
            self.payload_size =size
            return TransactionStatus.SUCCESS.value

    def set_autoreconnect(self):
        self.autoreconnect = True

    def reset_autoreconnect(self):
        self.autoreconnect = False
