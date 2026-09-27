import time
from typing import Any

import requests

from src.config import (
    DEFAULT_RETRIES,
    DEFAULT_TIMEOUT,
    IFOOD_AUTH_URL,
    IFOOD_CLIENT_ID,
    IFOOD_CLIENT_SECRET,
)

_TOKEN_CACHE: dict[str, Any] = {
    "access_token": None,
    "expires_at": 0.0,
}

_REFRESH_BUFFER_SEC = 120


def get_access_token(*, force_refresh: bool = False) -> str:
    if not IFOOD_CLIENT_ID or not IFOOD_CLIENT_SECRET:
        raise ValueError("IFOOD_CLIENT_ID and IFOOD_CLIENT_SECRET must be set")

    now = time.time()
    cached = _TOKEN_CACHE.get("access_token")
    expires_at = float(_TOKEN_CACHE.get("expires_at") or 0)
    if cached and not force_refresh and now < expires_at - _REFRESH_BUFFER_SEC:
        return cached

    last_exc: Exception | None = None
    for attempt in range(1, DEFAULT_RETRIES + 1):
        try:
            response = requests.post(
                IFOOD_AUTH_URL,
                data={
                    "clientId": IFOOD_CLIENT_ID,
                    "clientSecret": IFOOD_CLIENT_SECRET,
                    "grantType": "client_credentials",
                },
                timeout=DEFAULT_TIMEOUT,
            )
            response.raise_for_status()
            payload = response.json()
            token = payload.get("accessToken") or payload.get("access_token")
            if not token:
                raise ValueError("OAuth response missing access token")

            expires_in = int(payload.get("expiresIn") or payload.get("expires_in") or 3600)
            _TOKEN_CACHE["access_token"] = token
            _TOKEN_CACHE["expires_at"] = now + expires_in
            return token

        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as exc:
            last_exc = exc
            if attempt == DEFAULT_RETRIES:
                break
            time.sleep(attempt * 2)

        except requests.exceptions.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else None
            body = (exc.response.text or "")[:500] if exc.response is not None else ""
            raise RuntimeError(f"iFood OAuth failed HTTP {status}: {body}") from exc

    raise RuntimeError(f"iFood OAuth failed after {DEFAULT_RETRIES} attempts: {last_exc}")


def clear_token_cache() -> None:
    _TOKEN_CACHE["access_token"] = None
    _TOKEN_CACHE["expires_at"] = 0.0
