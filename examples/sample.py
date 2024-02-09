import sys

sys.path.append(".")
sys.path.append("..")
sys.path.append("../..")

from zoho_iot_sdk import ZohoIoTClient

client = ZohoIoTClient()
client.set_logger(loglevel="DEBUG", filename="test.log")
client.init(mqttUserName="<user name>", mqttPassword="<password>")
rc = client.connect()

if rc == 0:
    client.add_data_point(key="temperature", value=35, asset_name="floor_1")
    client.add_data_point(key="humidity", value=70, asset_name="floor_1")
    client.add_data_point(key="temperature", value=30, asset_name="floor_2")
    client.add_data_point(key="humidity", value=50, asset_name="floor_2")
    client.dispatch_asset(asset_name="home")
    client.disconnect()
else:
    print("unable to establish connection: " + rc)
