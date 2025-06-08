from collections import defaultdict, deque
from typing import Dict, List, Union, Optional, Any
import os
import time

# === Configuration ===
DEFAULT_HISTORY = 10
MAX_HISTORY = int(os.getenv("CAN_HISTORY_LENGTH", DEFAULT_HISTORY))

# === Internal Data Store ===
_data_store: Dict[str, deque] = defaultdict(lambda: deque(maxlen=MAX_HISTORY))


def normalize_can_id(can_id: Union[str, int]) -> str:
    """
    Normalize the CAN ID to a consistent lowercase hex string (e.g., "0x123").

    Accepts either a string like "0x123" or an int (e.g., 291).
    """
    try:
        return hex(int(can_id, 16) if isinstance(can_id, str) else can_id).lower()
    except (ValueError, TypeError):
        return "0x0"


def update_data(
    can_id: Union[str, int],
    payload: List[int],
    timestamp: Optional[Union[float, str]] = None,
    extended: bool = False,
    source: Optional[str] = None
) -> None:
    """
    Store a new CAN message into the buffer for a given CAN ID.

    Args:
        can_id: The CAN ID (e.g., "0x123" or 0x123).
        payload: List of CAN data bytes (integers 0–255).
        timestamp: Optional UNIX timestamp. Defaults to now.
        extended: True if using extended 29-bit ID.
        source: Optional source label (e.g. "MQTT", "HTTP", etc.)
    """
    try:
        if timestamp is None:
            timestamp = time.time()
        else:
            timestamp = float(timestamp)
    except Exception:
        timestamp = time.time()

    can_id_str = normalize_can_id(can_id)

    _data_store[can_id_str].append({
        'timestamp': timestamp,
        'payload': payload,
        'extended': extended,
        'source': source or "unknown"
    })


def get_data() -> Dict[str, List[Dict[str, Any]]]:
    """
    Get the full message history for all CAN IDs.

    Returns:
        Dict of CAN ID → list of message dicts.
    """
    return {can_id: list(messages) for can_id, messages in _data_store.items()}


def get_latest_per_id() -> Dict[str, Dict[str, Any]]:
    """
    Get the most recent message for each CAN ID.

    Returns:
        Dict of CAN ID → latest message dict.
    """
    return {
        can_id: messages[-1]
        for can_id, messages in _data_store.items()
        if messages
    }


def get_messages_for_id(can_id: Union[str, int]) -> List[Dict[str, Any]]:
    """
    Get message history for a specific CAN ID.

    Args:
        can_id: The CAN ID to query.
    Returns:
        List of messages or empty list.
    """
    return list(_data_store.get(normalize_can_id(can_id), []))


def clear_all() -> None:
    """Clear all stored CAN data. Useful for resets or testing."""
    _data_store.clear()
