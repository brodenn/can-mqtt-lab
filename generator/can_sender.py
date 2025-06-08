import can
import random
import time
import json
import paho.mqtt.client as mqtt

# === MQTT Setup ===
mqtt_client = mqtt.Client()
mqtt_client.connect("mqtt-broker", 1883)
mqtt_client.loop_start()

# === CAN Setup ===
bus = can.interface.Bus(channel='vcan0', interface='socketcan')

# === Simulated State ===
stops = ["Central", "Gullmars", "Frölunda", "Liseberg", "Backaplan"]
passenger_count = 20
stop_index = 0
speed = 0

def send_can_and_mqtt(can_id, payload):
    try:
        # Always 8 bytes for CAN
        payload = (payload + [0] * 8)[:8]
        msg = can.Message(arbitration_id=can_id, data=payload, is_extended_id=False)
        bus.send(msg)
        print(f"🚌 Sent CAN: ID={hex(can_id)}, Data={payload}")
        mqtt_payload = {
            "id": hex(can_id),
            "payload": payload
        }
        mqtt_client.publish("can/messages", json.dumps(mqtt_payload))
    except can.CanError as e:
        print("❌ CAN send error:", e)

while True:
    # 0x100 – GPS (lat/lon, two bytes each, padded to 8)
    lat = 57 + random.random()    # ~57.xxx
    lon = 11 + random.random()    # ~11.xxx
    lat_bytes = int(lat * 10000).to_bytes(2, 'big')
    lon_bytes = int(lon * 10000).to_bytes(2, 'big')
    gps_payload = list(lat_bytes + lon_bytes)  # 4 bytes
    send_can_and_mqtt(0x100, gps_payload)      # Function pads to 8 bytes

    # 0x101 – Door status (front, mid, rear: 0=closed, 1=open)
    doors = [random.randint(0, 1) for _ in range(3)]
    send_can_and_mqtt(0x101, doors)

    # 0x102 – Passenger count (byte 0)
    passenger_count = max(0, passenger_count + random.randint(-2, 3))
    send_can_and_mqtt(0x102, [passenger_count])

    # 0x103 – Next stop (ASCII, up to 8 chars)
    stop_name = stops[stop_index % len(stops)]
    stop_index += 1
    stop_payload = [ord(c) for c in stop_name[:8]]
    send_can_and_mqtt(0x103, stop_payload)

    # 0x104 – Speed (km/h, byte 0)
    speed = max(0, min(80, speed + random.randint(-5, 5)))
    send_can_and_mqtt(0x104, [speed])

    # Change update rate here!
    time.sleep(1)
