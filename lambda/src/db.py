import os
import re
import socket
import subprocess
import time

import psycopg
from psycopg.rows import tuple_row
from typing import LiteralString

from src.config import DATABASE_URL

_CF_TUNNEL_HOST   = os.getenv("CF_TUNNEL_HOSTNAME")
_CF_CLIENT_ID     = os.getenv("CF_CLIENT_ID")
_CF_CLIENT_SECRET = os.getenv("CF_CLIENT_SECRET")
_PROXY_PORT       = 15432
_cf_proc: subprocess.Popen | None = None


def _cloudflared_bin() -> str:
    path = "/var/task/cloudflared"
    return path if os.path.exists(path) else "cloudflared"


def _ensure_tunnel() -> None:
    global _cf_proc
    if not _CF_TUNNEL_HOST:
        return
    if _cf_proc and _cf_proc.poll() is None:
        return  # já em execução neste execution environment

    _cf_proc = subprocess.Popen(
        [
            _cloudflared_bin(), "access", "tcp",
            "--hostname",             _CF_TUNNEL_HOST,
            "--url",                  f"localhost:{_PROXY_PORT}",
            "--service-token-id",     _CF_CLIENT_ID     or "",
            "--service-token-secret", _CF_CLIENT_SECRET or "",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", _PROXY_PORT), timeout=0.5):
                print(f"[TUNNEL] cloudflared pronto na porta {_PROXY_PORT}")
                return
        except OSError:
            time.sleep(0.3)

    _cf_proc.kill()
    raise RuntimeError(f"[TUNNEL] cloudflared não ficou pronto em 10s — {_CF_TUNNEL_HOST}")


def _conn_url() -> str:
    if not _CF_TUNNEL_HOST:
        return DATABASE_URL
    # Substitui @host:port pelo proxy local; mantém credenciais, db e opções
    return re.sub(r"@[^/?]+", f"@localhost:{_PROXY_PORT}", DATABASE_URL)


def get_conn() -> psycopg.Connection:
    if not DATABASE_URL:
        raise ValueError("[FATAL] DATABASE_URL não definida")
    _ensure_tunnel()
    return psycopg.connect(_conn_url(), row_factory=tuple_row)


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


def execute(conn: psycopg.Connection, sql: str, params=None) -> None:
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
        conn.commit()
    except Exception:
        conn.rollback()
        raise