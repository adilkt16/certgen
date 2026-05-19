"""Rate limiter configuration for slowapi.

Key function: prefer API key when present, otherwise use a safe
IP-derived identifier. By default the code does NOT trust
client-supplied forwarding headers (X-Forwarded-For). If the
environment enables `USE_PROXY_HEADERS=true` the first X-Forwarded-For
entry will be used (only when operators explicitly opt in).
"""

import os
from slowapi import Limiter


def _get_socket_ip(request):
	client = getattr(request, "client", None)
	if client:
		host = getattr(client, "host", None)
		if host:
			return host
	return None


# Controlled by env var; default is safe (do not trust proxy headers).
USE_PROXY = os.environ.get("USE_PROXY_HEADERS", "").lower() in ("1", "true", "yes")


def key_func(request):
	# Prefer API key for per-key limits
	try:
		key = request.headers.get("X-API-Key")
		if key:
			return f"api_key:{key}"
	except Exception:
		pass

	# If proxy headers are explicitly enabled, honor X-Forwarded-For
	if USE_PROXY:
		try:
			xff = request.headers.get("X-Forwarded-For") or request.headers.get("x-forwarded-for")
			if xff:
				first = xff.split(",")[0].strip()
				if first:
					return f"ip:{first}"
		except Exception:
			pass

	# Default: use the socket-level client IP (not client-sent headers)
	sock = _get_socket_ip(request)
	if sock:
		return f"ip:{sock}"

	# Fallback
	return "ip:unknown"


# Create limiter instance (separate from main.py to avoid circular imports)
limiter = Limiter(key_func=key_func)
