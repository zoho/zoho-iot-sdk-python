import sys

sys.path.append(".")
sys.path.append("..")
sys.path.append("../..")

import json
import time
import signal
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
        ack_client.publishConfigAck(correlation_id=correlation_id,
                                    status_code=MqttConstants.ConfigAckResponseCodes.SUCCESSFULLY_EXECUTED,
                                    responseMessage="Config Executed.")


signal.signal(signal.SIGINT, handler)
client = ZohoIoTClient(secureConnection=True)
client.setLogger(loglevel="DEBUG")
client.init(mqttUserName="<user name>", mqttPassword="<password>",
            caCertificate="<ZohoIoTServerRootCA.pem file location>")

rc = client.connect()

if rc == 0:
    client.subscribeCommandCallback(function=command_callback)
    client.subscribeConfigCallback(function=config_callback)
    while True:
        client.addDataPoint(key="temperature", value=35)
        client.addDataPoint(key="humidity", value=70)
        client.markDataPointAsError(key="pressure")
        client.dispatchAsset(assetName="home")
        time.sleep(30)
