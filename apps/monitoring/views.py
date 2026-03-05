from datetime import datetime, time, timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import Count, Max, Q, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.views.generic import DetailView, ListView, TemplateView

from .models import (
    Agent,
    AgentDayStats,
    AgentEvent,
    AgentWorkday,
    JobNameChoices,
    JobRun,
    JobRunStatusChoices,
)
from .utils import format_run_duration_hhmm, format_seconds_hhmm


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        selected_date = self._selected_date()
        search = (self.request.GET.get("q") or "").strip()
        day_start, day_end = self._day_window(selected_date)

        stats_qs = AgentDayStats.objects.filter(data_ref=selected_date).select_related("agent")
        events_day_qs = AgentEvent.objects.filter(dt_inicio__gte=day_start, dt_inicio__lt=day_end)
        workday_day_qs = AgentWorkday.objects.filter(work_date=selected_date)
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
            if search.isdigit():
                search_filter |= Q(cd_operador=int(search))
                event_filter |= Q(cd_operador=int(search))
                workday_filter |= Q(cd_operador=int(search))
            stats_qs = stats_qs.filter(search_filter)
            events_day_qs = events_day_qs.filter(event_filter)
            workday_day_qs = workday_day_qs.filter(workday_filter)

        stats_totals = stats_qs.aggregate(
            agents_count=Count("id"),
        )

        active_agents_count = Agent.objects.filter(ativo=True).count()
        operators_with_events = set(
            events_day_qs.values_list("cd_operador", flat=True).distinct()
        )
        operators_with_workday = set(
            workday_day_qs.values_list("cd_operador", flat=True).distinct()
        )
        agents_with_activity_count = len(operators_with_events | operators_with_workday)
        total_events_day = events_day_qs.count()

        pause_events_qs = events_day_qs.filter(tp_evento__iexact="PAUSA")
        pause_totals = pause_events_qs.aggregate(
            total_pausas=Count("id"),
            total_tempo_pausas=Coalesce(Sum("duracao_seg"), 0),
        )
        total_pausas_hoje = pause_totals["total_pausas"] or 0
        total_tempo_pausas = pause_totals["total_tempo_pausas"] or 0

        total_logged_time = (
            workday_day_qs.aggregate(total=Coalesce(Sum("duracao_seg"), 0))["total"] or 0
        )
        logged_time_source = "workday"
        if total_logged_time <= 0:
            total_logged_time = self._estimate_login_seconds_from_events(
                events_day_qs=events_day_qs,
                day_end=day_end,
                selected_date=selected_date,
            )
            logged_time_source = "event_estimate"
        productive_time = max(0, int(total_logged_time) - int(total_tempo_pausas))

        stats_warning = False
        top_pause_time = []
        top_pause_count = []
        if stats_qs.exists():
            top_pause_time = list(
                stats_qs.order_by("-tempo_pausas_seg", "-qtd_pausas", "cd_operador")[:10]
            )
            top_pause_count = list(
                stats_qs.order_by("-qtd_pausas", "-tempo_pausas_seg", "cd_operador")[:10]
            )
            for item in top_pause_time:
                item.agent_name = item.agent.nm_agente or "Sem nome"
                item.tempo_pausas_hhmm = format_seconds_hhmm(item.tempo_pausas_seg)
            for item in top_pause_count:
                item.agent_name = item.agent.nm_agente or "Sem nome"
                item.tempo_pausas_hhmm = format_seconds_hhmm(item.tempo_pausas_seg)
        else:
            if total_events_day > 0 or workday_day_qs.exists():
                stats_warning = True
            top_pause_time, top_pause_count = self._build_fallback_rankings(
                pause_events_qs=pause_events_qs,
                workday_day_qs=workday_day_qs,
            )

        pause_distribution = self._build_pause_distribution(pause_events_qs=pause_events_qs)

        last_job_run = JobRun.objects.order_by("-started_at").first()
        recent_job_runs = list(JobRun.objects.order_by("-started_at")[:5])
        for run in recent_job_runs:
            run.duration_hhmm = format_run_duration_hhmm(run)
        last_job_duration = format_run_duration_hhmm(last_job_run) if last_job_run else "-"
        last_sync = JobRun.objects.filter(job_name=JobNameChoices.SYNC).order_by("-started_at").first()

        context.update(
            {
                "selected_date": selected_date,
                "search": search,
                "active_agents_count": active_agents_count,
                "agents_with_activity_count": agents_with_activity_count,
                "total_events_day": total_events_day,
                "agents_with_stats_count": stats_totals["agents_count"] or 0,
                "total_pausas_hoje": total_pausas_hoje,
                "tempo_total_pausas_hhmm": format_seconds_hhmm(total_tempo_pausas),
                "tempo_logado_total_hhmm": format_seconds_hhmm(total_logged_time),
                "tempo_produtivo_total_hhmm": format_seconds_hhmm(productive_time),
                "tempo_logado_source": logged_time_source,
                "top_pause_time": top_pause_time,
                "top_pause_count": top_pause_count,
                "pause_distribution": pause_distribution,
                "stats_warning": stats_warning,
                "last_job_run": last_job_run,
                "last_job_duration": last_job_duration,
                "recent_job_runs": recent_job_runs,
                "last_sync": last_sync,
            }
        )
        return context

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
    def _estimate_login_seconds_from_events(events_day_qs, day_end, selected_date):
        log_events = events_day_qs.filter(
            Q(tp_evento__iexact="LOGON") | Q(tp_evento__iexact="LOGOFF")
        ).order_by("cd_operador", "dt_inicio", "id")

        now = timezone.now()
        close_time = day_end
        if selected_date == timezone.localdate():
            close_time = min(day_end, now)

        current_logon_by_operator: dict[int, datetime] = {}
        total_seconds = 0
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
                    total_seconds += int((event_dt - start_dt).total_seconds())

        for start_dt in current_logon_by_operator.values():
            if close_time > start_dt:
                total_seconds += int((close_time - start_dt).total_seconds())

        return max(0, total_seconds)

    @staticmethod
    def _build_fallback_rankings(pause_events_qs, workday_day_qs):
        aggregated_rows = list(
            pause_events_qs.values("cd_operador")
            .annotate(
                qtd_pausas=Count("id"),
                tempo_pausas_seg=Coalesce(Sum("duracao_seg"), 0),
                ultima_pausa_inicio=Max("dt_inicio"),
            )
        )
        operator_ids = {int(row["cd_operador"]) for row in aggregated_rows if row.get("cd_operador")}
        agents_by_operator = {
            agent.cd_operador: agent
            for agent in Agent.objects.filter(cd_operador__in=operator_ids)
        }
        names_from_workday = {
            int(row["cd_operador"]): (row["nm_operador"] or "Sem nome")
            for row in workday_day_qs.values("cd_operador", "nm_operador").distinct()
            if row.get("cd_operador")
        }

        items = []
        for row in aggregated_rows:
            cd_operador = int(row["cd_operador"])
            agent = agents_by_operator.get(cd_operador)
            agent_name = (
                (agent.nm_agente if agent else None)
                or names_from_workday.get(cd_operador)
                or f"Operador {cd_operador}"
            )
            total_pause_seconds = int(row.get("tempo_pausas_seg") or 0)
            items.append(
                {
                    "cd_operador": cd_operador,
                    "agent_name": agent_name,
                    "qtd_pausas": int(row.get("qtd_pausas") or 0),
                    "tempo_pausas_seg": total_pause_seconds,
                    "tempo_pausas_hhmm": format_seconds_hhmm(total_pause_seconds),
                    "ultima_pausa_inicio": row.get("ultima_pausa_inicio"),
                }
            )

        top_pause_time = sorted(
            items,
            key=lambda item: (-item["tempo_pausas_seg"], -item["qtd_pausas"], item["cd_operador"]),
        )[:10]
        top_pause_count = sorted(
            items,
            key=lambda item: (-item["qtd_pausas"], -item["tempo_pausas_seg"], item["cd_operador"]),
        )[:10]
        return top_pause_time, top_pause_count

    @staticmethod
    def _build_pause_distribution(pause_events_qs, top_n: int = 6):
        rows = list(
            pause_events_qs.values("nm_pausa")
            .annotate(
                qtd=Count("id"),
                tempo_seg=Coalesce(Sum("duracao_seg"), 0),
            )
            .order_by("-qtd", "nm_pausa")
        )
        items = []
        for row in rows[:top_n]:
            tempo_seg = int(row.get("tempo_seg") or 0)
            items.append(
                {
                    "pause_type": row.get("nm_pausa") or "PAUSA",
                    "qtd": int(row.get("qtd") or 0),
                    "tempo_hhmm": format_seconds_hhmm(tempo_seg),
                }
            )

        remaining = rows[top_n:]
        if remaining:
            others_qtd = sum(int(row.get("qtd") or 0) for row in remaining)
            others_tempo = sum(int(row.get("tempo_seg") or 0) for row in remaining)
            items.append(
                {
                    "pause_type": "Outros",
                    "qtd": others_qtd,
                    "tempo_hhmm": format_seconds_hhmm(others_tempo),
                }
            )
        return items


class AgentListView(LoginRequiredMixin, ListView):
    model = Agent
    template_name = "monitoring/agents_list.html"
    context_object_name = "agents"
    paginate_by = 25

    def get_queryset(self):
        queryset = Agent.objects.all().order_by("cd_operador")
        search = (self.request.GET.get("q") or "").strip()
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
        context["page_query_suffix"] = self._query_suffix(exclude_keys={"page"})
        return context

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
