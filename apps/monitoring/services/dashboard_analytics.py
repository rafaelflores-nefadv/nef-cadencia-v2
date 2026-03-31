from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, time, timedelta

from django.db.models import Q, Sum
from django.utils import timezone

from apps.monitoring.models import PauseCategoryChoices, PauseClassification
from apps.monitoring.services.pause_classification import (
    UNCLASSIFIED_CATEGORY,
    normalize_pause_name,
    normalize_source,
    resolve_pause_category,
)
from apps.monitoring.services.risk_scoring import RiskScoringConfig
from apps.monitoring.utils import format_seconds_hhmm


def resolve_event_duration_seconds(event_row: dict, *, period_end_dt: datetime | None = None) -> int:
    duration_raw = event_row.get("duracao_seg")
    if duration_raw is not None:
        try:
            return max(0, int(duration_raw))
        except (TypeError, ValueError):
            pass

    start_dt = event_row.get("dt_inicio")
    end_dt = event_row.get("dt_fim")
    if start_dt is None:
        return 0
    if end_dt is None and period_end_dt is not None:
        end_dt = period_end_dt
    if end_dt is None or end_dt <= start_dt:
        return 0
    return int((end_dt - start_dt).total_seconds())


def build_pause_category_map(pause_events_qs) -> dict[tuple[str, str], str]:
    normalized_pairs = {
        (normalize_source(source), normalize_pause_name(name))
        for source, name in pause_events_qs.values_list("source", "nm_pausa")
    }
    normalized_pairs = {pair for pair in normalized_pairs if pair[1]}
    if not normalized_pairs:
        return {}

    normalized_names = {name for _, name in normalized_pairs}
    normalized_sources = {source for source, _ in normalized_pairs if source}
    active_classifications = list(
        PauseClassification.objects.filter(
            is_active=True,
            pause_name_normalized__in=normalized_names,
        )
        .filter(Q(source="") | Q(source__in=normalized_sources))
        .values_list("source", "pause_name_normalized", "category")
    )

    source_specific_map: dict[tuple[str, str], str] = {}
    global_map: dict[str, str] = {}
    for source, pause_name_normalized, category in active_classifications:
        source_normalized = normalize_source(source)
        if source_normalized:
            source_specific_map[(source_normalized, pause_name_normalized)] = category
        else:
            global_map[pause_name_normalized] = category

    category_map: dict[tuple[str, str], str] = {}
    for source_normalized, normalized_name in normalized_pairs:
        category = source_specific_map.get((source_normalized, normalized_name))
        if category is None:
            category = global_map.get(normalized_name)
        if category is None:
            category = resolve_pause_category(normalized_name, source=source_normalized)
        category_map[(source_normalized, normalized_name)] = category
    return category_map


def build_pause_type_rankings(
    pause_events_qs,
    *,
    period_end_dt: datetime,
    limit: int = 6,
) -> tuple[list[dict], list[dict]]:
    aggregates: dict[str, dict] = {}
    for row in pause_events_qs.values("nm_pausa", "duracao_seg", "dt_inicio", "dt_fim"):
        raw_label = str(row.get("nm_pausa") or "").strip()
        label = raw_label or "Sem nome"
        duration_seconds = resolve_event_duration_seconds(row, period_end_dt=period_end_dt)
        item = aggregates.setdefault(
            label,
            {
                "label": label,
                "count": 0,
                "tempo_seg": 0,
            },
        )
        item["count"] += 1
        item["tempo_seg"] += duration_seconds

    by_time = sorted(
        aggregates.values(),
        key=lambda item: (-int(item["tempo_seg"]), -int(item["count"]), str(item["label"]).upper()),
    )[:limit]
    by_count = sorted(
        aggregates.values(),
        key=lambda item: (-int(item["count"]), -int(item["tempo_seg"]), str(item["label"]).upper()),
    )[:limit]

    for collection in (by_time, by_count):
        for item in collection:
            item["tempo_hhmm"] = format_seconds_hhmm(int(item.get("tempo_seg") or 0))
    return by_time, by_count


