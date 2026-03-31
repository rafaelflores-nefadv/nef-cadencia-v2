"""
Validadores do app rules.
"""
from django.core.exceptions import ValidationError
import json


def validate_json_string(value: str):
    """Valida se uma string é um JSON válido."""
    try:
        json.loads(value)
    except json.JSONDecodeError:
        raise ValidationError('Valor deve ser um JSON válido')


def validate_config_key(value: str):
    """Valida chave de configuração."""
    if not value or not value.strip():
        raise ValidationError('Chave de configuração não pode ser vazia')
    
    if len(value) > 100:
        raise ValidationError('Chave de configuração não pode exceder 100 caracteres')
    
    # Apenas letras, números, pontos e underscores
    import re
    if not re.match(r'^[a-zA-Z0-9._]+$', value):
        raise ValidationError('Chave deve conter apenas letras, números, pontos e underscores')
