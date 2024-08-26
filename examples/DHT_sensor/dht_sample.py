import sys
import logging
import time
import signal
import board
import adafruit_dht

# Import the Zoho IoT SDK
from zoho_iot_sdk import ZohoIoTClient, MqttConstants

MQTT_USER_NAME = "<user name>"
MQTT_PASSWORD = "<password>"
CA_CERTIFICATE = "../certificate/ZohoIoTServerRootCA.pem"

def create_logger(name):
    filename = "dht_sample.log"
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

# Create an instance of the ZohoIoTClient with secure connection
client = ZohoIoTClient(secure_connection=True,logger=logger)

sensor = adafruit_dht.DHT22(board.D4)


# Initialize the DHT22 sensor (data pin connected to GPIO 4)
# Uncomment the following line to use the DHT11 sensor instead
# sensor = adafruit_dht.DHT11(board.D4)

# Define a signal handler to cleanly disconnect and exit on SIGINT (Ctrl+C)
def handler(sig, frame):
    client.disconnect()
    sys.exit(0)


def main():
    # Register the signal handler for SIGINT
    signal.signal(signal.SIGINT, handler)

    # Initialize the Zoho IoT client with MQTT credentials and CA certificate
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
                temperature_c = sensor.temperature
                humidity = sensor.humidity

                # Add data points for temperature and humidity
                client.add_data_point(key="temperature", value=temperature_c)
                client.add_data_point(key="humidity", value=humidity)

                # Dispatch the data points to the asset named "room"
                client.dispatch()
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
