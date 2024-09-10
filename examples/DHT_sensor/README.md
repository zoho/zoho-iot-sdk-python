# Zoho IOT SDK - Raspberry Pi DHT Sensor Example

## Overview

This example demonstrates how to use the Zoho IOT SDK with a Raspberry Pi to read data from a DHT sensor and send it to the Zoho IOT application. The script interacts with the GPIO pins on the Raspberry Pi to collect temperature and humidity data from the DHT sensor, which is then transmitted to Zoho IOT for monitoring and analysis.

## Setup

### Prerequisites

Before running this example, ensure you have the following:

- **Raspberry Pi 4** or **Raspberry Pi 5** with an internet connection
- Python 3.6 or higher installed on the Raspberry Pi
- A DHT sensor (e.g., DHT11 or DHT22) properly connected to the Raspberry Pi
- Required Python packages listed in the `requirements.txt` file

### Installation

1. **Install Dependencies**: Ensure you have the necessary Python packages installed. You can do this by running the following command:

    ```bash
    pip install -r requirements.txt
    ```

2. **Connect the DHT Sensor**: Connect your DHT sensor to the Raspberry Pi. By default, the program is set up to use a DHT22 sensor connected to GPIO pin 4.

    ```python
    # Initialize the DHT22 sensor (data pin connected to GPIO 4)
    sensor = DHT_SENSOR(pin=4,dht_model="22")
    # Uncomment the following line to use the DHT11 sensor instead
    # sensor = DHT_SENSOR(pin=4,dht_model="11")
    ```

3. **Add Zoho IoT TLS Credentials**: Open the script and add your Zoho IOT TLS credentials in the appropriate section:

    ```python
    # Initialize the Zoho IOT client with MQTT credentials and CA certificate
   MQTT_USER_NAME = "<user name>"
   MQTT_PASSWORD = "<password>"
   CA_CERTIFICATE = "../certificate/ZohoIoTServerRootCA.pem"
    ```

4. **Run the Script**: Once you've set up the sensor and added your credentials, execute the Python script to start reading data from the DHT sensor and send it to the Zoho IoT platform:

    ```bash
    python dht_sample.py
    ```
