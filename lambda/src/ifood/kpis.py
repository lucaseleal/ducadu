from __future__ import annotations

from datetime import date


def orders_kpis_body_order_status(*, gte: str, lte: str) -> dict:
    return {
        "filter": {"referenceDate": {"gte": gte, "lte": lte}},
        "agg": {
            "metrics": {"gmv": ["sum"]},
            "groupBy": {"fields": ["orderStatus"]},
        },
        "page": 1,
        "size": 50,
    }


def parse_order_status_counts(payload: dict) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in payload.get("data") or []:
        gb = item.get("groupByKey") or {}
        val = gb.get("value") or {}
        status = val.get("orderStatus")
        if status:
            counts[str(status)] = counts.get(str(status), 0) + int(gb.get("count") or 0)
            continue
        os_block = item.get("orderStatus")
        if isinstance(os_block, dict):
            inner = os_block.get("value")
            if isinstance(inner, dict):
                for k, v in inner.items():
                    counts[str(k)] = counts.get(str(k), 0) + int(v)
    return counts


def day_reference_bounds(day: date) -> tuple[str, str]:
    return f"{day.isoformat()} 00:00:00", f"{day.isoformat()} 23:59:59"
