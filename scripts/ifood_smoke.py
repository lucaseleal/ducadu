"""Local smoke test: OAuth client_credentials + list merchants. Reads .env from repo root."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://merchant-api.ifood.com.br"


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
    client_id = os.environ.get("IFOOD_CLIENT_ID")
    client_secret = os.environ.get("IFOOD_CLIENT_SECRET")
    if not client_id or not client_secret:
        print("Missing IFOOD_CLIENT_ID or IFOOD_CLIENT_SECRET in .env", file=sys.stderr)
        return 1

    with httpx.Client(timeout=30) as client:
        token_resp = client.post(
            f"{BASE}/authentication/v1.0/oauth/token",
            data={
                "clientId": client_id,
                "clientSecret": client_secret,
                "grantType": "client_credentials",
            },
        )
        print("token_status", token_resp.status_code)
        if token_resp.status_code != 200:
            print(token_resp.text[:800], file=sys.stderr)
            return 1

        data = token_resp.json()
        token = data.get("accessToken") or data.get("access_token")
        if not token:
            print("No access token in response", file=sys.stderr)
            return 1

        print("expires_in", data.get("expiresIn") or data.get("expires_in"))

        merchants_resp = client.get(
            f"{BASE}/merchant/v1.0/merchants",
            headers={"Authorization": f"Bearer {token}"},
        )
        print("merchants_status", merchants_resp.status_code)
        if merchants_resp.status_code != 200:
            print(merchants_resp.text[:800], file=sys.stderr)
            return 1

        merchants = merchants_resp.json()
        print("merchant_count", len(merchants))
        for m in merchants:
            mid = m.get("id")
            name = (m.get("name") or "")[:80]
            print(f"  {mid}  {name}")

        expected = os.environ.get("IFOOD_TEST_MERCHANT_ID", "8021db2f-8a8b-498b-9461-1c8825d3cde6")
        ids = {m.get("id") for m in merchants}
        if expected in ids:
            print("ok: test merchant visible in token scope")
        else:
            print(f"warn: expected merchant {expected} not in list", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
