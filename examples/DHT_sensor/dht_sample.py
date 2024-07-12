import sys
import logging
import json
import time
import signal
import board
import adafruit_dht

# Append the necessary directories to the system path for module imports
sys.path.append(".")
sys.path.append("..")
sys.path.append("../..")

# Import the Zoho IoT SDK
from zoho_iot_sdk import ZohoIoTClient, MqttConstants

# Create an instance of the ZohoIoTClient with secure connection
client = ZohoIoTClient(secure_connection=True)


# Define a signal handler to cleanly disconnect and exit on SIGINT (Ctrl+C)
def handler(sig, frame):
    client.disconnect()
    sys.exit(0)


def main():
    # Register the signal handler for SIGINT
    signal.signal(signal.SIGINT, handler)

    # Initialize the DHT22 sensor (data pin connected to GPIO 4)
    sensor = adafruit_dht.DHT22(board.D4)
    # Uncomment the following line to use the DHT11 sensor instead
    # sensor = adafruit_dht.DHT11(board.D4)

    # Set up logging
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    client.enable_logger(logger, filename="dht_sample.log")

    # Initialize the Zoho IoT client with MQTT credentials and CA certificate
    client.init(mqtt_user_name="<user name>", mqtt_password="<password>",
                ca_certificate="<ZohoIoTServerRootCA.pem file location>")

    # Attempt to connect to the MQTT server
    rc = client.connect()

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
                client.dispatch_asset(asset_name="room")
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
