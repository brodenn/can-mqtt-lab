import can
import requests
import json
import paho.mqtt.client as mqtt
import time
import os
from datetime import datetime
import signal
import sys
from pathlib import Path

# ==== Configurations ====
API_URL = "http://api:5000/api/data"
MQTT_BROKER = "mqtt-broker"  # Use "localhost" if not running in Docker
MQTT_PORT = 1883
MQTT_TOPIC = "can/messages"
LOG_DIR = Path("logs")
JSON_LOG_FILE = LOG_DIR / "can_log.jsonl"
CSV_LOG_FILE = LOG_DIR / "can_log.csv"

# ==== Prepare log directory ====
LOG_DIR.mkdir(parents=True, exist_ok=True)

# ==== MQTT Status Flag ====
mqtt_connected = False

# ==== Setup MQTT ====
mqtt_client = mqtt.Client()

def on_connect(client, userdata, flags, rc):
    global mqtt_connected
    mqtt_connected = (rc == 0)
    print("✅ MQTT connected successfully." if mqtt_connected else f"❌ MQTT connect failed: {rc}")

def on_disconnect(client, userdata, rc):
    global mqtt_connected
    mqtt_connected = False
    print("🔌 MQTT disconnected.")

mqtt_client.on_connect = on_connect
mqtt_client.on_disconnect = on_disconnect
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
mqtt_client.loop_start()

# ==== Setup CAN interface ====
bus = can.interface.Bus(channel='vcan0', interface='socketcan')

print("🚀 CAN reader started. Sending to API, MQTT, and logging...")

# ==== Graceful exit handler ====
def shutdown(signum, frame):
    print("\n🛑 Shutting down gracefully...")
    mqtt_client.loop_stop()
    mqtt_client.disconnect()
    sys.exit(0)

signal.signal(signal.SIGINT, shutdown)
signal.signal(signal.SIGTERM, shutdown)

# ==== Logging Helpers ====
def log_to_jsonl(data):
    try:
        with open(JSON_LOG_FILE, "a") as f:
            f.write(json.dumps(data) + "\n")
    except Exception as e:
        print(f"⚠️ JSON log error: {e}")

def log_to_csv(msg):
    try:
        write_header = not CSV_LOG_FILE.exists()
        with open(CSV_LOG_FILE, "a", newline='') as f:
            import csv
            writer = csv.writer(f)
            if write_header:
                writer.writerow(["timestamp", "can_id", "is_extended", "payload"])
            writer.writerow([msg["timestamp"], msg["id"], msg["extended"], ",".join(map(str, msg["payload"]))])
    except Exception as e:
        print(f"⚠️ CSV log error: {e}")

# ==== Main Loop ====
while True:
    msg = bus.recv()
    if msg is None:
        continue

    timestamp = datetime.utcnow().isoformat()
    payload = list(msg.data)
    can_id = hex(msg.arbitration_id)

    post_data = {
        "id": can_id,
        "payload": payload,
        "timestamp": timestamp,
        "extended": msg.is_extended_id
    }

    # Send to API
    try:
        requests.post(API_URL, json=post_data, timeout=1)
        print(f"📡 API: {post_data}")
    except Exception as e:
        print(f"❌ API error: {e}")

    # Send to MQTT
    try:
        mqtt_client.publish(MQTT_TOPIC, json.dumps(post_data))
        print(f"📬 MQTT: {post_data}")
    except Exception as e:
        print(f"❌ MQTT error: {e}")

    # Log to files
    log_to_jsonl(post_data)
    log_to_csv(post_data)
