from datetime import datetime

from src.config import (
    API_SALES_ITEMS,
    LANDING_SALES_ITEMS,
    DEFAULT_LIMIT,
    DEFAULT_TIMEOUT,
    DEFAULT_RETRIES,
    DEFAULT_BACKOFF,
)

from src.db import get_conn, upsert
from src.utils.dates import daterange
from src.utils.http import fetch_paginated
from src.utils.storage import build_prefix, already_ingested, save_json, delete_prefix
from src.utils.params import sales_items_params_builder


# --------------------------------------------------
# TRANSFORM
# --------------------------------------------------
def transform_sales_items(payload: list):
    items = []
    choices = []

    for sale in payload:
        for item in sale.get("items", []):
            items.append((
                item.get("id_sale_item"),
                sale.get("id_sale"),
                sale.get("id_store"),
                item.get("desc_sale_item"),
                item.get("quantity"),
                item.get("unit_price"),
                item.get("notes"),
                item.get("status"),
                item.get("deleted"),
                item.get("done_at"),
                item.get("created_at"),
                item.get("updated_at"),
                item.get("integration_code"),
                item.get("id_store_item"),
                item.get("id_store_variation"),
                item.get("group_sequence"),
            ))

            for choice in item.get("choices", []):
                choices.append((
                    choice.get("id_sale_item_choice"),
                    item.get("id_sale_item"),
                    choice.get("desc_sale_item_choice"),
                    choice.get("desc_store_choice_item"),
                    choice.get("aditional_price"),
                    choice.get("deleted"),
                    choice.get("notes"),
                    choice.get("integration_code"),
                ))

    return items, choices


# --------------------------------------------------
# SQL
# --------------------------------------------------
UPSERT_SALES_ITEMS_SQL = """
INSERT INTO sales_items (
    id_sale_item,
    id_sale,
    id_store,
    desc_sale_item,
    quantity,
    unit_price,
    notes,
    status,
    deleted,
    done_at,
    created_at,
    updated_at,
    integration_code,
    id_store_item,
    id_store_variation,
    group_sequence
)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (id_sale_item) DO UPDATE SET
    quantity = EXCLUDED.quantity,
    unit_price = EXCLUDED.unit_price,
    updated_at = EXCLUDED.updated_at;
"""

UPSERT_SALES_ITEM_CHOICES_SQL = """
INSERT INTO sales_item_choices (
    id_sale_item_choice,
    id_sale_item,
    desc_sale_item_choice,
    desc_store_choice_item,
    aditional_price,
    deleted,
    notes,
    integration_code
)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (id_sale_item_choice) DO NOTHING;
"""


# --------------------------------------------------
# MAIN
# --------------------------------------------------
def main(start_date: datetime, end_date: datetime, headers: dict, store: str, incremental: bool = True):
    conn = get_conn()
    total_items = 0

    for day_start, day_end in daterange(start_date, end_date):
        day = day_start.date()
        prefix = build_prefix(LANDING_SALES_ITEMS, store, str(day))

        if incremental and already_ingested(prefix):
            print(f"[SKIP] Sales items - Store {store}, Day {day}")
            continue

        if not incremental:
            print(f"[OVERWRITE] Sales items - Store {store}, Day {day}")
            delete_prefix(prefix)

        print(f"[INFO] Sales items - Store {store}, Day: {day}")

        items_rows = []
        choices_rows = []

        for offset, data in fetch_paginated(
            url=API_SALES_ITEMS,
            headers=headers,
            params_builder=sales_items_params_builder(day_start, day_end, DEFAULT_LIMIT),
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

            items, choices = transform_sales_items(data)
            items_rows.extend(items)
            choices_rows.extend(choices)

        if items_rows:
            upsert(conn, UPSERT_SALES_ITEMS_SQL, items_rows, mode="batch")
            mark_success(prefix)

        if choices_rows:
            upsert(conn, UPSERT_SALES_ITEM_CHOICES_SQL, choices_rows, mode="batch")

        total_items += len(items_rows)
        print(f"[PAGE] sales items {store}, {day}, db_rows={len(items_rows)}")

    conn.close()
    print(f"[DONE] Total sales items ingested: {total_items}")
