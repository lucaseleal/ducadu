import json
import os
import boto3
from datetime import datetime, date, time, timedelta, timezone

from src.ingest.ingest_job import main


def _parse_event(event: dict) -> tuple[datetime, datetime, bool]:
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


def _schedule_retry(event: dict, function_arn: str, delay_minutes: int = 60) -> None:
    scheduler_role_arn = os.getenv("SCHEDULER_ROLE_ARN")
    if not scheduler_role_arn:
        print("[WARN] SCHEDULER_ROLE_ARN não definida — retry não agendado")
        return

    fire_at = datetime.now(timezone.utc) + timedelta(minutes=delay_minutes)
    schedule_name = f"ingest-retry-{fire_at.strftime('%Y%m%dT%H%M%S')}"

    try:
        boto3.client("scheduler", region_name="sa-east-1").create_schedule(
            Name=schedule_name,
            ScheduleExpression=f"at({fire_at.strftime('%Y-%m-%dT%H:%M:%S')})",
            ScheduleExpressionTimezone="UTC",
            FlexibleTimeWindow={"Mode": "OFF"},
            Target={
                "Arn": function_arn,
                "RoleArn": scheduler_role_arn,
                "Input": json.dumps(event),
            },
            ActionAfterCompletion="DELETE",
        )
        print(f"[RETRY-SCHEDULED] Retry agendado para {fire_at.strftime('%Y-%m-%dT%H:%M:%S')} UTC — {schedule_name}")
    except Exception as e:
        print(f"[WARN] Falha ao agendar retry: {e}")


def lambda_handler(event: dict, context) -> dict:
    print(f"[EVENT] {json.dumps(event)}")

    try:
        start_date, end_date, incremental = _parse_event(event)
    except ValueError as e:
        print(f"[ERROR] Parâmetro inválido: {e}")
        return {"statusCode": 400, "body": json.dumps({"error": str(e)})}

    print(f"[CONFIG] start={start_date.date()} end={end_date.date()} incremental={incremental}")

    try:
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

    except Exception as e:
        print(f"[ERROR] Falha na ingestão: {e}")

        retry_event = {
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "incremental": incremental,
        }
        _schedule_retry(retry_event, context.invoked_function_arn)

        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
