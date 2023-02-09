#!/usr/bin/env python3
from zoho_iot_sdk.MqttConstants import ConnectionStatus, MqttCodes
import paho.mqtt.client as MqttClient


class Utils:
    @staticmethod
    def is_blank(Input):
        if Input is not None and Input.strip() != "":
            return False
        return True

def connectionStatusMessage(conAck_code):
    if conAck_code == ConnectionStatus.SUCCESS.value:
        return "Connection Accepted."
    elif conAck_code == ConnectionStatus.INVALID_PROTOCOL_VERSION.value:
        return "Connection Refused: unacceptable protocol version."
    elif conAck_code == ConnectionStatus.INVALID_CLIENT_ID.value:
        return "Connection Refused: identifier rejected."
    elif conAck_code == ConnectionStatus.BROKER_UNAVAILABLE.value:
        return "Connection Refused: broker unavailable."
    elif conAck_code == ConnectionStatus.FAILED_AUTHENTICATION.value:
        return "Connection Refused: bad user name or password."
    elif conAck_code == ConnectionStatus.NOT_AUTHORIZED.value:
        return "Connection Refused: not authorised."
    elif conAck_code == ConnectionStatus.FAILURE.value:
        return "Connection Refused: failed to connect."
    elif conAck_code == ConnectionStatus.SSL_FAILURE.value:
        return "Connection Refused: SSL failure "
    elif conAck_code == ConnectionStatus.SERVER_CONNECT_ERROR.value:
        return "Connection Refused: server connect error"
    else:
        return "Connection Refused: unknown reason."

def publishStatusMessage(pubAck_code):
    if pubAck_code == MqttCodes.MQTT_ERR_SUCCESS.value:
        return "No error."
    elif pubAck_code == MqttCodes.MQTT_ERR_NOMEM.value:
        return "Out of memory."
    elif pubAck_code == MqttCodes.MQTT_ERR_PROTOCOL.value:
        return "A network protocol error occurred when communicating with the broker."
    elif pubAck_code == MqttCodes.MQTT_ERR_INVAL.value:
        return "Invalid function arguments provided."
    elif pubAck_code == MqttCodes.MQTT_ERR_NO_CONN.value:
        return "The client is not currently connected."
    elif pubAck_code == MqttCodes.MQTT_ERR_CONN_REFUSED.value:
        return "The connection was refused."
    elif pubAck_code == MqttCodes.MQTT_ERR_NOT_FOUND.value:
        return "Message not found (internal error)."
    elif pubAck_code == MqttCodes.MQTT_ERR_CONN_LOST.value:
        return "The connection was lost."
    elif pubAck_code == MqttCodes.MQTT_ERR_TLS.value:
        return "A TLS error occurred."
    elif pubAck_code == MqttCodes.MQTT_ERR_PAYLOAD_SIZE.value:
        return "Payload too large."
    elif pubAck_code == MqttCodes.MQTT_ERR_NOT_SUPPORTED.value:
        return "This feature is not supported."
    elif pubAck_code == MqttCodes.MQTT_ERR_AUTH.value:
        return "Authorisation failed."
    elif pubAck_code == MqttCodes.MQTT_ERR_ACL_DENIED.value:
        return "Access denied by ACL."
    elif pubAck_code == MqttCodes.MQTT_ERR_UNKNOWN.value:
        return "Unknown error."
    elif pubAck_code == MqttCodes.MQTT_ERR_ERRNO.value:
        return "Error defined by err no."
    elif pubAck_code == MqttCodes.MQTT_ERR_QUEUE_SIZE.value:
        return "Message queue full."
    elif pubAck_code == MqttCodes.MQTT_ERR_KEEPALIVE.value:
        return "Client or broker did not communicate in the keep alive interval."
    else:
        return "Unknown error."
