from __future__ import annotations

from datetime import date, datetime
import os

from psycopg.types.json import Json

from src.config import (
    IFOOD_MERCHANT_IDS,
    LANDING_IFOOD_REVIEWS,
    LANDING_IFOOD_SALES,
)
from src.db import get_conn, upsert
from src.ifood.client import IfoodClient
from src.utils.dates import daterange
from src.utils.storage import already_ingested, build_prefix, delete_prefix, mark_success, save_json


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.lower() in ("1", "true", "yes")


def resolve_merchant_ids(client: IfoodClient) -> list[str]:
    if IFOOD_MERCHANT_IDS:
        return IFOOD_MERCHANT_IDS
    return [m["id"] for m in client.list_merchants() if m.get("id")]


def _payment_total(sale: dict) -> float | None:
    methods = (sale.get("payments") or {}).get("methods") or []
    if not methods:
        return None
    return float(sum((m.get("value") or 0) for m in methods))


def _sale_balance(sale: dict) -> float | None:
    billing = sale.get("billingSummary") or {}
    value = billing.get("saleBalance")
    return float(value) if value is not None else None


def _parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def transform_order_row(
    sale: dict,
    *,
    merchant_id: str,
    sales_date: date,
    raw_order: dict | None,
) -> tuple:
    merchant = sale.get("merchant") or {}
    return (
        sale["id"],
        merchant_id,
        sales_date,
        sale.get("shortId"),
        _parse_ts(sale.get("createdAt")),
        sale.get("type"),
        sale.get("category"),
        sale.get("salesChannel"),
        sale.get("currentStatus"),
        merchant.get("name"),
        _sale_balance(sale),
        _payment_total(sale),
        Json(sale),
        Json(raw_order) if raw_order else None,
    )


def transform_event_rows(
    sale: dict,
    *,
    merchant_id: str,
    sales_date: date,
) -> list[tuple]:
    order_id = sale.get("id")
    rows = []
    for ev in sale.get("orderEvents") or []:
        eid = ev.get("id")
        if not eid or not order_id:
            continue
        rows.append(
            (
                eid,
                order_id,
                merchant_id,
                sales_date,
                ev.get("fullCode"),
                ev.get("code"),
                _parse_ts(ev.get("createdAt")),
                Json(ev),
            )
        )
    return rows


def _review_id(review: dict) -> str | None:
    for key in ("id", "reviewId", "uuid"):
        value = review.get(key)
        if value:
            return str(value)
    return None


def transform_review_row(review: dict, *, merchant_id: str) -> tuple | None:
    rid = _review_id(review)
    if not rid:
        return None

    created = _parse_ts(review.get("createdAt") or review.get("reviewedAt"))
    review_date = created.date() if created else None
    rating = review.get("score") or review.get("rating") or review.get("grade")
    comment = review.get("comment") or review.get("description")
    order_id = review.get("orderId") or review.get("order_id")

    return (
        rid,
        merchant_id,
        review_date,
        created,
        float(rating) if rating is not None else None,
        comment,
        order_id,
        Json(review),
    )


UPSERT_ORDERS_SQL = """
INSERT INTO ifood_orders (
    id, merchant_id, sales_date, short_id, created_at,
    order_type, category, sales_channel, current_status, merchant_name,
    sale_balance, payment_total, raw_sale, raw_order
)
VALUES (
    %s, %s, %s, %s, %s,
    %s, %s, %s, %s, %s,
    %s, %s, %s, %s
)
ON CONFLICT (id) DO UPDATE SET
    merchant_id     = EXCLUDED.merchant_id,
    sales_date      = EXCLUDED.sales_date,
    short_id        = EXCLUDED.short_id,
    created_at      = EXCLUDED.created_at,
    order_type      = EXCLUDED.order_type,
    category        = EXCLUDED.category,
    sales_channel   = EXCLUDED.sales_channel,
    current_status  = EXCLUDED.current_status,
    merchant_name   = EXCLUDED.merchant_name,
    sale_balance    = EXCLUDED.sale_balance,
    payment_total   = EXCLUDED.payment_total,
    raw_sale        = EXCLUDED.raw_sale,
    raw_order       = EXCLUDED.raw_order,
    ingested_at     = NOW();
"""

UPSERT_EVENTS_SQL = """
INSERT INTO ifood_order_events (
    id, order_id, merchant_id, sales_date,
    full_code, code, event_created_at, raw_event
)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (id) DO UPDATE SET
    order_id          = EXCLUDED.order_id,
    merchant_id       = EXCLUDED.merchant_id,
    sales_date        = EXCLUDED.sales_date,
    full_code         = EXCLUDED.full_code,
    code              = EXCLUDED.code,
    event_created_at  = EXCLUDED.event_created_at,
    raw_event         = EXCLUDED.raw_event,
    ingested_at       = NOW();
"""

