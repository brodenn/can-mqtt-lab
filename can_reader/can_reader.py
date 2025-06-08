import os
import sys
import json
import csv
import time
import signal
import socket
import requests
import can
import paho.mqtt.client as mqtt
from datetime import datetime
from pathlib import Path

# ==== Configuration ====
API_URL = os.getenv("API_URL", "http://localhost:5000/api/data")
MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "can/messages")
CAN_CHANNEL = os.getenv("CAN_CHANNEL", "vcan0")
CAN_INTERFACE = os.getenv("CAN_INTERFACE", "socketcan")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

LOG_DIR = Path("logs")
JSON_LOG_FILE = LOG_DIR / "can_log.jsonl"
CSV_LOG_FILE = LOG_DIR / "can_log.csv"

# ==== Prepare log directory ====
LOG_DIR.mkdir(parents=True, exist_ok=True)

# ==== MQTT Setup ====
mqtt_connected = False
mqtt_client = mqtt.Client(protocol=mqtt.MQTTv311)

def on_connect(client, userdata, flags, rc):
    global mqtt_connected
    mqtt_connected = (rc == 0)
    print("✅ MQTT connected." if mqtt_connected else f"❌ MQTT connect failed: {rc}")

def on_disconnect(client, userdata, rc):
    global mqtt_connected
    mqtt_connected = False
    print("🔌 MQTT disconnected.")

mqtt_client.on_connect = on_connect
mqtt_client.on_disconnect = on_disconnect

# Retry MQTT connect
while not mqtt_connected:
    try:
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        mqtt_client.loop_start()
        print(f"⏳ Connecting to MQTT at {MQTT_BROKER}:{MQTT_PORT}...")
        time.sleep(2)
    except socket.error as e:
        print(f"❌ MQTT connection failed: {e}. Retrying in 2s...")
        time.sleep(2)

# ==== CAN Setup ====
try:
    bus = can.interface.Bus(channel=CAN_CHANNEL, interface=CAN_INTERFACE)
    print(f"🚍 CAN Reader started on {CAN_CHANNEL} ({CAN_INTERFACE})")
except can.CanError as e:
    print(f"❌ CAN bus error: {e}")
    sys.exit(1)

# ==== Graceful Shutdown ====
def shutdown(signum, frame):
    print("\n🛑 Shutting down...")
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

def log_to_csv(data):
    try:
        write_header = not CSV_LOG_FILE.exists()
        with open(CSV_LOG_FILE, "a", newline='') as f:
            writer = csv.writer(f)
            if write_header:
                writer.writerow(["timestamp", "can_id", "is_extended", "payload"])
            writer.writerow([
                data["timestamp"],
                data["id"],
                data["extended"],
                ",".join(map(str, data["payload"]))
            ])
    except Exception as e:
        print(f"⚠️ CSV log error: {e}")

# ==== Main Loop ====
def main():
    while True:
        try:
            msg = bus.recv()
            if msg is None:
                continue

            timestamp = datetime.utcnow().isoformat()
            can_id = hex(msg.arbitration_id)
            payload = list(msg.data)

            post_data = {
                "id": can_id,
                "payload": payload,
                "timestamp": timestamp,
                "extended": msg.is_extended_id
            }

            # Send to API
            try:
                requests.post(API_URL, json=post_data, timeout=1)
                if DEBUG:
                    print(f"📡 Sent to API: {post_data}")
            except Exception as e:
                print(f"❌ API error: {e}")

            # Publish to MQTT
            try:
                mqtt_client.publish(MQTT_TOPIC, json.dumps(post_data))
                if DEBUG:
                    print(f"📬 Published to MQTT: {post_data}")
            except Exception as e:
                print(f"❌ MQTT publish error: {e}")

            # Log to files
            log_to_jsonl(post_data)
            log_to_csv(post_data)

        except KeyboardInterrupt:
            shutdown(None, None)
        except Exception as e:
            print(f"⚠️ Runtime error: {e}")
            time.sleep(0.5)

if __name__ == "__main__":
    main()
