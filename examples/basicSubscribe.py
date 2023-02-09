import time
import signal
import sys
import json

sys.path.append(".")
sys.path.append("..")
sys.path.append("../..")

from zoho_iot_sdk import ZohoIoTClient, MqttConstants
#TODO: file to be removed.

def handler(sig, frame):
    client.disconnect()
    sys.exit(0)


def callback(ack_client, message):
    array = json.loads(message.payload)
    time.sleep(1)
    for i in range(len(array)):
        correlationId = array[i]["correlation_id"]
        command_name = array[i]["command_name"]
        array_payload = array[i]["payload"]
        print("correlation_id :" + correlationId)
        print("command_name :" + command_name)
        for payload in array_payload:
            edge_command_key = payload["edge_command_key"]
            value = payload["value"]
            print("edge_command_key :"+edge_command_key)
            print("value :"+value)

        ack_client.publishCommandAck(correlation_id=correlationId,
                                     status_code=MqttConstants.CommandAckResponseCodes.SUCCESFULLY_EXECUTED,
                                     responseMessage="Command based task Executed.")



signal.signal(signal.SIGINT, handler)
client = ZohoIoTClient()
client.setLogger(loglevel="DEBUG", filename="test.log")
client.init(mqttUserName="/79937niary.zohoiothub.com/v1/devices/321000000165121/connect",
            mqttPassword="283cac823fc55657b18b18e46b49858e127894ea5fd3c40b6b99d2dd044272")

rc = client.connect()
client.subscribeCommandCallback(topic="/devices/321000000165121/commands", function=callback)
while True:
    pass
