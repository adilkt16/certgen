"""Rate limiter configuration for slowapi."""

from slowapi import Limiter
from slowapi.util import get_remote_address

# Create limiter instance (separate from main.py to avoid circular imports)
limiter = Limiter(key_func=get_remote_address)
