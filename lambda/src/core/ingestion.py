import psycopg
from typing import Callable, LiteralString

from src.utils.dates import daterange
from src.utils.storage import build_prefix, already_ingested, delete_prefix, save_json, mark_success
from src.utils.http import fetch_paginated
from src.db import upsert


def run_job(
    *,
    name: str,
    api_url: str,
    params_builder: Callable,
    transform_fn: Callable[[list], list],
    sql: LiteralString,
    landing_key: str,
    start_date,
    end_date,
    headers: dict,
    store: str,
    conn: psycopg.Connection,
    limit: int,
    timeout: int,
    retries: int,
    backoff: int,
    incremental: bool = True,
) -> int:
    """
    Orquestra paginação + storage S3 + upsert para um job de ingestão.
    Retorna o total de linhas inseridas/atualizadas.
    """
    total = 0

    for day_start, day_end in daterange(start_date, end_date):
        day = day_start.date()
        prefix = build_prefix(landing_key, store, str(day))

        if incremental and already_ingested(prefix):
            print(f"[SKIP] {name} - {store} - {day}")
            continue

        if not incremental:
            print(f"[OVERWRITE] {name} - {store} - {day}")
            delete_prefix(prefix)

        print(f"[INFO] {name} - {store} - {day}")

        rows: list = []

        for offset, data in fetch_paginated(
            url=api_url,
            headers=headers,
            params_builder=params_builder(day_start, day_end, limit),
            limit=limit,
            timeout=timeout,
            retries=retries,
            backoff=backoff,
        ):
            save_json(payload=data, prefix=prefix, file_prefix=f"offset={offset:05d}")
            rows.extend(transform_fn(data))

        if rows:
            upsert(conn, sql, rows)
            mark_success(prefix)
            total += len(rows)

        print(f"[DONE-DAY] {name} - {store} - {day} rows={len(rows)}")

    print(f"[DONE] {name} total rows: {total}")
    return total