"""
Selectors para queries do app integrations.
"""
from django.db.models import QuerySet
from .models import Integration


def get_enabled_integrations() -> QuerySet:
    """Retorna todas as integrações habilitadas."""
    return Integration.objects.filter(enabled=True).order_by('name')


def get_integrations_by_channel(channel: str) -> QuerySet:
    """Retorna integrações de um canal específico."""
    return Integration.objects.filter(channel=channel).order_by('name')


def get_integration_by_name(name: str):
    """Busca integração por nome."""
    return Integration.objects.filter(name=name).first()
