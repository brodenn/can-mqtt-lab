from collections import defaultdict, deque
import time

MAX_HISTORY = 10

# Dictionary to store CAN ID → deque of recent messages
_data_store = defaultdict(lambda: deque(maxlen=MAX_HISTORY))

def update_data(can_id, payload):
    """
    Add a new CAN message to the store with timestamp.
    
    Args:
        can_id (str): CAN ID as hex string (e.g., "0x123")
        payload (list[int]): List of 0-255 integers representing message data
    """
    _data_store[can_id].append({
        'timestamp': time.time(),
        'payload': payload
    })

def get_data():
    """
    Return the entire CAN data store as a serializable dictionary.
    
    Returns:
        dict: { "0x123": [ {timestamp, payload}, ... ], ... }
    """
    return {can_id: list(messages) for can_id, messages in _data_store.items()}
