import json
import os
import re
from datetime import date, datetime, timedelta
from typing import Any

from django.core.management.base import CommandError
from django.utils import timezone

from apps.monitoring.utils import hms_to_seconds

SOURCE_NAME = "LH_ALIVE"


def add_date_filter_arguments(parser) -> None:
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--all",
        action="store_true",
        help="Importar todos os registros disponíveis (sem filtro de data)",
    )
    group.add_argument(
        "--today",
        action="store_true",
        help="Importa/apaga apenas registros do dia atual (padrao).",
    )
    group.add_argument(
        "--date",
        type=str,
        help="Data especifica no formato YYYY-MM-DD.",
    )
    group.add_argument(
        "--days",
        type=int,
        help="Ultimos N dias (incluindo hoje).",
    )
    parser.add_argument(
        "--from",
        dest="date_from",
        type=str,
        help="Data inicial no formato YYYY-MM-DD",
    )
    parser.add_argument(
        "--to",
        dest="date_to",
        type=str,
        help="Data final no formato YYYY-MM-DD",
    )


def resolve_date_window(options: dict[str, Any]) -> tuple[date | None, date | None]:
    all_option = bool(options.get("all"))
    date_option = options.get("date")
    days_option = options.get("days")
    today_option = bool(options.get("today"))
    date_from_option = options.get("date_from")
    date_to_option = options.get("date_to")

    if bool(date_from_option) != bool(date_to_option):
        raise CommandError("Use --from e --to juntos.")

    if date_from_option and date_to_option:
        if any([all_option, today_option, bool(date_option), days_option is not None]):
            raise CommandError(
                "Nao combine --from/--to com --all, --today, --date ou --days."
            )
        try:
            start_date = date.fromisoformat(date_from_option)
        except ValueError as exc:
            raise CommandError("Formato invalido para --from. Use YYYY-MM-DD.") from exc
        try:
            end_date = date.fromisoformat(date_to_option)
        except ValueError as exc:
            raise CommandError("Formato invalido para --to. Use YYYY-MM-DD.") from exc
        if start_date > end_date:
            raise CommandError("--from nao pode ser maior que --to.")
        return start_date, end_date

    selected_flags = [
        flag_name
        for flag_name, enabled in (
            ("--all", all_option),
            ("--date", bool(date_option)),
            ("--days", days_option is not None),
            ("--today", today_option),
        )
        if enabled
    ]
    if len(selected_flags) > 1:
        raise CommandError(
            "Flags conflitantes. Use apenas uma entre: --all, --date, --days, --today."
        )

    if all_option:
        return None, None

    if date_option:
        try:
            target_date = date.fromisoformat(date_option)
        except ValueError as exc:
            raise CommandError("Formato invalido para --date. Use YYYY-MM-DD.") from exc
        return target_date, target_date

    if days_option is not None:
        if days_option < 1:
            raise CommandError("--days deve ser maior ou igual a 1.")
        end_date = timezone.localdate()
        start_date = end_date - timedelta(days=days_option - 1)
        return start_date, end_date

    today = timezone.localdate()
    return today, today


def sql_date_where(column_name: str) -> str:
    return f"{column_name} >= ? AND {column_name} <= ?"


def sql_datetime_day_range_where(column_name: str) -> str:
    return f"{column_name} >= ? AND {column_name} < DATEADD(day, 1, ?)"


def sql_date_params(start_date: date, end_date: date) -> list[date]:
    return [start_date, end_date]


def connect_legacy():
    try:
        import pyodbc
    except ImportError as exc:
        raise CommandError(
            "pyodbc nao esta instalado. Instale para executar importacao do LH_ALIVE."
        ) from exc

    driver = os.getenv("LEGACY_DRIVER")
    server = os.getenv("LEGACY_SERVER")
    port = os.getenv("LEGACY_PORT")
    user = os.getenv("LEGACY_USER")
    password = os.getenv("LEGACY_PASSWORD")
    database = os.getenv("LEGACY_DATABASE")

    missing = [
        key
        for key, value in (
            ("LEGACY_DRIVER", driver),
            ("LEGACY_SERVER", server),
            ("LEGACY_USER", user),
            ("LEGACY_PASSWORD", password),
            ("LEGACY_DATABASE", database),
        )
        if not value
    ]
    if missing:
        raise CommandError(
            f"Variaveis de ambiente ausentes para legado: {', '.join(missing)}"
        )

    server_part = str(server) if not port else f"{server},{port}"
    conn_parts = [
        f"DRIVER={{{driver}}}",
        f"SERVER={server_part}",
        f"DATABASE={database}",
        f"UID={user}",
        f"PWD={password}",
        "TrustServerCertificate=yes",
    ]
    return pyodbc.connect(";".join(conn_parts))


def get_legacy_schema(default: str = "dbo") -> str:
    schema = os.getenv("LEGACY_SCHEMA", default) or default
    if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", str(schema)):
        raise CommandError(f"Valor invalido para LEGACY_SCHEMA: {schema}")
    return str(schema)


def fetch_rows(connection, query: str, params: list[Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    cursor = connection.cursor()
    cursor.execute(query, params)
    columns = [desc[0] for desc in cursor.description]
    for raw in cursor.fetchall():
        rows.append(dict(zip(columns, raw)))
    return rows


def get_row_value(row: dict[str, Any], *keys: str):
    for key in keys:
        if key in row:
            return row[key]

    lowered = {str(k).lower(): v for k, v in row.items()}
    for key in keys:
        if key.lower() in lowered:
            return lowered[key.lower()]
    return None


def to_clean_str(value: Any) -> str | None:
    if value is None:
        return None
    cleaned = str(value).strip()
    return cleaned or None


def to_bigint(value: Any) -> int | None:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def to_positive_int(value: Any) -> int | None:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def to_date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        try:
            return date.fromisoformat(value[:10])
        except ValueError:
            return None
    return None


def to_aware_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if not isinstance(value, datetime):
        return None
    if timezone.is_naive(value):
        return timezone.make_aware(value, timezone.get_current_timezone())
    return timezone.localtime(value, timezone.get_current_timezone())


def json_safe(payload: Any) -> Any:
    def _default(value: Any):
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, date):
            return value.isoformat()
        return str(value)

    return json.loads(json.dumps(payload, default=_default))
