from django.contrib import admin

from .models import (
    Agent,
    AgentDayStats,
    AgentEvent,
    JobRun,
    NotificationHistory,
    NotificationThrottle,
)


@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = ("cd_operador", "nm_agente", "nm_agente_code", "ativo")
    list_filter = ("ativo",)
    search_fields = ("=cd_operador", "nm_agente", "nm_agente_code", "email", "nr_ramal")


@admin.register(AgentEvent)
class AgentEventAdmin(admin.ModelAdmin):
    list_display = ("tp_evento", "nm_pausa", "dt_inicio", "cd_operador", "source")
    list_filter = ("tp_evento", "nm_pausa", "source", "dt_inicio")
    search_fields = ("=cd_operador", "tp_evento", "nm_pausa", "source_event_hash")


@admin.register(AgentDayStats)
class AgentDayStatsAdmin(admin.ModelAdmin):
    list_display = ("data_ref", "cd_operador", "qtd_pausas", "tempo_pausas_seg")
    list_filter = ("data_ref",)
    search_fields = ("=cd_operador",)


@admin.register(NotificationHistory)
class NotificationHistoryAdmin(admin.ModelAdmin):
    list_display = (
        "created_at",
        "status",
        "notification_type",
        "channel",
        "recipient",
        "cd_operador",
    )
    list_filter = ("status", "notification_type", "channel", "created_at")
    search_fields = ("recipient", "=cd_operador", "error_message")


@admin.register(NotificationThrottle)
class NotificationThrottleAdmin(admin.ModelAdmin):
    list_display = ("notification_type", "day_ref", "sent_count_today", "last_sent_at")
    list_filter = ("notification_type", "day_ref")
    search_fields = ("=agent__cd_operador", "notification_type")


@admin.register(JobRun)
class JobRunAdmin(admin.ModelAdmin):
    list_display = ("job_name", "status", "started_at", "finished_at")
    list_filter = ("job_name", "status", "started_at")
    search_fields = ("job_name", "summary", "error_detail")
