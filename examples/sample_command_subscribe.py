import sys
import logging
import json
import time
import signal
from os.path import exists

sys.path.append(".")
sys.path.append("..")
sys.path.append("../..")

from zoho_iot_sdk import ZohoIoTClient, MqttConstants


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
        if payload_data[0].get("MQTT", {}).get("sending_interval") is not None:
            file = open(json_file_location, "w")
            file.write(json.dumps(payload_data[0]))
            file.close()
            global interval
            interval = payload_data[0]["MQTT"]["sending_interval"]
            ack_client.publish_config_ack(correlation_id=correlation_id,
                                          status_code=MqttConstants.ConfigAckResponseCodes.SUCCESSFULLY_EXECUTED,
                                          response_message="Config Executed.")
        else:
            ack_client.publish_config_ack(correlation_id=correlation_id,
                                          status_code=MqttConstants.ConfigAckResponseCodes.EXECUTION_FAILURE,
                                          response_message="Failed to execute")


if __name__ == "__main__":

    interval = 30
    signal.signal(signal.SIGINT, handler)
    json_file_location = "setup.json"
    json_data = {}
    if exists(json_file_location):
        f = open(json_file_location, "r")
        try:
            json_data = json.loads(f.read())
            f.close()
        except ValueError as err:
            print("invalid setup data")
            f.close()
            sys.exit()

    else:
        print("setup file not exits")
        sys.exit()
    if json_data.get("MQTT", {}).get("sending_interval") is not None:
        interval = json_data["MQTT"]["sending_interval"]
    else:
        print("invalid interval ,continuing on default")
    client = ZohoIoTClient(secure_connection=True)

    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    client.enable_logger(logger, filename="sample_command_subscribe.log")

    client.init(mqtt_user_name="<user name>", mqtt_password="<password>",
                ca_certificate="<ZohoIoTServerRootCA.pem file location>")

    rc = client.connect()

    if rc == 0:
        client.subscribe_command_callback(function=command_callback)
        client.subscribe_config_callback(function=config_callback)
        while True:
            client.add_data_point(key="temperature", value=35)
            client.add_data_point(key="humidity", value=70)
            client.mark_data_point_as_error(key="pressure")
            client.dispatch()
            time.sleep(interval)
