import sys
import logging
import json
import time
import signal
import gpiod
import threading

# Import the Zoho IoT SDK
from zoho_iot_sdk import ZohoIoTClient, MqttConstants

MQTT_USER_NAME = "<user name>"
MQTT_PASSWORD = "<password>"
CA_CERTIFICATE = "<ZohoIoTServerRootCA.pem file location>"

# Create an instance of the ZohoIoTClient with secure connection
client = ZohoIoTClient(secure_connection=True)

# Define GPIO chip and line numbers
CHIP = 'gpiochip4'
OUTPUT_LINE = 17  # GPIO pin for LED
SWITCH_LINE = 27  # GPIO pin for Switch
INTERRUPT_LINE = 22  # GPIO pin for Interrupt

# Open the GPIO chip
chip = gpiod.Chip(CHIP)

# Get the lines for LED, Switch, and Interrupt
led_line = chip.get_line(OUTPUT_LINE)
switch_line = chip.get_line(SWITCH_LINE)
interrupt_line = chip.get_line(INTERRUPT_LINE)

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
client.enable_logger(logger, filename="rpi_gpio_sample.py")


# Define a signal handler to cleanly disconnect and exit on SIGINT (Ctrl+C)
def handler(sig, frame):
    led_line.release()
    switch_line.release()
    interrupt_line.release()
    client.disconnect()
    sys.exit(0)


# Function to turn LED on or off
def set_led(state):
    led_line.set_value(state)


# Interrupt handler
def handle_interrupt():
    previous_value = interrupt_line.get_value()
    while True:
        current_value = interrupt_line.get_value()
        if previous_value != current_value:
            logging.debug("state changed")
            logging.debug(current_value)
            # Update the interrupt state
            client.add_data_point(key="interrupt", value=current_value)
            # Dispatch the data points to the asset named "room"
            client.dispatch()
            previous_value = current_value
        time.sleep(0.5)


def command_callback(ack_client, message):
    payload_array = json.loads(message.payload)
    time.sleep(1)
    for payload in payload_array:
        correlation_id = payload["correlation_id"]
        command_name = payload["command_name"]
        payload_data = payload["payload"]
        print("correlation_id :" + correlation_id)
        print("command_name :" + command_name)
        if command_name == "LED ON/OFF":
            if payload_data[0]["value"] == "on":
                set_led(1)
                logger.debug("LED turned ON")
                ack_client.publish_command_ack(correlation_id=correlation_id,
                                               status_code=MqttConstants.CommandAckResponseCodes.SUCCESSFULLY_EXECUTED,
                                               response_message="Led turned ON")
            elif payload_data[0]["value"] == "off":
                set_led(0)
                logger.debug("LED turned OFF")
                ack_client.publish_command_ack(correlation_id=correlation_id,
                                               status_code=MqttConstants.CommandAckResponseCodes.SUCCESSFULLY_EXECUTED,
                                               response_message="Led turned OFF")
            else:
                ack_client.publish_command_ack(correlation_id=correlation_id,
                                               status_code=MqttConstants.CommandAckResponseCodes.EXECUTION_FAILURE,
                                               response_message="Command value error, please use on or off")
        else:
            ack_client.publish_command_ack(correlation_id=correlation_id,
                                           status_code=MqttConstants.CommandAckResponseCodes.EXECUTION_FAILURE,
                                           response_message="Unknown command")


def main():
    # Register the signal handler for SIGINT
    signal.signal(signal.SIGINT, handler)

    # Request the lines
    led_line.request(consumer="LED", type=gpiod.LINE_REQ_DIR_OUT)
    switch_line.request(consumer="Switch", type=gpiod.LINE_REQ_DIR_IN, flags=gpiod.LINE_REQ_FLAG_BIAS_PULL_DOWN)
    interrupt_line.request(consumer="Interrupt", type=gpiod.LINE_REQ_DIR_IN, flags=gpiod.LINE_REQ_FLAG_BIAS_PULL_DOWN)

    # Initialize the Zoho IoT client with MQTT credentials and CA certificate
    rc = client.init(MQTT_USER_NAME, MQTT_PASSWORD,
                CA_CERTIFICATE)
    if rc == 0:
        # Attempt to connect to the MQTT server
        rc = client.connect()
    else:
        exit(-1)

    # Check if the connection was successful
    if rc == 0:
        client.subscribe_command_callback(function=command_callback)
        interrupt_thread = threading.Thread(target=handle_interrupt)
        interrupt_thread.start()
        while True:
            try:
                # Update the switch state
                client.add_data_point(key="switch", value=switch_line.get_value())
                # Dispatch the data points to the asset named "room"
                client.dispatch()
            except Exception as error:
                logger.error(error)

            # Wait for 30 seconds before reading the switch again
            time.sleep(30)


if __name__ == "__main__":
    main()
