from datetime import date, datetime
from typing import Any

from django.db import transaction
from django.db.models import Count, Max, Min, Q, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone

from apps.monitoring.models import Agent, AgentDayStats, AgentEvent, AgentWorkday


def rebuild_agent_day_stats(
    date_from: date,
    date_to: date,
    source: str | None = None,
) -> dict[str, Any]:
    if date_from > date_to:
        raise ValueError("date_from nao pode ser maior que date_to")

    event_qs = AgentEvent.objects.filter(
        dt_inicio__date__gte=date_from,
        dt_inicio__date__lte=date_to,
    )
    workday_qs = AgentWorkday.objects.filter(
        work_date__gte=date_from,
        work_date__lte=date_to,
    )
    if source:
        event_qs = event_qs.filter(source=source)
        workday_qs = workday_qs.filter(source=source)

    # AgentDayStats is keyed by (agent, day), so we rebuild only affected pairs.
    event_pairs = {
        (agent_id, data_ref)
        for agent_id, data_ref in event_qs.values_list("agent_id", "dt_inicio__date").distinct()
        if agent_id and data_ref
    }

    workday_rows = list(
        workday_qs.values("cd_operador", "nm_operador", "work_date").distinct()
    )
    workday_cds = {int(row["cd_operador"]) for row in workday_rows if row.get("cd_operador")}
    agents_by_cd = {
        agent.cd_operador: agent
        for agent in Agent.objects.filter(cd_operador__in=workday_cds)
    }

    workday_pairs: set[tuple[int, date]] = set()
    for row in workday_rows:
        cd_operador = row.get("cd_operador")
        work_date = row.get("work_date")
        if not cd_operador or not work_date:
            continue

        agent = agents_by_cd.get(int(cd_operador))
        if agent is None:
            agent = Agent.objects.create(
                cd_operador=int(cd_operador),
                nm_agente=(row.get("nm_operador") or "Sem nome")[:100],
                ativo=True,
            )
            agents_by_cd[int(cd_operador)] = agent
        elif row.get("nm_operador"):
            incoming_name = str(row["nm_operador"]).strip()[:100]
            if incoming_name and incoming_name != (agent.nm_agente or ""):
                agent.nm_agente = incoming_name
                agent.save(update_fields=["nm_agente"])

        workday_pairs.add((agent.id, work_date))

    affected_pairs = event_pairs | workday_pairs
    if not affected_pairs:
        return {
            "date_from": date_from,
            "date_to": date_to,
            "source": source,
            "pairs_total": 0,
            "created": 0,
            "updated": 0,
        }

    aggregated = (
        event_qs.values("agent_id", "dt_inicio__date")
        .annotate(
            qtd_pausas=Count("id", filter=Q(tp_evento__iexact="PAUSA")),
            tempo_pausas_seg=Coalesce(Sum("duracao_seg", filter=Q(tp_evento__iexact="PAUSA")), 0),
            ultima_pausa_inicio=Max("dt_inicio", filter=Q(tp_evento__iexact="PAUSA")),
            ultima_pausa_fim=Max("dt_fim", filter=Q(tp_evento__iexact="PAUSA")),
            ultimo_logon=Max("dt_inicio", filter=Q(tp_evento__iexact="LOGON")),
            ultimo_logoff=Max("dt_inicio", filter=Q(tp_evento__iexact="LOGOFF")),
        )
    )
    aggregate_map = {
        (int(row["agent_id"]), row["dt_inicio__date"]): row
        for row in aggregated
        if row.get("agent_id") and row.get("dt_inicio__date")
    }

    agents_by_id = {
        agent.id: agent
        for agent in Agent.objects.filter(id__in={pair[0] for pair in affected_pairs})
    }

    created = 0
    updated = 0

    with transaction.atomic():
        for agent_id, data_ref in sorted(affected_pairs, key=lambda item: (item[1], item[0])):
            agent = agents_by_id.get(agent_id)
            if agent is None:
                continue

            row = aggregate_map.get((agent_id, data_ref), {})
            values = {
                "cd_operador": agent.cd_operador,
                "qtd_pausas": row.get("qtd_pausas") or 0,
                "tempo_pausas_seg": row.get("tempo_pausas_seg") or 0,
                "ultima_pausa_inicio": row.get("ultima_pausa_inicio"),
                "ultima_pausa_fim": row.get("ultima_pausa_fim"),
                "ultimo_logon": row.get("ultimo_logon"),
                "ultimo_logoff": row.get("ultimo_logoff"),
            }

            stats_obj, was_created = AgentDayStats.objects.get_or_create(
                agent=agent,
                data_ref=data_ref,
                defaults=values,
            )
            if was_created:
                created += 1
                continue

            changed_fields: list[str] = []
            for field, incoming in values.items():
                if getattr(stats_obj, field) != incoming:
                    setattr(stats_obj, field, incoming)
                    changed_fields.append(field)

            if changed_fields:
                stats_obj.save(update_fields=changed_fields)
                updated += 1

    return {
        "date_from": date_from,
        "date_to": date_to,
        "source": source,
        "pairs_total": len(affected_pairs),
        "created": created,
        "updated": updated,
    }


def infer_rebuild_window_for_all(source: str | None = None) -> tuple[date, date] | None:
    event_qs = AgentEvent.objects.all()
    workday_qs = AgentWorkday.objects.all()
    if source:
        event_qs = event_qs.filter(source=source)
        workday_qs = workday_qs.filter(source=source)

    event_range = event_qs.aggregate(min_date=Min("dt_inicio"), max_date=Max("dt_inicio"))
    workday_range = workday_qs.aggregate(min_date=Min("work_date"), max_date=Max("work_date"))

    min_candidates = [
        _as_date(event_range.get("min_date")),
        _as_date(workday_range.get("min_date")),
    ]
    max_candidates = [
        _as_date(event_range.get("max_date")),
        _as_date(workday_range.get("max_date")),
    ]
    min_values = [value for value in min_candidates if value is not None]
    max_values = [value for value in max_candidates if value is not None]
    if not min_values or not max_values:
        return None
    return min(min_values), max(max_values)


def _as_date(value) -> date | None:
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        if timezone.is_aware(value):
            value = timezone.localtime(value, timezone.get_current_timezone())
        return value.date()
    return None
