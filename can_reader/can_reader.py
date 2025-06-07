import can
import requests

bus = can.interface.Bus(channel='vcan0', interface='socketcan')

while True:
    msg = bus.recv()
    if msg is not None:
        payload = list(msg.data)
        post_data = {"id": hex(msg.arbitration_id), "payload": payload}
        try:
            # Använd rätt adress för ditt API!
            requests.post("http://localhost:5000/api/data", json=post_data)
            print(f"Sent to API: {post_data}")
        except Exception as e:
            print("Failed to post to API:", e)
