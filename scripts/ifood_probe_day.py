"""
Fetch one calendar day of iFood sales + reviews for configured merchant(s).

Usage (from repo root):
  uv run --project lambda python scripts/ifood_probe_day.py
  uv run --project lambda python scripts/ifood_probe_day.py --date 2026-09-24
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAMBDA_ROOT = ROOT / "lambda"
sys.path.insert(0, str(LAMBDA_ROOT))


def load_env() -> None:
    env_path = ROOT / ".env"
    if not env_path.is_file():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Probe iFood sales + reviews for one day")
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="Calendar day (YYYY-MM-DD). Default: yesterday (UTC).",
    )
    parser.add_argument(
        "--merchant-id",
        type=str,
        default=os.getenv("IFOOD_TEST_MERCHANT_ID", "8021db2f-8a8b-498b-9461-1c8825d3cde6"),
    )
    parser.add_argument(
        "--fetch-order-details",
        action="store_true",
        help="Try GET /order for each sale id (may 404 on homologation fixtures).",
    )
    return parser.parse_args()


def main() -> int:
    load_env()
    args = parse_args()

    if args.date:
        target = datetime.strptime(args.date, "%Y-%m-%d").date()
    else:
        target = date.today() - timedelta(days=1)

    from src.ifood.client import IfoodClient

    client = IfoodClient()
    merchants = client.list_merchants()
    print(f"merchants_in_token={len(merchants)}")

    merchant_id = args.merchant_id
    sales_payload = client.list_sales(merchant_id, begin=target, end=target, page=1)
    sales = sales_payload.get("sales") or []
    print(f"day={target.isoformat()} merchant={merchant_id} sales_count={len(sales)}")

    if sales:
        sample = sales[0]
        print(
            "sample_sale",
            json.dumps(
                {
                    "id": sample.get("id"),
                    "shortId": sample.get("shortId"),
                    "createdAt": sample.get("createdAt"),
                    "currentStatus": sample.get("currentStatus"),
                    "merchantName": (sample.get("merchant") or {}).get("name"),
                },
                ensure_ascii=False,
            ),
        )

    reviews_payload = client.list_reviews(
        merchant_id,
        begin=target,
        end=target,
        page=1,
        size=50,
    )
    reviews = reviews_payload.get("reviews") or []
    print(f"reviews_count={len(reviews)}")

    events = client.poll_order_events()
    print(f"order_events_pending={len(events)}")

    if args.fetch_order_details and sales:
        for sale in sales[:3]:
            order_id = sale.get("id")
            if not order_id:
                continue
            try:
                detail = client.get_order(order_id)
                print(
                    f"order_detail ok id={order_id} displayId={detail.get('displayId')} isTest={detail.get('isTest')}",
                )
            except Exception as exc:
                print(f"order_detail fail id={order_id}: {exc}")

    print(
        "note: sandbox/homologation uses iFood fixture data (not Ducadu stores). "
        "Set IFOOD_USE_HOMOLOGATION=false when calling production merchants."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
