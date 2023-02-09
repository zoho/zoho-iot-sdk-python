#!/usr/bin/env python3
from enum import Enum, auto


class TransactionStatus(Enum):
    SUCCESS = 0
    FAILURE = -1
    CONNECTION_ERROR = -2


class ClientStatus(Enum):
    NOT_INITIALIZED = auto()
    INITIALIZED = auto()
    CONNECTED = auto()
    DISCONNECTED = auto()
    RETRYING = auto() #TODO: Remove this unused enum


#TODO: use constants from paho library
class ConnectionStatus(Enum):
    FAILURE = -1
    SSL_FAILURE = -2
    SUCCESS = 0
    INVALID_PROTOCOL_VERSION = 1
    INVALID_CLIENT_ID = 2
    BROKER_UNAVAILABLE = 3
    FAILED_AUTHENTICATION = 4
    NOT_AUTHORIZED = 5
    SERVER_CONNECT_ERROR = 6

#TODO: use constants from paho library
class MqttCodes(Enum):
    MQTT_ERR_AGAIN = -1
    MQTT_ERR_SUCCESS = 0
    MQTT_ERR_NOMEM = 1
    MQTT_ERR_PROTOCOL = 2
    MQTT_ERR_INVAL = 3
    MQTT_ERR_NO_CONN = 4
    MQTT_ERR_CONN_REFUSED = 5
    MQTT_ERR_NOT_FOUND = 6
    MQTT_ERR_CONN_LOST = 7
    MQTT_ERR_TLS = 8
    MQTT_ERR_PAYLOAD_SIZE = 9
    MQTT_ERR_NOT_SUPPORTED = 10
    MQTT_ERR_AUTH = 11
    MQTT_ERR_ACL_DENIED = 12
    MQTT_ERR_UNKNOWN = 13
    MQTT_ERR_ERRNO = 14
    MQTT_ERR_QUEUE_SIZE = 15
    MQTT_ERR_KEEPALIVE = 16


class CommandAckResponseCodes(Enum):
    COMMAND_RECEIVED_ACK_CODE = 1000
    SUCCESSFULLY_EXECUTED = 1001
    EXECUTION_FAILURE = 4000
    METHOD_NOT_FOUND = 4001
    EXECUTING_PREVIOUS_COMMAND = 4002
    INSUFFICIENT_INPUTS = 4003
    DEVICE_CONNECTIVITY_ISSUES = 4004
    PARTIAL_EXECUTION = 4005
    ALREADY_ON_SAME_STATE = 4006

#TODO: use individual response codes for config settings
class ConfigAckResponseCodes(Enum):
    SUCCESSFULLY_EXECUTED = 1001
    EXECUTION_FAILURE = 4000