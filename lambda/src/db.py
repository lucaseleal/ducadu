import psycopg
from psycopg.rows import tuple_row
from typing import LiteralString
from src.config import DATABASE_URL


def get_conn() -> psycopg.Connection:
    if not DATABASE_URL:
        raise ValueError("[FATAL] DATABASE_URL não definida")
    return psycopg.connect(DATABASE_URL, row_factory=tuple_row)


def upsert(conn: psycopg.Connection, sql: LiteralString, rows: list, page_size: int = 1000) -> None:
    if not rows:
        return

    try:
        with conn.cursor() as cur:
            for i in range(0, len(rows), page_size):
                cur.executemany(sql, rows[i : i + page_size])
        conn.commit()

    except Exception:
        conn.rollback()
        raise