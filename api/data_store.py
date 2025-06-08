from collections import defaultdict, deque
import time

# Max number of messages to keep per CAN ID
MAX_HISTORY = 10

# Internal data store: CAN ID → deque of messages
_data_store = defaultdict(lambda: deque(maxlen=MAX_HISTORY))

def update_data(can_id, payload, timestamp=None, extended=False):
    """
    Store a new CAN message.

    Args:
        can_id (str): CAN ID as hex string (e.g., "0x123")
        payload (list[int]): List of 0–255 integers (CAN data bytes)
        timestamp (float|str|None): Unix timestamp or ISO string (optional)
        extended (bool): Whether the frame is extended
    """
    if timestamp is None:
        timestamp = time.time()
    _data_store[can_id].append({
        'timestamp': timestamp,
        'payload': payload,
        'extended': extended
    })

def get_data():
    """
    Get the full message history for all CAN IDs.

    Returns:
        dict: {
            "0x123": [
                { "timestamp": ..., "payload": [...], "extended": False },
                ...
            ],
            ...
        }
    """
    return {can_id: list(messages) for can_id, messages in _data_store.items()}

def get_latest_per_id():
    """
    Get only the most recent message per CAN ID.

    Returns:
        dict: {
            "0x123": { "timestamp": ..., "payload": [...], "extended": False },
            ...
        }
    """
    return {
        can_id: messages[-1]
        for can_id, messages in _data_store.items()
        if messages
    }

def clear_all():
    """
    Clear all CAN data (useful for testing/reset).
    """
    _data_store.clear()
