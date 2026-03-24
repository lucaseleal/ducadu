import json
from datetime import datetime, date, time, timedelta, timezone

from src.ingest.ingest_job import main


def _parse_event(event: dict) -> tuple[datetime, datetime, bool]:
    """
    Lê start_date, end_date e incremental do evento.
    Todos os parâmetros são opcionais.

    Formato esperado no event:
    {
        "start_date": "2026-03-01",   // opcional, default: hoje - 15 dias
        "end_date":   "2026-03-19",   // opcional, default: hoje
        "incremental": true           // opcional, default: true
    }
    """
    today: date = datetime.now(timezone.utc).date()

    raw_start = event.get("start_date")
    raw_end = event.get("end_date")
    incremental: bool = event.get("incremental", False)

    try:
        start_date = datetime.combine(
            datetime.strptime(raw_start, "%Y-%m-%d").date() if raw_start else today - timedelta(days=2),
            time.min,
            tzinfo=timezone.utc,
        )
        end_date = datetime.combine(
            datetime.strptime(raw_end, "%Y-%m-%d").date() if raw_end else today,
            time.max,
            tzinfo=timezone.utc,
        )
    except ValueError as e:
        raise ValueError(f"Formato de data inválido: {e}. Use YYYY-MM-DD.") from e

    if start_date > end_date:
        raise ValueError(f"start_date ({raw_start}) não pode ser maior que end_date ({raw_end})")

    return start_date, end_date, incremental


def lambda_handler(event: dict, context) -> dict:
    print(f"[EVENT] {json.dumps(event)}")

    try:
        start_date, end_date, incremental = _parse_event(event)

        print(f"[CONFIG] start={start_date.date()} end={end_date.date()} incremental={incremental}")

        main(start_date=start_date, end_date=end_date, incremental=incremental)

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Ingestion completed",
                "start_date": str(start_date.date()),
                "end_date": str(end_date.date()),
                "incremental": incremental,
            }),
        }

    except ValueError as e:
        print(f"[ERROR] Parâmetro inválido: {e}")
        return {
            "statusCode": 400,
            "body": json.dumps({"error": str(e)}),
        }

    except Exception as e:
        print(f"[ERROR] Falha na ingestão: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)}),
        }