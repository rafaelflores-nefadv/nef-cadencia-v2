import logging
from collections import defaultdict
from datetime import datetime, time, timedelta

from django.db.utils import OperationalError, ProgrammingError
from django.db.models import Q
from django.utils import timezone
from django.utils.dateparse import parse_date

from apps.monitoring.models import (
    Agent,
    AgentDayStats,
    AgentEvent,
    AgentWorkday,
    PauseCategoryChoices,
    PauseClassification,
)
from apps.monitoring.services.dashboard_period_filter import resolve_dashboard_period_filter
from apps.monitoring.services.pause_classification import (
    UNCLASSIFIED_CATEGORY,
    normalize_pause_name,
    normalize_source,
    resolve_pause_category,
)
from apps.monitoring.utils import format_seconds_hhmm
from apps.rules.services.system_config import get_int, get_json

logger = logging.getLogger(__name__)


def _parse_date(value: str | None):
    parsed = parse_date(value or "")
    return parsed or timezone.localdate()


def _build_day_window(day_ref):
    tz = timezone.get_current_timezone()
    start = timezone.make_aware(datetime.combine(day_ref, time.min), tz)
    end = start + timedelta(days=1)
    return start, end


def _normalize_pause_key(value: str | None) -> str:
    return (value or "").strip().lower()


def _resolve_pause_limit_minutes(pause_type: str | None) -> int:
    limits = get_json("PAUSE_LIMITS_JSON", default={})
    default_limit = max(1, get_int("PAUSE_LIMIT_DEFAULT_MINUTES", default=10))
    if not isinstance(limits, dict):
        return default_limit

    normalized_limits = {}
    for key, val in limits.items():
        try:
            normalized_limits[_normalize_pause_key(str(key))] = max(1, int(val))
        except (TypeError, ValueError):
            continue

    if pause_type:
        return normalized_limits.get(_normalize_pause_key(pause_type), default_limit)

    return normalized_limits.get("default", default_limit)


