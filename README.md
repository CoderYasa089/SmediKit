# SmediKit: Edge-AI Telemedicine Node

SmediKit is an Industrial IoT (IIoT 4.0) healthcare prototype designed to provide real-time, hands-free patient vital monitoring while ensuring data sovereignty through edge and fog computing architectures.

## Project Overview
Designed to operate without reliance on public cloud infrastructure, SmediKit utilizes an ESP32-S3 edge node to securely transmit patient telemetry (Temperature and BPM) to a localized Fog Server. It features an acoustic RMS trigger for a completely hands-free interface and a real-time asynchronous web dashboard for medical triage and anomaly detection.

## System Architecture
The system is divided into three distinct operational layers:
1. The Edge Node (Hardware): Captures biometric data and handles continuous acoustic environmental monitoring.
2. The Fog Layer (Network): A localized Mosquitto MQTT broker that securely routes data within a private LAN.
3. The Triage UI (Software): A Python and NiceGUI dashboard that analyzes the data stream and visually flags anomalies such as fevers or irregular rhythms.

## Hardware Stack
* Microcontroller: ESP32-S3 (Dual-Core, 8MB PSRAM)
* Heart Rate and Pulse: MAX30102 Oximetry Sensor
* Temperature: DS18B20 1-Wire Waterproof Probe
* Audio Input: INMP441 I2S Omnidirectional Microphone
* Display: 0.96 inch I2C OLED Display

## Software and Network Stack
* Edge Firmware: C++ (Arduino Core) with RTOS yield task management
* Networking: Secure Local MQTT (PubSubClient)
* Fog Broker: Eclipse Mosquitto
* Backend and Dashboard: Python, FastAPI, NiceGUI

## Key Features
* Acoustic Trigger (Edge AI): Calculates the Root Mean Square (RMS) of the I2S audio buffer to act as a hands-free volume trigger.
* Zero-Cloud Data Sovereignty: Patient data never touches the public internet, satisfying strict medical privacy requirements.
* Real-Time Visualization: 60fps telemetry charting using ECharts integration.
* Edge Anomaly Detection: The local fog node actively monitors thresholds to trigger UI alerts for abnormal vitals.

## Getting Started
(Detailed setup instructions for hardware wiring and software deployment will be added here in future commits).

***
Developed by Yasa Christian