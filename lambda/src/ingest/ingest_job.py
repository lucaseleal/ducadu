from datetime import datetime

from src.config import STORE_TOKENS, build_headers


def main(start_date: datetime, end_date: datetime, incremental: bool = True) -> None:
    # Importações locais para evitar circular import e manter o módulo leve no cold start
    from src.ingest.inventory import main as ingest_inventory
    from src.ingest.sales import main as ingest_sales
    from src.ingest.sales_items import main as ingest_sales_items

    for store, token in STORE_TOKENS.items():
        if not token:
            print(f"[WARN] Token não definido para loja '{store}' — pulando")
            continue

        print(f"\n===== INGEST STORE: {store.upper()} =====")
        headers = build_headers(token)

        ingest_inventory(
            start_date=start_date,
            end_date=end_date,
            headers=headers,
            store=store,
            incremental=incremental,
        )

        ingest_sales(
            start_date=start_date,
            end_date=end_date,
            headers=headers,
            store=store,
            incremental=incremental,
        )

        ingest_sales_items(
            start_date=start_date,
            end_date=end_date,
            headers=headers,
            store=store,
            incremental=incremental,
        )