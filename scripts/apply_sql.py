"""Apply sql/*.sql to DATABASE_URL (local ops; run once per migration)."""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAMBDA_ROOT = ROOT / "lambda"
sys.path.insert(0, str(LAMBDA_ROOT))

_NEON_IP_ALLOW_HINT = """
Neon rejeitou o IP de saída desta máquina (IP Allow).

WARP (1.1.1.1) troca o egress para IPs Cloudflare (ex.: 104.28.x), mas isso NÃO
equivale ao caminho da Lambda nem libera o banco sozinho — o IP ainda precisa
estar na allowlist OU você precisa usar o mesmo túnel Cloudflare Access da Lambda.

Opções:
  1) No .env, iguais à Lambda: CF_TUNNEL_HOSTNAME, CF_CLIENT_ID, CF_CLIENT_SECRET
     + cloudflared no PATH → o script usa localhost:15432 via `cloudflared access tcp`.
  2) Neon Console → SQL Editor: colar sql/001_ifood_tables.sql (sem IP Allow).
  3) Neon → IP Allow: liberar seu IP fixo (WARP muda; opção 1 ou 2 costuma ser melhor).
"""


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


def main() -> int:
    load_env()
    sql_dir = ROOT / "sql"
    files = sorted(sql_dir.glob("*.sql"))
    if not files:
        print("No sql/*.sql files found")
        return 1

    from src.db import get_conn

    try:
        conn = get_conn()
    except Exception as exc:
        msg = str(exc)
        if "not allowed to connect" in msg.lower():
            print(_NEON_IP_ALLOW_HINT, file=sys.stderr)
        raise
    try:
        for path in files:
            sql = path.read_text(encoding="utf-8")
            print(f"Applying {path.name} ...")
            with conn.cursor() as cur:
                cur.execute(sql)
            conn.commit()
            print(f"OK {path.name}")
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
