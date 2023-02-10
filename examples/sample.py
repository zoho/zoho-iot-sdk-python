import sys

sys.path.append(".")
sys.path.append("..")
sys.path.append("../..")

from zoho_iot_sdk import ZohoIoTClient

client = ZohoIoTClient()
client.setLogger(loglevel="DEBUG", filename="test.log")
client.init(mqttUserName="/79937niary.zohoiothub.com/v1/devices/321000000165121/connect",
            mqttPassword="283cac823fc55657b18b18e46b49858e127894ea5fd3c40b6b99d2dd044272")
# client.init(mqttUserName="<user name>", mqttPassword="<password>")
rc = client.connect()

if rc == 0:
    client.addDataPoint(key="temperature", value=35, assetName="floor_1")
    client.addDataPoint(key="humidity", value=70, assetName="floor_1")
    client.addDataPoint(key="temperature", value=30, assetName="floor_2")
    client.addDataPoint(key="humidity", value=50, assetName="floor_2")
    client.dispatchAsset(assetName="home")
    client.disconnect()
else:
    print("unable to establish connection: " + rc)
