"""Simple API key helpers.

Public certificate routes are intentionally left unauthenticated so the
browser never needs to carry a secret. API keys remain available for
server-side-only checks such as metrics or future admin endpoints.
"""
import os
from typing import Set

from fastapi import Request, HTTPException


def _load_keys() -> Set[str]:
    raw = os.environ.get("API_KEYS") or os.environ.get("API_KEY") or ""
    return set(k.strip() for k in raw.split(",") if k.strip())


def is_protected_path(path: str) -> bool:
    # The public frontend calls certificate generation endpoints directly.
    # Keep this as False so no browser client needs to ship a secret key.
    return False


async def verify_api_key(request: Request):
    """Verify X-API-Key for protected paths.

    This is currently a no-op for public routes.
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
