from src.config import STORE_TOKENS, build_headers
from src.ingest.inventory import main as ingest_inventory_movements
from src.ingest.sales import main as ingest_sales
from src.ingest.sales_items import main as ingest_sales_items
from datetime import datetime, date, time, timedelta

today = datetime.utcnow().date()

start_date = datetime.combine(today - timedelta(days=15), time.min)
end_date = datetime.combine(today, time.max)

def main(start_date: datetime, end_date: datetime, incremental: bool = True):
    for store, token in STORE_TOKENS.items():
        print(f"\n===== INGEST STORE: {store.upper()} =====")

        headers = build_headers(token)

        ingest_inventory_movements(
            start_date=start_date,
            end_date=end_date,
            headers=headers,
            incremental=incremental,
            store=store,
        )

        ingest_sales(
            start_date=start_date,
            end_date=end_date,
            headers=headers,
            incremental=incremental,
            store=store,
        )

        ingest_sales_items(
            start_date=start_date,
            end_date=end_date,
            headers=headers,
            incremental=incremental,
            store=store,
        )

if __name__ == "__main__":
    main(start_date, end_date,incremental = True)