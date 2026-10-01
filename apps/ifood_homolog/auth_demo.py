"""Gravação homologação — Authentication (client_credentials). Sem exibir secret."""
from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LAMBDA_ROOT = ROOT / "lambda"
sys.path.insert(0, str(LAMBDA_ROOT))


def load_dotenv() -> None:
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
    load_dotenv()
    client_id = os.getenv("IFOOD_CLIENT_ID", "")
    homolog = os.getenv("IFOOD_USE_HOMOLOGATION", "true")

    print("=== Ducadu — Authentication (homologação) ===")
    print("UTC:", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"))
    print("Ambiente: teste / homologação")
    print("Grant: client_credentials (app centralizado)")
    print("client_id:", client_id or "(não definido)")
    print("x-request-homologation:", homolog)
    print("client_secret: [oculto]")
    print()

    if not client_id:
        print("Defina IFOOD_CLIENT_ID no .env")
        return 1

    from src.ifood.auth import get_access_token
    from src.ifood.client import IfoodClient

    token = get_access_token()
    print("access_token: obtido (JWT, não exibido por completo)")
    print("access_token prefix:", token[:24] + "...")

    merchants = IfoodClient().list_merchants()
    print(f"GET /merchant/v1.0/merchants → {len(merchants)} loja(s)")
    for m in merchants[:5]:
        print(f"  - {m.get('id')} | {m.get('name', '')[:70]}")

    print()
    print("OK — fluxo Authentication demonstrado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
