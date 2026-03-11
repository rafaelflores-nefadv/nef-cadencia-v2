from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Mapping

from django.utils import timezone
from django.utils.dateparse import parse_date

MONTH_OPTIONS = [
    {"value": 1, "label": "Janeiro"},
    {"value": 2, "label": "Fevereiro"},
    {"value": 3, "label": "Marco"},
    {"value": 4, "label": "Abril"},
    {"value": 5, "label": "Maio"},
    {"value": 6, "label": "Junho"},
    {"value": 7, "label": "Julho"},
    {"value": 8, "label": "Agosto"},
    {"value": 9, "label": "Setembro"},
    {"value": 10, "label": "Outubro"},
    {"value": 11, "label": "Novembro"},
    {"value": 12, "label": "Dezembro"},
]

QUICK_RANGE_OPTIONS = [
    {"key": "today", "label": "Hoje"},
    {"key": "yesterday", "label": "Ontem"},
    {"key": "last_7_days", "label": "Ultimos 7 dias"},
    {"key": "this_month", "label": "Este mes"},
    {"key": "last_month", "label": "Mes passado"},
    {"key": "this_year", "label": "Este ano"},
]

QUICK_RANGE_KEYS = {item["key"] for item in QUICK_RANGE_OPTIONS}


@dataclass(frozen=True)
class DashboardPeriodFilter:
    mode: str
    date_from: date
    date_to: date
    dt_start: datetime
    dt_end: datetime
    selected_date: date
    selected_data_ref: date | None
    selected_year: int | None
    selected_month: int | None
    selected_date_from: date | None
    selected_date_to: date | None
    selected_quick_range: str
    warning: str | None

    @property
    def is_single_day(self) -> bool:
        return self.date_from == self.date_to

    @property
    def period_label(self) -> str:
        return format_period_label(self.date_from, self.date_to)

    @property
    def scope_label(self) -> str:
        return "dia" if self.is_single_day else "periodo"


def format_period_label(date_from: date, date_to: date) -> str:
    if date_from == date_to:
        return date_from.strftime("%d/%m/%Y")
    return f"{date_from:%d/%m/%Y} ate {date_to:%d/%m/%Y}"


def format_period_command_args(date_from: date, date_to: date) -> str:
    if date_from == date_to:
        return f"--date {date_from.isoformat()}"
    return f"--from {date_from.isoformat()} --to {date_to.isoformat()}"


def resolve_dashboard_period_filter(params: Mapping[str, str]) -> DashboardPeriodFilter:
    today = timezone.localdate()
    current_tz = timezone.get_current_timezone()

    selected_quick_range = (params.get("quick_range") or "").strip().lower()
    selected_data_ref = _parse_date_param(params, "data_ref")
    selected_date_from = _parse_date_param(params, "date_from")
    selected_date_to = _parse_date_param(params, "date_to")
    selected_year = _parse_int_param(params, "year", min_value=2000, max_value=2100)
    selected_month = _parse_int_param(params, "month", min_value=1, max_value=12)

    warning: str | None = None
    date_from: date | None = None
    date_to: date | None = None
    mode = ""

    if selected_date_from and selected_date_to:
        if selected_date_from > selected_date_to:
            warning = "Data inicial nao pode ser maior que data final."
        else:
            date_from = selected_date_from
            date_to = selected_date_to
            mode = "custom_range"
    elif selected_date_from or selected_date_to:
        warning = "Informe data inicial e data final para usar periodo personalizado."

    if date_from is None or date_to is None:
        if selected_year and selected_month:
            month_end_day = _month_last_day(selected_year, selected_month)
            date_from = date(selected_year, selected_month, 1)
            date_to = date(selected_year, selected_month, month_end_day)
            mode = "year_month"
        elif selected_year:
            date_from = date(selected_year, 1, 1)
            date_to = date(selected_year, 12, 31)
            mode = "year"
        elif selected_month:
            if warning is None:
                warning = "Filtro por mes exige ano."

    if date_from is None or date_to is None:
        if selected_quick_range in QUICK_RANGE_KEYS:
            date_from, date_to = _resolve_shortcut_range(selected_quick_range, today)
            mode = "shortcut"
            selected_date_from = date_from
            selected_date_to = date_to
            selected_year = None
            selected_month = None

    if date_from is None or date_to is None:
        if selected_data_ref:
            date_from = selected_data_ref
            date_to = selected_data_ref
            mode = "legacy_day"
        else:
            date_from = today
            date_to = today
            mode = "default_today"

    dt_start = timezone.make_aware(datetime.combine(date_from, time.min), current_tz)
    dt_end = timezone.make_aware(datetime.combine(date_to + timedelta(days=1), time.min), current_tz)
    if selected_data_ref:
        selected_date = selected_data_ref
    elif date_from <= today <= date_to:
        selected_date = today
    else:
        selected_date = date_to

    return DashboardPeriodFilter(
        mode=mode,
        date_from=date_from,
        date_to=date_to,
        dt_start=dt_start,
        dt_end=dt_end,
        selected_date=selected_date,
        selected_data_ref=selected_data_ref,
        selected_year=selected_year,
        selected_month=selected_month,
        selected_date_from=selected_date_from,
        selected_date_to=selected_date_to,
        selected_quick_range=selected_quick_range if selected_quick_range in QUICK_RANGE_KEYS else "",
        warning=warning,
    )


def _resolve_shortcut_range(shortcut_key: str, today: date) -> tuple[date, date]:
    if shortcut_key == "today":
        return today, today
    if shortcut_key == "yesterday":
        yesterday = today - timedelta(days=1)
        return yesterday, yesterday
    if shortcut_key == "last_7_days":
        return today - timedelta(days=6), today
    if shortcut_key == "this_month":
        start = today.replace(day=1)
        return start, today
    if shortcut_key == "last_month":
        first_day_this_month = today.replace(day=1)
        end = first_day_this_month - timedelta(days=1)
        start = end.replace(day=1)
        return start, end
    if shortcut_key == "this_year":
        return date(today.year, 1, 1), today
    return today, today


def _parse_date_param(params: Mapping[str, str], key: str) -> date | None:
    raw_value = (params.get(key) or "").strip()
    if not raw_value:
        return None
    return parse_date(raw_value)


def _parse_int_param(
    params: Mapping[str, str],
    key: str,
    *,
    min_value: int,
    max_value: int,
) -> int | None:
    raw_value = (params.get(key) or "").strip()
    if not raw_value:
        return None
    try:
        parsed = int(raw_value)
    except (TypeError, ValueError):
        return None
    if parsed < min_value or parsed > max_value:
        return None
    return parsed


def _month_last_day(year: int, month: int) -> int:
    if month == 12:
        next_month = date(year + 1, 1, 1)
    else:
        next_month = date(year, month + 1, 1)
    return (next_month - timedelta(days=1)).day
