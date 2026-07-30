import json
import os

from src.ingest.sheets import main as ingest_sheets

_SYNC_TOKEN = os.getenv("SHEETS_SYNC_TOKEN")


def lambda_handler(event: dict, context) -> dict:
    # When invoked via Function URL, validate the token
    if event.get("requestContext"):
        headers = {k.lower(): v for k, v in (event.get("headers") or {}).items()}
        if _SYNC_TOKEN and headers.get("x-sync-token") != _SYNC_TOKEN:
            return {"statusCode": 403, "body": json.dumps({"error": "Forbidden"})}

    try:
        ingest_sheets()
        return {"statusCode": 200, "body": json.dumps({"message": "Sheets sync complete"})}
    except Exception as e:
        print(f"[ERROR] Falha no sheets sync: {e}")
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
