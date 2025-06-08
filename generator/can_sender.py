import os
import can
import json
import time
import random
import paho.mqtt.client as mqtt

# === Configuration ===
CAN_CHANNEL = os.getenv("CAN_CHANNEL", "vcan0")
CAN_INTERFACE = os.getenv("CAN_INTERFACE", "socketcan")
MQTT_BROKER = os.getenv("MQTT_BROKER", "mqtt-broker")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_TOPIC = "can/messages"
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# === Simulated Stops (Name, Latitude, Longitude) ===
stops = [
    ("Central",   57.7072, 11.9668),
    ("Gullmars",  57.6890, 11.9820),
    ("Frölunda",  57.6520, 11.9110),
    ("Liseberg",  57.6960, 11.9865),
    ("Backaplan", 57.7235, 11.9511)
]

# === State Variables ===
stop_index = 0
passenger_count = 20
speed = 0
lat, lon = stops[0][1], stops[0][2]
at_stop_counter = 0
approaching_stop = False

# === MQTT Setup ===
mqtt_client = mqtt.Client()
while True:
    try:
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT)
        mqtt_client.loop_start()
        print(f"✅ Connected to MQTT at {MQTT_BROKER}:{MQTT_PORT}")
        break
    except Exception as e:
        print(f"❌ MQTT connect error: {e} — retrying in 2s")
        time.sleep(2)

# === CAN Bus Setup ===
try:
    bus = can.interface.Bus(channel=CAN_CHANNEL, interface=CAN_INTERFACE)
    print(f"🚍 Generator using {CAN_CHANNEL} ({CAN_INTERFACE})")
except can.CanError as e:
    print(f"❌ CAN bus error: {e}")
    exit(1)

# === Send Function ===
def send_can_and_mqtt(can_id, payload, label=None):
    payload = (payload + [0] * 16)[:16]  # Allow for long UTF-8 strings
    msg = can.Message(arbitration_id=can_id, data=payload[:8], is_extended_id=False)
    try:
        bus.send(msg)
        mqtt_payload = {
            "id": hex(can_id),
            "payload": payload,
            "timestamp": time.time(),
            "extended": False
        }
        mqtt_client.publish(MQTT_TOPIC, json.dumps(mqtt_payload))
        if DEBUG or label:
            print(f"📤 {hex(can_id)} → {payload[:8]} {f'| {label}' if label else ''}")
    except can.CanError as e:
        print(f"❌ CAN send failed: {e}")

# === Simulation Loop ===
while True:
    current = stops[stop_index % len(stops)]
    next_stop = stops[(stop_index + 1) % len(stops)]

    # Speed logic
    if approaching_stop:
        speed = max(0, speed - random.randint(5, 15))
        if speed == 0:
            at_stop_counter += 1
    else:
        speed = min(50, speed + random.randint(0, 5))

    # 0x100: GPS (lat/lon in 4 bytes total)
    lat += (next_stop[1] - lat) * 0.05
    lon += (next_stop[2] - lon) * 0.05
    lat_bytes = int(lat * 10_000).to_bytes(2, 'big')
    lon_bytes = int(lon * 10_000).to_bytes(2, 'big')
    send_can_and_mqtt(0x100, list(lat_bytes + lon_bytes), "GPS")

    # 0x101: Door status
    doors = [1, 1, 0] if speed < 3 else [0, 0, 0]
    send_can_and_mqtt(0x101, doors, "Doors")

    # 0x102: Passenger count
    if speed == 0 and any(doors):
        passenger_count = max(0, passenger_count + random.randint(-3, 5))
    send_can_and_mqtt(0x102, [passenger_count], "Passengers")

    # 0x103: Stop name (UTF-8 padded to 16 bytes)
    stop_name = next_stop[0]
    padded = list(stop_name.encode("utf-8").ljust(16, b'\x00'))
    send_can_and_mqtt(0x103, padded, f"Next='{stop_name}'")

    # 0x104: Speed
    send_can_and_mqtt(0x104, [speed], "Speed")

    # 0x105: Brake status
    brake = 1 if speed > 30 and random.random() < 0.01 else 0
    send_can_and_mqtt(0x105, [brake], "Brake" if brake else None)

    # 0x106: Stop request
    stop_req = 1 if random.random() < 0.05 else 0
    send_can_and_mqtt(0x106, [stop_req], "Stop Req" if stop_req else None)

    # 0x107: Delay (signed byte)
    delay = random.randint(-5, 5) & 0xFF
    send_can_and_mqtt(0x107, [delay], f"Delay {delay-256 if delay > 127 else delay:+}min")

    # 0x108: Temperature (0.1°C units)
    temp = int(random.uniform(20.0, 25.0) * 10)
    send_can_and_mqtt(0x108, list(temp.to_bytes(2, 'big')), f"Temp {temp/10:.1f}°C")

    # 0x109: Fuel %
    fuel = random.randint(30, 100)
    send_can_and_mqtt(0x109, [fuel], f"Fuel {fuel}%")

    # === Stop logic ===
    if at_stop_counter > 3:
        at_stop_counter = 0
        stop_index += 1
        lat, lon = next_stop[1], next_stop[2]
        approaching_stop = False
    elif abs(lat - next_stop[1]) < 0.0005 and abs(lon - next_stop[2]) < 0.0005:
        approaching_stop = True

    time.sleep(1)
