from collections import defaultdict
from datetime import datetime, time, timedelta

from django.db.models import Q
from django.utils import timezone
from django.utils.dateparse import parse_date

from apps.monitoring.models import Agent, AgentDayStats, AgentEvent
from apps.rules.services.system_config import get_int, get_json


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
