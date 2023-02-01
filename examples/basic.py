import sys

sys.path.append(".")
sys.path.append("..")
sys.path.append("../..")

from zoho_iot_sdk import ZohoIoTClient
import logging

logging.basicConfig(level=logging.DEBUG)
test = ZohoIoTClient()
test.init(mqttUserName="/79937niary.zohoiothub.com/v1/devices/321000000165121/connect",
          mqttPassword="283cac823fc55657b18b18e46b49858e127894ea5fd3c40b6b99d2dd044272")
rc = test.connect()
if rc == 0:
    test.addDataPoint("temperature", 10)
    test.addDataPoint("pressure", 11)
    test.dispatchEvent(assetName="test")
    test.disconnect()
