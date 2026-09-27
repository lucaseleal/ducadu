"""Run iFood D-1 ingest locally (requires Neon IP allowlist + AWS creds for S3 landing)."""
from __future__ import annotations

import os
import sys
from datetime import datetime, time, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAMBDA_ROOT = ROOT / "lambda"
sys.path.insert(0, str(LAMBDA_ROOT))


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
    day = os.environ.get("IFOOD_INGEST_DAY", "2025-08-01")
    d = datetime.strptime(day, "%Y-%m-%d").date()
    start = datetime.combine(d, time.min, tzinfo=timezone.utc)
    end = datetime.combine(d, time.max, tzinfo=timezone.utc)

    from src.ingest.ifood import main as ingest_main

    ingest_main(start, end, incremental=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