def _event_minutes(event: AgentEvent, now):
    if event.duracao_seg is not None:
        return max(0, int(event.duracao_seg) // 60)
    end_time = event.dt_fim or now
    seconds = int((end_time - event.dt_inicio).total_seconds())
    return max(0, seconds // 60)


def _agent_name(agent):
    if not agent:
        return "Sem nome"
    return agent.nm_agente or agent.nm_agente_code or f"Operador {agent.cd_operador}"


def _coerce_optional_int(value) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _normalize_metric(metric: str | None) -> str:
    normalized = str(metric or "").strip().lower()
    aliases = {
        "productivity": "productivity",
        "produtividade": "productivity",
        "productive": "productivity",
        "improductivity": "improductivity",
        "improdutividade": "improductivity",
        "improductive": "improductivity",
        "performance": "performance",
        "desempenho": "performance",
    }
    return aliases.get(normalized, "improductivity")


def _normalize_group_by(group_by: str | None) -> str:
    normalized = str(group_by or "").strip().lower()
    if normalized in {"team", "equipe", "equipes"}:
        return "team"
    return "agent"


def _normalize_ranking_order(ranking_order: str | None, metric: str) -> str:
    normalized = str(ranking_order or "").strip().lower()
    if normalized in {"best", "melhor", "melhores"}:
        return "best"
    if normalized in {"worst", "pior", "piores"}:
        return "worst"
    if metric == "productivity":
        return "best"
    return "worst"


def _resolve_analytics_period(
    *,
    date_from: str | None = None,
    date_to: str | None = None,
    year=None,
    month=None,
    period_key: str | None = None,
):
    params = {}
    if date_from:
        params["date_from"] = str(date_from)
    if date_to:
        params["date_to"] = str(date_to)
    if period_key:
        params["quick_range"] = str(period_key)
    parsed_year = _coerce_optional_int(year)
    parsed_month = _coerce_optional_int(month)
    if parsed_year is not None:
        params["year"] = str(parsed_year)
    if parsed_month is not None:
        params["month"] = str(parsed_month)
    return resolve_dashboard_period_filter(params)


def _build_logged_seconds_by_operator(workday_rows: list[dict]) -> dict[int, int]:
    totals: dict[int, int] = {}
    for row in workday_rows:
        cd_operador = row.get("cd_operador")
        if cd_operador is None:
            continue
        totals[int(cd_operador)] = (
            totals.get(int(cd_operador), 0) + max(0, int(row.get("duracao_seg") or 0))
        )
    return totals


def _estimate_login_seconds_per_operator(events_qs, period_end, period_end_date) -> dict[int, int]:
    log_events = events_qs.filter(
        Q(tp_evento__iexact="LOGON") | Q(tp_evento__iexact="LOGOFF")
    ).order_by("cd_operador", "dt_inicio", "id")

    now = timezone.now()
    close_time = period_end
    if period_end_date >= timezone.localdate():
        close_time = min(period_end, now)

    current_logon_by_operator: dict[int, datetime] = {}
    total_seconds_by_operator: dict[int, int] = {}
    for item in log_events.values("cd_operador", "tp_evento", "dt_inicio"):
        cd_operador = item.get("cd_operador")
        event_dt = item.get("dt_inicio")
        if cd_operador is None or event_dt is None:
            continue

        cd_operador = int(cd_operador)
        event_type = str(item.get("tp_evento") or "").upper()
        if event_type == "LOGON":
            current_logon_by_operator.setdefault(cd_operador, event_dt)
            continue

        if event_type == "LOGOFF":
            start_dt = current_logon_by_operator.pop(cd_operador, None)
            if start_dt is not None and event_dt > start_dt:
                total_seconds_by_operator[cd_operador] = (
                    total_seconds_by_operator.get(cd_operador, 0)
                    + int((event_dt - start_dt).total_seconds())
                )

    for cd_operador, start_dt in current_logon_by_operator.items():
        if close_time > start_dt:
            total_seconds_by_operator[cd_operador] = (
                total_seconds_by_operator.get(cd_operador, 0)
                + int((close_time - start_dt).total_seconds())
            )

    return {key: max(0, value) for key, value in total_seconds_by_operator.items()}


def _estimate_event_span_seconds_per_operator(events_qs, period_end) -> dict[int, int]:
    now = timezone.now()
    close_time = min(period_end, now)
    bounds_by_operator: dict[int, dict[str, datetime | None]] = {}

    for item in events_qs.values("cd_operador", "dt_inicio", "dt_fim"):
        cd_operador = item.get("cd_operador")
        start_dt = item.get("dt_inicio")
        if cd_operador is None or start_dt is None:
            continue

        cd_operador = int(cd_operador)
        raw_end_dt = item.get("dt_fim")
        end_dt = raw_end_dt or start_dt
        if end_dt > close_time:
            end_dt = close_time
        if end_dt < start_dt:
            end_dt = start_dt

        bounds = bounds_by_operator.setdefault(
            cd_operador,
            {"min_start": None, "max_end": None},
        )
        min_start = bounds["min_start"]
        max_end = bounds["max_end"]
        if min_start is None or start_dt < min_start:
            bounds["min_start"] = start_dt
        if max_end is None or end_dt > max_end:
            bounds["max_end"] = end_dt

    totals: dict[int, int] = {}
    for cd_operador, bounds in bounds_by_operator.items():
        start_dt = bounds.get("min_start")
        end_dt = bounds.get("max_end")
        if start_dt is None or end_dt is None or end_dt <= start_dt:
            totals[cd_operador] = 0
            continue
        totals[cd_operador] = max(0, int((end_dt - start_dt).total_seconds()))
    return totals


def _build_agent_index(operator_ids, workday_rows: list[dict]) -> dict[int, dict]:
    if not operator_ids:
        return {}

    agent_index = {
        int(row["cd_operador"]): {
            "agent_id": int(row["id"]),
            "agent_name": row.get("nm_agente") or f"Operador {row['cd_operador']}",
        }
        for row in Agent.objects.filter(cd_operador__in=operator_ids).values(
            "id",
            "cd_operador",
            "nm_agente",
        )
    }
    for row in workday_rows:
        cd_operador = row.get("cd_operador")
        if cd_operador is None:
            continue
        info = agent_index.setdefault(
            int(cd_operador),
            {
                "agent_id": None,
                "agent_name": row.get("nm_operador") or f"Operador {cd_operador}",
            },
        )
        if not info.get("agent_name"):
            info["agent_name"] = row.get("nm_operador") or f"Operador {cd_operador}"

    for cd_operador in operator_ids:
        agent_index.setdefault(
            int(cd_operador),
            {
                "agent_id": None,
                "agent_name": f"Operador {cd_operador}",
            },
        )
    return agent_index


def _empty_pause_category_dict(default_value=0):
    return {
        PauseCategoryChoices.LEGAL: default_value,
        PauseCategoryChoices.NEUTRAL: default_value,
        PauseCategoryChoices.HARMFUL: default_value,
        UNCLASSIFIED_CATEGORY: default_value,
    }


def _build_pause_category_map(pause_events_qs) -> dict[tuple[str, str], str]:
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

    category_map = {}
    for source_normalized, normalized_name in normalized_pairs:
        category = source_specific_map.get((source_normalized, normalized_name))
        if category is None:
            category = global_map.get(normalized_name)
        if category is None:
            category = resolve_pause_category(normalized_name, source=source_normalized)
        category_map[(source_normalized, normalized_name)] = category
    return category_map


def _resolve_period_event_duration_seconds(event_row: dict, period_end_dt) -> int:
    duration_raw = event_row.get("duracao_seg")
    if duration_raw is not None:
        try:
            return max(0, int(duration_raw))
        except (TypeError, ValueError):
            pass

    start_dt = event_row.get("dt_inicio")
    end_dt = event_row.get("dt_fim") or timezone.now()
    if start_dt is None:
        return 0
    end_dt = min(end_dt, period_end_dt)
    if end_dt <= start_dt:
        return 0
    return int((end_dt - start_dt).total_seconds())


def _build_pause_classified_aggregates(pause_events_qs, period_end_dt) -> dict:
    pause_category_map = _build_pause_category_map(pause_events_qs=pause_events_qs)
    totals_seconds = _empty_pause_category_dict(default_value=0)
    totals_count = _empty_pause_category_dict(default_value=0)
    by_operator: dict[int, dict] = {}

    total_events = 0
    total_seconds = 0
    for event in pause_events_qs.values(
        "cd_operador",
        "source",
        "nm_pausa",
        "duracao_seg",
        "dt_inicio",
        "dt_fim",
    ):
        total_events += 1
        duration_seconds = _resolve_period_event_duration_seconds(event, period_end_dt)
        total_seconds += duration_seconds

        source_normalized = normalize_source(event.get("source"))
        normalized_name = normalize_pause_name(event.get("nm_pausa"))
        category = pause_category_map.get(
            (source_normalized, normalized_name),
            UNCLASSIFIED_CATEGORY,
        )
        if category not in totals_seconds:
            category = UNCLASSIFIED_CATEGORY

        totals_seconds[category] += duration_seconds
        totals_count[category] += 1

        cd_operador = event.get("cd_operador")
        if cd_operador is None:
            continue
        operator_key = int(cd_operador)
        row = by_operator.setdefault(
            operator_key,
            {
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
            },
        )
        row["qtd_pausas"] += 1
        row["tempo_pausas_seg"] += duration_seconds
        if category == PauseCategoryChoices.LEGAL:
            row["qtd_produtivas"] += 1
            row["tempo_produtivo_seg"] += duration_seconds
        elif category == PauseCategoryChoices.NEUTRAL:
            row["qtd_neutras"] += 1
            row["tempo_neutro_seg"] += duration_seconds
        elif category == PauseCategoryChoices.HARMFUL:
            row["qtd_improdutivas"] += 1
            row["tempo_improdutivo_seg"] += duration_seconds
        else:
            row["qtd_nao_classificadas"] += 1
            row["tempo_nao_classificado_seg"] += duration_seconds

    return {
        "total_events": total_events,
        "total_seconds": total_seconds,
        "totals_seconds": totals_seconds,
        "totals_count": totals_count,
        "by_operator": by_operator,
    }


def _build_pause_event_fallback_aggregates(pause_events_qs, period_end_dt) -> dict:
    totals_seconds = _empty_pause_category_dict(default_value=0)
    totals_count = _empty_pause_category_dict(default_value=0)
    by_operator: dict[int, dict] = {}

    total_events = 0
    total_seconds = 0
    for event in pause_events_qs.values("cd_operador", "duracao_seg", "dt_inicio", "dt_fim"):
        total_events += 1
        duration_seconds = _resolve_period_event_duration_seconds(event, period_end_dt)
        total_seconds += duration_seconds
        totals_seconds[PauseCategoryChoices.HARMFUL] += duration_seconds
        totals_count[PauseCategoryChoices.HARMFUL] += 1

        cd_operador = event.get("cd_operador")
        if cd_operador is None:
            continue

        operator_key = int(cd_operador)
        row = by_operator.setdefault(
            operator_key,
            {
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
            },
        )
        row["qtd_pausas"] += 1
        row["tempo_pausas_seg"] += duration_seconds
        row["qtd_improdutivas"] += 1
        row["tempo_improdutivo_seg"] += duration_seconds

    return {
        "total_events": total_events,
        "total_seconds": total_seconds,
        "totals_seconds": totals_seconds,
        "totals_count": totals_count,
        "by_operator": by_operator,
    }


def _has_classified_pause_signal(aggregates: dict) -> bool:
    totals_count = aggregates.get("totals_count") if isinstance(aggregates, dict) else {}
    if not isinstance(totals_count, dict):
        return False
    return any(
        int(totals_count.get(category) or 0) > 0
        for category in (
            PauseCategoryChoices.LEGAL,
            PauseCategoryChoices.NEUTRAL,
            PauseCategoryChoices.HARMFUL,
        )
    )


def _load_workday_rows(period_filter) -> tuple[list[dict], list[str]]:
    try:
        workday_rows = list(
            AgentWorkday.objects.filter(
                work_date__gte=period_filter.date_from,
                work_date__lte=period_filter.date_to,
            ).values("cd_operador", "duracao_seg", "nm_operador")
        )
        if workday_rows:
            return workday_rows, ["agent_workday_used"]
        return [], ["agent_workday_empty"]
    except (ProgrammingError, OperationalError) as exc:
        logger.warning("assistant.get_productivity_analytics_workday_unavailable: %s", exc)
        return [], ["agent_workday_missing"]


def _build_stats_by_operator(stats_qs) -> dict[int, dict]:
    items: dict[int, dict] = {}
    for row in stats_qs.values(
        "cd_operador",
        "qtd_pausas",
        "tempo_pausas_seg",
        "ultimo_logon",
        "ultimo_logoff",
    ):
        cd_operador = row.get("cd_operador")
        if cd_operador is None:
            continue
        cd_operador = int(cd_operador)
        logon_dt = row.get("ultimo_logon")
        logoff_dt = row.get("ultimo_logoff")
        tempo_logado_seg = 0
        if logon_dt and logoff_dt and logoff_dt > logon_dt:
            tempo_logado_seg = int((logoff_dt - logon_dt).total_seconds())
        item = items.setdefault(
            cd_operador,
            {
                "qtd_pausas": 0,
                "tempo_pausas_seg": 0,
                "tempo_logado_seg": 0,
            },
        )
        item["qtd_pausas"] += int(row.get("qtd_pausas") or 0)
        item["tempo_pausas_seg"] += int(row.get("tempo_pausas_seg") or 0)
        item["tempo_logado_seg"] += max(0, tempo_logado_seg)
    return items


def _build_relevant_events_by_operator(events_qs) -> dict[int, int]:
    relevant_events_qs = events_qs.filter(
        Q(tp_evento__iexact="PAUSA")
        | (Q(nm_pausa__isnull=False) & ~Q(nm_pausa__exact=""))
        | Q(tp_evento__icontains="ATEND")
    )
    rows = list(relevant_events_qs.values("cd_operador"))
    totals: dict[int, int] = {}
    for row in rows:
        cd_operador = row.get("cd_operador")
        if cd_operador is None:
            continue
        totals[int(cd_operador)] = totals.get(int(cd_operador), 0) + 1
    return totals


def _resolve_productivity_seconds(
    *,
    logged_seg: int,
    pause_info: dict,
    stats_info: dict,
    relevant_events_count: int,
) -> tuple[int, int, str]:
    harmful_seg = int(pause_info.get("tempo_improdutivo_seg") or 0)
    total_pause_seg = int(pause_info.get("tempo_pausas_seg") or 0)
    stats_pause_seg = int(stats_info.get("tempo_pausas_seg") or 0)

    if harmful_seg > 0:
        improductive_basis = harmful_seg
        basis = "classified_improductivity"
    elif total_pause_seg > 0:
        improductive_basis = total_pause_seg
        basis = "total_pause_fallback"
    elif stats_pause_seg > 0 and (
        int(stats_info.get("qtd_pausas") or 0) > 0 or relevant_events_count > 0
    ):
        improductive_basis = stats_pause_seg
        basis = "day_stats_pause_fallback"
    else:
        improductive_basis = 0
        basis = "no_improductive_basis"

    if logged_seg <= 0:
        return 0, improductive_basis, basis
    return max(0, logged_seg - improductive_basis), improductive_basis, basis


def _build_operator_metrics(
    operator_ids,
    agent_index,
    pause_by_operator,
    stats_by_operator,
    logged_by_operator,
    estimated_logged_by_operator,
    event_span_by_operator,
    relevant_events_by_operator,
):
    items = []
    for cd_operador in sorted(operator_ids):
        stats_info = stats_by_operator.get(int(cd_operador), {})
        pause_info = pause_by_operator.get(int(cd_operador), {})
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

        logged_source = "workday"
        logged_seg = int(logged_by_operator.get(int(cd_operador), 0) or 0)
        if logged_seg <= 0:
            logged_seg = int(estimated_logged_by_operator.get(int(cd_operador), 0) or 0)
            logged_source = "logon_logoff"
        if logged_seg <= 0:
            logged_seg = int(event_span_by_operator.get(int(cd_operador), 0) or 0)
            logged_source = "event_span"
        if logged_seg <= 0:
            logged_seg = int(stats_info.get("tempo_logado_seg") or 0)
            logged_source = "day_stats"
        if logged_seg <= 0:
            logged_source = "none"

        relevant_events_count = int(relevant_events_by_operator.get(int(cd_operador), 0) or 0)
        if relevant_events_count <= 0 and (
            int(stats_info.get("qtd_pausas") or 0) > 0
            or int(stats_info.get("tempo_logado_seg") or 0) > 0
        ):
            relevant_events_count = 1

        neutral_seg = int(pause_info.get("tempo_neutro_seg") or 0)
        harmful_seg = int(pause_info.get("tempo_improdutivo_seg") or 0)
        unclassified_seg = int(pause_info.get("tempo_nao_classificado_seg") or 0)
        total_pause_seg = int(pause_info.get("tempo_pausas_seg") or 0)
        productive_seg, improductive_basis_seg, productivity_basis = _resolve_productivity_seconds(
            logged_seg=logged_seg,
            pause_info=pause_info,
            stats_info=stats_info,
            relevant_events_count=relevant_events_count,
        )

        occupancy_pct = round((productive_seg / logged_seg) * 100, 2) if logged_seg else None
        agent_info = agent_index.get(
            int(cd_operador),
            {"agent_id": None, "agent_name": f"Operador {cd_operador}"},
        )
        items.append(
            {
                "agent_id": agent_info.get("agent_id"),
                "cd_operador": int(cd_operador),
                "agent_name": agent_info.get("agent_name") or f"Operador {cd_operador}",
                "qtd_pausas": int(pause_info.get("qtd_pausas") or 0),
                "qtd_improdutivas": int(pause_info.get("qtd_improdutivas") or 0),
                "tempo_pausas_seg": total_pause_seg,
                "tempo_pausas_hhmm": format_seconds_hhmm(total_pause_seg),
                "tempo_produtivo_seg": productive_seg,
                "tempo_produtivo_hhmm": format_seconds_hhmm(productive_seg),
                "tempo_improdutivo_seg": harmful_seg,
                "tempo_improdutivo_hhmm": format_seconds_hhmm(harmful_seg),
                "tempo_improdutivo_base_seg": improductive_basis_seg,
                "tempo_neutro_seg": neutral_seg,
                "tempo_nao_classificado_seg": unclassified_seg,
                "tempo_logado_seg": logged_seg,
                "tempo_logado_hhmm": format_seconds_hhmm(logged_seg),
                "qtd_eventos_relevantes": relevant_events_count,
                "taxa_ocupacao_pct": occupancy_pct,
                "productivity_basis": productivity_basis,
                "logged_source": logged_source,
            }
        )
    return items


def _sort_productivity_ranking(item: dict, ranking_order: str):
    occupancy = float(item.get("taxa_ocupacao_pct") or 0.0)
    productive = int(item.get("tempo_produtivo_seg") or 0)
    harmful = int(item.get("tempo_improdutivo_seg") or 0)
    if ranking_order == "worst":
        return (productive, occupancy, -harmful, item["cd_operador"])
    return (-productive, -occupancy, harmful, item["cd_operador"])


def _sort_improductivity_ranking(item: dict, ranking_order: str):
    occupancy = float(item.get("taxa_ocupacao_pct") or 0.0)
    harmful = int(item.get("tempo_improdutivo_seg") or 0)
    harmful_count = int(item.get("qtd_improdutivas") or 0)
    productive = int(item.get("tempo_produtivo_seg") or 0)
    if ranking_order == "best":
        return (harmful, harmful_count, -occupancy, -productive, item["cd_operador"])
    return (-harmful, -harmful_count, occupancy, productive, item["cd_operador"])


def _sort_performance_ranking(item: dict, ranking_order: str):
    occupancy = item.get("taxa_ocupacao_pct")
    occupancy = float(occupancy if occupancy is not None else 0.0)
    harmful = int(item.get("tempo_improdutivo_seg") or 0)
    productive = int(item.get("tempo_produtivo_seg") or 0)
    if ranking_order == "best":
        return (-occupancy, -productive, harmful, item["cd_operador"])
    return (occupancy, -harmful, productive, item["cd_operador"])


def _build_productivity_analytics_ranking(
    operator_metrics: list[dict],
    *,
    metric: str,
    ranking_order: str,
    limit: int,
) -> list[dict]:
    if metric == "productivity":
        candidates = [
            item for item in operator_metrics
            if int(item.get("tempo_produtivo_seg") or 0) > 0
        ]
        if not candidates:
            candidates = [
                item for item in operator_metrics
                if int(item.get("tempo_logado_seg") or 0) > 0
                or int(item.get("tempo_pausas_seg") or 0) > 0
                or int(item.get("tempo_improdutivo_seg") or 0) > 0
            ]
        return sorted(
            candidates,
            key=lambda item: _sort_productivity_ranking(item, ranking_order),
        )[:limit]

    if metric == "performance":
        candidates = [
            item for item in operator_metrics
            if int(item.get("tempo_logado_seg") or 0) > 0
            or int(item.get("tempo_produtivo_seg") or 0) > 0
            or int(item.get("tempo_improdutivo_seg") or 0) > 0
        ]
        return sorted(
            candidates,
            key=lambda item: _sort_performance_ranking(item, ranking_order),
        )[:limit]

    candidates = [
        item for item in operator_metrics
        if int(item.get("tempo_improdutivo_seg") or 0) > 0
    ]
    return sorted(
        candidates,
        key=lambda item: _sort_improductivity_ranking(item, ranking_order),
    )[:limit]


def get_productivity_analytics(
    *,
    date_from: str | None = None,
    date_to: str | None = None,
    year=None,
    month=None,
    period_key: str | None = None,
    metric: str | None = None,
    group_by: str | None = None,
    ranking_order: str | None = None,
    limit: int = 10,
) -> dict:
    try:
        period_filter = _resolve_analytics_period(
            date_from=date_from,
            date_to=date_to,
            year=year,
            month=month,
            period_key=period_key,
        )
        normalized_metric = _normalize_metric(metric)
        normalized_group_by = _normalize_group_by(group_by)
        normalized_ranking_order = _normalize_ranking_order(ranking_order, normalized_metric)
        try:
            parsed_limit = int(limit or 10)
        except (TypeError, ValueError):
            parsed_limit = 10
        normalized_limit = max(1, min(parsed_limit, 100))

        diagnostics: list[str] = []
        workday_rows, workday_diagnostics = _load_workday_rows(period_filter)
        diagnostics.extend(workday_diagnostics)
        stats_qs = AgentDayStats.objects.filter(
            data_ref__gte=period_filter.date_from,
            data_ref__lte=period_filter.date_to,
        )
        events_qs = AgentEvent.objects.filter(
            dt_inicio__gte=period_filter.dt_start,
            dt_inicio__lt=period_filter.dt_end,
        )
        pause_events_qs = events_qs.filter(
            Q(tp_evento__iexact="PAUSA")
            | (Q(nm_pausa__isnull=False) & ~Q(nm_pausa__exact=""))
        )
        pause_named_qs = events_qs.filter(Q(nm_pausa__isnull=False) & ~Q(nm_pausa__exact=""))

        stats_rows_count = stats_qs.count()
        event_rows_count = events_qs.count()
        pause_event_rows_count = pause_events_qs.count()
        pause_named_rows_count = pause_named_qs.count()

        logged_by_operator = _build_logged_seconds_by_operator(workday_rows)
        estimated_logged_by_operator = _estimate_login_seconds_per_operator(
            events_qs,
            period_filter.dt_end,
            period_filter.date_to,
        )
        event_span_by_operator = _estimate_event_span_seconds_per_operator(
            events_qs,
            period_filter.dt_end,
        )
        stats_by_operator = _build_stats_by_operator(stats_qs)
        pause_classified = _build_pause_classified_aggregates(
            pause_events_qs,
            period_filter.dt_end,
        )
        pause_event_fallback = _build_pause_event_fallback_aggregates(
            pause_events_qs,
            period_filter.dt_end,
        )
        relevant_events_by_operator = _build_relevant_events_by_operator(events_qs)

        if stats_by_operator:
            diagnostics.append("agent_day_stats_used")
        else:
            diagnostics.append("agent_day_stats_empty")
        if relevant_events_by_operator or pause_event_fallback["total_events"] > 0:
            diagnostics.append("agent_event_used")
        else:
            diagnostics.append("agent_event_empty")

        pause_aggregates = pause_classified
        chosen_source = "pause_classified"
        if _has_classified_pause_signal(pause_classified):
            diagnostics.append("pause_events_classified")
        elif pause_event_fallback["total_events"] > 0:
            pause_aggregates = pause_event_fallback
            chosen_source = "agent_event_raw_pause_fallback"
            diagnostics.append("pause_events_raw_fallback_used")
        else:
            chosen_source = "none"
            diagnostics.append("pause_events_empty")

        operator_ids = sorted(
            {
                *logged_by_operator.keys(),
                *estimated_logged_by_operator.keys(),
                *event_span_by_operator.keys(),
                *stats_by_operator.keys(),
                *pause_aggregates["by_operator"].keys(),
                *relevant_events_by_operator.keys(),
            }
        )
        agent_index = _build_agent_index(operator_ids, workday_rows)
        operator_metrics = _build_operator_metrics(
            operator_ids=operator_ids,
            agent_index=agent_index,
            pause_by_operator=pause_aggregates["by_operator"],
            stats_by_operator=stats_by_operator,
            logged_by_operator=logged_by_operator,
            estimated_logged_by_operator=estimated_logged_by_operator,
            event_span_by_operator=event_span_by_operator,
            relevant_events_by_operator=relevant_events_by_operator,
        )

        productivity_basis_counts: dict[str, int] = {}
        logged_source_counts: dict[str, int] = {}
        for item in operator_metrics:
            basis_key = str(item.get("productivity_basis") or "unknown")
            productivity_basis_counts[basis_key] = productivity_basis_counts.get(basis_key, 0) + 1
            logged_source_key = str(item.get("logged_source") or "unknown")
            logged_source_counts[logged_source_key] = logged_source_counts.get(logged_source_key, 0) + 1

        sample_operators = [
            {
                "cd_operador": int(item.get("cd_operador") or 0),
                "agent_name": item.get("agent_name"),
                "tempo_logado_seg": int(item.get("tempo_logado_seg") or 0),
                "tempo_improdutivo_base_seg": int(item.get("tempo_improdutivo_base_seg") or 0),
                "tempo_improdutivo_seg": int(item.get("tempo_improdutivo_seg") or 0),
                "tempo_produtivo_seg": int(item.get("tempo_produtivo_seg") or 0),
                "productivity_basis": item.get("productivity_basis"),
                "logged_source": item.get("logged_source"),
            }
            for item in sorted(
                operator_metrics,
                key=lambda row: (
                    -int(row.get("tempo_produtivo_seg") or 0),
                    -int(row.get("tempo_logado_seg") or 0),
                    int(row.get("cd_operador") or 0),
                ),
            )[:3]
        ]

        summary = {
            "total_agents_considered": len(operator_metrics),
            "total_logged_seconds": sum(int(item.get("tempo_logado_seg") or 0) for item in operator_metrics),
            "total_productive_seconds": sum(int(item.get("tempo_produtivo_seg") or 0) for item in operator_metrics),
            "total_improductive_seconds": sum(
                int(item.get("tempo_improdutivo_seg") or 0) for item in operator_metrics
            ),
            "total_pause_seconds": sum(int(item.get("tempo_pausas_seg") or 0) for item in operator_metrics),
            "productivity_basis_counts": productivity_basis_counts,
            "logged_source_counts": logged_source_counts,
        }
        summary["total_logged_hhmm"] = format_seconds_hhmm(summary["total_logged_seconds"])
        summary["total_productive_hhmm"] = format_seconds_hhmm(summary["total_productive_seconds"])
        summary["total_improductive_hhmm"] = format_seconds_hhmm(summary["total_improductive_seconds"])
        summary["total_pause_hhmm"] = format_seconds_hhmm(summary["total_pause_seconds"])
        reason_no_data = None
        if not operator_ids:
            diagnostics.append("filter_without_match")
            reason_no_data = "filter_without_match"

        logger.warning(
            (
                "assistant.get_productivity_analytics "
                "start_date=%s end_date=%s metric=%s group_by=%s ranking_order=%s "
                "stats_date_field=data_ref event_date_field=dt_inicio pause_filter=\"tp_evento=PAUSA OR nm_pausa IS NOT NULL\" "
                "agent_day_stats_rows=%s agent_event_rows=%s pause_event_rows=%s pause_named_rows=%s "
                "workday_rows=%s chosen_source=%s total_agents=%s reason_no_data=%s "
                "productivity_basis_counts=%s logged_source_counts=%s sample_operators=%s diagnostics=%s"
            ),
            period_filter.date_from.isoformat(),
            period_filter.date_to.isoformat(),
            normalized_metric,
            normalized_group_by,
            normalized_ranking_order,
            stats_rows_count,
            event_rows_count,
            pause_event_rows_count,
            pause_named_rows_count,
            len(workday_rows),
            chosen_source,
            len(operator_metrics),
            reason_no_data,
            productivity_basis_counts,
            logged_source_counts,
            sample_operators,
            ",".join(diagnostics),
        )

        if normalized_group_by == "team":
            return {
                "date_from": period_filter.date_from.isoformat(),
                "date_to": period_filter.date_to.isoformat(),
                "period_label": period_filter.period_label,
                "metric": normalized_metric,
                "group_by": normalized_group_by,
                "ranking_order": normalized_ranking_order,
                "limit": normalized_limit,
                "dimension_available": False,
                "dimension_unavailable_reason": "team_dimension_not_available",
                "ranking": [],
                "summary": summary,
                "warning": period_filter.warning,
                "diagnostics": diagnostics,
                "agent_day_stats_rows": stats_rows_count,
                "agent_event_rows": event_rows_count,
                "pause_event_rows": pause_event_rows_count,
                "pause_named_rows": pause_named_rows_count,
                "chosen_source": chosen_source,
                "reason_no_data": reason_no_data or "team_dimension_not_available",
                "sample_operators": sample_operators,
            }

        ranking = _build_productivity_analytics_ranking(
            operator_metrics,
            metric=normalized_metric,
            ranking_order=normalized_ranking_order,
            limit=normalized_limit,
        )
        if not ranking and reason_no_data is None:
            reason_no_data = "ranking_empty_after_aggregation"
        logger.warning(
            "assistant.get_productivity_analytics.final ranking_size=%s reason_no_data=%s",
            len(ranking),
            reason_no_data,
        )
        return {
            "date_from": period_filter.date_from.isoformat(),
            "date_to": period_filter.date_to.isoformat(),
            "period_label": period_filter.period_label,
            "metric": normalized_metric,
            "group_by": normalized_group_by,
            "ranking_order": normalized_ranking_order,
            "limit": normalized_limit,
            "dimension_available": True,
            "ranking": ranking,
            "summary": summary,
            "warning": period_filter.warning,
            "diagnostics": diagnostics,
            "agent_day_stats_rows": stats_rows_count,
            "agent_event_rows": event_rows_count,
            "pause_event_rows": pause_event_rows_count,
            "pause_named_rows": pause_named_rows_count,
            "chosen_source": chosen_source,
            "reason_no_data": reason_no_data,
            "sample_operators": sample_operators,
        }
    except Exception:
        logger.exception(
            "assistant.get_productivity_analytics_failed date_from=%s date_to=%s year=%s month=%s period_key=%s metric=%s group_by=%s ranking_order=%s limit=%s",
            date_from,
            date_to,
            year,
            month,
            period_key,
            metric,
            group_by,
            ranking_order,
            limit,
        )
        raise


def get_pause_ranking(date: str, limit: int = 10, pause_type: str | None = None) -> dict:
    day_ref = _parse_date(date)
    try:
        parsed_limit = int(limit or 10)
    except (TypeError, ValueError):
        parsed_limit = 10
    limit = max(1, min(parsed_limit, 100))
    pause_limit_minutes = _resolve_pause_limit_minutes(pause_type)
    start, end = _build_day_window(day_ref)

    ranking = []
    if pause_type:
        now = timezone.now()
        grouped = {}
        events = (
            AgentEvent.objects
            .select_related("agent")
            .filter(
                tp_evento="PAUSA",
                dt_inicio__gte=start,
                dt_inicio__lt=end,
                nm_pausa__iexact=pause_type,
            )
            .order_by("agent_id", "dt_inicio")
        )
        for event in events:
            agent_id = event.agent_id
            data = grouped.setdefault(
                agent_id,
                {
                    "agent_id": agent_id,
                    "agent_name": _agent_name(event.agent),
                    "total_minutes": 0,
                    "events_count": 0,
                },
            )
            data["total_minutes"] += _event_minutes(event, now)
            data["events_count"] += 1

        for _, item in grouped.items():
            total_minutes = int(item["total_minutes"])
            ranking.append(
                {
                    "agent_id": item["agent_id"],
                    "agent_name": item["agent_name"],
                    "total_minutes": total_minutes,
                    "overflow_minutes": max(0, total_minutes - pause_limit_minutes),
                    "events_count": int(item["events_count"]),
                }
            )
    else:
        stats_rows = (
            AgentDayStats.objects
            .select_related("agent")
            .filter(data_ref=day_ref)
            .order_by("-tempo_pausas_seg", "-qtd_pausas", "cd_operador")
        )
        for row in stats_rows:
            total_minutes = int(row.tempo_pausas_seg // 60)
            ranking.append(
                {
                    "agent_id": row.agent_id,
                    "agent_name": _agent_name(row.agent),
                    "total_minutes": total_minutes,
                    "overflow_minutes": max(0, total_minutes - pause_limit_minutes),
                    "events_count": int(row.qtd_pausas),
                }
            )

    ranking.sort(key=lambda item: (-item["overflow_minutes"], -item["total_minutes"], item["agent_id"]))
    return {
        "date": day_ref.isoformat(),
        "pause_type": pause_type,
        "pause_limit_minutes": pause_limit_minutes,
        "limit": limit,
        "ranking": ranking[:limit],
    }


def get_current_pauses(pause_type: str | None = None) -> dict:
    now = timezone.now()
    qs = (
        AgentEvent.objects
        .select_related("agent")
        .filter(
            tp_evento="PAUSA",
            dt_inicio__lte=now,
        ).filter(
            Q(dt_fim__isnull=True) | Q(dt_fim__gt=now)
        )
        .order_by("dt_inicio", "id")
    )
    if pause_type:
        qs = qs.filter(nm_pausa__iexact=pause_type)

    items = []
    counts = defaultdict(int)
    for event in qs:
        normalized_pause_type = (event.nm_pausa or "PAUSA").strip() or "PAUSA"
        counts[normalized_pause_type] += 1
        items.append(
            {
                "agent_id": event.agent_id,
                "agent_name": _agent_name(event.agent),
                "pause_type": normalized_pause_type,
                "started_at": event.dt_inicio.isoformat(),
                "minutes": _event_minutes(event, now),
            }
        )

    by_type = [
        {"pause_type": key, "count": counts[key]}
        for key in sorted(counts.keys())
    ]
    return {
        "generated_at": now.isoformat(),
        "total_in_pause": len(items),
        "pause_type_filter": pause_type,
        "by_type": by_type,
        "items": items,
    }


def get_day_summary(date: str) -> dict:
    day_ref = _parse_date(date)
    stats_qs = AgentDayStats.objects.select_related("agent").filter(data_ref=day_ref)
    stats = list(stats_qs)

    total_pause_minutes = int(sum(item.tempo_pausas_seg for item in stats) // 60)
    total_events = int(sum(item.qtd_pausas for item in stats))
    agents_with_stats = len(stats)
    active_agents = Agent.objects.filter(ativo=True).count()
    in_pause_now = get_current_pauses().get("total_in_pause", 0)

    avg_pause_minutes = 0.0
    if agents_with_stats > 0:
        avg_pause_minutes = round(total_pause_minutes / agents_with_stats, 2)

    top3_rows = sorted(
        stats,
        key=lambda item: (-item.tempo_pausas_seg, -item.qtd_pausas, item.agent_id),
    )[:3]
    top3 = [
        {
            "agent_id": row.agent_id,
            "agent_name": _agent_name(row.agent),
            "total_minutes": int(row.tempo_pausas_seg // 60),
            "events_count": int(row.qtd_pausas),
        }
        for row in top3_rows
    ]

    return {
        "date": day_ref.isoformat(),
        "totals": {
            "active_agents": int(active_agents),
            "agents_with_stats": int(agents_with_stats),
            "in_pause_now": int(in_pause_now),
            "total_pause_minutes": int(total_pause_minutes),
            "total_pause_events": int(total_events),
            "avg_pause_minutes_per_agent": avg_pause_minutes,
        },
        "top3": top3,
        "scope": "global",
    }
