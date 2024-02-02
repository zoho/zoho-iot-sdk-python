#!/usr/bin/env python3
from zoho_iot_sdk.MqttConstants import ConnectionStatus, MqttCodes


class Utils:
    @staticmethod
    def is_blank(Input):
        if Input is None or Input.strip() == "":
            return True
        return False


def connack_string(connack_code):
    if connack_code == ConnectionStatus.SUCCESS.value:
        return "Connection Accepted."
    elif connack_code == ConnectionStatus.INVALID_PROTOCOL_VERSION.value:
        return "Connection Refused: unacceptable protocol version."
    elif connack_code == ConnectionStatus.INVALID_CLIENT_ID.value:
        return "Connection Refused: identifier rejected."
    elif connack_code == ConnectionStatus.BROKER_UNAVAILABLE.value:
        return "Connection Refused: broker unavailable."
    elif connack_code == ConnectionStatus.FAILED_AUTHENTICATION.value:
        return "Connection Refused: bad user name or password."
    elif connack_code == ConnectionStatus.NOT_AUTHORIZED.value:
        return "Connection Refused: not authorised."
    elif connack_code == ConnectionStatus.FAILURE.value:
        return "Connection Refused: failed to connect."
    elif connack_code == ConnectionStatus.SSL_FAILURE.value:
        return "Connection Refused: SSL failure "
    elif connack_code == ConnectionStatus.SERVER_CONNECT_ERROR.value:
        return "Connection Refused: server connect error"
    else:
        return "Connection Refused: unknown reason."


def puback_string(puback_code):
    if puback_code == MqttCodes.MQTT_ERR_SUCCESS.value:
        return "No error."
    elif puback_code == MqttCodes.MQTT_ERR_NOMEM.value:
        return "Out of memory."
    elif puback_code == MqttCodes.MQTT_ERR_PROTOCOL.value:
        return "A network protocol error occurred when communicating with the broker."
    elif puback_code == MqttCodes.MQTT_ERR_INVAL.value:
        return "Invalid function arguments provided."
    elif puback_code == MqttCodes.MQTT_ERR_NO_CONN.value:
        return "The client is not currently connected."
    elif puback_code == MqttCodes.MQTT_ERR_CONN_REFUSED.value:
        return "The connection was refused."
    elif puback_code == MqttCodes.MQTT_ERR_NOT_FOUND.value:
        return "Message not found (internal error)."
    elif puback_code == MqttCodes.MQTT_ERR_CONN_LOST.value:
        return "The connection was lost."
    elif puback_code == MqttCodes.MQTT_ERR_TLS.value:
        return "A TLS error occurred."
    elif puback_code == MqttCodes.MQTT_ERR_PAYLOAD_SIZE.value:
        return "Payload too large."
    elif puback_code == MqttCodes.MQTT_ERR_NOT_SUPPORTED.value:
        return "This feature is not supported."
    elif puback_code == MqttCodes.MQTT_ERR_AUTH.value:
        return "Authorisation failed."
    elif puback_code == MqttCodes.MQTT_ERR_ACL_DENIED.value:
        return "Access denied by ACL."
    elif puback_code == MqttCodes.MQTT_ERR_UNKNOWN.value:
        return "Unknown error."
    elif puback_code == MqttCodes.MQTT_ERR_ERRNO.value:
        return "Error defined by err no."
    elif puback_code == MqttCodes.MQTT_ERR_QUEUE_SIZE.value:
        return "Message queue full."
    elif puback_code == MqttCodes.MQTT_ERR_KEEPALIVE.value:
        return "Client or broker did not communicate in the keep alive interval."
    else:
        return "Unknown error."
