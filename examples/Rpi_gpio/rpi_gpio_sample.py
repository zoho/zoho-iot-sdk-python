import sys
import logging
import json
import time
import signal
import threading
import board
import digitalio

# Import the Zoho IOT SDK
from zoho_iot_sdk import ZohoIoTClient, MqttConstants


# Define GPIO pins based on rpi model
OUTPUT_PIN = board.D17
SWITCH_PIN = board.D27
INTERRUPT_PIN = board.D22

# Initialize the Zoho IOT client with MQTT credentials and CA certificate
MQTT_USER_NAME = "<user name>"
MQTT_PASSWORD = "<password>"
CA_CERTIFICATE = "../certificate/ZohoIoTServerRootCA.pem"

def create_logger():
    filename = "rpi_gpio_sample.log"
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

# Create an instance of the ZohoIoTClient with secure connection
logger = create_logger()
client = ZohoIoTClient(secure_connection=True,logger=logger)


# Initialize GPIO pins
led_pin = digitalio.DigitalInOut(OUTPUT_PIN)
led_pin.direction = digitalio.Direction.OUTPUT

switch_pin = digitalio.DigitalInOut(SWITCH_PIN)
switch_pin.direction = digitalio.Direction.INPUT

interrupt_pin = digitalio.DigitalInOut(INTERRUPT_PIN)
interrupt_pin.direction = digitalio.Direction.INPUT

# Define a signal handler to cleanly disconnect and exit on SIGINT (Ctrl+C)
def handler(sig, frame):
    client.disconnect()
    sys.exit(0)

# Function to turn LED on or off
def set_led(state):
    led_pin.value = state

# Interrupt handler
def handle_interrupt():
    previous_value = interrupt_pin.value
    while True:
        current_value = interrupt_pin.value
        if previous_value != current_value:
            logging.debug("Interrupt state changed: %d", current_value)
            # Update the interrupt state
            client.add_data_point(key="interrupt", value=current_value)
            client.dispatch()
            previous_value = current_value
        time.sleep(0.5)

def command_callback(ack_client, message):
    payload_array = json.loads(message.payload)
    time.sleep(1)
    for payload in payload_array:
        correlation_id = payload["correlation_id"]
        payload_data = payload["payload"]
        command_key = payload_data[0]["edge_command_key"]
        logging.info("Received command key: %s with correlation ID: %s", command_key, correlation_id)
        if command_key == "LED_control":
            if payload_data[0]["value"] == "on":
                set_led(True)
                logger.debug("LED turned ON")
                ack_client.publish_command_ack(correlation_id=correlation_id,
                                               status_code=MqttConstants.CommandAckResponseCodes.SUCCESSFULLY_EXECUTED,
                                               response_message="LED turned ON")
            elif payload_data[0]["value"] == "off":
                set_led(False)
                logger.debug("LED turned OFF")
                ack_client.publish_command_ack(correlation_id=correlation_id,
                                               status_code=MqttConstants.CommandAckResponseCodes.SUCCESSFULLY_EXECUTED,
                                               response_message="LED turned OFF")
            else:
                ack_client.publish_command_ack(correlation_id=correlation_id,
                                               status_code=MqttConstants.CommandAckResponseCodes.EXECUTION_FAILURE,
                                               response_message="Command value error, please use 'on' or 'off'")
        else:
            ack_client.publish_command_ack(correlation_id=correlation_id,
                                           status_code=MqttConstants.CommandAckResponseCodes.EXECUTION_FAILURE,
                                           response_message="Unknown command")

def main():
    # Register the signal handler for SIGINT
    signal.signal(signal.SIGINT, handler)

    # Initialize the Zoho IOT client with MQTT credentials and CA certificate
    rc = client.init(mqtt_user_name=MQTT_USER_NAME, mqtt_password=MQTT_PASSWORD, ca_certificate=CA_CERTIFICATE)
    if rc == 0:
        # Attempt to connect to the MQTT server
        rc = client.connect()
    else:
        logger.error("Failed to initialize client")
        sys.exit(-1)

    # Check if the connection was successful
    if rc == 0:
        client.subscribe_command_callback(function=command_callback)
        interrupt_thread = threading.Thread(target=handle_interrupt)
        interrupt_thread.start()
        while True:
            try:
                # Update the switch state
                client.add_data_point(key="switch", value=switch_pin.value)
                # Dispatch the data points to the asset named "room"
                client.dispatch()
            except Exception as error:
                logger.error("Error occurred: %s", error)
            # Wait for 30 seconds before reading the switch again
            time.sleep(30)

if __name__ == "__main__":
    main()