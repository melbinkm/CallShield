"""API key authentication for CallShield Developer API.

Design invariant: when no api_keys.json exists, all endpoints remain open
(dev mode). Auth only activates after generating a key via
scripts/generate_api_key.py.
"""

import json
import logging
import os
from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader
from typing import Optional

logger = logging.getLogger(__name__)

API_KEYS_FILE = os.path.join(os.path.dirname(__file__), "api_keys.json")

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def _load_keys() -> dict:
    """Read api_keys.json, returning {} if missing, empty, or malformed."""
    try:
        with open(API_KEYS_FILE) as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
        return {}
    except (FileNotFoundError, json.JSONDecodeError, OSError) as e:
        if not isinstance(e, FileNotFoundError):
            logger.warning("Could not load %s: %s", API_KEYS_FILE, e)
        return {}


def is_auth_enabled() -> bool:
    """True when at least one API key is configured."""
    return len(_load_keys()) > 0


def verify_api_key(key: str) -> bool:
    """Check that key exists and is active."""
    keys = _load_keys()
    entry = keys.get(key)
    if entry is None:
        return False
    return entry.get("active", False)


async def require_api_key(api_key: Optional[str] = Security(_api_key_header)):
    """FastAPI dependency for API key authentication.

    - No keys configured → open access (returns None)
    - Keys configured, none provided → HTTP 401
    - Invalid or inactive key → HTTP 403
    """
    if not is_auth_enabled():
        return None

    if not api_key:
        raise HTTPException(
            status_code=401,
            detail={"error": "missing_api_key", "detail": "X-API-Key header required."},
        )

    if not verify_api_key(api_key):
        raise HTTPException(
            status_code=403,
            detail={"error": "invalid_api_key", "detail": "Invalid or inactive API key."},
        )

    return api_key


def verify_ws_api_key(key) -> bool:
    """WebSocket auth: returns True if auth disabled or key is valid."""
    if not is_auth_enabled():
        return True
    if not key:
        return False
    return verify_api_key(key)
