import logging
from zoho_iot_sdk import ZohoIoTClient
from zoho_iot_sdk import TransactionStatus
MQTT_USER_NAME = "<user name>"
MQTT_PASSWORD = "<password>"

def create_logger(name):
    filename = "sample.log"
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)  
    console_handler = logging.StreamHandler()
    file_handler = logging.FileHandler(filename) 
    formatter = logging.Formatter('%(asctime)s %(levelname)5s  %(filename)s:%(lineno)d %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger

logger = create_logger(__name__)

client = ZohoIoTClient(logger=logger)

rc = client.init(mqtt_user_name=MQTT_USER_NAME, mqtt_password=MQTT_PASSWORD)
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
    logger.error("unable to establish connection: " + str(rc))
