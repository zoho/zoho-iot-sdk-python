import sys
import logging
sys.path.append(".")
sys.path.append("..")
sys.path.append("../..")

from zoho_iot_sdk import ZohoIoTClient

client = ZohoIoTClient()

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
client.enable_logger(logger,filename="test.log")

client.init(mqtt_user_name="<user name>", mqtt_password="<password>")
rc = client.connect()

if rc == 0:
    client.add_data_point(key="temperature", value=35, asset_name="floor_1")
    client.add_data_point(key="humidity", value=70, asset_name="floor_1")
    client.add_data_point(key="temperature", value=30, asset_name="floor_2")
    client.add_data_point(key="humidity", value=50, asset_name="floor_2")
    client.dispatch_asset(asset_name="home")
    client.disconnect()
else:
    print("unable to establish connection: " + str(rc))
