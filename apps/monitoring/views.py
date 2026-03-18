import re
import logging
from collections import defaultdict
from urllib.parse import urlencode
from datetime import datetime, time, timedelta

from django.contrib import messages
from django.contrib import admin as django_admin
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.db.models import Count, F, Max, Min, Q, Sum
from django.db.models.functions import Coalesce
from django.db.models.functions import ExtractHour
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.views import View
from django.views.generic import DetailView, ListView, TemplateView

from .models import (
    Agent,
    AgentDayStats,
    AgentEvent,
    AgentWorkday,
    JobNameChoices,
    JobRun,
    JobRunStatusChoices,
    PauseCategoryChoices,
    PauseClassification,
)
from .services.day_stats_service import rebuild_agent_day_stats
from .services.dashboard_period_filter import (
    MONTH_OPTIONS,
    QUICK_RANGE_OPTIONS,
    format_period_command_args,
    resolve_dashboard_period_filter,
)
from .services.pause_classification import (
    UNCLASSIFIED_CATEGORY,
    list_distinct_event_pause_names,
    list_event_pause_names_by_classification,
    normalize_pause_name,
    normalize_source,
    resolve_pause_category,
)
from .services.risk_scoring import (
    DEFAULT_RISK_CONFIG,
    calculate_agent_risk,
    is_no_activity_metric,
)
from .utils import format_run_duration_hhmm, format_seconds_hhmm

