from datetime import datetime
from src.config import API_SALES, LANDING_SALES, DEFAULT_LIMIT, DEFAULT_TIMEOUT, DEFAULT_RETRIES, DEFAULT_BACKOFF
from src.db import get_conn, upsert, execute
from src.utils.dates import daterange
from src.utils.http import fetch_paginated
from src.utils.storage import build_prefix, already_ingested, save_json, delete_prefix, mark_success
from src.utils.params import sales_params_builder


def transform_sale(s: dict) -> tuple:
    partner  = s.get("partner_sale") or {}
    nfce     = s.get("nfce") or {}
    delivery = s.get("delivery") or {}
    customer = s.get("customer") or {}
    cashier  = s.get("cashier") or {}
    shift    = s.get("store_shift") or {}

    return (
        # core
        s["id_sale"],
        s["id_store"],
        s.get("sale_number"),
        s["shift_date"],
        s["created_at"],
        s["updated_at"],
        s.get("id_sale_type"),
        # financial
        s.get("total_amount"),
        s.get("total_amount_items"),
        s.get("total_discount"),
        s.get("total_increase"),
        # status
        s.get("canceled"),
        s.get("count_canceled_items"),
        s.get("has_items_resolved_by_resolution_service"),
        # notes
        s.get("notes"),
        s.get("desc_sale"),
        s.get("discount_reason"),
        s.get("increase_reason"),
        # customer
        customer.get("id_customer"),
        customer.get("name"),
        customer.get("email"),
        customer.get("phone"),
        customer.get("cpf_cnpj"),
        customer.get("birth_date"),
        # cashier
        cashier.get("id_store_cashier"),
        cashier.get("id_user"),
        cashier.get("opened_at"),
        cashier.get("closed_at"),
        # shift
        shift.get("desc_store_shift"),
        shift.get("starting_time"),
        # partner
        partner.get("desc_partner_sale"),
        partner.get("partner_status"),
        partner.get("cod_sale1"),
        partner.get("cod_sale2"),
        partner.get("cod_store"),
        partner.get("desc_store_partner"),
        partner.get("import_delivery_fee"),
        # delivery
        delivery.get("delivery_fee"),
        delivery.get("delivery_time"),
        delivery.get("delivery_by"),
        delivery.get("city"),
        delivery.get("state"),
        delivery.get("street"),
        delivery.get("number"),
        delivery.get("zipcode"),
        delivery.get("district"),
        delivery.get("complement"),
        delivery.get("reference"),
        # nfce
        nfce.get("serie"),
        nfce.get("numero"),
        nfce.get("chave_acesso"),
        nfce.get("data_emissao"),
    )


def transform_payments(data: list) -> list[tuple]:
    rows = []
    for s in data:
        for p in (s.get("payments") or []):
            rows.append((
                s["id_sale"],
                p.get("payment_amount"),
                p.get("desc_store_payment_type"),
                p.get("change_for"),
                p.get("created_at"),
            ))
    return rows


