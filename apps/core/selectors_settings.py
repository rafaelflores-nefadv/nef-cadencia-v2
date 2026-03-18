"""
Selectors para queries relacionadas ao módulo de Configurações.

Este módulo centraliza todas as queries necessárias para montar
o dashboard de configurações com dados reais do sistema.
"""
from django.db.models import QuerySet, Count, Q, Max
from django.contrib.auth.models import User
from datetime import datetime, timedelta


def get_system_configs_stats() -> dict:
    """
    Retorna estatísticas das configurações do sistema.
    
    Returns:
        Dict com total, categorias e última atualização
    """
    from apps.rules.models import SystemConfig
    
    configs = SystemConfig.objects.all()
    total = configs.count()
    last_updated = configs.aggregate(Max('updated_at'))['updated_at__max']
    
    # Agrupar por categoria (prefixo antes do ponto)
    categories = {}
    for config in configs:
        if '.' in config.config_key:
            category = config.config_key.split('.')[0]
        else:
            category = 'geral'
        
        categories[category] = categories.get(category, 0) + 1
    
    return {
        'total': total,
        'categories': categories,
        'categories_count': len(categories),
        'last_updated': last_updated,
    }


def get_integrations_stats() -> dict:
    """
    Retorna estatísticas das integrações.
    
    Returns:
        Dict com total, ativas, inativas e por canal
    """
    from apps.integrations.models import Integration
    
    integrations = Integration.objects.all()
    total = integrations.count()
    enabled = integrations.filter(enabled=True).count()
    disabled = total - enabled
    last_updated = integrations.aggregate(Max('updated_at'))['updated_at__max']
    
    # Contar por canal
    by_channel = {}
    for integration in integrations:
        channel = integration.channel
        by_channel[channel] = by_channel.get(channel, 0) + 1
    
    return {
        'total': total,
        'enabled': enabled,
        'disabled': disabled,
        'by_channel': by_channel,
        'last_updated': last_updated,
    }


def get_message_templates_stats() -> dict:
    """
    Retorna estatísticas dos templates de mensagens.
    
    Returns:
        Dict com total, ativos, inativos e por canal
    """
    from apps.messaging.models import MessageTemplate
    
    templates = MessageTemplate.objects.all()
    total = templates.count()
    active = templates.filter(active=True).count()
    inactive = total - active
    last_updated = templates.aggregate(Max('updated_at'))['updated_at__max']
    
    # Contar por canal
    by_channel = templates.values('channel').annotate(count=Count('id'))
    by_channel_dict = {item['channel']: item['count'] for item in by_channel}
    
    # Contar por tipo
    by_type = templates.values('template_type').annotate(count=Count('id'))
    by_type_dict = {item['template_type']: item['count'] for item in by_type}
    
    return {
        'total': total,
        'active': active,
        'inactive': inactive,
        'by_channel': by_channel_dict,
        'by_type': by_type_dict,
        'last_updated': last_updated,
    }


def get_pause_classification_stats() -> dict:
    """
    Retorna estatísticas da classificação de pausas.
    
    Returns:
        Dict com total, ativas, inativas e por categoria
    """
    from apps.monitoring.models import PauseClassification
    
    classifications = PauseClassification.objects.all()
    total = classifications.count()
    active = classifications.filter(is_active=True).count()
    inactive = total - active
    
    # Contar por categoria
    by_category = classifications.filter(is_active=True).values('category').annotate(
        count=Count('id')
    )
    by_category_dict = {item['category']: item['count'] for item in by_category}
    
    # Contar por fonte
    by_source = classifications.filter(is_active=True).values('source').annotate(
        count=Count('id')
    )
    by_source_dict = {item['source']: item['count'] for item in by_source}
    
    return {
        'total': total,
        'active': active,
        'inactive': inactive,
        'by_category': by_category_dict,
        'by_source': by_source_dict,
    }


def get_assistant_stats() -> dict:
    """
    Retorna estatísticas do assistente IA.
    
    Returns:
        Dict com conversas, mensagens e configurações
    """
    from apps.assistant.models import AssistantConversation, AssistantMessage
    from apps.rules.models import SystemConfig
    
    # Conversas
    conversations = AssistantConversation.objects.all()
    total_conversations = conversations.count()
    active_conversations = conversations.filter(status='ACTIVE').count()
    
    # Mensagens
    total_messages = AssistantMessage.objects.count()
    
    # Conversas recentes (últimos 7 dias)
    seven_days_ago = datetime.now() - timedelta(days=7)
    recent_conversations = conversations.filter(created_at__gte=seven_days_ago).count()
    
    # Configurações do assistente
    assistant_configs = SystemConfig.objects.filter(
        config_key__startswith='assistant'
    ).count()
    
    return {
        'total_conversations': total_conversations,
        'active_conversations': active_conversations,
        'total_messages': total_messages,
        'recent_conversations': recent_conversations,
        'configs': assistant_configs,
    }


def get_users_stats() -> dict:
    """
    Retorna estatísticas de usuários e agentes.
    
    Returns:
        Dict com usuários e agentes
    """
    from apps.monitoring.models import Agent
    
    # Usuários
    users = User.objects.all()
    total_users = users.count()
    active_users = users.filter(is_active=True).count()
    staff_users = users.filter(is_staff=True).count()
    superusers = users.filter(is_superuser=True).count()
    
    # Agentes
    agents = Agent.objects.all()
    total_agents = agents.count()
    active_agents = agents.filter(ativo=True).count()
    
    return {
        'total_users': total_users,
        'active_users': active_users,
        'staff_users': staff_users,
        'superusers': superusers,
        'total_agents': total_agents,
        'active_agents': active_agents,
    }


def get_operational_rules_stats() -> dict:
    """
    Retorna estatísticas das regras operacionais.
    
    Returns:
        Dict com regras operacionais
    """
    from apps.rules.models import SystemConfig
    
    # Buscar configurações relacionadas a regras operacionais
    operational_configs = SystemConfig.objects.filter(
        Q(config_key__startswith='operational') |
        Q(config_key__startswith='threshold') |
        Q(config_key__startswith='limit')
    )
    
    total = operational_configs.count()
    
    # Agrupar por prefixo
    by_prefix = {}
    for config in operational_configs:
        prefix = config.config_key.split('.')[0] if '.' in config.config_key else 'other'
        by_prefix[prefix] = by_prefix.get(prefix, 0) + 1
    
    return {
        'total': total,
        'by_prefix': by_prefix,
    }


def get_recent_config_changes(limit: int = 10) -> QuerySet:
    """
    Retorna as configurações alteradas recentemente.
    
    Args:
        limit: Número máximo de resultados
    
    Returns:
        QuerySet de SystemConfig ordenado por updated_at
    """
    from apps.rules.models import SystemConfig
    
    return SystemConfig.objects.all().order_by('-updated_at')[:limit]


def get_recent_integration_changes(limit: int = 5) -> QuerySet:
    """
    Retorna as integrações alteradas recentemente.
    
    Args:
        limit: Número máximo de resultados
    
    Returns:
        QuerySet de Integration ordenado por updated_at
    """
    from apps.integrations.models import Integration
    
    return Integration.objects.all().order_by('-updated_at')[:limit]


def get_recent_template_changes(limit: int = 5) -> QuerySet:
    """
    Retorna os templates alterados recentemente.
    
    Args:
        limit: Número máximo de resultados
    
    Returns:
        QuerySet de MessageTemplate ordenado por updated_at
    """
    from apps.messaging.models import MessageTemplate
    
    return MessageTemplate.objects.all().order_by('-updated_at')[:limit]
