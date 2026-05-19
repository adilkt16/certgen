"""Simple API key middleware and helpers."""
import os
from typing import Set

from fastapi import Request, HTTPException


def _load_keys() -> Set[str]:
    raw = os.environ.get("API_KEYS") or os.environ.get("API_KEY") or ""
    return set(k.strip() for k in raw.split(",") if k.strip())


API_KEYS = _load_keys()


def is_protected_path(path: str) -> bool:
    # Protect API routes under /api/ but allow health
    if path == "/health":
        return False
    return path.startswith("/api")


async def verify_api_key(request: Request):
    if not is_protected_path(request.url.path):
        return
    if not API_KEYS:
        # No keys configured => behave permissively (dev mode)
        return
    key = request.headers.get("X-API-Key")
    if not key or key not in API_KEYS:
        raise HTTPException(status_code=401, detail={"error": "Unauthorized", "code": "INVALID_API_KEY"})
