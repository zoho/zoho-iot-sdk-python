import sys

sys.path.append(".")
sys.path.append("..")
sys.path.append("../..")

import json
import time
import signal
from zoho_iot_sdk import ZohoIoTClient, MqttConstants
from os.path import exists


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

        ack_client.publishCommandAck(correlation_id=correlation_id,
                                     status_code=MqttConstants.CommandAckResponseCodes.SUCCESSFULLY_EXECUTED,
                                     responseMessage="Command based task Executed.")


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
            ack_client.publishConfigAck(correlation_id=correlation_id,
                                        status_code=MqttConstants.ConfigAckResponseCodes.SUCCESSFULLY_EXECUTED,
                                        responseMessage="Config Executed.")
        else:
            ack_client.publishConfigAck(correlation_id=correlation_id,
                                        status_code=MqttConstants.ConfigAckResponseCodes.EXECUTION_FAILURE,
                                        responseMessage="Failed to execute")


if __name__ == "__main__":

    interval = 10
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
    client = ZohoIoTClient(secureConnection=True)
    client.setLogger(loglevel="DEBUG")
    client.init(mqttUserName="/79937niary.zohoiothub.com/v1/devices/321000000167133/connect",
                mqttPassword="5262d78fd4e269847e22e79fa378be2f16cfddd957acc826be6c8145de51eb",
                caCertificate="basicTLS/ZohoIoTServerRootCA.pem")

    # client.init(mqttUserName="<user name>", mqttPassword="<password>",
    #             caCertificate="<ZohoIoTServerRootCA.pem file location>")

    rc = client.connect()

    if rc == 0:
        client.subscribeCommandCallback(function=command_callback)
        client.subscribeConfigCallback(function=config_callback)
        while True:
            client.addDataPoint(key="temperature", value=35)
            client.addDataPoint(key="humidity", value=70)
            client.markDataPointAsError(key="pressure")
            client.dispatchAsset(assetName="home")
            time.sleep(interval)