logger = logging.getLogger(__name__)


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "monitoring/dashboard_executive.html"
    RISK_CONFIG = DEFAULT_RISK_CONFIG
    PAUSE_ALERT_THRESHOLD_MIN = int(DEFAULT_RISK_CONFIG.high_harmful_minutes_threshold)
    LOW_OCCUPANCY_THRESHOLD_PCT = int(DEFAULT_RISK_CONFIG.low_occupancy_threshold_pct)
    EVENT_GAP_ALERT_HOURS = 2
    PAUSE_CATEGORY_ORDER = [
        PauseCategoryChoices.LEGAL,
        PauseCategoryChoices.NEUTRAL,
        PauseCategoryChoices.HARMFUL,
        UNCLASSIFIED_CATEGORY,
    ]
    PAUSE_CATEGORY_DISPLAY = {
        PauseCategoryChoices.LEGAL: "Tempo Produtivo",
        PauseCategoryChoices.NEUTRAL: "Tempo Neutro",
        PauseCategoryChoices.HARMFUL: "Tempo Improdutivo",
        UNCLASSIFIED_CATEGORY: "Tempo Nao Classificado",
    }
    TEMPLATE_CONTEXT_EXCLUDE = {
        "monitoring/dashboard_executive.html": {
            "command_snippets",
            "can_manage_jobs",
            "summary_kpis",
            "ranking_counts",
            "day_detail_url",
        },
        "monitoring/dashboard_productivity.html": {
            "top_pause_time",
            "top_pause_count",
            "risk_agents",
            "alerts",
            "active_agents_without_activity",
            "events_by_hour",
            "pauses_by_hour",
            "completeness_panel",
            "last_job_run",
            "last_job_duration",
            "last_job_processed_count",
            "recent_job_runs",
            "command_snippets",
            "day_detail_url",
            "can_manage_jobs",
            "stats_warning",
            "pause_block_message",
            "pause_data_state",
            "summary_kpis",
            "ranking_counts",
        },
        "monitoring/dashboard_risk.html": {
            "top_pause_count",
            "top_productivity",
            "operator_metrics",
            "pause_distribution",
            "pauses_by_hour",
            "events_by_hour",
            "completeness_panel",
            "last_job_run",
            "last_job_duration",
            "last_job_processed_count",
            "recent_job_runs",
            "command_snippets",
            "day_detail_url",
            "can_manage_jobs",
            "stats_warning",
            "pause_block_message",
            "pause_data_state",
            "summary_kpis",
            "ranking_counts",
        },
        "monitoring/dashboard_pipeline.html": {
            "top_pause_time",
            "top_pause_count",
            "top_productivity",
            "operator_metrics",
            "risk_agents",
            "alerts",
            "active_agents_without_activity",
            "pause_distribution",
            "pauses_by_hour",
            "events_by_hour",
            "stats_warning",
            "pause_block_message",
            "pause_data_state",
            "summary_kpis",
            "ranking_counts",
        },
    }

    @staticmethod
    def _calculate_operational_score(taxa_ocupacao_pct: float, alert_totals: dict[str, int]) -> int:
        base_score = int(round(max(0.0, min(float(taxa_ocupacao_pct or 0.0), 100.0))))
        crit_penalty = min(int(alert_totals.get("crit", 0)) * 8, 40)
        warn_penalty = min(int(alert_totals.get("warn", 0)) * 3, 24)
        info_penalty = min(int(alert_totals.get("info", 0)), 8)
        return max(0, base_score - crit_penalty - warn_penalty - info_penalty)

    @staticmethod
    def _resolve_health_status(score: int) -> str:
        if score >= 85:
            return "Excelente"
        if score >= 70:
            return "Estavel"
        if score >= 50:
            return "Atencao"
        return "Critico"

    @staticmethod
    def _pipeline_stability_from_job(last_job_run) -> int:
        if not last_job_run:
            return 55
        status_text = str(getattr(last_job_run, "status", "") or "").lower()
        if any(token in status_text for token in ("success", "completed", "done", "ok")):
            return 92
        if "running" in status_text:
            return 75
        if any(token in status_text for token in ("error", "failed", "fail")):
            return 35
        return 65

    @staticmethod
    def _calculate_health_score(
        produtividade_score: float,
        risco_score: float,
        ocupacao_score: float,
        pipeline_score: float,
    ) -> int:
        weighted = (
            (float(produtividade_score or 0.0) * 0.35)
            + (float(risco_score or 0.0) * 0.25)
            + (float(ocupacao_score or 0.0) * 0.20)
            + (float(pipeline_score or 0.0) * 0.20)
        )
        return max(0, min(int(round(weighted)), 100))

    @staticmethod
    def _build_gamified_leaderboard(leaderboard_agents: list[dict], operation_average: float) -> list[dict]:
        medals = {
            1: {"name": "Ouro", "emoji": "ðŸ¥‡"},
            2: {"name": "Prata", "emoji": "ðŸ¥ˆ"},
            3: {"name": "Bronze", "emoji": "ðŸ¥‰"},
        }
        average = float(operation_average or 0.0)
        cards: list[dict] = []
        for position, item in enumerate(leaderboard_agents, start=1):
            agent_score = float(item.get("taxa_ocupacao_pct") or 0.0)
            logged_seconds = int(item.get("tempo_logado_seg") or 0)
            logged_hours = logged_seconds / 3600 if logged_seconds > 0 else 0.0
            if logged_hours < 2:
                streak_days = 0
            elif agent_score >= 85:
                streak_days = 7
            elif agent_score >= 75:
                streak_days = 5
            elif agent_score >= 65:
                streak_days = 3
            elif agent_score >= 55:
                streak_days = 2
            else:
                streak_days = 1
            badges = []
            if position == 1:
                badges.append("Operador do turno")
            if agent_score >= 85:
                badges.append("Consistencia alta")
            if agent_score > average:
                badges.append("Acima da media")
            cards.append(
                {
                    **item,
                    "position": position,
                    "medal": medals.get(position),
                    "streak_days": streak_days,
                    "badges": badges[:3],
                    "progress_vs_average_pct": max(0, min(int(round((agent_score / max(average, 1)) * 100)), 180)),
                    "score_delta_vs_average": round(agent_score - average, 1),
                }
            )
        return cards

    def _prune_context_for_template(self, context: dict) -> dict:
        excluded_keys = self.TEMPLATE_CONTEXT_EXCLUDE.get(self.template_name, set())
        for key in excluded_keys:
            context.pop(key, None)
        return context

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        period_filter = resolve_dashboard_period_filter(self.request.GET)
        selected_date = period_filter.selected_date
        period_date_from = period_filter.date_from
        period_date_to = period_filter.date_to
        period_start = period_filter.dt_start
        period_end = period_filter.dt_end
        search = (self.request.GET.get("q") or "").strip()

        active_agents_qs = Agent.objects.filter(ativo=True)
        stats_qs = AgentDayStats.objects.filter(
            data_ref__gte=period_date_from,
            data_ref__lte=period_date_to,
        ).select_related("agent")
        events_day_qs = AgentEvent.objects.filter(
            dt_inicio__gte=period_start,
            dt_inicio__lt=period_end,
        ).select_related("agent")
        workday_day_qs = AgentWorkday.objects.filter(
            work_date__gte=period_date_from,
            work_date__lte=period_date_to,
        )
        if search:
            search_filter = (
                Q(agent__nm_agente__icontains=search)
                | Q(agent__nm_agente_code__icontains=search)
                | Q(agent__nr_ramal__icontains=search)
            )
            event_filter = (
                Q(agent__nm_agente__icontains=search)
                | Q(agent__nm_agente_code__icontains=search)
                | Q(nm_pausa__icontains=search)
            )
            workday_filter = Q(nm_operador__icontains=search)
            active_filter = Q(nm_agente__icontains=search) | Q(nm_agente_code__icontains=search)
            if search.isdigit():
                search_filter |= Q(cd_operador=int(search))
                event_filter |= Q(cd_operador=int(search))
                workday_filter |= Q(cd_operador=int(search))
                active_filter |= Q(cd_operador=int(search))
            active_agents_qs = active_agents_qs.filter(active_filter)
            stats_qs = stats_qs.filter(search_filter)
            events_day_qs = events_day_qs.filter(event_filter)
            workday_day_qs = workday_day_qs.filter(workday_filter)

        stats_agents_count = stats_qs.count()
        workday_count = workday_day_qs.count()
        stats_by_operator = self._build_stats_by_operator(stats_qs=stats_qs)
        operators_with_stats_activity = {
            int(cd_operador)
            for cd_operador in stats_qs.filter(
                Q(qtd_pausas__gt=0)
                | Q(tempo_pausas_seg__gt=0)
                | Q(ultimo_logon__isnull=False)
                | Q(ultimo_logoff__isnull=False)
            ).values_list("cd_operador", flat=True).distinct()
            if cd_operador is not None
        }
        stats_signal_count = len(operators_with_stats_activity)

        active_agents_count = active_agents_qs.count()
        operators_with_events = set(
            events_day_qs.values_list("cd_operador", flat=True).distinct()
        )
        operators_with_workday = set(
            workday_day_qs.values_list("cd_operador", flat=True).distinct()
        )
        activity_operator_ids = operators_with_events | operators_with_workday | operators_with_stats_activity
        agents_with_activity_count = len(activity_operator_ids)
        total_events_day = events_day_qs.count()

        pause_events_qs = events_day_qs.filter(
            Q(tp_evento__iexact="PAUSA")
            | (Q(nm_pausa__isnull=False) & ~Q(nm_pausa__exact=""))
        )
        pause_classified = self._build_pause_classified_aggregates(pause_events_qs=pause_events_qs)
        pause_by_operator = pause_classified["by_operator"]
        pause_category_totals = pause_classified["totals_seconds"]
        pause_category_counts = pause_classified["totals_count"]
        total_pausas_hoje = int(pause_classified["total_events"])
        total_tempo_pausas = int(pause_classified["total_seconds"])

        tempo_produtivo_classificado_seg = int(
            pause_category_totals.get(PauseCategoryChoices.LEGAL, 0)
        )
        tempo_neutro_seg = int(pause_category_totals.get(PauseCategoryChoices.NEUTRAL, 0))
        tempo_improdutivo_seg = int(pause_category_totals.get(PauseCategoryChoices.HARMFUL, 0))
        tempo_nao_classificado_seg = int(pause_category_totals.get(UNCLASSIFIED_CATEGORY, 0))

        pause_distribution = self._build_pause_distribution(
            pause_category_totals=pause_category_totals,
            pause_category_counts=pause_category_counts,
        )
        pause_type_breakdowns = self._build_pause_type_breakdowns(
            pause_events_qs=pause_events_qs,
            limit=6,
        )
        pause_type_by_time = pause_type_breakdowns["by_time"]
        pause_type_by_count = pause_type_breakdowns["by_count"]
        pause_hourly_distribution = self._build_pause_hourly_distribution(pause_events_qs=pause_events_qs)

        workday_logged_rows = list(
            workday_day_qs.values("cd_operador")
            .annotate(logged_seg=Coalesce(Sum("duracao_seg"), 0))
        )
        logged_by_operator = {
            int(row["cd_operador"]): int(row["logged_seg"] or 0)
            for row in workday_logged_rows
            if row.get("cd_operador")
        }
        total_logged_time = sum(logged_by_operator.values())
        logged_time_source = "workday" if total_logged_time > 0 else "event_estimate"

        estimated_logged_by_operator = self._estimate_login_seconds_per_operator(
            events_day_qs=events_day_qs,
            period_end=period_end,
            period_end_date=period_date_to,
        )
        if total_logged_time <= 0:
            total_logged_time = sum(estimated_logged_by_operator.values())

        pause_data_state = self._resolve_pause_data_state(
            pause_count=total_pausas_hoje,
            events_count=total_events_day,
            workday_count=workday_count,
            stats_count=stats_agents_count,
        )
        pause_total_display = "N/A" if pause_data_state == "missing" else str(total_pausas_hoje)

        media_pausas_por_agente = (
            round(total_pausas_hoje / agents_with_activity_count, 2)
            if agents_with_activity_count
            else 0.0
        )
        tempo_medio_pausa_seg = (
            int(total_tempo_pausas // total_pausas_hoje)
            if total_pausas_hoje
            else 0
        )

        stats_warning = False
        if stats_agents_count == 0 and (total_events_day > 0 or workday_day_qs.exists()):
            stats_warning = True

        names_by_operator = self._build_names_map(
            operator_ids=activity_operator_ids,
            workday_day_qs=workday_day_qs,
        )
        operator_metrics = self._build_operator_metrics(
            operator_ids=activity_operator_ids,
            names_by_operator=names_by_operator,
            pause_by_operator=pause_by_operator,
            stats_by_operator=stats_by_operator,
            logged_by_operator=logged_by_operator,
            estimated_logged_by_operator=estimated_logged_by_operator,
            relevant_events_by_operator=self._build_relevant_events_by_operator(
                events_day_qs=events_day_qs
            ),
        )
        top_pause_time, top_pause_count = self._build_pause_rankings(
            operator_metrics=operator_metrics,
        )
        top_productivity = self._build_productivity_ranking(operator_metrics=operator_metrics)
        self._attach_bar_pct(top_pause_time, "tempo_pausas_seg")
        self._attach_bar_pct(top_pause_count, "qtd_pausas")
        self._attach_bar_pct(top_productivity, "tempo_produtivo_seg")
        productive_time = sum(int(item.get("tempo_produtivo_seg") or 0) for item in operator_metrics)
        taxa_ocupacao_pct = (
            round((productive_time / total_logged_time) * 100, 2)
            if total_logged_time
            else 0.0
        )

        active_agents_without_activity = list(
            active_agents_qs.exclude(cd_operador__in=activity_operator_ids)
            .order_by("cd_operador")
            .values("cd_operador", "nm_agente")[:30]
        )

        events_by_hour = self._build_hourly_series(events_day_qs=events_day_qs)
        pauses_by_hour = (
            self._build_hourly_series(events_day_qs=pause_events_qs)
            if pause_data_state != "missing"
            else self._empty_hourly_series()
        )

        event_window = self._extract_range(events_day_qs, "dt_inicio", "dt_inicio")
        pause_window = self._extract_range(pause_events_qs, "dt_inicio", "dt_inicio")
        workday_window = self._extract_range(workday_day_qs, "dt_inicio", "dt_fim")
        stats_window = self._extract_stats_window(stats_qs)
        jobs_day_qs = JobRun.objects.filter(started_at__gte=period_start, started_at__lt=period_end)
        jobs_day_count = jobs_day_qs.count()
        jobs_window = self._extract_range(jobs_day_qs, "started_at", "started_at")

        last_job_run = JobRun.objects.order_by("-started_at").first()
        recent_job_runs = list(JobRun.objects.order_by("-started_at")[:5])
        for run in recent_job_runs:
            run.duration_hhmm = format_run_duration_hhmm(run)
            run.processed_count = self._extract_processed_count(run.summary)
        last_job_duration = format_run_duration_hhmm(last_job_run) if last_job_run else "-"
        last_job_processed_count = (
            self._extract_processed_count(last_job_run.summary) if last_job_run else None
        )
        if last_job_run:
            last_job_run.processed_count = self._extract_processed_count(last_job_run.summary)

        pause_p90_seg = self._percentile(
            [int(item.get("tempo_pausas_seg") or 0) for item in pause_by_operator.values()],
            90,
        )
        pause_p90_display = (
            "N/A" if pause_data_state == "missing" else format_seconds_hhmm(pause_p90_seg)
        )
        risk_agents = self._build_risk_agents(
            operator_metrics=operator_metrics,
            risk_config=self.RISK_CONFIG,
        )[:10]
        no_activity_agents = self._build_no_activity_agents(operator_metrics=operator_metrics)
        alerts = self._build_operational_alerts(
            operator_metrics=operator_metrics,
            no_activity_agents=no_activity_agents,
            events_day_qs=events_day_qs,
            events_by_hour=events_by_hour,
            total_events_day=total_events_day,
            pause_category_totals=pause_category_totals,
            pause_category_counts=pause_category_counts,
        )
        alert_totals = {"crit": 0, "warn": 0, "info": 0}
        for alert in alerts:
            severity_key = str(alert.get("severity") or "info").lower()
            if severity_key not in alert_totals:
                severity_key = "info"
            alert_totals[severity_key] += 1
        score_operacional = self._calculate_operational_score(
            taxa_ocupacao_pct=taxa_ocupacao_pct,
            alert_totals=alert_totals,
        )
        stability_score = max(
            0,
            min(
                100,
                100 - (alert_totals["crit"] * 12) - (alert_totals["warn"] * 5) - (alert_totals["info"] * 2),
            ),
        )
        top3_productivity = top_productivity[:3]
        leaderboard_agents = top_productivity[:10]
        pipeline_stability_score = self._pipeline_stability_from_job(last_job_run)
        risk_health_score = max(
            0,
            min(100, 100 - (alert_totals["crit"] * 18) - (alert_totals["warn"] * 8) - (alert_totals["info"] * 3)),
        )
        occupancy_coverage_score = (
            round((agents_with_activity_count / active_agents_count) * 100, 1) if active_agents_count else 0.0
        )
        health_score = self._calculate_health_score(
            produtividade_score=taxa_ocupacao_pct,
            risco_score=risk_health_score,
            ocupacao_score=occupancy_coverage_score,
            pipeline_score=pipeline_stability_score,
        )
        health_status = self._resolve_health_status(health_score)
        gamified_leaderboard = self._build_gamified_leaderboard(
            leaderboard_agents=leaderboard_agents,
            operation_average=taxa_ocupacao_pct,
        )
        medalists_top3 = gamified_leaderboard[:3]
        low_productivity_agents = sorted(
            [item for item in operator_metrics if item.get("tempo_logado_seg", 0) > 0],
            key=lambda item: float(item.get("taxa_ocupacao_pct") or 0.0),
        )[:5]
        risk_radar_dimensions = [
            {"label": "Pausas", "value": max(0, min(int(round((total_tempo_pausas / max(total_logged_time, 1)) * 100 * 1.3)), 100))},
            {"label": "Ociosidade", "value": max(0, min(int(round(100 - float(taxa_ocupacao_pct or 0.0))), 100))},
            {"label": "Alertas", "value": max(0, min((alert_totals["crit"] * 35) + (alert_totals["warn"] * 15) + (alert_totals["info"] * 5), 100))},
            {"label": "Prod. baixa", "value": max(0, min(int(round(max(0.0, 70 - float(taxa_ocupacao_pct or 0.0)) * 1.6)), 100))},
            {"label": "Falhas op.", "value": max(0, min(int(round(100 - stability_score)), 100))},
        ]
        executive_pause_radar = self._build_executive_pause_radar(
            total_pause_events=total_pausas_hoje,
            total_pause_seconds=total_tempo_pausas,
            tempo_improdutivo_seg=tempo_improdutivo_seg,
            tempo_neutro_seg=tempo_neutro_seg,
            tempo_nao_classificado_seg=tempo_nao_classificado_seg,
            total_logged_time=total_logged_time,
            alert_totals=alert_totals,
            taxa_ocupacao_pct=taxa_ocupacao_pct,
        )
        ranking_counts = {
            "top_pause_time": len(top_pause_time),
            "top_pause_count": len(top_pause_count),
            "top_productivity": len(top_productivity),
        }
        logger.debug(
            "dashboard rankings period=%s..%s mode=%s pause_state=%s events=%s workday=%s counts=%s",
            period_date_from,
            period_date_to,
            period_filter.mode,
            pause_data_state,
            total_events_day,
            workday_count,
            ranking_counts,
        )

        day_iso = selected_date.isoformat()
        command_args = format_period_command_args(period_date_from, period_date_to)
        command_snippets = {
            "import_events": "python manage.py sync_legacy_events --lookback-minutes 1440",
            "import_pause": f"python manage.py import_lh_pause_events {command_args}",
            "import_workday": f"python manage.py import_lh_workday {command_args}",
            "import_all": f"python manage.py import_lh_all {command_args}",
            "rebuild_stats": f"python manage.py rebuild_agent_day_stats {command_args}",
        }
        completeness_panel = self._build_completeness_panel(
            period_date_from=period_date_from,
            period_date_to=period_date_to,
            total_events_day=total_events_day,
            event_window=event_window,
            total_pausas=total_pausas_hoje,
            pause_window=pause_window,
            workday_count=workday_count,
            workday_window=workday_window,
            stats_count=stats_signal_count,
            stats_total_count=stats_agents_count,
            stats_window=stats_window,
            jobs_count=jobs_day_count,
            jobs_window=jobs_window,
            last_job_run=last_job_run,
            command_snippets=command_snippets,
        )
        day_detail_url = f"{reverse('dashboard-day-detail')}?{urlencode({'data_ref': day_iso})}"

        pause_block_message = None
        if pause_data_state == "missing":
            pause_block_message = (
                f"Sem dados de pausas importados para o periodo {period_filter.period_label}. "
                f"Execute: {command_snippets['import_pause']}"
            )
        elif pause_data_state == "zero":
            pause_block_message = "Total de pausas: 0 (dados presentes no periodo)."

        available_years = self._build_available_year_options(selected_year=period_filter.selected_year)
        is_empty_period = total_events_day <= 0 and workday_count <= 0 and stats_agents_count <= 0

        context.update(
            {
                "selected_date": selected_date,
                "day_iso": day_iso,
                "selected_year": period_filter.selected_year,
                "selected_month": period_filter.selected_month,
                "selected_data_ref": period_filter.selected_data_ref,
                "selected_date_from": period_filter.selected_date_from,
                "selected_date_to": period_filter.selected_date_to,
                "selected_quick_range": period_filter.selected_quick_range,
                "available_years": available_years,
                "month_options": MONTH_OPTIONS,
                "quick_range_options": QUICK_RANGE_OPTIONS,
                "applied_period_label": period_filter.period_label,
                "period_scope_label": period_filter.scope_label,
                "is_single_day_period": period_filter.is_single_day,
                "filter_warning": period_filter.warning,
                "is_empty_period": is_empty_period,
                "search": search,
                "active_agents_count": active_agents_count,
                "agents_with_activity_count": agents_with_activity_count,
                "active_agents_without_activity": active_agents_without_activity,
                "total_events_day": total_events_day,
                "workday_count": workday_count,
                "agents_with_stats_count": stats_signal_count,
                "agents_with_stats_total_count": stats_agents_count,
                "total_pausas_hoje": total_pausas_hoje,
                "total_pausas_display": pause_total_display,
                "tempo_total_pausas_hhmm": format_seconds_hhmm(total_tempo_pausas),
                "tempo_medio_pausa_hhmm": format_seconds_hhmm(tempo_medio_pausa_seg),
                "media_pausas_por_agente": media_pausas_por_agente,
                "tempo_logado_total_hhmm": format_seconds_hhmm(total_logged_time),
                "tempo_produtivo_total_hhmm": format_seconds_hhmm(productive_time),
                "tempo_neutro_total_hhmm": format_seconds_hhmm(tempo_neutro_seg),
                "tempo_improdutivo_total_hhmm": format_seconds_hhmm(tempo_improdutivo_seg),
                "tempo_nao_classificado_total_hhmm": format_seconds_hhmm(tempo_nao_classificado_seg),
                "taxa_ocupacao_pct": taxa_ocupacao_pct,
                "score_operacional": score_operacional,
                "stability_score": stability_score,
                "pipeline_stability_score": pipeline_stability_score,
                "health_score": health_score,
                "health_status": health_status,
                "health_score_breakdown": {
                    "produtividade": round(float(taxa_ocupacao_pct or 0.0), 1),
                    "risco": risk_health_score,
                    "ocupacao": occupancy_coverage_score,
                    "pipeline": pipeline_stability_score,
                },
                "pause_p90_hhmm": pause_p90_display,
                "tempo_logado_source": logged_time_source,
                "pause_classification_totals_seg": pause_category_totals,
                "pause_classification_counts": pause_category_counts,
                "pause_category_display": self.PAUSE_CATEGORY_DISPLAY,
                "top_pause_time": top_pause_time,
                "top_pause_count": top_pause_count,
                "top_productivity": top_productivity,
                "top3_productivity": top3_productivity,
                "leaderboard_agents": leaderboard_agents,
                "gamified_leaderboard": gamified_leaderboard,
                "medalists_top3": medalists_top3,
                "low_productivity_agents": low_productivity_agents,
                "operator_metrics": operator_metrics,
                "risk_agents": risk_agents,
                "risk_radar_dimensions": risk_radar_dimensions,
                "alerts": alerts,
                "alert_totals": alert_totals,
                "ranking_counts": ranking_counts,
                "pause_distribution": pause_distribution,
                "pause_type_by_time": pause_type_by_time,
                "pause_type_by_count": pause_type_by_count,
                "pause_hourly_distribution": pause_hourly_distribution,
                "executive_pause_radar": executive_pause_radar,
                "pauses_by_hour": pauses_by_hour,
                "events_by_hour": events_by_hour,
                "stats_warning": stats_warning,
                "pause_data_state": pause_data_state,
                "pause_block_message": pause_block_message,
                "last_job_run": last_job_run,
                "last_job_duration": last_job_duration,
                "last_job_processed_count": last_job_processed_count,
                "recent_job_runs": recent_job_runs,
                "completeness_panel": completeness_panel,
                "command_snippets": command_snippets,
                "day_detail_url": day_detail_url,
                "can_manage_jobs": bool(self.request.user.is_staff),
                "summary_kpis": {
                    "active_agents_count": active_agents_count,
                    "agents_with_activity_count": agents_with_activity_count,
                    "total_events_day": total_events_day,
                    "agents_with_stats_count": stats_signal_count,
                    "agents_with_stats_total_count": stats_agents_count,
                    "tempo_logado_total_hhmm": format_seconds_hhmm(total_logged_time),
                    "tempo_total_pausas_hhmm": format_seconds_hhmm(total_tempo_pausas),
                    "tempo_produtivo_total_hhmm": format_seconds_hhmm(productive_time),
                    "tempo_neutro_total_hhmm": format_seconds_hhmm(tempo_neutro_seg),
                    "tempo_improdutivo_total_hhmm": format_seconds_hhmm(tempo_improdutivo_seg),
                    "tempo_nao_classificado_total_hhmm": format_seconds_hhmm(tempo_nao_classificado_seg),
                    "taxa_ocupacao_pct": taxa_ocupacao_pct,
                    "score_operacional": score_operacional,
                    "media_pausas_por_agente": media_pausas_por_agente,
                    "tempo_medio_pausa_hhmm": format_seconds_hhmm(tempo_medio_pausa_seg),
                    "pause_p90_hhmm": pause_p90_display,
                },
            }
        )
        return self._prune_context_for_template(context)


class DashboardProductivityView(DashboardView):
    template_name = "monitoring/dashboard_productivity.html"


class DashboardRiskView(DashboardView):
    template_name = "monitoring/dashboard_risk.html"


class DashboardPipelineView(DashboardView):
    template_name = "monitoring/dashboard_pipeline.html"

    def _selected_date(self):
        date_str = self.request.GET.get("data_ref")
        parsed = parse_date(date_str) if date_str else None
        return parsed or timezone.localdate()

    @staticmethod
    def _day_window(day_ref):
        current_tz = timezone.get_current_timezone()
        day_start = timezone.make_aware(datetime.combine(day_ref, time.min), current_tz)
        day_end = day_start + timedelta(days=1)
        return day_start, day_end

    @staticmethod
    def _build_available_year_options(selected_year: int | None = None) -> list[int]:
        years: set[int] = set()

        stats_years = AgentDayStats.objects.order_by().values_list("data_ref__year", flat=True).distinct()
        workday_years = AgentWorkday.objects.order_by().values_list("work_date__year", flat=True).distinct()
        for year in list(stats_years) + list(workday_years):
            if year:
                years.add(int(year))

        if not years:
            event_bounds = AgentEvent.objects.aggregate(
                min_dt=Min("dt_inicio"),
                max_dt=Max("dt_inicio"),
            )
            for boundary in [event_bounds.get("min_dt"), event_bounds.get("max_dt")]:
                if boundary is None:
                    continue
                if timezone.is_aware(boundary):
                    boundary = timezone.localtime(boundary, timezone.get_current_timezone())
                years.add(int(boundary.year))

        years.add(timezone.localdate().year)
        if selected_year:
            years.add(int(selected_year))
        return sorted(years, reverse=True)

    @staticmethod
    def _resolve_pause_data_state(pause_count: int, events_count: int, workday_count: int, stats_count: int):
        if pause_count > 0:
            return "present"
        if events_count > 0 or workday_count > 0 or stats_count > 0:
            return "zero"
        return "missing"

    @staticmethod
    def _extract_range(queryset, start_field: str, end_field: str):
        values = queryset.aggregate(start_value=Min(start_field), end_value=Max(end_field))
        return values.get("start_value"), values.get("end_value")

    @staticmethod
    def _extract_stats_window(stats_qs):
        values = stats_qs.aggregate(
            min_logon=Min("ultimo_logon"),
            min_pause=Min("ultima_pausa_inicio"),
            max_logoff=Max("ultimo_logoff"),
            max_pause=Max("ultima_pausa_fim"),
        )
        mins = [item for item in [values.get("min_logon"), values.get("min_pause")] if item is not None]
        maxs = [item for item in [values.get("max_logoff"), values.get("max_pause")] if item is not None]
        return (min(mins), max(maxs)) if mins and maxs else (None, None)

    @classmethod
    def _format_coverage(cls, start_value, end_value):
        if start_value is None or end_value is None:
            return "-"
        if timezone.is_aware(start_value):
            start_value = timezone.localtime(start_value, timezone.get_current_timezone())
        if timezone.is_aware(end_value):
            end_value = timezone.localtime(end_value, timezone.get_current_timezone())
        return f"{start_value:%H:%M} - {end_value:%H:%M}"

    @classmethod
    def _build_completeness_panel(
        cls,
        period_date_from,
        period_date_to,
        total_events_day: int,
        event_window,
        total_pausas: int,
        pause_window,
        workday_count: int,
        workday_window,
        stats_count: int,
        stats_total_count: int,
        stats_window,
        jobs_count: int,
        jobs_window,
        last_job_run,
        command_snippets: dict[str, str],
    ):
        period_label = (
            period_date_from.isoformat()
            if period_date_from == period_date_to
            else f"{period_date_from.isoformat()}..{period_date_to.isoformat()}"
        )
        panel = [
            {
                "key": "events",
                "label": "Eventos (AgentEvent)",
                "count": total_events_day,
                "status": "OK" if total_events_day > 0 else "EMPTY",
                "coverage": cls._format_coverage(*event_window),
                "hint": (
                    None
                    if total_events_day > 0
                    else "Importe eventos: python manage.py sync_legacy_events --lookback-minutes 1440"
                ),
            },
            {
                "key": "pauses",
                "label": "Pausas",
                "count": total_pausas,
                "status": "OK" if total_pausas > 0 else "EMPTY",
                "coverage": cls._format_coverage(*pause_window),
                "hint": (
                    None
                    if total_pausas > 0
                    else f"Importe pausas: {command_snippets['import_pause']}"
                ),
            },
            {
                "key": "workday",
                "label": "Jornada (AgentWorkday)",
                "count": workday_count,
                "status": "OK" if workday_count > 0 else "EMPTY",
                "coverage": cls._format_coverage(*workday_window),
                "hint": (
                    None
                    if workday_count > 0
                    else f"Importe jornada: {command_snippets['import_workday']}"
                ),
            },
            {
                "key": "stats",
                "label": "Stats (AgentDayStats)",
                "count": stats_count,
                "status": "OK" if stats_count > 0 else "EMPTY",
                "coverage": cls._format_coverage(*stats_window),
                "hint": (
                    (
                        f"Registros totais: {stats_total_count}. "
                        f"Somente {stats_count} com sinal de atividade."
                        if stats_total_count > stats_count
                        else None
                    )
                    if stats_count > 0
                    else f"Gere stats: {command_snippets['rebuild_stats']}"
                ),
            },
            {
                "key": "jobs",
                "label": "Jobs/Sync",
                "count": jobs_count,
                "status": "OK" if jobs_count > 0 else "EMPTY",
                "coverage": cls._format_coverage(*jobs_window),
                "hint": (
                    None
                    if jobs_count > 0
                    else f"Sem jobs em {period_label}. Rode sync/import e verifique /runs."
                ),
                "last_run": (
                    timezone.localtime(last_job_run.started_at).strftime("%d/%m/%Y %H:%M")
                    if last_job_run
                    else "-"
                ),
            },
        ]
        for item in panel:
            item["status_class"] = (
                "bg-emerald-500/20 text-emerald-300"
                if item["status"] == "OK"
                else "bg-amber-500/20 text-amber-300"
            )
        return panel

    @staticmethod
    def _estimate_login_seconds_per_operator(events_day_qs, period_end, period_end_date):
        log_events = events_day_qs.filter(
            Q(tp_evento__iexact="LOGON") | Q(tp_evento__iexact="LOGOFF")
        ).order_by("cd_operador", "dt_inicio", "id")

        now = timezone.now()
        close_time = period_end
        if period_end_date >= timezone.localdate():
            close_time = min(period_end, now)

        current_logon_by_operator: dict[int, datetime] = {}
        total_seconds_by_operator: dict[int, int] = {}
        for item in log_events.values("cd_operador", "tp_evento", "dt_inicio"):
            cd_operador = int(item["cd_operador"])
            event_type = str(item.get("tp_evento") or "").upper()
            event_dt = item.get("dt_inicio")
            if event_dt is None:
                continue

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

    @staticmethod
    def _build_names_map(operator_ids, workday_day_qs):
        if not operator_ids:
            return {}
        names_by_operator = {
            int(row["cd_operador"]): (row["nm_agente"] or "Sem nome")
            for row in Agent.objects.filter(cd_operador__in=operator_ids).values("cd_operador", "nm_agente")
        }
        for row in workday_day_qs.values("cd_operador", "nm_operador").distinct():
            cd_operador = row.get("cd_operador")
            if not cd_operador:
                continue
            cd_operador = int(cd_operador)
            if not names_by_operator.get(cd_operador):
                names_by_operator[cd_operador] = row.get("nm_operador") or f"Operador {cd_operador}"
        for cd_operador in operator_ids:
            names_by_operator.setdefault(int(cd_operador), f"Operador {cd_operador}")
        return names_by_operator

    @staticmethod
    def _empty_pause_category_dict(default_value=0):
        return {
            PauseCategoryChoices.LEGAL: default_value,
            PauseCategoryChoices.NEUTRAL: default_value,
            PauseCategoryChoices.HARMFUL: default_value,
            UNCLASSIFIED_CATEGORY: default_value,
        }

    def _build_pause_category_map(self, pause_events_qs):
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

        # Resolution order: source-specific classification first, then global fallback.
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

    @staticmethod
    def _resolve_event_duration_seconds(event_row: dict) -> int:
        duration_raw = event_row.get("duracao_seg")
        if duration_raw is not None:
            try:
                return max(0, int(duration_raw))
            except (TypeError, ValueError):
                pass

        start_dt = event_row.get("dt_inicio")
        end_dt = event_row.get("dt_fim")
        if start_dt and end_dt and end_dt > start_dt:
            return int((end_dt - start_dt).total_seconds())
        return 0

    def _build_pause_classified_aggregates(self, pause_events_qs):
        pause_category_map = self._build_pause_category_map(pause_events_qs=pause_events_qs)
        totals_seconds = self._empty_pause_category_dict(default_value=0)
        totals_count = self._empty_pause_category_dict(default_value=0)
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
            duration_seconds = self._resolve_event_duration_seconds(event)
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
            if not cd_operador:
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
                    "ultima_pausa_inicio": None,
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

            pause_started_at = event.get("dt_inicio")
            if pause_started_at and (
                row["ultima_pausa_inicio"] is None or pause_started_at > row["ultima_pausa_inicio"]
            ):
                row["ultima_pausa_inicio"] = pause_started_at

        return {
            "total_events": total_events,
            "total_seconds": total_seconds,
            "totals_seconds": totals_seconds,
            "totals_count": totals_count,
            "by_operator": by_operator,
        }

    @staticmethod
    def _build_pause_rankings(operator_metrics):
        top_pause_time_candidates = []
        top_pause_count_candidates = []
        for metric in operator_metrics:
            harmful_seconds = int(metric.get("tempo_improdutivo_seg") or 0)
            harmful_count = int(metric.get("qtd_improdutivas") or 0)
            row = {
                "cd_operador": int(metric["cd_operador"]),
                "agent_name": metric["agent_name"],
                "qtd_pausas": harmful_count,
                "tempo_pausas_seg": harmful_seconds,
                "tempo_pausas_hhmm": format_seconds_hhmm(harmful_seconds),
            }
            if harmful_seconds > 0:
                top_pause_time_candidates.append(row)
            if harmful_count > 0:
                top_pause_count_candidates.append(row)

        top_pause_time = sorted(
            top_pause_time_candidates,
            key=lambda item: (-item["tempo_pausas_seg"], -item["qtd_pausas"], item["cd_operador"]),
        )[:10]
        top_pause_count = sorted(
            top_pause_count_candidates,
            key=lambda item: (-item["qtd_pausas"], -item["tempo_pausas_seg"], item["cd_operador"]),
        )[:10]
        return top_pause_time, top_pause_count

    @staticmethod
    def _build_operator_metrics(
        operator_ids,
        names_by_operator,
        pause_by_operator,
        stats_by_operator,
        logged_by_operator,
        estimated_logged_by_operator,
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
                    "ultima_pausa_inicio": stats_info.get("ultima_pausa_inicio"),
                }
            logged_seg = int(
                logged_by_operator.get(int(cd_operador), estimated_logged_by_operator.get(int(cd_operador), 0))
                or 0
            )
            if logged_seg <= 0:
                logged_seg = int(stats_info.get("tempo_logado_seg") or 0)
            relevant_events_count = int(relevant_events_by_operator.get(int(cd_operador), 0) or 0)
            if relevant_events_count <= 0 and (
                int(stats_info.get("qtd_pausas") or 0) > 0
                or int(stats_info.get("tempo_logado_seg") or 0) > 0
            ):
                relevant_events_count = 1
            productive_classified_seg = int(pause_info.get("tempo_produtivo_seg") or 0)
            neutral_seg = int(pause_info.get("tempo_neutro_seg") or 0)
            harmful_seg = int(pause_info.get("tempo_improdutivo_seg") or 0)
            unclassified_seg = int(pause_info.get("tempo_nao_classificado_seg") or 0)
            total_pause_seg = int(pause_info.get("tempo_pausas_seg") or 0)
            productive_estimated_seg = max(0, logged_seg - total_pause_seg) if logged_seg else 0
            if productive_classified_seg > 0:
                productive_seg = productive_classified_seg
            elif relevant_events_count > 0:
                productive_seg = productive_estimated_seg
            else:
                productive_seg = 0
            occupancy_pct = round((productive_seg / logged_seg) * 100, 2) if logged_seg else None
            items.append(
                {
                    "cd_operador": int(cd_operador),
                    "agent_name": names_by_operator.get(int(cd_operador), f"Operador {cd_operador}"),
                    "qtd_pausas": int(pause_info.get("qtd_pausas") or 0),
                    "qtd_improdutivas": int(pause_info.get("qtd_improdutivas") or 0),
                    "tempo_pausas_seg": total_pause_seg,
                    "tempo_produtivo_classificado_seg": productive_classified_seg,
                    "tempo_produtivo_estimado_seg": productive_estimated_seg,
                    "tempo_produtivo_seg": productive_seg,
                    "tempo_neutro_seg": neutral_seg,
                    "tempo_improdutivo_seg": harmful_seg,
                    "tempo_nao_classificado_seg": unclassified_seg,
                    "tempo_produtivo_hhmm": format_seconds_hhmm(productive_seg),
                    "tempo_neutro_hhmm": format_seconds_hhmm(neutral_seg),
                    "tempo_improdutivo_hhmm": format_seconds_hhmm(harmful_seg),
                    "tempo_nao_classificado_hhmm": format_seconds_hhmm(unclassified_seg),
                    "tempo_logado_hhmm": format_seconds_hhmm(logged_seg),
                    "tempo_logado_seg": logged_seg,
                    "qtd_eventos_relevantes": relevant_events_count,
                    "taxa_ocupacao_pct": occupancy_pct,
                }
            )
        return items

    @staticmethod
    def _build_stats_by_operator(stats_qs):
        items = {}
        for row in stats_qs.values(
            "cd_operador",
            "qtd_pausas",
            "tempo_pausas_seg",
            "ultimo_logon",
            "ultimo_logoff",
            "ultima_pausa_inicio",
        ):
            cd_operador = row.get("cd_operador")
            if cd_operador is None:
                continue
            logon_dt = row.get("ultimo_logon")
            logoff_dt = row.get("ultimo_logoff")
            tempo_logado_seg = 0
            if logon_dt and logoff_dt and logoff_dt > logon_dt:
                tempo_logado_seg = int((logoff_dt - logon_dt).total_seconds())
            items[int(cd_operador)] = {
                "qtd_pausas": int(row.get("qtd_pausas") or 0),
                "tempo_pausas_seg": int(row.get("tempo_pausas_seg") or 0),
                "tempo_logado_seg": max(0, tempo_logado_seg),
                "ultima_pausa_inicio": row.get("ultima_pausa_inicio"),
            }
        return items

    @staticmethod
    def _build_relevant_events_by_operator(events_day_qs):
        relevant_events_qs = events_day_qs.filter(
            Q(tp_evento__iexact="PAUSA")
            | (Q(nm_pausa__isnull=False) & ~Q(nm_pausa__exact=""))
            | Q(tp_evento__icontains="ATEND")
        )
        rows = list(
            relevant_events_qs.values("cd_operador")
            .annotate(total=Count("id"))
        )
        return {
            int(row["cd_operador"]): int(row["total"] or 0)
            for row in rows
            if row.get("cd_operador") is not None
        }

    @staticmethod
    def _build_productivity_ranking(operator_metrics):
        candidates = [
            item for item in operator_metrics
            if int(item.get("tempo_produtivo_seg") or 0) > 0
        ]
        return sorted(
            candidates,
            key=lambda item: (-item["tempo_produtivo_seg"], item["cd_operador"]),
        )[:10]

    def _build_pause_distribution(self, pause_category_totals, pause_category_counts):
        items = []
        for category in self.PAUSE_CATEGORY_ORDER:
            tempo_seg = int(pause_category_totals.get(category) or 0)
            qtd = int(pause_category_counts.get(category) or 0)
            if tempo_seg <= 0 and qtd <= 0:
                continue
            items.append(
                {
                    "pause_type": self.PAUSE_CATEGORY_DISPLAY.get(category, str(category)),
                    "qtd": qtd,
                    "tempo_seg": tempo_seg,
                    "tempo_hhmm": format_seconds_hhmm(tempo_seg),
                }
            )
        return items

    def _build_pause_type_breakdowns(self, pause_events_qs, limit: int = 6):
        by_type = defaultdict(lambda: {"tempo_seg": 0, "count": 0})
        for event in pause_events_qs.values("nm_pausa", "duracao_seg", "dt_inicio", "dt_fim"):
            raw_label = str(event.get("nm_pausa") or "").strip()
            label = raw_label if raw_label else "Sem classificacao"
            by_type[label]["count"] += 1
            by_type[label]["tempo_seg"] += self._resolve_event_duration_seconds(event)

        rows = [
            {"label": label, "tempo_seg": int(values["tempo_seg"]), "count": int(values["count"])}
            for label, values in by_type.items()
        ]
        by_time = sorted(rows, key=lambda row: (-row["tempo_seg"], -row["count"], row["label"]))[:limit]
        by_count = sorted(rows, key=lambda row: (-row["count"], -row["tempo_seg"], row["label"]))[:limit]
        for row in by_time:
            row["tempo_hhmm"] = format_seconds_hhmm(int(row["tempo_seg"]))
        for row in by_count:
            row["tempo_hhmm"] = format_seconds_hhmm(int(row["tempo_seg"]))
        return {"by_time": by_time, "by_count": by_count}

    def _build_pause_hourly_distribution(self, pause_events_qs):
        tz = timezone.get_current_timezone()
        hourly = {hour: {"count": 0, "tempo_seg": 0} for hour in range(24)}
        for event in pause_events_qs.values("dt_inicio", "duracao_seg", "dt_fim"):
            started_at = event.get("dt_inicio")
            if started_at is None:
                continue
            local_dt = timezone.localtime(started_at, timezone=tz)
            hour = int(local_dt.hour)
            hourly[hour]["count"] += 1
            hourly[hour]["tempo_seg"] += self._resolve_event_duration_seconds(event)
        return [
            {
                "hour_label": f"{hour:02d}h",
                "count": int(data["count"]),
                "tempo_seg": int(data["tempo_seg"]),
            }
            for hour, data in hourly.items()
        ]

    @staticmethod
    def _build_executive_pause_radar(
        total_pause_events: int,
        total_pause_seconds: int,
        tempo_improdutivo_seg: int,
        tempo_neutro_seg: int,
        tempo_nao_classificado_seg: int,
        total_logged_time: int,
        alert_totals: dict[str, int],
        taxa_ocupacao_pct: float,
    ) -> list[dict]:
        logged = max(int(total_logged_time or 0), 1)
        pause_ratio_pct = (int(total_pause_seconds or 0) / logged) * 100
        improdutivo_ratio_pct = (int(tempo_improdutivo_seg or 0) / logged) * 100
        neutro_ratio_pct = (int(tempo_neutro_seg or 0) / logged) * 100
        nao_classificado_ratio_pct = (int(tempo_nao_classificado_seg or 0) / logged) * 100
        alert_pressure = (
            (int(alert_totals.get("crit", 0)) * 30)
            + (int(alert_totals.get("warn", 0)) * 14)
            + (int(alert_totals.get("info", 0)) * 5)
        )
        idle_pressure = max(0.0, 100.0 - float(taxa_ocupacao_pct or 0.0))
        return [
            {"label": "Pausas totais", "value": max(0, min(int(round(pause_ratio_pct * 1.8)), 100))},
            {"label": "Pausas improdutivas", "value": max(0, min(int(round(improdutivo_ratio_pct * 3.2)), 100))},
            {"label": "Pausas neutras", "value": max(0, min(int(round(neutro_ratio_pct * 2.3)), 100))},
            {"label": "Nao classificadas", "value": max(0, min(int(round(nao_classificado_ratio_pct * 2.6)), 100))},
            {"label": "Alertas", "value": max(0, min(int(round(alert_pressure)), 100))},
            {"label": "Ociosidade", "value": max(0, min(int(round(idle_pressure)), 100))},
            {"label": "Pausas (qtd)", "value": max(0, min(int(round((int(total_pause_events or 0) / 120) * 100)), 100))},
        ]

    @staticmethod
    def _build_hourly_series(events_day_qs):
        tz = timezone.get_current_timezone()
        rows = list(
            events_day_qs.annotate(hour=ExtractHour("dt_inicio", tzinfo=tz))
            .values("hour")
            .annotate(total=Count("id"))
            .order_by("hour")
        )
        counts_by_hour = {
            int(row["hour"]): int(row["total"])
            for row in rows
            if row.get("hour") is not None
        }
        labels = []
        values = []
        for hour in range(24):
            labels.append(f"{hour:02d}h")
            values.append(counts_by_hour.get(hour, 0))
        non_zero_hours = [idx for idx, value in enumerate(values) if value > 0]
        return {"labels": labels, "counts": values, "non_zero_hours": non_zero_hours}

    @staticmethod
    def _empty_hourly_series():
        labels = [f"{hour:02d}h" for hour in range(24)]
        return {"labels": labels, "counts": [0] * 24, "non_zero_hours": []}

    @staticmethod
    def _percentile(values: list[int], percentile: int) -> int:
        if not values:
            return 0
        ordered = sorted(values)
        if len(ordered) == 1:
            return int(ordered[0])
        rank = (max(0, min(percentile, 100)) / 100) * (len(ordered) - 1)
        lower_index = int(rank)
        upper_index = min(lower_index + 1, len(ordered) - 1)
        weight = rank - lower_index
        interpolated = (ordered[lower_index] * (1 - weight)) + (ordered[upper_index] * weight)
        return int(round(interpolated))

    @staticmethod
    def _attach_bar_pct(items: list[dict], metric_key: str):
        max_value = max((int(item.get(metric_key) or 0) for item in items), default=0)
        for item in items:
            value = int(item.get(metric_key) or 0)
            item["bar_pct"] = int((value / max_value) * 100) if max_value > 0 else 0
        return items

    @staticmethod
    def _build_risk_agents(operator_metrics, risk_config):
        risk_items = []
        for item in operator_metrics:
            risk_data = calculate_agent_risk(item, config=risk_config)
            harmful_seg = int(item.get("tempo_improdutivo_seg") or 0)
            occupancy = item.get("taxa_ocupacao_pct")
            if is_no_activity_metric(item):
                occupancy = 0.0
            if occupancy is None:
                occupancy = 0.0

            risk_items.append(
                {
                    "cd_operador": item["cd_operador"],
                    "agent_name": item["agent_name"],
                    "tempo_improdutivo_hhmm": format_seconds_hhmm(harmful_seg),
                    "taxa_ocupacao_pct": occupancy,
                    "risk_score": int(risk_data["risk_score"]),
                    "primary_reason": risk_data["primary_reason"],
                    "reasons": ", ".join(risk_data["reasons"]),
                    "unclassified_pct": float(risk_data.get("unclassified_pct") or 0),
                    # Explicit aliases for template/API compatibility.
                    "operator_id": item["cd_operador"],
                    "operator_name": item["agent_name"],
                    "tempo_improdutivo": format_seconds_hhmm(harmful_seg),
                    "ocupacao_percent": occupancy,
                    "score": int(risk_data["risk_score"]),
                }
            )

        return sorted(risk_items, key=lambda row: (-row["risk_score"], row["cd_operador"]))

    @staticmethod
    def _build_no_activity_agents(operator_metrics):
        items = []
        for item in operator_metrics:
            if is_no_activity_metric(item):
                items.append(
                    {
                        "cd_operador": int(item["cd_operador"]),
                        "nm_agente": item["agent_name"],
                    }
                )
        return sorted(items, key=lambda row: row["cd_operador"])

    def _build_operational_alerts(
        self,
        operator_metrics,
        no_activity_agents,
        events_day_qs,
        events_by_hour,
        total_events_day: int,
        pause_category_totals,
        pause_category_counts,
    ):
        alerts = []
        risk_cfg = self.RISK_CONFIG
        harmful_warn_sec = int(risk_cfg.high_harmful_minutes_threshold * 60)
        harmful_crit_sec = int(risk_cfg.critical_harmful_minutes_threshold * 60)
        harmful_count_threshold = int(risk_cfg.high_harmful_events_threshold)
        for item in operator_metrics:
            if is_no_activity_metric(item):
                continue
            harmful_seg = int(item.get("tempo_improdutivo_seg") or 0)
            harmful_count = int(item.get("qtd_improdutivas") or 0)
            if harmful_seg > harmful_warn_sec:
                alerts.append(
                    {
                        "severity": "crit" if harmful_seg >= harmful_crit_sec else "warn",
                        "title": f"Operador {item['cd_operador']} com tempo improdutivo acima do limite",
                        "detail": (
                            f"{item['agent_name']} acumulou {format_seconds_hhmm(harmful_seg)} "
                            f"(limite {int(risk_cfg.high_harmful_minutes_threshold)} min)."
                        ),
                    }
                )
            if harmful_count >= harmful_count_threshold:
                alerts.append(
                    {
                        "severity": "warn",
                        "title": f"Excesso de pausas improdutivas: operador {item['cd_operador']}",
                        "detail": (
                            f"{item['agent_name']} registrou {harmful_count} pausa(s) improdutiva(s)."
                        ),
                    }
                )
            occupancy = item.get("taxa_ocupacao_pct")
            if occupancy is not None and occupancy < risk_cfg.low_occupancy_threshold_pct:
                alerts.append(
                    {
                        "severity": (
                            "crit"
                            if occupancy < risk_cfg.critical_occupancy_threshold_pct
                            else "warn"
                        ),
                        "title": f"Baixa ocupacao do operador {item['cd_operador']}",
                        "detail": f"{item['agent_name']} com ocupacao de {occupancy:.2f}%.",
                    }
                )

        for agent in no_activity_agents[:5]:
            alerts.append(
                {
                    "severity": "crit",
                    "title": f"Agente ativo sem atividade: {agent['cd_operador']}",
                    "detail": (
                        f"{agent.get('nm_agente') or 'Sem nome'} logado no dia sem eventos "
                        "relevantes (pausa/atendimento)."
                    ),
                }
            )

        unclassified_seconds = int(pause_category_totals.get(UNCLASSIFIED_CATEGORY) or 0)
        unclassified_count = int(pause_category_counts.get(UNCLASSIFIED_CATEGORY) or 0)
        total_pause_seconds = sum(int(val or 0) for val in pause_category_totals.values())
        unclassified_pct = 0.0
        if total_pause_seconds > 0:
            unclassified_pct = (unclassified_seconds / total_pause_seconds) * 100
        if unclassified_seconds > 0 or unclassified_count > 0:
            alerts.append(
                {
                    "severity": (
                        "warn"
                        if unclassified_pct >= risk_cfg.high_unclassified_pct_threshold
                        else "info"
                    ),
                    "title": "Pausas ainda nao classificadas",
                    "detail": (
                        f"{unclassified_count} pausa(s) sem classificacao "
                        f"({format_seconds_hhmm(unclassified_seconds)})."
                    ),
                }
            )
        if unclassified_pct >= risk_cfg.high_unclassified_pct_threshold:
            alerts.append(
                {
                    "severity": "warn",
                    "title": "Alto percentual de tempo nao classificado",
                    "detail": (
                        f"{unclassified_pct:.2f}% do tempo total de pausas esta sem classificacao."
                    ),
                }
            )

        inconsistent_count = events_day_qs.filter(
            Q(dt_fim__lt=F("dt_inicio"))
            | Q(duracao_seg__lt=0)
            | (
                (Q(tp_evento__iexact="PAUSA") | (Q(nm_pausa__isnull=False) & ~Q(nm_pausa__exact="")))
                & (Q(nm_pausa__isnull=True) | Q(nm_pausa__exact=""))
            )
        ).count()
        if inconsistent_count > 0:
            alerts.append(
                {
                    "severity": "crit",
                    "title": "Eventos inconsistentes detectados",
                    "detail": f"{inconsistent_count} evento(s) com duracao/data invalida ou pausa sem nome.",
                }
            )

        gaps = self._find_hour_gaps(
            hourly_counts=events_by_hour.get("counts") or [],
            non_zero_hours=events_by_hour.get("non_zero_hours") or [],
            min_gap=self.EVENT_GAP_ALERT_HOURS,
        )
        if total_events_day <= 0:
            alerts.append(
                {
                    "severity": "crit",
                    "title": "Sem eventos no periodo",
                    "detail": "Nao ha eventos no periodo selecionado. Verifique import/sync.",
                }
            )
        elif gaps:
            first_gap = gaps[0]
            alerts.append(
                {
                    "severity": "warn",
                    "title": "Buraco de importacao detectado",
                    "detail": (
                        f"Intervalo sem eventos de {first_gap['start_label']} ate "
                        f"{first_gap['end_label']} ({first_gap['hours']}h)."
                    ),
                }
            )

        if not alerts:
            alerts.append(
                {
                    "severity": "info",
                    "title": "Sem alertas relevantes",
                    "detail": "Nenhuma anomalia foi detectada para o periodo selecionado.",
                }
            )

        severity_rank = {"crit": 3, "warn": 2, "info": 1}
        for alert in alerts:
            severity = alert.get("severity") or "info"
            alert["severity_label"] = severity.upper()
            alert["severity_class"] = {
                "crit": "bg-red-500/20 text-red-300",
                "warn": "bg-amber-500/20 text-amber-300",
                "info": "bg-sky-500/20 text-sky-300",
            }.get(severity, "bg-slate-500/20 text-slate-300")
            alert["_rank"] = severity_rank.get(severity, 0)

        alerts_sorted = sorted(
            alerts,
            key=lambda item: (
                -item.get("_rank", 0),
                str(item.get("title") or ""),
                str(item.get("detail") or ""),
            ),
        )
        for alert in alerts_sorted:
            alert.pop("_rank", None)
        return alerts_sorted[:10]

    @staticmethod
    def _find_hour_gaps(hourly_counts: list[int], non_zero_hours: list[int], min_gap: int):
        if not hourly_counts or not non_zero_hours:
            return []
        first_hour = min(non_zero_hours)
        last_hour = max(non_zero_hours)
        gaps = []
        gap_start = None
        for hour in range(first_hour, last_hour + 1):
            count = hourly_counts[hour]
            if count == 0 and gap_start is None:
                gap_start = hour
            elif count > 0 and gap_start is not None:
                gap_hours = hour - gap_start
                if gap_hours >= min_gap:
                    gaps.append(
                        {
                            "start_hour": gap_start,
                            "end_hour": hour - 1,
                            "start_label": f"{gap_start:02d}h",
                            "end_label": f"{hour - 1:02d}h",
                            "hours": gap_hours,
                        }
                    )
                gap_start = None
        if gap_start is not None:
            gap_hours = (last_hour + 1) - gap_start
            if gap_hours >= min_gap:
                gaps.append(
                    {
                        "start_hour": gap_start,
                        "end_hour": last_hour,
                        "start_label": f"{gap_start:02d}h",
                        "end_label": f"{last_hour:02d}h",
                        "hours": gap_hours,
                    }
                )
        return gaps

    @staticmethod
    def _extract_processed_count(summary: str | None):
        if not summary:
            return None
        summary_text = str(summary)
        key_values = {}
        for chunk in summary_text.split(";"):
            if "=" not in chunk:
                continue
            key, value = chunk.split("=", 1)
            key = key.strip().lower()
            value = value.strip()
            if not value:
                continue
            try:
                key_values[key] = int(value)
            except ValueError:
                continue

        if "events_fetched" in key_values:
            return key_values["events_fetched"]
        if "records_processed" in key_values:
            return key_values["records_processed"]
        if "pairs_total" in key_values:
            return key_values["pairs_total"]
        if isinstance(summary, dict):
            for key in ["processed", "total", "count", "events", "rows"]:
                value = summary.get(key)
                if isinstance(value, int):
                    return value
                if isinstance(value, str) and value.isdigit():
                    return int(value)
        return None


# Backward compatibility:
# DashboardView.get_context_data relies on helper methods that currently live in
# DashboardPipelineView. Copy them to DashboardView so /dashboard and derived
# views keep working.
for _helper_name, _helper_attr in DashboardPipelineView.__dict__.items():
    if _helper_name.startswith("_") and not _helper_name.startswith("__"):
        if not hasattr(DashboardView, _helper_name):
            setattr(DashboardView, _helper_name, _helper_attr)


class DashboardRebuildStatsView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return bool(self.request.user.is_staff)

    def post(self, request, *args, **kwargs):
        selected_date = parse_date(request.POST.get("data_ref") or "")
        if selected_date is None:
            selected_date = timezone.localdate()

        source = (request.POST.get("source") or "").strip() or None
        started_at = timezone.now()
        job = JobRun.objects.create(
            job_name=JobNameChoices.RELATORIOS,
            started_at=started_at,
            status=JobRunStatusChoices.RUNNING,
            summary=f"rebuild_agent_day_stats date={selected_date}",
        )

        try:
            result = rebuild_agent_day_stats(
                date_from=selected_date,
                date_to=selected_date,
                source=source,
            )
            job.status = JobRunStatusChoices.SUCCESS
            job.finished_at = timezone.now()
            job.summary = (
                f"pairs_total={result['pairs_total']};"
                f"created={result['created']};"
                f"updated={result['updated']}"
            )
            job.save(update_fields=["status", "finished_at", "summary"])
            messages.success(
                request,
                (
                    f"Stats gerados para {selected_date}: "
                    f"pairs_total={result['pairs_total']}, created={result['created']}, "
                    f"updated={result['updated']}."
                ),
            )
        except Exception as exc:
            job.status = JobRunStatusChoices.ERROR
            job.finished_at = timezone.now()
            job.error_detail = str(exc)
            job.summary = "Erro ao gerar stats no dashboard"
            job.save(update_fields=["status", "finished_at", "summary", "error_detail"])
            messages.error(request, f"Falha ao gerar stats: {exc}")

        return redirect(f"{reverse('dashboard')}?{urlencode({'data_ref': selected_date.isoformat()})}")


class PauseClassificationConfigView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = "monitoring/pause_classification.html"
    FRONTEND_CATEGORY_LABELS = {
        PauseCategoryChoices.LEGAL: "Tempo Produtivo",
        PauseCategoryChoices.NEUTRAL: "Tempo Neutro",
        PauseCategoryChoices.HARMFUL: "Tempo Improdutivo",
        UNCLASSIFIED_CATEGORY: "Tempo Nao Classificado",
    }

    def test_func(self):
        return bool(self.request.user.is_staff)

    @classmethod
    def _frontend_category_label(cls, category_key: str) -> str:
        return cls.FRONTEND_CATEGORY_LABELS.get(category_key, category_key)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(django_admin.site.each_context(self.request))
        context["title"] = "Classificacao de pausas"
        context["subtitle"] = "Monitoring"
        categories = [choice[0] for choice in PauseCategoryChoices.choices]

        active_items_qs = (
            PauseClassification.objects
            .filter(is_active=True, source="")
            .order_by("pause_name_normalized")
        )
        columns = {
            key: {
                "key": key,
                "label": self._frontend_category_label(key),
                "items": [],
            }
            for key in categories
        }
        for item in active_items_qs:
            if item.category not in columns:
                continue
            columns[item.category]["items"].append(item)

        distinct_pause_names = list_distinct_event_pause_names()
        split_by_status = list_event_pause_names_by_classification()
        available_pause_names = split_by_status.get("unclassified", [])

        dataset_category_counts = {
            PauseCategoryChoices.LEGAL: 0,
            PauseCategoryChoices.NEUTRAL: 0,
            PauseCategoryChoices.HARMFUL: 0,
            UNCLASSIFIED_CATEGORY: 0,
        }
        for pause_name in distinct_pause_names:
            resolved = resolve_pause_category(pause_name)
            dataset_category_counts[resolved] = dataset_category_counts.get(resolved, 0) + 1

        dataset_category_summary = [
            {
                "label": self._frontend_category_label(category),
                "count": dataset_category_counts.get(category, 0),
            }
            for category in [
                PauseCategoryChoices.LEGAL,
                PauseCategoryChoices.NEUTRAL,
                PauseCategoryChoices.HARMFUL,
                UNCLASSIFIED_CATEGORY,
            ]
        ]

        context.update(
            {
                "category_columns": [columns[key] for key in categories],
                "category_choices": [
                    {"key": key, "label": self._frontend_category_label(key)}
                    for key in categories
                ],
                "available_pause_names": available_pause_names,
                "total_distinct_pause_names": len(distinct_pause_names),
                "dataset_category_summary": dataset_category_summary,
            }
        )
        return context

    def post(self, request, *args, **kwargs):
        action = (request.POST.get("action") or "").strip().lower()
        if action == "add":
            self._handle_add(request)
        elif action == "remove":
            self._handle_remove(request)
        elif action == "move":
            self._handle_move(request)
        else:
            messages.error(request, "Acao invalida para classificacao de pausas.")
        return redirect("pause-classification-config")

    @staticmethod
    def _valid_categories() -> set[str]:
        return {choice[0] for choice in PauseCategoryChoices.choices}

    def _handle_add(self, request):
        target_category = (request.POST.get("category") or "").strip().upper()
        if target_category not in self._valid_categories():
            messages.error(request, "Categoria invalida.")
            return

        normalized_pause_name = normalize_pause_name(request.POST.get("pause_name"))
        if not normalized_pause_name:
            messages.error(request, "Selecione uma pausa valida para adicionar.")
            return

        available_pause_names = set(list_event_pause_names_by_classification().get("unclassified", []))
        if normalized_pause_name not in available_pause_names:
            current_category = resolve_pause_category(normalized_pause_name)
            if current_category != UNCLASSIFIED_CATEGORY:
                messages.error(
                    request,
                    (
                        f"A pausa '{normalized_pause_name}' ja esta classificada como "
                        f"{self._frontend_category_label(current_category)}."
                    ),
                )
            else:
                messages.error(
                    request,
                    f"A pausa '{normalized_pause_name}' nao esta disponivel para classificacao.",
                )
            return

        try:
            PauseClassification.objects.create(
                source="",
                pause_name=normalized_pause_name,
                category=target_category,
                is_active=True,
            )
        except (ValidationError, ValueError, IntegrityError) as exc:
            messages.error(request, f"Nao foi possivel adicionar a pausa: {exc}")
            return

        messages.success(
            request,
            (
                f"Pausa '{normalized_pause_name}' classificada como "
                f"{self._frontend_category_label(target_category)}."
            ),
        )

    def _handle_remove(self, request):
        classification_id = (request.POST.get("classification_id") or "").strip()
        if not classification_id.isdigit():
            messages.error(request, "Classificacao invalida para remocao.")
            return

        classification = PauseClassification.objects.filter(
            id=int(classification_id),
            is_active=True,
            source="",
        ).first()
        if classification is None:
            messages.error(request, "Classificacao nao encontrada ou ja removida.")
            return

        classification.is_active = False
        classification.save(update_fields=["is_active", "updated_at"])
        messages.success(request, f"Pausa '{classification.pause_name}' removida da classificacao.")

    def _handle_move(self, request):
        classification_id = (request.POST.get("classification_id") or "").strip()
        target_category = (request.POST.get("target_category") or "").strip().upper()
        if not classification_id.isdigit():
            messages.error(request, "Classificacao invalida para mover.")
            return
        if target_category not in self._valid_categories():
            messages.error(request, "Categoria de destino invalida.")
            return

        classification = PauseClassification.objects.filter(
            id=int(classification_id),
            is_active=True,
            source="",
        ).first()
        if classification is None:
            messages.error(request, "Classificacao nao encontrada ou inativa.")
            return

        if classification.category == target_category:
            messages.info(
                request,
                (
                    f"A pausa '{classification.pause_name}' ja esta em "
                    f"{self._frontend_category_label(target_category)}."
                ),
            )
            return

        try:
            classification.category = target_category
            classification.save(update_fields=["category", "updated_at"])
        except (ValidationError, ValueError, IntegrityError) as exc:
            messages.error(request, f"Nao foi possivel mover a pausa: {exc}")
            return

        messages.success(
            request,
            (
                f"Pausa '{classification.pause_name}' movida para "
                f"{self._frontend_category_label(target_category)}."
            ),
        )


class DashboardDayDetailView(LoginRequiredMixin, TemplateView):
    template_name = "monitoring/dashboard_day_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        selected_date = self._selected_date()
        search = (self.request.GET.get("q") or "").strip()
        pause_type = (self.request.GET.get("pause_type") or "").strip()
        hour_filter = (self.request.GET.get("hour") or "").strip()
        day_start, day_end = DashboardView._day_window(selected_date)

        events_qs = AgentEvent.objects.filter(
            dt_inicio__gte=day_start,
            dt_inicio__lt=day_end,
        ).select_related("agent").order_by("-dt_inicio", "-id")
        pause_qs = events_qs.filter(
            Q(tp_evento__iexact="PAUSA")
            | (Q(nm_pausa__isnull=False) & ~Q(nm_pausa__exact=""))
        )
        workday_qs = AgentWorkday.objects.filter(work_date=selected_date).order_by("-dt_inicio", "-id")
        stats_qs = AgentDayStats.objects.filter(data_ref=selected_date).select_related("agent").order_by(
            "-tempo_pausas_seg", "cd_operador"
        )

        if search:
            search_filter = (
                Q(agent__nm_agente__icontains=search)
                | Q(agent__nm_agente_code__icontains=search)
                | Q(nm_pausa__icontains=search)
            )
            workday_filter = Q(nm_operador__icontains=search)
            stats_filter = Q(agent__nm_agente__icontains=search)
            if search.isdigit():
                search_filter |= Q(cd_operador=int(search))
                workday_filter |= Q(cd_operador=int(search))
                stats_filter |= Q(cd_operador=int(search))
            events_qs = events_qs.filter(search_filter)
            pause_qs = pause_qs.filter(search_filter)
            workday_qs = workday_qs.filter(workday_filter)
            stats_qs = stats_qs.filter(stats_filter)

        if pause_type:
            pause_qs = pause_qs.filter(nm_pausa=pause_type)

        selected_hour = None
        if hour_filter:
            try:
                selected_hour = int(hour_filter)
            except ValueError:
                selected_hour = None
            if selected_hour is not None and 0 <= selected_hour <= 23:
                hour_start = day_start + timedelta(hours=selected_hour)
                hour_end = hour_start + timedelta(hours=1)
                events_qs = events_qs.filter(dt_inicio__gte=hour_start, dt_inicio__lt=hour_end)
                pause_qs = pause_qs.filter(dt_inicio__gte=hour_start, dt_inicio__lt=hour_end)
                workday_qs = workday_qs.filter(dt_inicio__lt=hour_end, dt_fim__gte=hour_start)
                stats_qs = stats_qs.filter(
                    Q(ultimo_logon__gte=hour_start, ultimo_logon__lt=hour_end)
                    | Q(ultima_pausa_inicio__gte=hour_start, ultima_pausa_inicio__lt=hour_end)
                )
            else:
                selected_hour = None

        distinct_pause_types = list(
            AgentEvent.objects.filter(
                dt_inicio__gte=day_start,
                dt_inicio__lt=day_end,
                nm_pausa__isnull=False,
            )
            .exclude(nm_pausa__exact="")
            .order_by("nm_pausa")
            .values_list("nm_pausa", flat=True)
            .distinct()
        )

        events_page = Paginator(events_qs, 50).get_page(self.request.GET.get("events_page"))
        pauses_page = Paginator(pause_qs, 50).get_page(self.request.GET.get("pauses_page"))
        workday_page = Paginator(workday_qs, 50).get_page(self.request.GET.get("workday_page"))
        stats_page = Paginator(stats_qs, 50).get_page(self.request.GET.get("stats_page"))

        for stat in stats_page.object_list:
            stat.tempo_pausas_hhmm = format_seconds_hhmm(stat.tempo_pausas_seg)
        for event in events_page.object_list:
            event.duracao_hhmm = format_seconds_hhmm(event.duracao_seg) if event.duracao_seg is not None else "-"
        for item in pauses_page.object_list:
            item.duracao_hhmm = format_seconds_hhmm(item.duracao_seg) if item.duracao_seg is not None else "-"
        for item in workday_page.object_list:
            item.duracao_hhmm = format_seconds_hhmm(item.duracao_seg)

        context.update(
            {
                "selected_date": selected_date,
                "search": search,
                "pause_type": pause_type,
                "selected_hour": selected_hour,
                "distinct_pause_types": distinct_pause_types,
                "events_page": events_page,
                "pauses_page": pauses_page,
                "workday_page": workday_page,
                "stats_page": stats_page,
                "events_query_suffix": self._query_suffix(exclude_keys={"events_page"}),
                "pauses_query_suffix": self._query_suffix(exclude_keys={"pauses_page"}),
                "workday_query_suffix": self._query_suffix(exclude_keys={"workday_page"}),
                "stats_query_suffix": self._query_suffix(exclude_keys={"stats_page"}),
            }
        )
        return context

    def _selected_date(self):
        date_str = self.request.GET.get("data_ref")
        parsed = parse_date(date_str) if date_str else None
        return parsed or timezone.localdate()

    def _query_suffix(self, exclude_keys: set[str]):
        params = self.request.GET.copy()
        for key in exclude_keys:
            params.pop(key, None)
        encoded = params.urlencode()
        return f"&{encoded}" if encoded else ""


class AgentListView(LoginRequiredMixin, ListView):
    model = Agent
    template_name = "monitoring/agents_list.html"
    context_object_name = "agents"
    paginate_by = 25

    def get_queryset(self):
        queryset = Agent.objects.all().order_by("cd_operador")
        search = (self.request.GET.get("q") or "").strip()
        status = (self.request.GET.get("status") or "").strip().lower()
        if status == "ativos":
            queryset = queryset.filter(ativo=True)
        elif status == "inativos":
            queryset = queryset.filter(ativo=False)

        if not search:
            return queryset

        search_filter = (
            Q(nm_agente__icontains=search)
            | Q(nm_agente_code__icontains=search)
            | Q(nr_ramal__icontains=search)
        )
        if search.isdigit():
            search_filter |= Q(cd_operador=int(search))
        return queryset.filter(search_filter)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search"] = (self.request.GET.get("q") or "").strip()
        context["selected_status"] = (self.request.GET.get("status") or "").strip().lower()

        today = timezone.localdate()
        selected_date_from = parse_date(self.request.GET.get("date_from") or "") or (today - timedelta(days=6))
        selected_date_to = parse_date(self.request.GET.get("date_to") or "") or today
        if selected_date_to < selected_date_from:
            selected_date_from, selected_date_to = selected_date_to, selected_date_from

        productive_min_raw = (self.request.GET.get("produtivo_min") or "").strip()
        try:
            productive_min_minutes = max(0, int(productive_min_raw))
        except ValueError:
            productive_min_minutes = 0

        page_obj = context.get("page_obj")
        metrics_by_operator = self._build_agent_metrics_map(
            agents=page_obj.object_list if page_obj else [],
            date_from=selected_date_from,
            date_to=selected_date_to,
        )

        filtered_agents = []
        if page_obj:
            for agent in page_obj.object_list:
                metrics = metrics_by_operator.get(agent.cd_operador) or {
                    "tempo_logado_hhmm": None,
                    "tempo_logado_display": "Sem dados",
                    "tempo_produtivo_hhmm": None,
                    "taxa_ocupacao_pct": None,
                    "taxa_ocupacao_display": "Sem dados",
                    "risk_label": "Indisponivel",
                    "risk_class": "",
                    "tempo_produtivo_seg": 0,
                    "has_metrics_data": False,
                }
                if metrics["tempo_produtivo_seg"] < (productive_min_minutes * 60):
                    continue
                agent.dashboard_metrics = metrics
                filtered_agents.append(agent)
            page_obj.object_list = filtered_agents
            context["agents"] = filtered_agents

        context["selected_date_from"] = selected_date_from
        context["selected_date_to"] = selected_date_to
        context["selected_produtivo_min"] = productive_min_minutes if productive_min_minutes > 0 else ""
        context["page_query_suffix"] = self._query_suffix(exclude_keys={"page"})
        return context

    @staticmethod
    def _build_agent_metrics_map(agents, date_from, date_to):
        operator_ids = [agent.cd_operador for agent in agents if getattr(agent, "cd_operador", None)]
        if not operator_ids:
            return {}

        stats_rows = AgentDayStats.objects.filter(
            cd_operador__in=operator_ids,
            data_ref__gte=date_from,
            data_ref__lte=date_to,
        ).values(
            "cd_operador",
            "tempo_pausas_seg",
            "ultimo_logon",
            "ultimo_logoff",
        )

        pause_by_operator = defaultdict(int)
        logged_by_operator = defaultdict(int)
        operators_with_metrics = set()
        for row in stats_rows:
            cd_operador = int(row.get("cd_operador") or 0)
            if cd_operador <= 0:
                continue
            operators_with_metrics.add(cd_operador)
            pause_by_operator[cd_operador] += int(row.get("tempo_pausas_seg") or 0)
            last_logon = row.get("ultimo_logon")
            last_logoff = row.get("ultimo_logoff")
            if last_logon and last_logoff and last_logoff > last_logon:
                logged_by_operator[cd_operador] += int((last_logoff - last_logon).total_seconds())

        metrics = {}
        for cd_operador in operator_ids:
            has_metrics_data = cd_operador in operators_with_metrics
            if not has_metrics_data:
                metrics[cd_operador] = {
                    "tempo_logado_hhmm": None,
                    "tempo_logado_display": "Sem dados",
                    "tempo_produtivo_hhmm": None,
                    "taxa_ocupacao_pct": None,
                    "taxa_ocupacao_display": "Sem dados",
                    "risk_label": "Indisponivel",
                    "risk_class": "",
                    "tempo_produtivo_seg": 0,
                    "has_metrics_data": False,
                }
                continue

            pause_seconds = int(pause_by_operator.get(cd_operador) or 0)
            logged_seconds = int(logged_by_operator.get(cd_operador) or 0)
            productive_seconds = max(0, logged_seconds - pause_seconds)
            occupancy_pct = round((productive_seconds / logged_seconds) * 100, 2) if logged_seconds > 0 else 0.0

            if occupancy_pct < 45:
                risk_label = "Alto"
                risk_class = "bg-red-500/20 text-red-300"
            elif occupancy_pct < 70:
                risk_label = "Medio"
                risk_class = "bg-amber-500/20 text-amber-300"
            else:
                risk_label = "Baixo"
                risk_class = "bg-emerald-500/20 text-emerald-300"

            metrics[cd_operador] = {
                "tempo_logado_hhmm": format_seconds_hhmm(logged_seconds),
                "tempo_logado_display": format_seconds_hhmm(logged_seconds),
                "tempo_produtivo_hhmm": format_seconds_hhmm(productive_seconds),
                "taxa_ocupacao_pct": occupancy_pct,
                "taxa_ocupacao_display": f"{occupancy_pct:.0f}%",
                "risk_label": risk_label,
                "risk_class": risk_class,
                "tempo_produtivo_seg": productive_seconds,
                "has_metrics_data": True,
            }
        return metrics

    def _query_suffix(self, exclude_keys: set[str]):
        params = self.request.GET.copy()
        for key in exclude_keys:
            params.pop(key, None)
        encoded = params.urlencode()
        return f"&{encoded}" if encoded else ""


class AgentDetailView(LoginRequiredMixin, DetailView):
    model = Agent
    template_name = "monitoring/agent_detail.html"
    context_object_name = "agent"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.localdate()
        stats_from = today - timedelta(days=6)
        events_from = timezone.now() - timedelta(days=2)

        stats_qs = (
            self.object.day_stats.filter(data_ref__gte=stats_from)
            .order_by("-data_ref")
        )
        stats_page = Paginator(stats_qs, 7).get_page(self.request.GET.get("stats_page"))
        for item in stats_page.object_list:
            item.tempo_pausas_hhmm = format_seconds_hhmm(item.tempo_pausas_seg)

        recent_events_qs = (
            self.object.events.filter(dt_inicio__gte=events_from)
            .order_by("-dt_inicio")[:200]
        )
        events_page = Paginator(recent_events_qs, 50).get_page(self.request.GET.get("events_page"))
        for item in events_page.object_list:
            item.duracao_hhmm = format_seconds_hhmm(item.duracao_seg) if item.duracao_seg else "-"

        context.update(
            {
                "stats_page": stats_page,
                "events_page": events_page,
                "stats_query_suffix": self._query_suffix(exclude_keys={"stats_page"}),
                "events_query_suffix": self._query_suffix(exclude_keys={"events_page"}),
            }
        )
        return context

    def _query_suffix(self, exclude_keys: set[str]):
        params = self.request.GET.copy()
        for key in exclude_keys:
            params.pop(key, None)
        encoded = params.urlencode()
        return f"&{encoded}" if encoded else ""


class JobRunListView(LoginRequiredMixin, ListView):
    model = JobRun
    template_name = "monitoring/runs_list.html"
    context_object_name = "runs"
    paginate_by = 25

    def get_queryset(self):
        queryset = JobRun.objects.all().order_by("-started_at")

        today = timezone.localdate()
        default_from = today - timedelta(days=6)
        date_from = parse_date(self.request.GET.get("date_from") or "") or default_from
        date_to = parse_date(self.request.GET.get("date_to") or "") or today
        if date_to < date_from:
            date_from, date_to = date_to, date_from

        queryset = queryset.filter(started_at__date__gte=date_from, started_at__date__lte=date_to)
        self.selected_date_from = date_from
        self.selected_date_to = date_to

        job_name = (self.request.GET.get("job_name") or "").strip()
        valid_job_names = {choice[0] for choice in JobNameChoices.choices}
        if job_name in valid_job_names:
            queryset = queryset.filter(job_name=job_name)
            self.selected_job_name = job_name
        else:
            self.selected_job_name = ""

        status = (self.request.GET.get("status") or "").strip()
        valid_status = {choice[0] for choice in JobRunStatusChoices.choices}
        if status in valid_status:
            queryset = queryset.filter(status=status)
            self.selected_status = status
        else:
            self.selected_status = ""

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        page = context["page_obj"]
        for run in page.object_list:
            run.duration_hhmm = format_run_duration_hhmm(run)

        context.update(
            {
                "selected_job_name": getattr(self, "selected_job_name", ""),
                "selected_status": getattr(self, "selected_status", ""),
                "selected_date_from": getattr(
                    self, "selected_date_from", timezone.localdate() - timedelta(days=6)
                ),
                "selected_date_to": getattr(self, "selected_date_to", timezone.localdate()),
                "job_name_choices": JobNameChoices.choices,
                "status_choices": JobRunStatusChoices.choices,
                "page_query_suffix": self._query_suffix(exclude_keys={"page"}),
            }
        )
        return context

    def _query_suffix(self, exclude_keys: set[str]):
        params = self.request.GET.copy()
        for key in exclude_keys:
            params.pop(key, None)
        encoded = params.urlencode()
        return f"&{encoded}" if encoded else ""


class JobRunDetailView(LoginRequiredMixin, DetailView):
    model = JobRun
    template_name = "monitoring/run_detail.html"
    context_object_name = "run"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["duration_hhmm"] = format_run_duration_hhmm(self.object)
        return context







