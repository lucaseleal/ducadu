import time
import random
import requests
from typing import Callable, Generator


def fetch_paginated(
    *,
    url: str,
    headers: dict,
    params_builder: Callable[[int], dict],
    limit: int,
    timeout: int,
    retries: int,
    backoff: int,
) -> Generator[tuple[int, list], None, None]:
    """
    Generator que abstrai paginação com retry e backoff exponencial.
    Yields (offset, data) para cada página retornada pela API.
    """
    offset = 0

    while True:
        params = params_builder(offset)
        data = _fetch_with_retry(url, headers, params, timeout, retries, backoff, offset)

        if not data:
            return

        yield offset, data

        if len(data) < limit:
            return

        offset += limit
        time.sleep(min(0.2 + offset / 10000, 1))


def _fetch_with_retry(
    url: str,
    headers: dict,
    params: dict,
    timeout: int,
    retries: int,
    backoff: int,
    offset: int,
) -> list:
    last_exc: Exception | None = None

    for attempt in range(1, retries + 1):
        try:
            r = requests.get(url, headers=headers, params=params, timeout=timeout)
            r.raise_for_status()
            return r.json()

        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            last_exc = e
            if attempt == retries:
                break
            wait = backoff * attempt + random.uniform(0, 1)
            print(f"[RETRY] offset={offset} attempt={attempt}/{retries} aguardando {wait:.1f}s — {type(e).__name__}")
            time.sleep(wait)

        except requests.exceptions.HTTPError as e:
            raise Exception(f"[ERROR] HTTP {e.response.status_code} offset={offset}: {e}") from e

        except requests.exceptions.RequestException as e:
            raise Exception(f"[ERROR] Request falhou offset={offset}: {e}") from e

    raise Exception(f"[ERROR] Timeout/ConnectionError após {retries} tentativas offset={offset}: {last_exc}")