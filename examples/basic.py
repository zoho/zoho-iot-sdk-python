
import sys

sys.path.append(".")
sys.path.append("..")
sys.path.append("../..")

from zoho_iot_sdk.ZohoIoTClient import ZohoIoTClient
obj = ZohoIoTClient("Shahul")
obj.print("pre ")
