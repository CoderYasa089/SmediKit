# SmediKit: AI-Powered Telemedicine & Remote Vitals Monitoring Hub

SmediKit is an Industrial IoT (IIoT 4.0) healthcare prototype designed to provide real-time, hands-free patient vital monitoring while ensuring data sovereignty through edge and fog computing architectures.

## Project Overview
Designed to operate without reliance on public cloud infrastructure, SmediKit utilizes an ESP32-S3 edge node to securely transmit patient telemetry (Wrist Temperature, SpO2, and BPM) to a localized Fog Server. It features an acoustic RMS trigger for a completely hands-free interface, a proximity gate to eliminate ambient noise artifacts, and a real-time asynchronous web dashboard that utilizes a Federated Learning (FedAvg) algorithm for privacy-preserving AI anomaly detection.

## System Architecture
The system is divided into three distinct operational layers:
1. The Edge Node (Hardware): Captures biometric data via an integrated sensor array and handles continuous acoustic environmental monitoring with debounce logic.
2. The Fog Layer (Network): A localized Mosquitto MQTT broker that securely routes data within a private LAN.
3. The Triage UI & FL Node (Software): A Python and NiceGUI dashboard that analyzes the data stream, visually flags anomalies, and acts as a localized edge trainer to aggregate machine learning weights without exposing raw data.

## Hardware Stack
* Microcontroller: ESP32-S3 (Dual-Core, 8MB PSRAM)
* Heart Rate and Blood Oxygen: MAX30102 Oximetry Sensor
* Temperature: MLX90614 Non-Contact Infrared Thermometer
* Audio Input: INMP441 I2S Omnidirectional Microphone
* Display: 0.96 inch I2C OLED Display

## Software and Network Stack
* Edge Firmware: C++ (Arduino Core) with RTOS yield task management
* Networking: Secure Local MQTT (PubSubClient)
* Fog Broker: Eclipse Mosquitto
* Backend and Dashboard: Python, NiceGUI, scikit-learn, numpy (for FedAvg ML logic)

## Key Features
* Acoustic Trigger (Edge AI): Calculates the Root Mean Square (RMS) of the I2S audio buffer with a 2-second debounce cooldown to act as a hands-free start/stop trigger.
* Zero-Cloud Data Sovereignty: Patient data never touches the public internet, satisfying strict medical privacy requirements.
* Proximity Gate: Automatically forces biometric readings to zero when the finger is removed, preventing phantom data transmission.
* Federated Averaging (FedAvg): The Python dashboard trains a local Logistic Regression model on the session data, injects Laplacian noise for differential privacy, aggregates weights globally, and securely purges raw patient data from memory upon completion.
* Real-Time Visualization: Seamless telemetry charting using ECharts integration with dynamic triage status updates.

## Getting Started

**Configuration Warning:** Before compiling the firmware, you must open the `Smedikit_Node.ino` file and update the `ssid`, `password`, and `mqtt_server` variables to match your local Wi-Fi credentials and the IPv4 address of your Fog Node (laptop). 

**System Activation & Usage Instructions:**
1. Ensure the Eclipse Mosquitto broker is actively running on your host machine (default port 1883).
2. Install the necessary Python dependencies (`pip install nicegui paho-mqtt scikit-learn numpy`) and launch the dashboard by running `python smedikit_dashboard.py`.
3. Power the ESP32-S3 edge node via USB. It will initialize the sensors, connect to the local Wi-Fi and MQTT broker, and enter STANDBY mode.
4. To initiate a diagnostic scan, speak the wake word "START" in a normal voice near the INMP441 microphone. The OLED and dashboard will dynamically switch to ACTIVE status.
5. Rest your index finger lightly on the MAX30102 sensor and hover your wrist over the MLX90614 sensor. Allow 5 to 10 seconds for the peak-detection and SpO2 algorithms to stabilize.
6. The scan will run for a predetermined 60-second duration. To conclude the scan early, speak the word "STOP".
7. Upon returning to STANDBY mode, the dashboard will automatically trigger the Federated Learning sequence, populating a dialog box to show the localized training, differential privacy injection, and final data purge.

***
Developed by Yasa Christian