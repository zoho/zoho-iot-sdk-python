import sys
sys.path.append(".")
sys.path.append("..")
sys.path.append("../..")

from zoho_iot_sdk import ZohoIoTClient

client = ZohoIoTClient()
client.initYaml("config.yaml")
rc = client.connect()
if rc == 0:
    eventData = {"temperature": 45, "humidity": 20}
    client.dispatchEvent(eventType="ALARM", eventDescription="Critical Temperature", eventDataKeymap=eventData)
    client.disconnect()
