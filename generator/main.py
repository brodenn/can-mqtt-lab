import time, random, requests

while True:
    fake_data = {
        "id": hex(random.randint(0x100, 0x1FF)),
        "payload": [random.randint(0, 255) for _ in range(8)]
    }
    try:
        requests.post("http://api:5000/api/data", json=fake_data)
    except Exception as e:
        print("API offline:", e)
    time.sleep(1)
