from __future__ import annotations

from datetime import date
from typing import Any

import requests

from src.config import DEFAULT_TIMEOUT, IFOOD_API_BASE, IFOOD_USE_HOMOLOGATION_HEADER
from src.ifood.auth import get_access_token


class IfoodClient:
    """Thin wrapper around iFood Merchant API (read-only helpers for ingest)."""

    def __init__(self, *, timeout: int = DEFAULT_TIMEOUT) -> None:
        self._timeout = timeout

    def _headers(self) -> dict[str, str]:
        headers = {"Authorization": f"Bearer {get_access_token()}"}
        if IFOOD_USE_HOMOLOGATION_HEADER:
            headers["x-request-homologation"] = "true"
        return headers

    def _url(self, path: str) -> str:
        return f"{IFOOD_API_BASE.rstrip('/')}/{path.lstrip('/')}"

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict | None = None,
        allow_empty: bool = False,
    ) -> Any:
        response = requests.request(
            method,
            self._url(path),
            headers=self._headers(),
            params=params,
            timeout=self._timeout,
        )
        if allow_empty and response.status_code == 204:
            return None
        response.raise_for_status()
        if not response.content:
            return None
        return response.json()

    def list_merchants(self) -> list[dict]:
        data = self._request("GET", "/merchant/v1.0/merchants")
        return data if isinstance(data, list) else []

    def poll_order_events(self) -> list[dict]:
        """Order module event queue (empty queue → HTTP 204)."""
        data = self._request("GET", "/order/v1.0/events:polling", allow_empty=True)
        if data is None:
            return []
        if isinstance(data, list):
            return data
        return data.get("events") or data.get("items") or []

    def get_order(self, order_id: str) -> dict:
        return self._request("GET", f"/order/v1.0/orders/{order_id}")

    def list_sales(
        self,
        merchant_id: str,
        *,
        begin: date,
        end: date,
        page: int = 1,
    ) -> dict:
        """Financial Sales API — primary source for D-1 order ids + amounts."""
        return self._request(
            "GET",
            f"/financial/v3.0/merchants/{merchant_id}/sales",
            params={
                "beginSalesDate": begin.isoformat(),
                "endSalesDate": end.isoformat(),
                "page": str(page),
            },
        )

    def iter_sales_pages(
        self,
        merchant_id: str,
        *,
        begin: date,
        end: date,
        max_pages: int = 100,
    ):
        page = 1
        seen_order_ids: set[str] = set()
        while page <= max_pages:
            payload = self.list_sales(merchant_id, begin=begin, end=end, page=page)
            sales = payload.get("sales") or []
            if not sales:
                break

            order_ids = {s["id"] for s in sales if s.get("id")}
            if order_ids and order_ids <= seen_order_ids:
                break
            seen_order_ids |= order_ids

            yield payload

            # Financial API should advance `page` in the response; homologation fixtures often repeat page 1.
            resp_page = payload.get("page")
            if resp_page is not None and int(resp_page) < page:
                break
            if len(sales) < int(payload.get("size") or len(sales)):
                break

            page += 1

    def iter_review_pages(
        self,
        merchant_id: str,
        *,
        begin: date | None = None,
        end: date | None = None,
        size: int = 50,
        max_pages: int = 100,
    ):
        page = 1
        seen_review_ids: set[str] = set()
        while page <= max_pages:
            payload = self.list_reviews(
                merchant_id,
                begin=begin,
                end=end,
                page=page,
                size=size,
            )
            reviews = payload.get("reviews") or []
            if not reviews:
                break

            review_ids = {str(r.get("id")) for r in reviews if r.get("id")}
            if review_ids and review_ids <= seen_review_ids:
                break
            seen_review_ids |= review_ids

            yield payload

            resp_page = payload.get("page")
            if resp_page is not None and int(resp_page) < page:
                break
            if len(reviews) < int(payload.get("size") or size):
                break

            page += 1

    def list_reviews(
        self,
        merchant_id: str,
        *,
        begin: date | None = None,
        end: date | None = None,
        page: int = 1,
        size: int = 50,
    ) -> dict:
        params: dict[str, str | int] = {"page": page, "size": size}
        if begin:
            params["beginReviewDate"] = begin.isoformat()
        if end:
            params["endReviewDate"] = end.isoformat()
        return self._request(
            "GET",
            f"/review/v2.0/merchants/{merchant_id}/reviews",
            params=params,
        )
