from datetime import datetime
from src.config import API_SALES, LANDING_SALES, DEFAULT_LIMIT, DEFAULT_TIMEOUT, DEFAULT_RETRIES, DEFAULT_BACKOFF
from src.db import get_conn, upsert
from src.utils.dates import daterange
from src.utils.http import fetch_paginated
from src.utils.storage import build_prefix, already_ingested, save_json, delete_prefix, mark_success
from src.utils.params import sales_params_builder


def transform_sale(s: dict) -> tuple:
    partner = s.get("partner_sale") or {}
    nfce = s.get("nfce") or {}
    delivery = s.get("delivery") or {}

    return (
        s["id_sale"],
        s["id_store"],
        s.get("sale_number"),
        s["shift_date"],
        s["created_at"],
        s["updated_at"],

        s.get("total_amount"),
        s.get("total_amount_items"),
        s.get("total_discount"),
        s.get("total_increase"),
        delivery.get("delivery_fee"),

        s.get("id_sale_type"),
        s.get("canceled"),
        s.get("count_canceled_items"),

        partner.get("desc_partner_sale"),
        partner.get("partner_status"),
        partner.get("cod_sale1"),
        partner.get("cod_sale2"),

        nfce.get("serie"),
        nfce.get("numero"),
        nfce.get("chave_acesso"),
        nfce.get("data_emissao"),
    )


# psycopg3: sem VALUES %s — usa placeholders individuais com executemany
UPSERT_SALES_SQL = """
INSERT INTO sales (
    id_sale,
    id_store,
    sale_number,
    shift_date,
    created_at,
    updated_at,

    total_amount,
    total_amount_items,
    total_discount,
    total_increase,
    delivery_fee,

    id_sale_type,
    canceled,
    count_canceled_items,

    partner_name,
    partner_status,
    partner_cod_sale1,
    partner_cod_sale2,

    nfce_serie,
    nfce_number,
    nfce_key,
    nfce_issued_at
)
VALUES (
    %s, %s, %s, %s, %s, %s,
    %s, %s, %s, %s, %s,
    %s, %s, %s,
    %s, %s, %s, %s,
    %s, %s, %s, %s
)
ON CONFLICT (id_sale) DO UPDATE SET
    updated_at           = EXCLUDED.updated_at,
    total_amount         = EXCLUDED.total_amount,
    total_amount_items   = EXCLUDED.total_amount_items,
    total_discount       = EXCLUDED.total_discount,
    total_increase       = EXCLUDED.total_increase,
    delivery_fee         = EXCLUDED.delivery_fee,
    partner_status       = EXCLUDED.partner_status,
    count_canceled_items = EXCLUDED.count_canceled_items;
"""


def main(start_date: datetime, end_date: datetime, headers: dict, store: str, incremental: bool = True):
    conn = get_conn()
    total = 0

    try:
        for day_start, day_end in daterange(start_date, end_date):
            day = day_start.date()
            prefix = build_prefix(LANDING_SALES, store, str(day))

            if incremental and already_ingested(prefix):
                print(f"[SKIP] Sales - Store {store}, Day {day}")
                continue

            if not incremental:
                print(f"[OVERWRITE] Sales - Store {store}, Day {day}")
                delete_prefix(prefix)

            print(f"[INFO] Sales - Store {store}, Day: {day}")

            rows = []

            for offset, data in fetch_paginated(
                url=API_SALES,
                headers=headers,
                params_builder=sales_params_builder(day_start, day_end, DEFAULT_LIMIT),
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
                rows.extend(transform_sale(s) for s in data)

            if rows:
                upsert(conn, UPSERT_SALES_SQL, rows)
                mark_success(prefix)
                total += len(rows)

            print(f"[DONE-DAY] sales {store}, {day}, db_rows={len(rows)}")

    finally:
        conn.close()

    print(f"[DONE] Total sales ingested: {total}")