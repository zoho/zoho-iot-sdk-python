import sys
import logging
import time
import signal

# Import the Zoho IOT SDK
from zoho_iot_sdk import ZohoIoTClient, MqttConstants
from utils.dht import DHT_SENSOR

MQTT_USER_NAME = "<user name>"
MQTT_PASSWORD = "<password>"
CA_CERTIFICATE = "../certificate/ZohoIoTServerRootCA.pem"

def create_logger():
    filename = "dht_sample.log"
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)  
    console_handler = logging.StreamHandler()
    file_handler = logging.FileHandler(filename) 
    formatter = logging.Formatter('%(asctime)s %(levelname)5s  %(filename)s:%(lineno)d %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger

logger = create_logger()

# Create an instance of the ZohoIoTClient with secure connection
client = ZohoIoTClient(secure_connection=True,logger=logger)

# Initialize the DHT22 sensor (data pin connected to GPIO 4)
sensor = DHT_SENSOR(pin=4,dht_model="22")
result = sensor.read()

# Define a signal handler to cleanly disconnect and exit on SIGINT (Ctrl+C)
def handler(sig, frame):
    client.disconnect()
    sys.exit(0)


def main():
    # Register the signal handler for SIGINT
    signal.signal(signal.SIGINT, handler)

    # Initialize the Zoho IOT client with MQTT credentials and CA certificate
    rc = client.init(mqtt_user_name=MQTT_USER_NAME, mqtt_password=MQTT_PASSWORD,
                ca_certificate=CA_CERTIFICATE)
    if rc == 0:
        # Attempt to connect to the MQTT server
        rc = client.connect()
    else:
        exit(-1)

    # Check if the connection was successful
    if rc == 0:
        while True:
            try:
                # Read temperature and humidity from the sensor
                if result.is_valid():
                    temperature_c = result.temperature
                    humidity = result.humidity
                    # Add data points for temperature and humidity
                    client.add_data_point(key="temperature", value=temperature_c)
                    client.add_data_point(key="humidity", value=humidity)

                    # Dispatch the data points to the asset named "room"
                    client.dispatch()
                else:
                    print('Failed to get reading from DHT sensor')
            except RuntimeError as error:
                # Handle common sensor reading errors by retrying after a short delay
                print(error.args[0])
                time.sleep(2.0)
                continue
            except Exception as error:
                # Clean up and raise any other exceptions
                sensor.exit()
                raise error
            # Wait for 30 seconds before reading the sensor again
            time.sleep(30)


if __name__ == "__main__":
    main()