UPSERT_SALES_SQL = """
INSERT INTO sales (
    id_sale,
    id_store,
    sale_number,
    shift_date,
    created_at,
    updated_at,
    id_sale_type,

    total_amount,
    total_amount_items,
    total_discount,
    total_increase,

    canceled,
    count_canceled_items,
    has_items_resolved,

    notes,
    desc_sale,
    discount_reason,
    increase_reason,

    customer_id,
    customer_name,
    customer_email,
    customer_phone,
    customer_cpf_cnpj,
    customer_birth_date,

    cashier_id,
    cashier_id_user,
    cashier_opened_at,
    cashier_closed_at,

    store_shift_desc,
    store_shift_starting_time,

    partner_name,
    partner_status,
    partner_cod_sale1,
    partner_cod_sale2,
    partner_cod_store,
    partner_desc_store,
    partner_import_delivery_fee,

    delivery_fee,
    delivery_time,
    delivery_by,
    delivery_city,
    delivery_state,
    delivery_street,
    delivery_number,
    delivery_zipcode,
    delivery_district,
    delivery_complement,
    delivery_reference,

    nfce_serie,
    nfce_number,
    nfce_key,
    nfce_issued_at
)
VALUES (
    %s, %s, %s, %s, %s, %s, %s,
    %s, %s, %s, %s,
    %s, %s, %s,
    %s, %s, %s, %s,
    %s, %s, %s, %s, %s, %s,
    %s, %s, %s, %s,
    %s, %s,
    %s, %s, %s, %s, %s, %s, %s,
    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
    %s, %s, %s, %s
)
ON CONFLICT (id_sale) DO UPDATE SET
    id_store                    = EXCLUDED.id_store,
    sale_number                 = EXCLUDED.sale_number,
    shift_date                  = EXCLUDED.shift_date,
    updated_at                  = EXCLUDED.updated_at,
    id_sale_type                = EXCLUDED.id_sale_type,
    total_amount                = EXCLUDED.total_amount,
    total_amount_items          = EXCLUDED.total_amount_items,
    total_discount              = EXCLUDED.total_discount,
    total_increase              = EXCLUDED.total_increase,
    canceled                    = EXCLUDED.canceled,
    count_canceled_items        = EXCLUDED.count_canceled_items,
    has_items_resolved          = EXCLUDED.has_items_resolved,
    notes                       = EXCLUDED.notes,
    desc_sale                   = EXCLUDED.desc_sale,
    discount_reason             = EXCLUDED.discount_reason,
    increase_reason             = EXCLUDED.increase_reason,
    customer_id                 = EXCLUDED.customer_id,
    customer_name               = EXCLUDED.customer_name,
    customer_email              = EXCLUDED.customer_email,
    customer_phone              = EXCLUDED.customer_phone,
    customer_cpf_cnpj           = EXCLUDED.customer_cpf_cnpj,
    customer_birth_date         = EXCLUDED.customer_birth_date,
    cashier_id                  = EXCLUDED.cashier_id,
    cashier_id_user             = EXCLUDED.cashier_id_user,
    cashier_opened_at           = EXCLUDED.cashier_opened_at,
    cashier_closed_at           = EXCLUDED.cashier_closed_at,
    store_shift_desc            = EXCLUDED.store_shift_desc,
    store_shift_starting_time   = EXCLUDED.store_shift_starting_time,
    partner_name                = EXCLUDED.partner_name,
    partner_status              = EXCLUDED.partner_status,
    partner_cod_sale1           = EXCLUDED.partner_cod_sale1,
    partner_cod_sale2           = EXCLUDED.partner_cod_sale2,
    partner_cod_store           = EXCLUDED.partner_cod_store,
    partner_desc_store          = EXCLUDED.partner_desc_store,
    partner_import_delivery_fee = EXCLUDED.partner_import_delivery_fee,
    delivery_fee                = EXCLUDED.delivery_fee,
    delivery_time               = EXCLUDED.delivery_time,
    delivery_by                 = EXCLUDED.delivery_by,
    delivery_city               = EXCLUDED.delivery_city,
    delivery_state              = EXCLUDED.delivery_state,
    delivery_street             = EXCLUDED.delivery_street,
    delivery_number             = EXCLUDED.delivery_number,
    delivery_zipcode            = EXCLUDED.delivery_zipcode,
    delivery_district           = EXCLUDED.delivery_district,
    delivery_complement         = EXCLUDED.delivery_complement,
    delivery_reference          = EXCLUDED.delivery_reference,
    nfce_serie                  = EXCLUDED.nfce_serie,
    nfce_number                 = EXCLUDED.nfce_number,
    nfce_key                    = EXCLUDED.nfce_key,
    nfce_issued_at              = EXCLUDED.nfce_issued_at;
"""

INSERT_SALE_PAYMENTS_SQL = """
INSERT INTO sale_payments (id_sale, payment_amount, desc_store_payment_type, change_for, created_at)
VALUES (%s, %s, %s, %s, %s)
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

            all_sales = []

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
                all_sales.extend(data)

            if all_sales:
                sale_rows = [transform_sale(s) for s in all_sales]
                upsert(conn, UPSERT_SALES_SQL, sale_rows)

                sale_ids = [s["id_sale"] for s in all_sales]
                execute(conn, "DELETE FROM sale_payments WHERE id_sale = ANY(%s)", [sale_ids])

                payment_rows = transform_payments(all_sales)
                if payment_rows:
                    upsert(conn, INSERT_SALE_PAYMENTS_SQL, payment_rows)

                mark_success(prefix)
                total += len(sale_rows)

            print(f"[DONE-DAY] sales {store}, {day}, db_rows={len(all_sales)}")

    finally:
        conn.close()

    print(f"[DONE] Total sales ingested: {total}")
