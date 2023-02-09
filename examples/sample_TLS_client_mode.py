import sys

sys.path.append(".")
sys.path.append("..")
sys.path.append("../..")

from zoho_iot_sdk import ZohoIoTClient

client = ZohoIoTClient(secureConnection=True, useClientCertificates=True)
client.init(mqttUserName="/79937niary.zohoiothub.com/v1/devices/321000000167145/connect",
            caCertificate="basicTLS_WithCA/ZohoIoTServerRootCA.pem",
            clientCertificate="basicTLS_WithCA/pythonsdk.cert.pem",
            privateKey="basicTLS_WithCA/pythonsdk.private.key")
rc = client.connect()
client.setLogger(loglevel="ERROR", filename="app.log")
if rc == 0:
    client.addDataPoint(key="temperature", value=35)
    client.addDataPoint(key="humidity", value=70)
    client.dispatch()
    client.disconnect()
