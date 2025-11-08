from __future__ import annotations

import hashlib
import hmac
import time
from typing import Dict

from fastapi import HTTPException, Request, status

from ..core.config import get_settings

settings = get_settings()


def _hash_key(key: str) -> str:
    return hmac.new(key.encode(), msg=b"movie-autotranslate", digestmod=hashlib.sha256).hexdigest()


RATE_LIMIT_WINDOW = 60  # seconds
request_counters: Dict[str, Dict[str, int]] = {}


def _check_rate_limit(client_id: str) -> None:
    window = int(time.time() // RATE_LIMIT_WINDOW)
    window_key = f"{client_id}:{window}"
    record = request_counters.setdefault(window_key, {"count": 0})
    record["count"] += 1
    if record["count"] > settings.rate_limit_per_minute:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded")


def require_api_key(request: Request) -> str:
    header_name = settings.api_key_header
    api_key = request.headers.get(header_name)
    if not settings.api_keys:
        request.state.client_id = "anonymous"
        return "anonymous"
    if not api_key or api_key not in settings.api_keys:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    client_id = _hash_key(api_key)
    _check_rate_limit(client_id)
    request.state.client_id = client_id
    return client_id
