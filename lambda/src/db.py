import psycopg2
from psycopg2.extras import execute_values, execute_batch
from src.config import DATABASE_URL

def get_conn():
    return psycopg2.connect(DATABASE_URL)

def upsert(conn, sql, rows, mode="batch", page_size=1000):
    if not rows:
        return

    try:
        with conn.cursor() as cur:
            if mode == "values":
                execute_values(cur, sql, rows, page_size=page_size)

            elif mode == "batch":
                execute_batch(cur, sql, rows, page_size=page_size)

            else:
                raise ValueError(f"Unknown upsert mode: {mode}")

        conn.commit()

    except Exception:
    conn.rollback()
    raise