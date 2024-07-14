import sys
import logging
import json
import time
import signal

sys.path.append(".")
sys.path.append("..")
sys.path.append("../..")

from zoho_iot_sdk import ZohoIoTClient, MqttConstants
MQTT_USER_NAME="<user name>"
MQTT_PASSWORD="<password>"
CA_CERTIFICATE="<ZohoIoTServerRootCA.pem file location>"


def handler(sig, frame):
    client.disconnect()
    sys.exit(0)


def command_callback(ack_client, message):
    payload_array = json.loads(message.payload)
    time.sleep(1)
    for payload in payload_array:
        correlation_id = payload["correlation_id"]
        command_name = payload["command_name"]
        payload_data = payload["payload"]
        print("correlation_id :" + correlation_id)
        print("command_name :" + command_name)
        for data in payload_data:
            edge_command_key = data["edge_command_key"]
            value = data["value"]
            print("edge_command_key :" + edge_command_key)
            print("value :" + value)

        ack_client.publish_command_ack(correlation_id=correlation_id,
                                       status_code=MqttConstants.CommandAckResponseCodes.SUCCESSFULLY_EXECUTED,
                                       response_message="Command based task Executed.")


def config_callback(ack_client, message):
    payload_array = json.loads(message.payload)
    time.sleep(1)
    for payload in payload_array:
        correlation_id = payload["correlation_id"]
        payload_data = payload["payload"]
        print("correlation_id :" + correlation_id)
        print("payload :" + str(payload_data))
        ack_client.publish_config_ack(correlation_id=correlation_id,
                                      status_code=MqttConstants.ConfigAckResponseCodes.SUCCESSFULLY_EXECUTED,
                                      response_message="Config Executed.")


signal.signal(signal.SIGINT, handler)
client = ZohoIoTClient(secure_connection=True)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
client.enable_logger(logger, filename="sample_TLS_mode.log")

client.init(MQTT_USER_NAME, MQTT_PASSWORD,
            CA_CERTIFICATE)

rc = client.connect()

if rc == 0:
    client.subscribe_command_callback(function=command_callback)
    client.subscribe_config_callback(function=config_callback)
    while True:
        client.add_data_point(key="temperature", value=35)
        client.add_data_point(key="humidity", value=70)
        client.mark_data_point_as_error(key="pressure")
        client.dispatch()
        time.sleep(30)
