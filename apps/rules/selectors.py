"""
Selectors para queries do app rules.
"""
from django.db.models import QuerySet
from .models import SystemConfig


def get_all_configs() -> QuerySet:
    """Retorna todas as configurações."""
    return SystemConfig.objects.all().order_by('config_key')


def get_config_by_key(key: str):
    """Busca configuração por chave."""
    return SystemConfig.objects.filter(config_key=key).first()


def get_configs_by_prefix(prefix: str) -> QuerySet:
    """Retorna configurações que começam com determinado prefixo."""
    return SystemConfig.objects.filter(config_key__startswith=prefix).order_by('config_key')
