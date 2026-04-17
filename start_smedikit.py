import socket
import time
import subprocess
import sys
import paho.mqtt.client as mqtt

print("========================================")
print(" SmediKit System Health & Launcher V4   ")
print("========================================")

# 1. Check if Mosquitto Broker is running
print("[1/3] Checking Local Mosquitto Broker...")
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
result = sock.connect_ex(('127.0.0.1', 1883))
if result == 0:
    print("      -> Broker is ACTIVE.")
else:
    print("      -> ERROR: Mosquitto is NOT running. Please start the Mosquitto service.")
    input("Press Enter to exit...")
    sys.exit()
sock.close()

# 2. Check for ESP32 MQTT Telemetry
print("[2/3] Listening for ESP32-S3 Edge Node...")
esp_found = False

def on_message(client, userdata, msg):
    global esp_found
    esp_found = True

# UPGRADED TO VERSION 2
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_message = on_message
client.connect("127.0.0.1", 1883, 60)
client.subscribe("smedikit/vitals")
client.loop_start()

# Wait 5 seconds for a ping from the hardware
for i in range(5):
    if esp_found:
        break
    time.sleep(1)

client.loop_stop()

if esp_found:
    print("      -> Hardware Detected! Telemetry is flowing.")
else:
    print("      -> WARNING: ESP32 not detected. Ensure it is powered and 'START' command was given.")
    print("      -> Proceeding anyway...")

# 3. Launch the Dashboard
print("[3/3] Launching Triage Dashboard...")
print("      -> KEEP THIS TERMINAL OPEN to keep the dashboard running.")
print("========================================")

try:
    # FIX: Using subprocess.run() forces the launcher to stay alive
    subprocess.run([sys.executable, "Dashboard/smedikit_dashboard.py"], check=True)
except KeyboardInterrupt:
    print("\nShutting down SmediKit...")
except Exception as e:
    print(f"\nERROR launching dashboard: {e}")