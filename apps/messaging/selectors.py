"""
Selectors para queries do app messaging.
"""
from django.db.models import QuerySet
from .models import MessageTemplate


def get_active_templates() -> QuerySet:
    """Retorna todos os templates ativos."""
    return MessageTemplate.objects.filter(active=True).order_by('template_type', 'channel')


def get_template_by_type_and_channel(template_type: str, channel: str):
    """
    Busca template ativo por tipo e canal.
    
    Args:
        template_type: Tipo do template
        channel: Canal de comunicação
        
    Returns:
        MessageTemplate ou None
    """
    return MessageTemplate.objects.filter(
        template_type=template_type,
        channel=channel,
        active=True
    ).order_by('-version').first()


def get_templates_by_type(template_type: str) -> QuerySet:
    """Retorna templates de um tipo específico."""
    return MessageTemplate.objects.filter(template_type=template_type).order_by('-version')


def get_templates_by_channel(channel: str) -> QuerySet:
    """Retorna templates de um canal específico."""
    return MessageTemplate.objects.filter(channel=channel).order_by('template_type', '-version')
