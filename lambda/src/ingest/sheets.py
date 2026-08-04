import base64
import json
import os
from datetime import datetime, timezone

import gspread

from src.db import get_conn, upsert, execute

SPREADSHEET_ID = os.getenv("SHEETS_SPREADSHEET_ID")
SA_JSON_B64    = os.getenv("GOOGLE_SA_JSON_B64")


def _gc():
    sa = json.loads(base64.b64decode((SA_JSON_B64 or "") + "==").decode())
    return gspread.service_account_from_dict(sa)


def _rows(gc, tab: str) -> list[dict]:
    return gc.open_by_key(SPREADSHEET_ID).worksheet(tab).get_all_records()


INSERT_DIM_LOJAS_SQL = """
INSERT INTO dim_lojas (id, loja)
VALUES (%s, %s)
"""

INSERT_DIM_PRODUTOS_SQL = """
INSERT INTO dim_produtos (nome_origem, nome_destino, categoria, origem_tipo)
VALUES (%s, %s, %s, %s)
"""

INSERT_FICHA_TECNICA_SQL = """
INSERT INTO ficha_tecnica (item, ingrediente, quantidade, unidade_medida)
VALUES (%s, %s, %s, %s)
"""


def _ingest_dim_lojas(conn, gc) -> None:
    rows = [(r["id"], r["loja"]) for r in _rows(gc, "de-para lojas")]
    execute(conn, "TRUNCATE TABLE dim_lojas")
    if rows:
        upsert(conn, INSERT_DIM_LOJAS_SQL, rows)
    print(f"[SHEETS] dim_lojas: {len(rows)} linhas")


def _ingest_dim_produtos(conn, gc) -> None:
    rows = [
        (r["nome_origem"], r["nome_destino"], r.get("categoria"), r.get("origem_tipo"))
        for r in _rows(gc, "de-para produtos")
    ]
    execute(conn, "TRUNCATE TABLE dim_produtos")
    if rows:
        upsert(conn, INSERT_DIM_PRODUTOS_SQL, rows)
    print(f"[SHEETS] dim_produtos: {len(rows)} linhas")


def _ingest_ficha_tecnica(conn, gc) -> None:
    rows = [
        (r["item"], r["ingrediente"], str(r["quantidade"]).replace(",", ".") if r.get("quantidade") not in (None, "") else None, r["unidade_medida"])
        for r in _rows(gc, "FT")
    ]
    execute(conn, "TRUNCATE TABLE ficha_tecnica")
    if rows:
        upsert(conn, INSERT_FICHA_TECNICA_SQL, rows)
    print(f"[SHEETS] ficha_tecnica: {len(rows)} linhas")


def _log_run(gc, status_code: int, message: str) -> None:
    try:
        ws = gc.open_by_key(SPREADSHEET_ID).worksheet("run_log")
        ws.append_row([
            datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            str(status_code),
            message,
        ])
    except Exception as e:
        print(f"[WARN] Falha ao escrever run_log: {e}")


def main() -> None:
    if not SPREADSHEET_ID or not SA_JSON_B64:
        print("[WARN] SHEETS_SPREADSHEET_ID ou GOOGLE_SA_JSON_B64 não definidos — pulando")
        return

    gc        = _gc()
    conn      = get_conn()
    error_msg = None

    try:
        _ingest_dim_lojas(conn, gc)
        _ingest_dim_produtos(conn, gc)
        _ingest_ficha_tecnica(conn, gc)
    except Exception as e:
        error_msg = str(e)
        raise
    finally:
        conn.close()
        # _log_run(gc, 500 if error_msg else 200, error_msg or "Sync concluído com sucesso")

    print("[DONE] Google Sheets ingest concluído")
