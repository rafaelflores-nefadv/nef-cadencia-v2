"""
Validadores do app integrations.
"""
from django.core.exceptions import ValidationError
import json


def validate_integration_config(value):
    """Valida configuração JSON da integração."""
    if isinstance(value, str):
        try:
            json.loads(value)
        except json.JSONDecodeError:
            raise ValidationError('Configuração deve ser um JSON válido')
    elif not isinstance(value, dict):
        raise ValidationError('Configuração deve ser um dicionário ou JSON válido')
