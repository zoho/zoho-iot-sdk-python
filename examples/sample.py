import logging
from zoho_iot_sdk import ZohoIoTClient
from zoho_iot_sdk import TransactionStatus
MQTT_USER_NAME = "<user name>"
MQTT_PASSWORD = "<password>"

client = ZohoIoTClient()

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
client.enable_logger(logger, filename="sample.log")

rc = client.init(MQTT_USER_NAME, MQTT_PASSWORD)
if rc == 0:
    rc = client.connect()
else:
    exit(-1)
if rc == 0:
    client.add_data_point(key="temperature", value=35, asset_name="floor_1")
    client.add_data_point(key="humidity", value=70, asset_name="floor_1")
    client.add_data_point(key="temperature", value=30, asset_name="floor_2")
    client.add_data_point(key="humidity", value=50, asset_name="floor_2")
    client.dispatch()
    client.disconnect()
else:
    print("unable to establish connection: " + str(rc))
