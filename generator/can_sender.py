import can
import random
import time

bus = can.interface.Bus(channel='vcan0', bustype='socketcan')

while True:
    can_id = 0x123
    data = [random.randint(0, 255) for _ in range(8)]
    msg = can.Message(arbitration_id=can_id, data=data, is_extended_id=False)
    try:
        bus.send(msg)
        print(f"Sent: ID={hex(can_id)}, Data={data}")
    except can.CanError as e:
        print("Failed to send:", e)
    time.sleep(1)
