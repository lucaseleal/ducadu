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


def _conn_params() -> tuple[str, dict]:
    """Retorna (url, kwargs_extras) para psycopg.connect()."""
    if not _CF_TUNNEL_HOST:
        return DATABASE_URL or "", {}

    db_url = DATABASE_URL or ""

    # Extrai endpoint ID do hostname original para roteamento NeonDB sem SNI
    # ex: ep-ancient-haze-acllxf1k-pooler.sa-east-1.aws.neon.tech → ep-ancient-haze-acllxf1k-pooler
    host_match = re.search(r"@([^/?:]+)", db_url)
    endpoint_id = host_match.group(1).split(".")[0] if host_match else ""

    # Substitui host pelo proxy local
    url = re.sub(r"@[^/?]+", f"@127.0.0.1:{_PROXY_PORT}", db_url)

    # Remove parâmetros incompatíveis com proxy TCP:
    # - channel_binding: NeonDB não detecta TLS end-to-end via proxy (SCRAM-SHA-256-PLUS indisponível)
    # - options: pode ter "=" no valor (ex: -c gai_family=ipv4) que psycopg3 rejeita na URI;
    #            será substituído pelo endpoint ID abaixo via kwarg
    for param in ("channel_binding", "options"):
        url = re.sub(rf"&{param}=[^&]*", "", url)
        url = re.sub(rf"\?{param}=[^&]*&", "?", url)
        url = re.sub(rf"\?{param}=[^&]*$", "", url)

    # options passado como kwarg para evitar rejeição do psycopg3 ao "=" dentro do valor de URI
    return url, {"options": f"endpoint={endpoint_id}"}


def get_conn() -> psycopg.Connection:
    if not DATABASE_URL:
        raise ValueError("[FATAL] DATABASE_URL não definida")
    _ensure_tunnel()
    url, extra = _conn_params()
    return psycopg.connect(url, row_factory=tuple_row, **extra)


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