def build_operational_timeline(
    *,
    period_filter,
    events_qs,
    pause_events_qs,
) -> list[dict]:
    category_map = build_pause_category_map(pause_events_qs)
    timeline = _init_bucket_map(period_filter, fill_zero=True)

    for row in events_qs.values("source", "tp_evento", "nm_pausa", "duracao_seg", "dt_inicio", "dt_fim"):
        start_dt = row.get("dt_inicio")
        if start_dt is None:
            continue
        bucket_key, hour_label = _resolve_bucket(period_filter, start_dt)
        if bucket_key not in timeline:
            continue

        entry = timeline[bucket_key]
        entry["event_count"] += 1

        pause_name = row.get("nm_pausa")
        event_type = str(row.get("tp_evento") or "").upper()
        is_pause = event_type == "PAUSA" or bool(str(pause_name or "").strip())
        if not is_pause:
            continue

        duration_seconds = resolve_event_duration_seconds(row, period_end_dt=period_filter.dt_end)
        entry["pause_count"] += 1
        entry["pause_seconds"] += duration_seconds

        source_normalized = normalize_source(row.get("source"))
        normalized_name = normalize_pause_name(pause_name)
        category = category_map.get((source_normalized, normalized_name), UNCLASSIFIED_CATEGORY)
        if category in {PauseCategoryChoices.HARMFUL, UNCLASSIFIED_CATEGORY}:
            entry["critical_count"] += 1
        if hour_label:
            entry["hour_label"] = hour_label

    items = list(timeline.values())
    for item in items:
        item["pause_hhmm"] = format_seconds_hhmm(int(item.get("pause_seconds") or 0))
    return items


