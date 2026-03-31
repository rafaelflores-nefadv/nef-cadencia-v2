from django.utils import timezone

from .models import JobRunStatusChoices


def hms_to_seconds(value) -> int | None:
    if value is None:
        return None

    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        parts = text.split(":")
        if len(parts) != 3:
            return None
        try:
            hours, minutes, seconds = (int(part) for part in parts)
        except ValueError:
            return None
        if hours < 0 or minutes < 0 or seconds < 0:
            return None
        if minutes > 59 or seconds > 59:
            return None
        return hours * 3600 + minutes * 60 + seconds

    # Support objects returned by pyodbc for TIME columns.
    if hasattr(value, "hour") and hasattr(value, "minute") and hasattr(value, "second"):
        hours = int(getattr(value, "hour", 0))
        minutes = int(getattr(value, "minute", 0))
        seconds = int(getattr(value, "second", 0))
        if hours < 0 or minutes < 0 or seconds < 0:
            return None
        return hours * 3600 + minutes * 60 + seconds

    return None


def format_seconds_hhmmss(total_seconds: int | None) -> str:
    if total_seconds is None:
        return "00:00:00"
    total_seconds = max(int(total_seconds), 0)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def format_seconds_hhmm(total_seconds: int | None) -> str:
    # Backward-compatible alias for existing call sites.
    return format_seconds_hhmmss(total_seconds)


def format_run_duration_hhmmss(run) -> str:
    if not run or not run.started_at:
        return "-"

    end_time = run.finished_at
    if end_time is None and run.status == JobRunStatusChoices.RUNNING:
        end_time = timezone.now()
    if end_time is None:
        return "-"

    total_seconds = int((end_time - run.started_at).total_seconds())
    return format_seconds_hhmmss(total_seconds)


def format_run_duration_hhmm(run) -> str:
    # Backward-compatible alias for existing call sites.
    return format_run_duration_hhmmss(run)
