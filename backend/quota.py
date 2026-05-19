"""Simple per-key daily quota tracker (in-memory).

Note: In production use Redis or another persistent store for atomic counters.
"""
import os
import threading
import datetime

PER_KEY_CERTS_PER_DAY = int(os.environ.get("PER_KEY_CERTS_PER_DAY", "10000"))

# keys: (api_key, date_str) -> int
_COUNTERS = {}
_LOCK = threading.Lock()


def _today():
    return datetime.date.today().isoformat()


def reserve(api_key: str, n: int) -> bool:
    """Attempt to reserve `n` certificates for `api_key` for today.
    Returns True if reserved, False if quota would be exceeded.
    """
    if not api_key:
        return True
    if PER_KEY_CERTS_PER_DAY <= 0:
        return True
    key = (api_key, _today())
    with _LOCK:
        current = _COUNTERS.get(key, 0)
        if current + n > PER_KEY_CERTS_PER_DAY:
            return False
        _COUNTERS[key] = current + n
        return True


def release(api_key: str, n: int) -> None:
    """Release previously reserved `n` certificates (on failure)."""
    if not api_key:
        return
    key = (api_key, _today())
    with _LOCK:
        current = _COUNTERS.get(key, 0)
        new = max(0, current - n)
        _COUNTERS[key] = new


def get_usage(api_key: str) -> int:
    if not api_key:
        return 0
    return _COUNTERS.get((api_key, _today()), 0)
