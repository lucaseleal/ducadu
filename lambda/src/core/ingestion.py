from src.utils.dates import daterange
from src.utils.storage import (
    build_prefix,
    already_ingested,
    delete_prefix,
    save_json,
    mark_success,
)
from src.utils.http import fetch_paginated


def run_job(
    name,
    api_url,
    params_builder,
    transform_fn,
    upsert_fn,
    landing_key,
    start_date,
    end_date,
    headers,
    store,
    incremental=True,
):
    total = 0

    for day_start, day_end in daterange(start_date, end_date):
        day = day_start.date()
        prefix = build_prefix(landing_key, store, str(day))

        if incremental and already_ingested(prefix):
            print(f"[SKIP] {name} - {store} - {day}")
            continue

        if not incremental:
            delete_prefix(prefix)

        rows_accumulated = []

        for offset, data in fetch_paginated(
            url=api_url,
            headers=headers,
            params_builder=params_builder(day_start, day_end),
        ):
            save_json(
                payload=data,
                prefix=prefix,
                offset=offset,
            )

            rows = transform_fn(data)
            rows_accumulated.extend(rows)

        if rows_accumulated:
            upsert_fn(rows_accumulated)
            total += len(rows_accumulated)

        mark_success(prefix)

        print(f"[DONE-DAY] {name} - {store} - {day} rows={len(rows_accumulated)}")

    print(f"[DONE] {name} total rows: {total}")