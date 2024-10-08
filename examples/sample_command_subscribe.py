import sys
import logging
import json
import time
import signal
from zoho_iot_sdk import ZohoIoTClient
from zoho_iot_sdk import TransactionStatus,CommandAckResponseCodes,ConfigAckResponseCodes

MQTT_USER_NAME = "<user name>"
MQTT_PASSWORD = "<password>"
CA_CERTIFICATE = "./certificate/ZohoIoTServerRootCA.pem"

def create_logger():
    filename = "sample_command_subscribe.log"
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)  
    console_handler = logging.StreamHandler()
    file_handler = logging.FileHandler(filename) 
    formatter = logging.Formatter('%(asctime)s %(levelname)5s  %(filename)s:%(lineno)d %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger

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
                                       status_code=CommandAckResponseCodes.SUCCESSFULLY_EXECUTED,
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
                                          status_code=ConfigAckResponseCodes.SUCCESSFULLY_EXECUTED,
                                          response_message="Config Executed.")

if __name__ == "__main__":

    interval = 30
    logger = create_logger()
    signal.signal(signal.SIGINT, handler)
    client = ZohoIoTClient(secure_connection=True,logger=logger)
    rc =client.init(mqtt_user_name=MQTT_USER_NAME, mqtt_password=MQTT_PASSWORD,
                ca_certificate=CA_CERTIFICATE)
    if rc == 0:
        rc = client.connect()
    else:
        exit(-1)
    if rc == 0:
        client.subscribe_command_callback(function=command_callback)
        client.subscribe_config_callback(function=config_callback)
        while True:
            client.add_data_point(key="temperature", value=35)
            client.add_data_point(key="humidity", value=70)
            client.mark_data_point_as_error(key="pressure")
            client.dispatch()
            time.sleep(interval)
