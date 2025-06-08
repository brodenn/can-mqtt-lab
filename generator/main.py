import time
import random
import requests

CAN_IDS = [0x100, 0x101, 0x102, 0x103, 0x104]  # Example fixed IDs

try:
    while True:
        can_id = random.choice(CAN_IDS)  # use a random ID from your simulated bus
        fake_data = {
            "id": hex(can_id),
            "payload": [random.randint(0, 255) for _ in range(8)],
            "timestamp": time.time(),
        }
        try:
            r = requests.post("http://api:5000/api/data", json=fake_data)
            print("Sent:", fake_data, "Status:", r.status_code)
        except Exception as e:
            print("API offline:", e)
        time.sleep(1)
except KeyboardInterrupt:
    print("\nStopped.")
