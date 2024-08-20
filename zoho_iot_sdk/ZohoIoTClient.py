#!/usr/bin/env python3
import logging

from .MqttConstants import *
from .version import VERSION
from .Utils import *
from .ConfigUtil import *
from os.path import exists
import paho.mqtt.client as mqtt_client
import json
import threading
import platform
import re


class ZohoIoTClient:
    def __init__(self, secure_connection=False, use_client_certificates=False):
        self.mqttUserName = None
        self.mqttPassword = None
        self.hostname = None
        self.clientID = None
        self.port = None
        self.connection_string = ""
        self.agentName = None
        self.agentVersion = None
        self.platformName = None
        self.osName = None
        self.osVersion = None

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
        self.autoReconnect = True

        self.pahoClient = None
        self.payloadJSON = {}
        self.eventJSON = {}
        self.failedAck = {}
        self.logger = None

        self.config_util = ConfigUtil()

    def enable_logger(self, logger=None, filename=None):
        if logger is None:
            return False
        self.logger = logger
        if not Utils.is_blank(filename):
            f_handler = logging.FileHandler(filename)
            f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            f_handler.setFormatter(f_format)
            self.logger.addHandler(f_handler)
        return True

    def log_debug(self, fmt: str, *args) -> None:
        if self.logger is not None:
            self.logger.debug(fmt, *args)

    def log_info(self, fmt: str, *args) -> None:
        if self.logger is not None:
            self.logger.info(fmt, *args)

    def log_error(self, fmt: str, *args) -> None:
        if self.logger is not None:
            self.logger.error(fmt, *args)

    def _on_connect(self, client, userdata, flags, rc):
        self.connectResponseCode = rc
        if self.connectResponseCode == 0:
            if self.clientStatus == ClientStatus.DISCONNECTED:
                self.log_info("Client reconnected")
                threading.Thread(target=self.resubscribe, args=()).start()
        self.clientStatus = ClientStatus.CONNECTED
        self.connectionEvent.set()
        temp_dict = self.failedAck.copy()
        for topic, ack_payload in self.failedAck.items():
            rc = self.publish_with_topic(topic=topic, message=json.dumps(ack_payload))
            if rc == 0:
                self.log_debug("Ack sent successfully in the topic %s", topic)
                temp_dict.pop(topic)
        self.failedAck = temp_dict.copy()

    def _on_publish(self, client, userdata, mid):
        self.connectionEvent.set()

    def _on_disconnect(self, client, userdata, rc):
        self.log_info("Client disconnected")
        self.clientStatus = ClientStatus.DISCONNECTED
        self.disconnectResponseCode = rc
        self.connectionEvent.set()

    def _on_subscribe(self, client, userdata, mid, granted_qos):
        self.subscribeEvent.set()

    def _on_message(self, client, userdata, msg):
        self.log_info("Message Received")
        self.log_debug("Message:%s ,Topic:%s ", msg.payload, msg.topic)
        if msg.topic == self.commandsTopic:
            threading.Thread(target=self.handle_command, args=(msg,)).start()
        elif msg.topic == self.configTopic:
            threading.Thread(target=self.handle_config, args=(msg,)).start()
        else:
            if msg.topic in self.callBackList:
                threading.Thread(target=self.callBackList[msg.topic], args=(self, msg,)).start()
            else:
                self.log_error("Invalid topic")

    def is_connected(self):
        return self.pahoClient.is_connected()

    def handle_command(self, message):
        rc = self.send_first_ack(message=message.payload, topic=self.commandsAckTopic,
                                 ack_code=CommandAckResponseCodes.COMMAND_RECEIVED_ACK_CODE)
        if rc != 0:
            self.log_error("sending first acknowledgement for handle_command failed")
            return -1
        if self.commandsTopic in self.callBackList:
            threading.Thread(target=self.callBackList[self.commandsTopic], args=(self, message,)).start()
            # for test_case
            return 0
        self.log_error("No callback is registered for the topic %s", self.commandsTopic)
        return -1

    def handle_config(self, message):
        rc = self.send_first_ack(message=message.payload, topic=self.configAckTopic,
                                 ack_code=ConfigAckResponseCodes.CONFIG_RECEIVED_ACK_CODE)
        if rc != 0:
            self.log_error("sending first acknowledgement for handle_config failed")
            return -1
        if self.configTopic in self.callBackList:
            threading.Thread(target=self.callBackList[self.configTopic], args=(self, message,)).start()
            # for test_case
            return 0
        self.log_error("No callback is registered for the topic %s", self.commandsTopic)
        return -1

    def send_first_ack(self, message, topic, ack_code):
        msg_lst = json.loads(message)
        ack_payload = {}
        for i in range(len(msg_lst)):
            correlation_id = msg_lst[i]["correlation_id"]
            if "is_new_config" in msg_lst[i]:
                new_config = msg_lst[i]["is_new_config"]
                if new_config:
                    ack_payload[correlation_id] = {"status_code": ack_code.value, "response": "", "is_new_config": True}
                    self.config_util.put(correlation_id,True)
                else:
                    ack_payload[correlation_id] = {"status_code": ack_code.value, "response": "",
                                                   "is_new_config": False}
                    self.config_util.put(correlation_id,True)
            else:
                ack_payload[correlation_id] = {"status_code": ack_code.value, "response": ""}
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
                    self.log_error("Correlation_id is empty or null")
                    continue_flag = False
                    break
                if status_code is None or type(status_code) != int:
                    self.log_error("Status_code key is either missing or not valid")
                    continue_flag = False
                    break
                if correlation_id["response"] is None:
                    self.log_error("Response string is missing")
                    continue_flag = False
                    break
                if len(correlation_id) > 2:
                    self.log_error("Correlation object has additional keys other than status_code and response")
                    continue_flag = False
                    break
        except ValueError as err:
            self.log_error("Command Ack message is an invalid JSON, Error message:%s", err)
            continue_flag = False

        if not continue_flag:
            self.log_error("Cannot publish with improper Command ACK structure :\n" + payload)
            return TransactionStatus.FAILURE.value

        return self.publish_with_topic(topic=topic, message=payload)

    def publish_command_ack(self, correlation_id, status_code, response_message):
        if status_code not in CommandAckResponseCodes:
            self.log_error("Invalid status code")
            return TransactionStatus.FAILURE.value
        return self.publish_ack(topic=self.commandsAckTopic, correlation_id=correlation_id, status_code=status_code,
                                response_message=response_message)

    def publish_config_ack(self, correlation_id, status_code, response_message):
        if status_code not in ConfigAckResponseCodes:
            self.log_error("Invalid status code")
            return TransactionStatus.FAILURE.value
        return self.publish_ack(topic=self.configAckTopic, correlation_id=correlation_id, status_code=status_code,
                                response_message=response_message)

    def publish_ack(self, topic, correlation_id, status_code, response_message):
        if Utils.is_blank(correlation_id) or response_message is None:
            self.log_error("Correlation ID or response Message can't be NULL or empty")
            return TransactionStatus.FAILURE.value
        ack_payload = {correlation_id: {"status_code": status_code.value, "response": response_message}}
        if topic == self.configAckTopic:
            if self.config_util.contains_correlation_id(correlation_id):
                ack_payload[correlation_id]["is_new_config"] = self.config_util.get(correlation_id)
        rc = self.publish_with_topic(topic=topic, message=json.dumps(ack_payload))
        if rc == 0:
            return rc
        if not self.is_connected():
            self.log_error("Error in publish ack due to lost connection")
            self.clientStatus = ClientStatus.DISCONNECTED
            self.failedAck[topic] = ack_payload
        return rc

    def validate_client_state(self):
        if self.clientStatus == ClientStatus.NOT_INITIALIZED:
            self.log_error("Client must be initialized")
            return TransactionStatus.FAILURE.value
        elif self.clientStatus == ClientStatus.DISCONNECTED:
            self.log_debug("Connection to server is disconnected")
            return TransactionStatus.CONNECTION_ERROR.value
        elif self.clientStatus == ClientStatus.INITIALIZED:
            self.log_debug("Client must be connected to HUB ")
            return TransactionStatus.FAILURE.value
        else:
            if self.is_connected():
                return TransactionStatus.SUCCESS.value
            else:
                return TransactionStatus.FAILURE.value

    def extract_host_name_and_client_id(self, mqtt_user_name):
        mqtt_user_name_array = mqtt_user_name.split("/")
        if len(mqtt_user_name_array) != 6:
            self.log_error("Wrong MQTTUserName format.")
            return False
        else:
            self.hostname = mqtt_user_name_array[1]
            self.clientID = mqtt_user_name_array[4]
            return True

    def init(self, mqtt_user_name, mqtt_password='', ca_certificate=None, client_certificate=None, private_key=None,
             private_key_password=None):
        if Utils.is_blank(mqtt_user_name):
            self.log_error("MQTTUserName cannot be empty")
            return TransactionStatus.FAILURE.value

        self.mqttUserName = str(mqtt_user_name).strip()
        self.mqttPassword = str(mqtt_password).strip()
        if not self.extract_host_name_and_client_id(self.mqttUserName):
            self.clientStatus = ClientStatus.NOT_INITIALIZED
            return TransactionStatus.FAILURE.value
        topic_prefix = "/devices/" + str(self.clientID)
        self.dataTopic = topic_prefix + "/telemetry"
        self.eventTopic = topic_prefix + "/events"
        self.commandsTopic = topic_prefix + "/commands"
        self.commandsAckTopic = str(self.commandsTopic) + "/ack"
        self.configTopic = topic_prefix + "/configsettings"
        self.configAckTopic = str(self.configTopic) + "/ack"
        self.subscriptionTopicsList.append(self.commandsTopic)
        self.subscriptionTopicsList.append(self.configTopic)

        if self.secureConnection:
            if Utils.is_blank(ca_certificate) or not exists(ca_certificate.strip()):
                self.log_error("CAFile file is not found/ empty or can't be accessed.")
                return TransactionStatus.FAILURE.value

            self.caCertificate = ca_certificate.strip()

            if self.useClientCertificates:
                if ((Utils.is_blank(client_certificate) or not exists(client_certificate.strip())) or (
                        Utils.is_blank(private_key) or not exists(private_key.strip()))):
                    self.log_error("ClientCertificate / PrivateKey file is not found or empty or can't be accessed.")
                    return TransactionStatus.FAILURE.value
                self.clientCertificate = client_certificate.strip()
                self.privateKey = private_key.strip()
                self.privateKeyPassword = private_key_password if Utils.is_blank(
                    private_key_password) else private_key_password.strip()
            else:
                # MQTTPassword is not applicable for Server TLS mode.
                if Utils.is_blank(self.mqttPassword):
                    self.log_error("MQTTPassword cannot be empty.")
                    return TransactionStatus.FAILURE.value
            self.port = 8883

        else:
            if Utils.is_blank(mqtt_password):
                self.log_error("MQTTPassword cannot be empty.")
                return TransactionStatus.FAILURE.value
            self.port = 1883

        self.clientStatus = ClientStatus.INITIALIZED
        self.log_debug("Client is Initialized")
        return TransactionStatus.SUCCESS.value

    def set_agent_name_and_version(self, name=None, version=None):
        if Utils.is_blank(name) or Utils.is_blank(version):
            self.log_error("Agent name or version is invalid")
            return False
        self.agentName = name
        self.agentVersion = version
        return True

    def set_platform_name(self, platform_name=None):
        if Utils.is_blank(platform_name):
            self.log_error("Platform name is invalid")
            return False
        self.platformName = platform_name
        return True

    def get_os_info(self):
        platform_info = platform.platform()
        system = platform.system()

        if system == 'Darwin':
            # macOS
            mac_version_match = re.search(r'macOS-(\d+\.\d+)', platform_info)
            if mac_version_match:
                os_name = 'macOS'
                os_version = mac_version_match.group(1)
            else:
                os_name = 'macOS'
                os_version = 'Unknown'
        elif system == 'Windows':
            # Windows
            os_name = 'Windows'
            os_version = platform.release()
        else:
            # Unix-like system (Linux, etc.)
            os_name = 'Unknown Unix-like'
            os_version = 'Unknown'
            try:
                with open('/etc/os-release') as f:
                    lines = f.readlines()
                    for line in lines:
                        if line.startswith('NAME='):
                            os_name = line.split('=')[1].strip().strip('"')
                        elif line.startswith('VERSION='):
                            os_version = line.split('=')[1].strip().strip('"')
            except FileNotFoundError:
                pass
                return False
        self.osName = os_name
        self.osVersion = os_version
        return True

    def form_connection_string(self, mqtt_user_name):
        self.connection_string = ""
        self.connection_string = mqtt_user_name + "?"
        self.connection_string = self.connection_string + "sdk_name" + "=" + "zoho-iot-sdk-python" + "&"
        self.connection_string = self.connection_string + "sdk_version" + "=" + VERSION + "&"
        if not Utils.is_blank(self.agentName) and not Utils.is_blank(self.agentVersion):
            self.connection_string = self.connection_string + "agent_name" + "=" + self.agentName + "&"
            self.connection_string = self.connection_string + "agent_version" + "=" + self.agentVersion + "&"
        if not Utils.is_blank(self.platformName):
            self.connection_string = self.connection_string + "agent_platform" + "=" + self.platformName + "&"

        if self.get_os_info() and not Utils.is_blank(self.osName) and not Utils.is_blank(self.osVersion):
            self.connection_string = self.connection_string + "os_name" + "=" + self.osName + "&"
            self.connection_string = self.connection_string + "os_version" + "=" + self.osVersion + "&"
        return self.connection_string

    def connect(self):
        self.log_debug("trying to  connect..")
        if self.clientStatus == ClientStatus.NOT_INITIALIZED:
            self.log_error("Client must be initialized")
            return TransactionStatus.FAILURE.value

        if self.clientStatus == ClientStatus.CONNECTED and self.is_connected():
            self.log_debug("already connected!")
            return mqtt_client.CONNACK_ACCEPTED

        try:
            if self.pahoClient is None:
                self.pahoClient = mqtt_client.Client(client_id=self.clientID, clean_session=True, protocol=4)

            self.pahoClient.username_pw_set(self.form_connection_string(self.mqttUserName), self.mqttPassword)
            if self.autoReconnect:
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

            self.log_debug("Connecting..")
            self.connectionEvent.clear()
            self.pahoClient.connect(self.hostname, self.port, keepalive=60)
            self.pahoClient.loop_start()

            if not self.connectionEvent.wait(timeout=60):
                self.log_error("Connection timeout, unable to connect to client: %s", self.hostname)
                self.pahoClient.loop_stop()
                return TransactionStatus.FAILURE.value

            if self.connectResponseCode == 0:
                self.log_info("Client connected to MQTT Broker! " + self.hostname)
            else:
                self.log_error("Error code: %d Reason: %s", self.connectResponseCode,
                               mqtt_client.connack_string(self.connectResponseCode))
                self.pahoClient.loop_stop()
                return self.connectResponseCode

            self.subscribe(topic_list=self.subscriptionTopicsList)

            return self.connectResponseCode

        except Exception as e:
            self.log_error("Exception :", e)
            return TransactionStatus.FAILURE.value

    def reconnect(self):
        if self.autoReconnect:
            self.log_error("Auto reconnect is enabled so not able to reconnect manually")
            return -1
        rc = self.connect()
        if rc != 0:
            self.log_error("reconnection is failure")
            return rc
        self.log_debug("reconnection is success")
        temp_dict = self.failedAck.copy()
        for topic, ack_payload in self.failedAck.items():
            rc = self.publish_with_topic(topic=topic, message=json.dumps(ack_payload))
            if rc == 0:
                self.log_debug("Ack sent successfully in the topic %s", topic)
                temp_dict.pop(topic)
        self.failedAck = temp_dict.copy()
        return 0

    def add_event_data_point(self, key, value):
        if Utils.is_blank(key):
            self.log_error("Can't add empty key")
            return False
        self.eventJSON[key] = value
        return True

    def add_data_point(self, key, value, asset_name=None):
        if Utils.is_blank(key):
            self.log_error("Can't add empty key")
            return False

        if Utils.is_blank(asset_name):
            self.payloadJSON[key] = value
        else:
            if asset_name in self.payloadJSON.keys():
                self.payloadJSON[asset_name][key] = value
            else:
                value_object = {key: value}
                self.payloadJSON[asset_name] = value_object
        return True

    def add_json(self, key, json_data):
        if Utils.is_blank(key):
            self.log_error("Can't add empty key")
            return False
        if Utils.is_json_blank(json_data):
            logging.error("Can't add empty json")
            return False
        try:
            self.payloadJSON[key] = json_data
            return True
        except json.JSONDecodeError:
            logging.error("Invalid json ")
        return False

    def mark_data_point_as_error(self, key, asset_name=None):
        return self.add_data_point(key=key, value="<ERROR>", asset_name=asset_name)

    def dispatch(self):
        rc = self.publish_with_topic(topic=self.dataTopic, message=json.dumps(self.payloadJSON))
        if rc == 0:
            self.payloadJSON = {}
        return rc

    def publish(self, message_string):
        if Utils.is_json_blank(message_string):
            self.log_error("publish message is invalid or empty")
            return TransactionStatus.FAILURE.value
        rc = self.publish_with_topic(topic=self.dataTopic, message=json.dumps(message_string))
        if rc == 0:
            self.payloadJSON = {}
        return rc

    def dispatch_event(self, event_type=None, event_description=None, asset_name=None):
        rc = self.dispatch_event_with_data(event_type, event_description, self.eventJSON, asset_name)
        self.eventJSON = {}
        return rc

    def dispatch_event_with_data(self, event_type=None, event_description=None, event_data_keymap=None,
                                 asset_name=None):
        if event_data_keymap is None:
            self.log_error("Can't append NULL arguments to Event.")
            return TransactionStatus.FAILURE.value
        payload = {}
        if not Utils.is_blank(event_type):
            payload["eventType"] = event_type
        if not Utils.is_blank(event_description):
            payload["eventDescription"] = event_description
        if event_data_keymap is not None:
            payload["eventData"] = event_data_keymap
        if Utils.is_blank(asset_name):
            return self.publish_with_topic(topic=self.eventTopic, message=json.dumps(payload))
        else:
            payload_temp = (asset_name, payload)
            return self.publish_with_topic(topic=self.eventTopic, message=json.dumps(payload_temp))

    def publish_with_topic(self, topic, message):
        if Utils.is_blank(topic):
            self.log_error("Topic can't be blank")
            return TransactionStatus.FAILURE.value
        if Utils.is_blank(message):
            self.log_error("Message can't be blank")
            return TransactionStatus.FAILURE.value
        client_state = self.validate_client_state()
        if client_state != 0:
            self.log_error("Client is not in connected state")
            return TransactionStatus.FAILURE.value
        self.connectionEvent.clear()
        rc = self.pahoClient.publish(topic=topic, payload=message, qos=0, retain=False)
        if not self.connectionEvent.wait(timeout=10):
            self.log_error("Publish timeout, unable to publish message")
            return TransactionStatus.FAILURE.value

        if rc[0] == 0:
            self.log_info("Message published successfully")
            self.log_debug("Message :%s , topic :%s", message, topic)
        else:
            self.log_error("Message publish Error code : %d Reason : %s", rc[0], mqtt_client.error_string(rc[0]))
        return rc[0]

    def disconnect(self):
        if self.clientStatus == ClientStatus.NOT_INITIALIZED:
            self.log_error("Client must be initialized")
            return TransactionStatus.FAILURE.value
        elif self.clientStatus == ClientStatus.INITIALIZED:
            self.log_debug("Client must be connected to HUB ")
            return TransactionStatus.FAILURE.value
        elif self.clientStatus == ClientStatus.DISCONNECTED:
            self.log_debug("Client already Disconnected")
            return TransactionStatus.SUCCESS.value

        if self.is_connected():
            self.connectionEvent.clear()
            self.pahoClient.loop_stop()
            self.pahoClient.disconnect()
            if not self.connectionEvent.wait(timeout=10):
                self.log_error("Disconnect timeout, unable to disconnect Client:%s", self.hostname)
                return TransactionStatus.FAILURE.value
        self.connectionEvent.clear()

        if self.disconnectResponseCode != 0:
            self.log_error("Unable to Disconnect paho client , with rc = %d", self.disconnectResponseCode)
            return TransactionStatus.FAILURE.value

        self.clientStatus = ClientStatus.DISCONNECTED
        self.log_info("Disconnected")
        return TransactionStatus.SUCCESS.value

    def resubscribe(self):
        self.subscribe(topic_list=self.subscriptionTopicsList)

    def subscribe(self, topic_list=None):
        if topic_list is None:
            self.log_error("List of topic is mandatory")
            return TransactionStatus.FAILURE.value
        elif len(topic_list) == 0:
            self.log_error("ListTopic can't be empty")
            return TransactionStatus.FAILURE.value

        client_state = self.validate_client_state()
        if client_state != 0:
            self.log_error("Client is not in connected state")
            return TransactionStatus.FAILURE.value

        is_failed = False
        if topic_list is not None:
            for Topic in topic_list:
                if Topic in self.subscriptionTopicsList:
                    self.subscribeEvent.clear()
                    rc = self.pahoClient.subscribe(Topic)
                    if not self.subscribeEvent.wait(timeout=20):
                        self.log_error("Subscribe timeout, unable to subscribe to topic: %s", Topic)
                        is_failed = True
                    if rc[0] == 0:
                        self.log_debug("Subscribed to topic:%s", Topic)
                    else:
                        is_failed = True
                else:
                    is_failed = True
                    self.log_error("Invalid topic:%s", Topic)

        return TransactionStatus.FAILURE.value if is_failed else TransactionStatus.SUCCESS.value

    def subscribe_command_callback(self, function):
        self.callBackList[self.commandsTopic] = function

    def subscribe_config_callback(self, function):
        self.callBackList[self.configTopic] = function

    def set_auto_reconnect(self, value):  # value is boolean(True or False)
        self.autoReconnect = value
