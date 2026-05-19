"""Simple API key middleware and helpers.

Behavior (hybrid):
- In development (default) an empty `API_KEYS` env lets the app run permissively.
- In production set `ENV=production` or `REQUIRE_API_KEYS=true` to require `API_KEYS`.

This module reads keys per-request so changes to the environment take effect
without restarting the process (useful for staged rollouts).
"""
import os
from typing import Set

from fastapi import Request, HTTPException


def _load_keys() -> Set[str]:
    raw = os.environ.get("API_KEYS") or os.environ.get("API_KEY") or ""
    return set(k.strip() for k in raw.split(",") if k.strip())


def is_protected_path(path: str) -> bool:
    # Protect API routes under /api/ but allow health
    if path == "/health":
        return False
    return path.startswith("/api")


async def verify_api_key(request: Request):
    """Verify X-API-Key for protected paths.

    If `REQUIRE_API_KEYS=true` or `ENV=production` and no keys are configured,
    requests will be rejected. Otherwise an empty key set behaves permissively
    to preserve developer ergonomics.
    """
    if not is_protected_path(request.url.path):
        return

    keys = _load_keys()

    require_keys = os.environ.get("REQUIRE_API_KEYS", "").lower() in ("1", "true", "yes")
    require_keys = require_keys or (os.environ.get("ENV", "").lower() == "production")

    if not keys:
        # No keys configured
        if require_keys:
            # In production / when explicitly required, reject requests
            raise HTTPException(status_code=401, detail={"error": "Unauthorized", "code": "INVALID_API_KEY"})
        # Dev-mode permissive fallback
        return

    key = request.headers.get("X-API-Key")
    if not key or key not in keys:
        raise HTTPException(status_code=401, detail={"error": "Unauthorized", "code": "INVALID_API_KEY"})