def build_productivity_evolution(
    *,
    period_filter,
    events_qs,
    pause_events_qs,
    workday_qs,
    stats_qs,
) -> list[dict]:
    pause_category_map = build_pause_category_map(pause_events_qs)
    pause_by_day_operator: dict[tuple[date, int], dict] = {}
    for row in pause_events_qs.values("cd_operador", "source", "nm_pausa", "duracao_seg", "dt_inicio", "dt_fim"):
        cd_operador = row.get("cd_operador")
        start_dt = row.get("dt_inicio")
        if cd_operador is None or start_dt is None:
            continue
        day_key = _to_local_date(start_dt)
        duration_seconds = resolve_event_duration_seconds(
            row,
            period_end_dt=_bucket_period_end(period_filter, day_key),
        )
        source_normalized = normalize_source(row.get("source"))
        normalized_name = normalize_pause_name(row.get("nm_pausa"))
        category = pause_category_map.get((source_normalized, normalized_name), UNCLASSIFIED_CATEGORY)

        operator_key = (day_key, int(cd_operador))
        item = pause_by_day_operator.setdefault(operator_key, _empty_pause_info())
        item["qtd_pausas"] += 1
        item["tempo_pausas_seg"] += duration_seconds
        if category == PauseCategoryChoices.LEGAL:
            item["qtd_produtivas"] += 1
            item["tempo_produtivo_seg"] += duration_seconds
        elif category == PauseCategoryChoices.NEUTRAL:
            item["qtd_neutras"] += 1
            item["tempo_neutro_seg"] += duration_seconds
        elif category == PauseCategoryChoices.HARMFUL:
            item["qtd_improdutivas"] += 1
            item["tempo_improdutivo_seg"] += duration_seconds
        else:
            item["qtd_nao_classificadas"] += 1
            item["tempo_nao_classificado_seg"] += duration_seconds

    logged_by_day_operator = {
        (row["work_date"], int(row["cd_operador"])): int(row["logged_seg"] or 0)
        for row in workday_qs.values("work_date", "cd_operador")
        .annotate(logged_seg=Sum("duracao_seg"))
        if row.get("work_date") and row.get("cd_operador") is not None
    }

    stats_by_day_operator: dict[tuple[date, int], dict] = {}
    for row in stats_qs.values(
        "data_ref",
        "cd_operador",
        "qtd_pausas",
        "tempo_pausas_seg",
        "ultimo_logon",
        "ultimo_logoff",
    ):
        data_ref = row.get("data_ref")
        cd_operador = row.get("cd_operador")
        if data_ref is None or cd_operador is None:
            continue
        logon_dt = row.get("ultimo_logon")
        logoff_dt = row.get("ultimo_logoff")
        tempo_logado_seg = 0
        if logon_dt and logoff_dt and logoff_dt > logon_dt:
            tempo_logado_seg = int((logoff_dt - logon_dt).total_seconds())
        stats_by_day_operator[(data_ref, int(cd_operador))] = {
            "qtd_pausas": int(row.get("qtd_pausas") or 0),
            "tempo_pausas_seg": int(row.get("tempo_pausas_seg") or 0),
            "tempo_logado_seg": max(0, tempo_logado_seg),
        }

    estimated_logged_by_day_operator = _estimate_login_seconds_by_day_operator(
        events_qs=events_qs,
        period_filter=period_filter,
    )
    event_span_by_day_operator = _estimate_event_span_seconds_by_day_operator(
        events_qs=events_qs,
        period_filter=period_filter,
    )

    summary_by_day = _init_bucket_map(period_filter, fill_zero=False)
    operator_day_keys = {
        *pause_by_day_operator.keys(),
        *logged_by_day_operator.keys(),
        *stats_by_day_operator.keys(),
        *estimated_logged_by_day_operator.keys(),
        *event_span_by_day_operator.keys(),
    }

    for day_key, cd_operador in sorted(operator_day_keys):
        pause_info = dict(pause_by_day_operator.get((day_key, cd_operador), {}))
        stats_info = stats_by_day_operator.get((day_key, cd_operador), {})
        if not pause_info and stats_info:
            stats_pause_count = int(stats_info.get("qtd_pausas") or 0)
            stats_pause_seconds = int(stats_info.get("tempo_pausas_seg") or 0)
            pause_info = {
                "qtd_pausas": stats_pause_count,
                "tempo_pausas_seg": stats_pause_seconds,
                "qtd_produtivas": 0,
                "qtd_neutras": 0,
                "qtd_improdutivas": 0,
                "qtd_nao_classificadas": stats_pause_count,
                "tempo_produtivo_seg": 0,
                "tempo_neutro_seg": 0,
                "tempo_improdutivo_seg": 0,
                "tempo_nao_classificado_seg": stats_pause_seconds,
            }

        logged_seg = int(
            logged_by_day_operator.get(
                (day_key, cd_operador),
                estimated_logged_by_day_operator.get(
                    (day_key, cd_operador),
                    event_span_by_day_operator.get((day_key, cd_operador), 0),
                ),
            )
            or 0
        )
        if logged_seg <= 0:
            logged_seg = int(stats_info.get("tempo_logado_seg") or 0)

        harmful_seg = int(pause_info.get("tempo_improdutivo_seg") or 0)
        neutral_seg = int(pause_info.get("tempo_neutro_seg") or 0)
        unclassified_seg = int(pause_info.get("tempo_nao_classificado_seg") or 0)
        productive_seg, _, _ = resolve_productivity_seconds(
            logged_seg=logged_seg,
            pause_info=pause_info,
            stats_info=stats_info,
        )
        total_pause_seg = int(pause_info.get("tempo_pausas_seg") or 0)

        day_summary = summary_by_day.setdefault(
            day_key,
            {
                "date_iso": day_key.isoformat(),
                "label": day_key.strftime("%d/%m"),
                "logged_seconds": 0,
                "productive_seconds": 0,
                "improductive_seconds": 0,
                "neutral_seconds": 0,
                "unclassified_seconds": 0,
                "active_agents": 0,
            },
        )
        day_summary["logged_seconds"] += logged_seg
        day_summary["productive_seconds"] += productive_seg
        day_summary["improductive_seconds"] += harmful_seg
        day_summary["neutral_seconds"] += neutral_seg
        day_summary["unclassified_seconds"] += unclassified_seg
        if logged_seg > 0 or total_pause_seg > 0:
            day_summary["active_agents"] += 1

    items: list[dict] = []
    current_day = period_filter.date_from
    while current_day <= period_filter.date_to:
        item = summary_by_day.get(
            current_day,
            {
                "date_iso": current_day.isoformat(),
                "label": current_day.strftime("%d/%m"),
                "logged_seconds": 0,
                "productive_seconds": 0,
                "improductive_seconds": 0,
                "neutral_seconds": 0,
                "unclassified_seconds": 0,
                "active_agents": 0,
            },
        )
        logged_seconds = int(item.get("logged_seconds") or 0)
        productive_seconds = int(item.get("productive_seconds") or 0)
        improductive_seconds = int(item.get("improductive_seconds") or 0)
        item["productive_hhmm"] = format_seconds_hhmm(productive_seconds)
        item["improductive_hhmm"] = format_seconds_hhmm(improductive_seconds)
        item["occupancy_pct"] = round((productive_seconds / logged_seconds) * 100, 2) if logged_seconds else 0.0
        items.append(item)
        current_day += timedelta(days=1)

    return items


def resolve_productivity_seconds(
    *,
    logged_seg: int,
    pause_info: dict,
    stats_info: dict,
) -> tuple[int, int, str]:
    productive_classified_seg = int(pause_info.get("tempo_produtivo_seg") or 0)
    total_pause_seg = int(pause_info.get("tempo_pausas_seg") or 0)
    stats_pause_seg = int(stats_info.get("tempo_pausas_seg") or 0)

    if productive_classified_seg > 0:
        return productive_classified_seg, 0, "classified_productive"
    if total_pause_seg > 0:
        return max(0, logged_seg - total_pause_seg), total_pause_seg, "total_pause_fallback"
    if stats_pause_seg > 0:
        return max(0, logged_seg - stats_pause_seg), stats_pause_seg, "day_stats_pause_fallback"
    if logged_seg > 0:
        return logged_seg, 0, "logged_time_fallback"
    return 0, 0, "no_logged_time"


