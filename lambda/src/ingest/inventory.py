from datetime import datetime
import json

from src.utils.http import fetch_paginated
from src.utils.dates import daterange
from src.db import get_conn, upsert
from src.utils.quantities import parse_quantity
from src.config import (
    API_INVENTORY_MOVEMENTS,
    DEFAULT_LIMIT,
    DEFAULT_TIMEOUT,
    DEFAULT_RETRIES,
    DEFAULT_BACKOFF,
    LANDING_INVENTORY,
)
from src.utils.storage import build_prefix, already_ingested, save_json, delete_prefix
from src.utils.params import inventory_params_builder


UPSERT_INVENTORY_SQL = """
    INSERT INTO inventory_movements (
        id_inventory_movement,
        id_store,
        movement_date,
        created_at,
        id_movement_type,
        quantity_raw,
        quantity_numeric,
        unit_measure,
        unit_cost,
        sale_id,
        sale_number,
        ingredient_id,
        ingredient_name,
        ingredient_group_id,
        ingredient_group_name,
        average_cost,
        current_inventory,
        control_inventory,
        include_in_cmv_calc,
        ingredient_created_at,
        notes,
        identification_nf,
        raw
    )
    VALUES (
        %s, %s, %s, %s, %s,
        %s, %s, %s, %s,
        %s, %s,
        %s, %s,
        %s, %s,
        %s, %s,
        %s, %s,
        %s,
        %s, %s,
        %s::jsonb
    )
    ON CONFLICT (id_inventory_movement) DO NOTHING
"""


def main(start_date: datetime, end_date: datetime, headers: dict, store: str, incremental: bool = True):
    conn = get_conn()
    total = 0

    for day_start, day_end in daterange(start_date, end_date):
        day = day_start.date()
        prefix = build_prefix(LANDING_INVENTORY, store, str(day))

        if incremental and already_ingested(prefix):
            print(f"[SKIP] Inventory - Store {store}, Day {day}")
            continue

        if not incremental:
            print(f"[OVERWRITE] Inventory - Store {store}, Day {day}")
            delete_prefix(prefix)

        print(f"[INFO] Inventory - Store {store}, Day: {day}")

        for offset, data in fetch_paginated(
            url=API_INVENTORY_MOVEMENTS,
            headers=headers,
            params_builder=inventory_params_builder(day_start, day_end, DEFAULT_LIMIT),
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

            rows = []

            for item in data:
                ingredient = item.get("ingredient") or {}
                group = ingredient.get("group") or {}
                sale = item.get("sale") or {}

                quantity_raw = item.get("quantity")
                quantity_numeric, unit_measure = parse_quantity(quantity_raw)

                rows.append((
                    item.get("id_store_ingred_movement"),
                    item.get("id_store"),
                    item.get("date_movement"),
                    item.get("created_at"),
                    item.get("id_movement_type"),
                    quantity_raw,
                    quantity_numeric,
                    unit_measure,
                    item.get("unit_cost"),
                    sale.get("id_sale"),
                    sale.get("sale_number"),
                    ingredient.get("id_store_ingredient"),
                    ingredient.get("desc_store_ingredient"),
                    group.get("id_store_group_ingredient"),
                    group.get("desc_store_group_ingredient"),
                    ingredient.get("average_cost"),
                    ingredient.get("current_inventory"),
                    ingredient.get("control_inventory") == "Y",
                    ingredient.get("include_in_cmv_calc") == "Y",
                    ingredient.get("ingredient_created_at"),
                    item.get("notes"),
                    item.get("identification_nf"),
                    json.dumps(item),
                ))
            
            if rows:
                upsert(conn, UPSERT_INVENTORY_SQL, rows)
                mark_success(prefix)

            total += len(rows)
            print(f"[PAGE] {store}, {day}, offset={offset}, api_items={len(data)}, db_rows={len(rows)}")

    conn.close()
    print(f"[DONE] Total inventory movements ingested: {total}")
