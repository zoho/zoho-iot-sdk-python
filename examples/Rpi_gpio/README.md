# Zoho IOT SDK - Raspberry Pi GPIO Example

## Overview

This example demonstrates how to use the Zoho IOT SDK with Raspberry Pi GPIO to control and monitor hardware components. The provided script shows how to interact with the GPIO pins on a Raspberry Pi board to perform actions such as controlling an LED, reading input from a switch, and handling an interrupt.


## Setup

### Prerequisites

Before running this example, ensure you have the following:

- **Raspberry Pi 4** or **Raspberry Pi 5** with an internet connection
- Python 3.6 or higher installed on the Raspberry Pi
- Required Python packages listed in the `requirements.txt` file
- Hardware components:
    - LED
    - Switch
    - Interrupt-triggered device (e.g., a door sensor or button)

### Installation

1. **Install Dependencies**: Ensure you have the necessary Python packages installed. You can do this by running the following command:

    ```bash
    pip install -r requirements.txt
    ```

2. **Connect the Hardware Components**: Connect the LED, switch, and interrupt-triggered device to the appropriate GPIO pins on the Raspberry Pi. The default script setup uses the following GPIO pin configuration:

    ```python
    # Define GPIO pins based on the Raspberry Pi model
    OUTPUT_PIN = board.D17
    SWITCH_PIN = board.D27
    INTERRUPT_PIN = board.D22
    ```

   Adjust the GPIO pins in the script if you are using different connections.

3. **Add Zoho IoT TLS Credentials**: Open the script and add your Zoho IOT TLS credentials in the appropriate section:

    ```python
    # Initialize the Zoho IOT client with MQTT credentials and CA certificate
    MQTT_USER_NAME = "<user name>"
    MQTT_PASSWORD = "<password>"
    CA_CERTIFICATE = "../certificate/ZohoIoTServerRootCA.pem"
    ```

4. **Run the Script**: Once you've connected the components and added your credentials, execute the Python script to start controlling the LED, reading input from the switch, and handling interrupts via the Zoho IOT application:

    ```bash
    python rpi_gpio_sample.py
    ```
