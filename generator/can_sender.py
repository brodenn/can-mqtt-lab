import can
import random
import time
import json
import paho.mqtt.client as mqtt

# MQTT setup
mqtt_client = mqtt.Client()
mqtt_client.connect("mqtt-broker", 1883)  # Container name from docker-compose

# CAN setup
bus = can.interface.Bus(channel='vcan0', interface='socketcan')  # use 'interface', not 'bustype'

while True:
    can_id = 0x123
    data = [random.randint(0, 255) for _ in range(8)]
    msg = can.Message(arbitration_id=can_id, data=data, is_extended_id=False)

    try:
        # Send to virtual CAN bus
        bus.send(msg)
        print(f"Sent: ID={hex(can_id)}, Data={data}")

        # Send to MQTT broker
        mqtt_payload = {
            "id": hex(can_id),
            "payload": data
        }
        mqtt_client.publish("canbus/data", json.dumps(mqtt_payload))
    except can.CanError as e:
        print("Failed to send CAN message:", e)

    time.sleep(1)
