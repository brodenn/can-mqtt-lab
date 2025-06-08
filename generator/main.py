import os
import random
import time
import json
import socket
import can
import paho.mqtt.client as mqtt
from paho.mqtt.client import CallbackAPIVersion

# === Config ===
MQTT_BROKER = os.getenv("MQTT_BROKER", "mqtt-broker")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
CAN_INTERFACE = os.getenv("CAN_INTERFACE", "socketcan")
CAN_CHANNEL = os.getenv("CAN_CHANNEL", "vcan0")
USE_CAN = True  # Will auto-disable if vcan0 not available

# === MQTT Setup ===
mqtt_client = mqtt.Client(
    protocol=mqtt.MQTTv5,
    callback_api_version=CallbackAPIVersion.VERSION2
)

while True:
    try:
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT)
        mqtt_client.loop_start()
        print(f"✅ Connected to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
        break
    except socket.error as e:
        print(f"⏳ MQTT connection failed: {e}. Retrying in 2s...")
        time.sleep(2)

# === CAN Setup ===
bus = None
try:
    bus = can.interface.Bus(channel=CAN_CHANNEL, interface=CAN_INTERFACE)
    print(f"🎯 Using CAN interface {CAN_CHANNEL} ({CAN_INTERFACE})")
except Exception as e:
    print(f"⚠️  CAN unavailable ({e}) — continuing with MQTT only")
    USE_CAN = False

# === Bus Stops: (Name, Latitude, Longitude) ===
stops = [
    ("Central",   57.7072, 11.9668),
    ("Gullmars",  57.6890, 11.9820),
    ("Frölunda",  57.6520, 11.9110),
    ("Liseberg",  57.6960, 11.9865),
    ("Backaplan", 57.7235, 11.9511)
]

# === State ===
stop_index = 0
passenger_count = 20
speed = 0
lat, lon = stops[0][1], stops[0][2]
at_stop_counter = 0
approaching_stop = False

# === CAN + MQTT Sender ===
def send_can_and_mqtt(can_id, payload, debug_label=None):
    payload = (payload + [0] * 16)[:16]  # Support extended UTF-8 strings

    if USE_CAN and bus:
        try:
            msg = can.Message(arbitration_id=can_id, data=payload[:8], is_extended_id=False)
            bus.send(msg)
            print(f"🚌 CAN {hex(can_id)} → {payload[:8]}" + (f" | {debug_label}" if debug_label else ""))
        except can.CanError as e:
            print("❌ CAN send error:", e)

    try:
        mqtt_payload = {
            "id": hex(can_id),
            "payload": payload,
            "timestamp": time.time(),
            "extended": False
        }
        mqtt_client.publish("can/messages", json.dumps(mqtt_payload))
        if not USE_CAN:
            print(f"📡 MQTT: {hex(can_id)} → {payload}" + (f" | {debug_label}" if debug_label else ""))
    except Exception as e:
        print("❌ MQTT publish error:", e)

# === Main Simulation Loop ===
def main():
    global stop_index, speed, passenger_count, lat, lon, at_stop_counter, approaching_stop

    while True:
        current_stop = stops[stop_index % len(stops)]
        next_stop = stops[(stop_index + 1) % len(stops)]

        if approaching_stop:
            speed = max(0, speed - random.randint(5, 15))
            if speed == 0:
                at_stop_counter += 1
        else:
            speed = min(50, speed + random.randint(0, 5))

        # 0x100: GPS
        lat += (next_stop[1] - lat) * 0.05
        lon += (next_stop[2] - lon) * 0.05
        lat_bytes = int(lat * 1_000_000).to_bytes(4, 'big', signed=True)
        lon_bytes = int(lon * 1_000_000).to_bytes(4, 'big', signed=True)
        send_can_and_mqtt(0x100, list(lat_bytes + lon_bytes), "GPS")

        # 0x101: Doors
        doors = [1, 1, 0] if speed < 3 else [0, 0, 0]
        send_can_and_mqtt(0x101, doors, "Doors")

        # 0x102: Passengers
        if speed == 0 and any(doors):
            passenger_count = max(0, passenger_count + random.randint(-3, 5))
        send_can_and_mqtt(0x102, [passenger_count], "Passengers")

        # 0x103: Next Stop (UTF-8 padded to 16 bytes)
        stop_name = next_stop[0]
        stop_payload = list(stop_name.encode("utf-8").ljust(16, b'\x00'))
        send_can_and_mqtt(0x103, stop_payload, f"NextStop='{stop_name}'")

        # 0x104: Speed
        send_can_and_mqtt(0x104, [speed], "Speed")

        # 0x105: Emergency brake
        emergency = 1 if random.random() < 0.01 else 0
        send_can_and_mqtt(0x105, [emergency], "Emergency Brake" if emergency else None)

        # 0x106: Stop request
        stop_request = 1 if random.random() < 0.1 else 0
        send_can_and_mqtt(0x106, [stop_request], "Stop Request" if stop_request else None)

        # 0x107: Delay (signed byte)
        delay = random.choice([-2, -1, 0, 1, 2, 3, 5])
        send_can_and_mqtt(0x107, [delay & 0xFF], f"Delay {delay:+}min")

        # 0x108: Temperature
        temp = int(random.uniform(10.0, 35.0) * 10)
        send_can_and_mqtt(0x108, [temp >> 8, temp & 0xFF], f"Temp {temp/10:.1f}°C")

        # 0x109: Fuel
        fuel = random.randint(20, 100)
        send_can_and_mqtt(0x109, [fuel], f"Fuel {fuel}%")

        # === Stop Logic ===
        if at_stop_counter > 3:
            at_stop_counter = 0
            stop_index += 1
            lat, lon = next_stop[1], next_stop[2]
            approaching_stop = False
        elif abs(lat - next_stop[1]) < 0.0005 and abs(lon - next_stop[2]) < 0.0005:
            approaching_stop = True

        time.sleep(1)

if __name__ == "__main__":
    main()