def build_risk_radar_dimensions(
    *,
    operator_metrics: list[dict],
    no_activity_agents: list[dict],
    active_agents_count: int,
    risk_config: RiskScoringConfig,
) -> list[dict]:
    logged_metrics = [
        item
        for item in operator_metrics
        if int(item.get("tempo_logado_seg") or 0) > 0
    ]
    total_logged_seconds = sum(int(item.get("tempo_logado_seg") or 0) for item in logged_metrics)
    total_harmful_seconds = sum(int(item.get("tempo_improdutivo_seg") or 0) for item in logged_metrics)
    total_unclassified_seconds = sum(int(item.get("tempo_nao_classificado_seg") or 0) for item in logged_metrics)
    total_harmful_events = sum(int(item.get("qtd_improdutivas") or 0) for item in logged_metrics)

    harmful_minutes_pressure = 0.0
    harmful_events_pressure = 0.0
    low_occupancy_pressure = 0.0
    unclassified_pressure = 0.0
    no_activity_pressure = 0.0

    if logged_metrics:
        operator_count = len(logged_metrics)
        harmful_minutes_threshold = max(1, operator_count * int(risk_config.high_harmful_minutes_threshold) * 60)
        harmful_event_threshold = max(1, operator_count * int(risk_config.high_harmful_events_threshold))
        harmful_minutes_pressure = min((total_harmful_seconds / harmful_minutes_threshold) * 100, 100.0)
        harmful_events_pressure = min((total_harmful_events / harmful_event_threshold) * 100, 100.0)
        low_occupancy_deficits = [
            max(
                0.0,
                (
                    (float(risk_config.low_occupancy_threshold_pct) - float(item.get("taxa_ocupacao_pct") or 0.0))
                    / max(float(risk_config.low_occupancy_threshold_pct), 1.0)
                )
                * 100,
            )
            for item in logged_metrics
            if not _is_no_activity_metric(item) and item.get("taxa_ocupacao_pct") is not None
        ]
        if low_occupancy_deficits:
            low_occupancy_pressure = min(
                sum(low_occupancy_deficits) / len(low_occupancy_deficits),
                100.0,
            )
        if total_logged_seconds > 0:
            unclassified_pressure = min((total_unclassified_seconds / total_logged_seconds) * 100, 100.0)

    if active_agents_count > 0:
        no_activity_pressure = min((len(no_activity_agents) / active_agents_count) * 100, 100.0)

    return [
        {"label": "Tempo improdutivo", "value": round(harmful_minutes_pressure, 2)},
        {"label": "Qtd improdutivas", "value": round(harmful_events_pressure, 2)},
        {"label": "Baixa ocupacao", "value": round(low_occupancy_pressure, 2)},
        {"label": "Nao classificado", "value": round(unclassified_pressure, 2)},
        {"label": "Sem atividade", "value": round(no_activity_pressure, 2)},
    ]


def _to_local_date(value: datetime) -> date:
    if timezone.is_aware(value):
        value = timezone.localtime(value, timezone.get_current_timezone())
    return value.date()


def _bucket_period_end(period_filter, bucket_date: date) -> datetime:
    tz = timezone.get_current_timezone()
    bucket_end = timezone.make_aware(datetime.combine(bucket_date + timedelta(days=1), time.min), tz)
    return min(bucket_end, period_filter.dt_end)


def _init_bucket_map(period_filter, *, fill_zero: bool) -> dict:
    if period_filter.is_single_day:
        items = {
            hour: {
                "key": hour,
                "hour": hour,
                "hour_label": f"{hour:02d}h",
                "label": f"{hour:02d}h",
                "event_count": 0,
                "pause_count": 0,
                "pause_seconds": 0,
                "critical_count": 0,
            }
            for hour in range(24)
        }
        return items if fill_zero else {}

    items = {}
    current_day = period_filter.date_from
    while current_day <= period_filter.date_to:
        items[current_day] = {
            "key": current_day.isoformat(),
            "date": current_day.isoformat(),
            "label": current_day.strftime("%d/%m"),
            "event_count": 0,
            "pause_count": 0,
            "pause_seconds": 0,
            "critical_count": 0,
        }
        current_day += timedelta(days=1)
    return items if fill_zero else {}


