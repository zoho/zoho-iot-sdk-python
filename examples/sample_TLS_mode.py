import sys

sys.path.append(".")
sys.path.append("..")
sys.path.append("../..")

from zoho_iot_sdk import ZohoIoTClient

client = ZohoIoTClient(secureConnection=True)
client.init(mqttUserName="/79937niary.zohoiothub.com/v1/devices/321000000167133/connect",
            mqttPassword="5262d78fd4e269847e22e79fa378be2f16cfddd957acc826be6c8145de51eb",
            caCertificate="basicTLS/ZohoIoTServerRootCA.pem")

client.init(mqttUserName="<user name>", mqttPassword="<password>",caCertificate="<ZohoIoTServerRootCA.pem file location>")

rc = client.connect()
client.setLogger(loglevel="DEBUG")
if rc == 0:
    client.addDataPoint(key="temperature", value=35)
    client.addDataPoint(key="humidity", value=70)
    client.markDataPointAsError(key="pressure")
    client.dispatchAsset(assetName="home")
    client.disconnect()
