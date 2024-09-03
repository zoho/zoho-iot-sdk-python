# Zoho IOT Python SDK

The Zoho IOT Python SDK provides a seamless interface for connecting to the Zoho IOT application. It supports managing connections, sending telemetry data, handling commands.



## Getting Started

### Installation

To install the Zoho IOT Python SDK:

1. Download the latest version of SDK:

    ```bash
    curl -L -o zoho-iot-sdk-python.zip https://github.com/zoho/zoho-iot-sdk-python/archive/refs/tags/0.1.0.zip
    unzip zoho-iot-sdk-python.zip
    mv zoho-iot-sdk-python-0.1.0 zoho-iot-sdk-python
    cd zoho-iot-sdk-python
    ```

2. Create a virtual environment:

   For **Linux**:

    ```bash
    python3 -m venv zoho-iot
    source zoho-iot/bin/activate
    ```

   For **Windows**:

    ```cmd
    python -m venv zoho-iot
    zoho-iot\Scripts\activate
    ```

3. Install the required dependencies:

    ```bash
    pip install -r requirements.txt
    ```

4. Install the SDK:

    ```bash
    pip install .
    ```

### Trying Out the Examples

The SDK comes with default example scripts. You can find them in the `examples` directory within the SDK package. To run an example, navigate to the `examples` directory and execute the script.

For specific examples, refer to the following:

- **DHT Sensor Example**: For using a Raspberry Pi with a DHT sensor, refer to the [DHT_sensor](examples/DHT_sensor/README.md) in the `examples` directory. This script demonstrates how to read data from a DHT sensor and send it to the Zoho IOT application.

- **GPIO Example**: For demonstrating GPIO functionality on a Raspberry Pi, refer to the [GPIO](examples/Rpi_gpio/README.md) example in the `examples` directory. This script shows how to control an LED, read input from a switch, and handle interrupts using the Zoho IoT SDK.