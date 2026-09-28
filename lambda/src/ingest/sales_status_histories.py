import os
from datetime import datetime

from src.config import (
    API_SALES_STATUS_HISTORIES,
    DEFAULT_BACKOFF,
    DEFAULT_LIMIT,
    DEFAULT_RETRIES,
    DEFAULT_TIMEOUT,
    LANDING_SALES_STATUS_HISTORIES,
)
from src.db import get_conn, upsert
from src.utils.dates import daterange
from src.utils.http import fetch_paginated
from src.utils.params import sales_status_histories_params_builder
from src.utils.storage import (
    already_ingested,
    build_prefix,
    delete_prefix,
    mark_success,
    save_json,
)

_STATUS_DATE_COLUMN = os.getenv("SAIPOS_STATUS_DATE_COLUMN", "shift_date")
_STATUS_ALSO_UPDATED_AT = os.getenv("SAIPOS_STATUS_INGEST_UPDATED_AT", "").lower() in (
    "1",
    "true",
    "yes",
)


def transform_status_histories(payload: list) -> list[tuple]:
    rows: list[tuple] = []
    for sale in payload:
        id_sale = sale.get("id_sale")
        id_store = sale.get("id_store")
        if id_sale is None or id_store is None:
            continue

        shift_date = sale.get("shift_date")
        sale_created_at = sale.get("created_at")
        sale_updated_at = sale.get("updated_at")

        for history in sale.get("histories") or []:
            hid = history.get("id_sale_status_history")
            if hid is None:
                continue

            user = history.get("user") or {}
            authorized = history.get("authorized_by") or {}

            rows.append(
                (
                    hid,
                    id_sale,
                    id_store,
                    shift_date,
                    sale_created_at,
                    sale_updated_at,
                    history.get("order"),
                    history.get("created_at"),
                    history.get("desc_store_sale_status"),
                    history.get("duration_time_seconds"),
                    history.get("desc_cancellation_reason") or None,
                    user.get("id_user"),
                    user.get("full_name"),
                    user.get("email"),
                    user.get("user_type"),
                    authorized.get("id_user"),
                    authorized.get("full_name"),
                    authorized.get("email"),
                )
            )
    return rows


UPSERT_SALES_STATUS_HISTORIES_SQL = """
INSERT INTO sales_status_histories (
    id_sale_status_history,
    id_sale,
    id_store,
    shift_date,
    sale_created_at,
    sale_updated_at,
    status_order,
    status_created_at,
    desc_store_sale_status,
    duration_time_seconds,
    desc_cancellation_reason,
    user_id,
    user_full_name,
    user_email,
    user_type,
    authorized_by_id,
    authorized_by_full_name,
    authorized_by_email
)
VALUES (
    %s, %s, %s, %s, %s, %s,
    %s, %s, %s, %s, %s,
    %s, %s, %s, %s,
    %s, %s, %s
)
ON CONFLICT (id_sale_status_history) DO UPDATE SET
    id_sale                  = EXCLUDED.id_sale,
    id_store                 = EXCLUDED.id_store,
    shift_date               = EXCLUDED.shift_date,
    sale_created_at          = EXCLUDED.sale_created_at,
    sale_updated_at          = EXCLUDED.sale_updated_at,
    status_order             = EXCLUDED.status_order,
    status_created_at        = EXCLUDED.status_created_at,
    desc_store_sale_status   = EXCLUDED.desc_store_sale_status,
    duration_time_seconds    = EXCLUDED.duration_time_seconds,
    desc_cancellation_reason = EXCLUDED.desc_cancellation_reason,
    user_id                  = EXCLUDED.user_id,
    user_full_name           = EXCLUDED.user_full_name,
    user_email               = EXCLUDED.user_email,
    user_type                = EXCLUDED.user_type,
    authorized_by_id         = EXCLUDED.authorized_by_id,
    authorized_by_full_name  = EXCLUDED.authorized_by_full_name,
    authorized_by_email      = EXCLUDED.authorized_by_email,
    ingested_at              = NOW();
"""


def _ingest_window(
    conn,
    *,
    start_date: datetime,
    end_date: datetime,
    headers: dict,
    store: str,
    incremental: bool,
    date_column: str,
    landing_suffix: str = "",
) -> int:
    total = 0
    suffix = f"_{landing_suffix}" if landing_suffix else ""

    for day_start, day_end in daterange(start_date, end_date):
        day = day_start.date()
        prefix = build_prefix(
            LANDING_SALES_STATUS_HISTORIES + suffix,
            store,
            str(day),
        )

        if incremental and already_ingested(prefix):
            print(f"[SKIP] Status histories ({date_column}) - Store {store}, Day {day}")
            continue

        if not incremental:
            print(f"[OVERWRITE] Status histories ({date_column}) - Store {store}, Day {day}")
            delete_prefix(prefix)

        print(f"[INFO] Status histories ({date_column}) - Store {store}, Day {day}")

        history_rows: list[tuple] = []

        for offset, data in fetch_paginated(
            url=API_SALES_STATUS_HISTORIES,
            headers=headers,
            params_builder=sales_status_histories_params_builder(
                day_start,
                day_end,
                DEFAULT_LIMIT,
                date_column=date_column,
            ),
            limit=DEFAULT_LIMIT,
            timeout=DEFAULT_TIMEOUT,
            retries=DEFAULT_RETRIES,
            backoff=DEFAULT_BACKOFF,
        ):
            save_json(
                payload=data,
                prefix=prefix,
                file_prefix=f"offset={offset:05d}",
            )
            history_rows.extend(transform_status_histories(data))

        if history_rows:
            upsert(conn, UPSERT_SALES_STATUS_HISTORIES_SQL, history_rows)
            mark_success(prefix)

        total += len(history_rows)
        print(f"[DONE-DAY] status histories {store}, {day}, rows={len(history_rows)}")

    return total


def main(
    start_date: datetime,
    end_date: datetime,
    headers: dict,
    store: str,
    incremental: bool = True,
) -> None:
    conn = get_conn()
    total = 0

    try:
        total += _ingest_window(
            conn,
            start_date=start_date,
            end_date=end_date,
            headers=headers,
            store=store,
            incremental=incremental,
            date_column=_STATUS_DATE_COLUMN,
        )

        if _STATUS_ALSO_UPDATED_AT and _STATUS_DATE_COLUMN != "updated_at":
            total += _ingest_window(
                conn,
                start_date=start_date,
                end_date=end_date,
                headers=headers,
                store=store,
                incremental=incremental,
                date_column="updated_at",
                landing_suffix="updated_at",
            )
    finally:
        conn.close()

    print(f"[DONE] Total sales status history rows ingested: {total}")
