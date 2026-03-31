"""
Selectors para queries reutilizáveis do app monitoring.

Este módulo contém funções para queries ORM complexas, filtros e agregações.
Todas as funções retornam QuerySets ou listas.
"""
from django.db.models import QuerySet, Count, Sum, Q
from .models import (
    Agent,
    AgentEvent,
    AgentDayStats,
    AgentWorkday,
    PauseClassification,
    JobRun,
    NotificationHistory,
)


def get_active_agents() -> QuerySet:
    """Retorna todos os agentes ativos."""
    return Agent.objects.filter(ativo=True)


def get_agent_by_code(cd_operador: int):
    """Busca agente por código."""
    return Agent.objects.filter(cd_operador=cd_operador).first()


def get_events_for_period(start_date, end_date, source=None, agent_ids=None) -> QuerySet:
    """
    Retorna eventos para um período específico.
    
    Args:
        start_date: Data/hora de início
        end_date: Data/hora de fim
        source: Filtro opcional por fonte
        agent_ids: Filtro opcional por IDs de agentes
    
    Returns:
        QuerySet de AgentEvent com select_related('agent')
    """
    qs = AgentEvent.objects.filter(
        dt_inicio__gte=start_date,
        dt_inicio__lt=end_date
    ).select_related('agent')
    
    if source:
        qs = qs.filter(source=source)
    
    if agent_ids:
        qs = qs.filter(agent_id__in=agent_ids)
    
    return qs


def get_pause_events_for_period(start_date, end_date, exclude_pause_names=None) -> QuerySet:
    """
    Retorna apenas eventos de pausa para um período.
    
    Args:
        start_date: Data/hora de início
        end_date: Data/hora de fim
        exclude_pause_names: Nomes de pausas a excluir
    
    Returns:
        QuerySet de AgentEvent filtrado por pausas
    """
    qs = get_events_for_period(start_date, end_date)
    qs = qs.filter(tp_evento='PAUSA')
    
    if exclude_pause_names:
        qs = qs.exclude(nm_pausa__in=exclude_pause_names)
    
    return qs


def get_day_stats_for_date(date, agent_ids=None) -> QuerySet:
    """
    Retorna estatísticas diárias para uma data.
    
    Args:
        date: Data de referência
        agent_ids: Filtro opcional por IDs de agentes
    
    Returns:
        QuerySet de AgentDayStats com select_related('agent')
    """
    qs = AgentDayStats.objects.filter(
        data_ref=date
    ).select_related('agent')
    
    if agent_ids:
        qs = qs.filter(agent_id__in=agent_ids)
    
    return qs


def get_workdays_for_date(date, source=None) -> QuerySet:
    """
    Retorna jornadas de trabalho para uma data.
    
    Args:
        date: Data de trabalho
        source: Filtro opcional por fonte
    
    Returns:
        QuerySet de AgentWorkday
    """
    qs = AgentWorkday.objects.filter(work_date=date)
    
    if source:
        qs = qs.filter(source=source)
    
    return qs


def get_active_pause_classifications(source=None) -> QuerySet:
    """
    Retorna classificações de pausa ativas.
    
    Args:
        source: Filtro opcional por fonte
    
    Returns:
        QuerySet de PauseClassification
    """
    qs = PauseClassification.objects.filter(is_active=True)
    
    if source:
        qs = qs.filter(source=source)
    
    return qs


def get_recent_job_runs(limit=10, job_name=None) -> QuerySet:
    """
    Retorna execuções recentes de jobs.
    
    Args:
        limit: Número máximo de resultados
        job_name: Filtro opcional por nome do job
    
    Returns:
        QuerySet de JobRun
    """
    qs = JobRun.objects.all()
    
    if job_name:
        qs = qs.filter(job_name=job_name)
    
    return qs.order_by('-started_at')[:limit]


def get_notification_history_for_agent(agent, notification_type=None, limit=50) -> QuerySet:
    """
    Retorna histórico de notificações de um agente.
    
    Args:
        agent: Instância de Agent
        notification_type: Filtro opcional por tipo
        limit: Número máximo de resultados
    
    Returns:
        QuerySet de NotificationHistory
    """
    qs = NotificationHistory.objects.filter(agent=agent)
    
    if notification_type:
        qs = qs.filter(notification_type=notification_type)
    
    return qs.order_by('-created_at')[:limit]
