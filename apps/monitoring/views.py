from datetime import timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import Count, Q, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.views.generic import DetailView, ListView, TemplateView

from .models import Agent, AgentDayStats, JobNameChoices, JobRun, JobRunStatusChoices
from .utils import format_run_duration_hhmm, format_seconds_hhmm


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard.html"
    page_size = 25

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        selected_date = self._selected_date()
        search = (self.request.GET.get("q") or "").strip()

        top_qs = AgentDayStats.objects.filter(data_ref=selected_date).select_related("agent")
        if search:
            search_filter = (
                Q(agent__nm_agente__icontains=search)
                | Q(agent__nm_agente_code__icontains=search)
                | Q(agent__nr_ramal__icontains=search)
            )
            if search.isdigit():
                search_filter |= Q(cd_operador=int(search))
            top_qs = top_qs.filter(search_filter)

        totals = top_qs.aggregate(
            agents_count=Count("id"),
            total_pausas=Coalesce(Sum("qtd_pausas"), 0),
            total_tempo_pausas=Coalesce(Sum("tempo_pausas_seg"), 0),
        )

        top_qs = top_qs.order_by("-tempo_pausas_seg", "-qtd_pausas", "cd_operador")
        top_page = Paginator(top_qs, self.page_size).get_page(self.request.GET.get("page"))
        for item in top_page.object_list:
            item.tempo_pausas_hhmm = format_seconds_hhmm(item.tempo_pausas_seg)

        last_sync = JobRun.objects.filter(job_name=JobNameChoices.SYNC).order_by("-started_at").first()
        last_sync_duration = format_run_duration_hhmm(last_sync) if last_sync else "-"

        context.update(
            {
                "selected_date": selected_date,
                "search": search,
                "top_page": top_page,
                "agents_with_stats_count": totals["agents_count"] or 0,
                "total_pausas_hoje": totals["total_pausas"] or 0,
                "tempo_total_pausas_hhmm": format_seconds_hhmm(totals["total_tempo_pausas"] or 0),
                "last_sync": last_sync,
                "last_sync_duration": last_sync_duration,
                "page_query_suffix": self._query_suffix(exclude_keys={"page"}),
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
