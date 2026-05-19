"""Rate limiter configuration for slowapi.

Key function: prefer API key when present, otherwise fall back to remote address.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address


def key_func(request):
	# Attempt to use X-API-Key for per-key limits; fall back to remote IP
	try:
		key = request.headers.get("X-API-Key")
		if key:
			return f"api_key:{key}"
	except Exception:
		pass
	return get_remote_address(request)


# Create limiter instance (separate from main.py to avoid circular imports)
limiter = Limiter(key_func=key_func)