def _resolve_bucket(period_filter, dt_value: datetime) -> tuple[int | date, str | None]:
    local_dt = timezone.localtime(dt_value, timezone.get_current_timezone()) if timezone.is_aware(dt_value) else dt_value
    if period_filter.is_single_day:
        return local_dt.hour, f"{local_dt.hour:02d}h"
    return local_dt.date(), None


def _estimate_login_seconds_by_day_operator(*, events_qs, period_filter) -> dict[tuple[date, int], int]:
    log_events = events_qs.filter(
        Q(tp_evento__iexact="LOGON") | Q(tp_evento__iexact="LOGOFF")
    ).order_by("cd_operador", "dt_inicio", "id")

    now = timezone.now()
    totals: dict[tuple[date, int], int] = defaultdict(int)
    open_logons: dict[tuple[date, int], datetime] = {}
    for row in log_events.values("cd_operador", "tp_evento", "dt_inicio"):
        cd_operador = row.get("cd_operador")
        event_dt = row.get("dt_inicio")
        if cd_operador is None or event_dt is None:
            continue
        local_dt = timezone.localtime(event_dt, timezone.get_current_timezone()) if timezone.is_aware(event_dt) else event_dt
        day_key = local_dt.date()
        operator_key = (day_key, int(cd_operador))
        event_type = str(row.get("tp_evento") or "").upper()
        if event_type == "LOGON":
            open_logons.setdefault(operator_key, event_dt)
            continue

        if event_type == "LOGOFF":
            start_dt = open_logons.pop(operator_key, None)
            if start_dt is not None and event_dt > start_dt:
                totals[operator_key] += int((event_dt - start_dt).total_seconds())

    for (day_key, cd_operador), start_dt in open_logons.items():
        close_time = _bucket_period_end(period_filter, day_key)
        if day_key >= timezone.localdate():
            close_time = min(close_time, now)
        if close_time > start_dt:
            totals[(day_key, cd_operador)] += int((close_time - start_dt).total_seconds())

    return {key: max(0, value) for key, value in totals.items()}


def _estimate_event_span_seconds_by_day_operator(*, events_qs, period_filter) -> dict[tuple[date, int], int]:
    now = timezone.now()
    totals: dict[tuple[date, int], int] = {}
    bounds_by_operator_day: dict[tuple[date, int], dict[str, datetime | None]] = {}

    for row in events_qs.values("cd_operador", "dt_inicio", "dt_fim"):
        cd_operador = row.get("cd_operador")
        start_dt = row.get("dt_inicio")
        if cd_operador is None or start_dt is None:
            continue

        day_key = _to_local_date(start_dt)
        operator_key = (day_key, int(cd_operador))
        close_time = min(_bucket_period_end(period_filter, day_key), now)
        raw_end_dt = row.get("dt_fim")
        end_dt = raw_end_dt or start_dt
        if end_dt > close_time:
            end_dt = close_time
        if end_dt < start_dt:
            end_dt = start_dt

        bounds = bounds_by_operator_day.setdefault(
            operator_key,
            {"min_start": None, "max_end": None},
        )
        min_start = bounds["min_start"]
        max_end = bounds["max_end"]
        if min_start is None or start_dt < min_start:
            bounds["min_start"] = start_dt
        if max_end is None or end_dt > max_end:
            bounds["max_end"] = end_dt

    for operator_key, bounds in bounds_by_operator_day.items():
        start_dt = bounds.get("min_start")
        end_dt = bounds.get("max_end")
        if start_dt is None or end_dt is None or end_dt <= start_dt:
            totals[operator_key] = 0
            continue
        totals[operator_key] = max(0, int((end_dt - start_dt).total_seconds()))
    return totals


def _empty_pause_info() -> dict:
    return {
        "qtd_pausas": 0,
        "tempo_pausas_seg": 0,
        "qtd_produtivas": 0,
        "qtd_neutras": 0,
        "qtd_improdutivas": 0,
        "qtd_nao_classificadas": 0,
        "tempo_produtivo_seg": 0,
        "tempo_neutro_seg": 0,
        "tempo_improdutivo_seg": 0,
        "tempo_nao_classificado_seg": 0,
    }


def _is_no_activity_metric(metric: dict) -> bool:
    logged_seg = max(0, int(metric.get("tempo_logado_seg") or 0))
    productive_seg = max(0, int(metric.get("tempo_produtivo_seg") or 0))
    relevant_events_count = int(metric.get("qtd_eventos_relevantes") or 0)
    return logged_seg > 0 and productive_seg == 0 and relevant_events_count == 0