UPSERT_REVIEWS_SQL = """
INSERT INTO ifood_reviews (
    id, merchant_id, review_date, created_at,
    rating, comment, order_id, raw_review
)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (id) DO UPDATE SET
    merchant_id   = EXCLUDED.merchant_id,
    review_date   = EXCLUDED.review_date,
    created_at    = EXCLUDED.created_at,
    rating        = EXCLUDED.rating,
    comment       = EXCLUDED.comment,
    order_id      = EXCLUDED.order_id,
    raw_review    = EXCLUDED.raw_review,
    ingested_at   = NOW();
"""


def _ingest_sales_day(
    conn,
    client: IfoodClient,
    *,
    merchant_id: str,
    day: date,
    incremental: bool,
    fetch_order_details: bool,
) -> int:
    prefix = build_prefix(LANDING_IFOOD_SALES, merchant_id, str(day))

    if incremental and already_ingested(prefix):
        print(f"[SKIP] iFood sales merchant={merchant_id} day={day}")
        return 0

    if not incremental:
        print(f"[OVERWRITE] iFood sales merchant={merchant_id} day={day}")
        delete_prefix(prefix)

    print(f"[INFO] iFood sales merchant={merchant_id} day={day}")

    all_sales: list[dict] = []
    for page_idx, payload in enumerate(client.iter_sales_pages(merchant_id, begin=day, end=day), start=1):
        sales = payload.get("sales") or []
        save_json(payload, prefix=prefix, file_prefix=f"page={page_idx:03d}")
        all_sales.extend(sales)

    if not all_sales:
        print(f"[DONE-DAY] iFood sales merchant={merchant_id} day={day} rows=0")
        return 0

    order_rows = []
    event_rows = []
    order_ids = []

    for sale in all_sales:
        raw_order = None
        if fetch_order_details:
            try:
                raw_order = client.get_order(sale["id"])
            except Exception as exc:
                print(f"[WARN] order detail id={sale.get('id')}: {exc}")

        order_rows.append(
            transform_order_row(
                sale,
                merchant_id=merchant_id,
                sales_date=day,
                raw_order=raw_order,
            )
        )
        event_rows.extend(
            transform_event_rows(sale, merchant_id=merchant_id, sales_date=day)
        )
        order_ids.append(sale["id"])

    upsert(conn, UPSERT_ORDERS_SQL, order_rows)
    if event_rows:
        upsert(conn, UPSERT_EVENTS_SQL, event_rows)

    mark_success(prefix)
    print(f"[DONE-DAY] iFood sales merchant={merchant_id} day={day} orders={len(order_rows)} events={len(event_rows)}")
    return len(order_rows)


def _ingest_reviews_day(
    conn,
    client: IfoodClient,
    *,
    merchant_id: str,
    day: date,
    incremental: bool,
) -> int:
    prefix = build_prefix(LANDING_IFOOD_REVIEWS, merchant_id, str(day))

    if incremental and already_ingested(prefix):
        print(f"[SKIP] iFood reviews merchant={merchant_id} day={day}")
        return 0

    if not incremental:
        delete_prefix(prefix)

    print(f"[INFO] iFood reviews merchant={merchant_id} day={day}")

    review_rows: list[tuple] = []
    for page_idx, payload in enumerate(
        client.iter_review_pages(merchant_id, begin=day, end=day),
        start=1,
    ):
        save_json(payload, prefix=prefix, file_prefix=f"page={page_idx:03d}")
        for review in payload.get("reviews") or []:
            row = transform_review_row(review, merchant_id=merchant_id)
            if row:
                review_rows.append(row)

    if review_rows:
        upsert(conn, UPSERT_REVIEWS_SQL, review_rows)
        mark_success(prefix)

    print(f"[DONE-DAY] iFood reviews merchant={merchant_id} day={day} rows={len(review_rows)}")
    return len(review_rows)


def main(
    start_date: datetime,
    end_date: datetime,
    *,
    incremental: bool = True,
    merchants: list[str] | None = None,
) -> None:
    client = IfoodClient()
    merchant_ids = merchants or resolve_merchant_ids(client)
    if not merchant_ids:
        raise RuntimeError("Nenhum merchant iFood configurado ou retornado pela API")

    fetch_order_details = _env_bool("IFOOD_FETCH_ORDER_DETAILS", False)
    conn = get_conn()
    total_orders = 0
    total_reviews = 0

    try:
        for merchant_id in merchant_ids:
            print(f"\n===== IFOOD MERCHANT: {merchant_id} =====")
            for day_start, _day_end in daterange(start_date, end_date):
                day = day_start.date()
                total_orders += _ingest_sales_day(
                    conn,
                    client,
                    merchant_id=merchant_id,
                    day=day,
                    incremental=incremental,
                    fetch_order_details=fetch_order_details,
                )
                total_reviews += _ingest_reviews_day(
                    conn,
                    client,
                    merchant_id=merchant_id,
                    day=day,
                    incremental=incremental,
                )
    finally:
        conn.close()

    print(f"[DONE] iFood ingest orders={total_orders} reviews={total_reviews}")
