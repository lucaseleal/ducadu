import time
import requests
from typing import Callable
import random


def fetch_paginated(
    *,
    url: str,
    headers: dict,
    params_builder: Callable[[int], dict],
    limit: int,
    timeout: int,
    retries: int,
    backoff: int,
):
    """
    Generator que abstrai paginação com retry.
    """
    offset = 0

    while True:
        params = params_builder(offset)

        for attempt in range(1, retries + 1):
            try:
                r = requests.get(
                    url,
                    headers=headers,
                    params=params,
                    timeout=timeout,
                )
                r.raise_for_status()
                data = r.json()
                break

            except requests.exceptions.ReadTimeout:
                if attempt == retries:
                    raise Exception(f"[WARN] Timeout offset={offset} attempt={attempt}")
                time.sleep(backoff * attempt + random.uniform(0, 1))

            except requests.exceptions.RequestException as e:
                raise Exception(f"[ERROR] Request failed offset={offset}: {e}")

        if data is None:
            raise Exception("Failed after retries")

        if not data:
            return

        yield offset, data

        if len(data) < limit:
            return

        offset += limit
        time.sleep(min(0.2 + offset / 10000, 1))
