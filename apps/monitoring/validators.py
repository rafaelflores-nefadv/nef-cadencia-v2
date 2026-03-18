"""
Validadores do app monitoring.
"""
from django.core.exceptions import ValidationError
from datetime import date


def validate_operator_code(value: int):
    """Valida código de operador."""
    if value <= 0:
        raise ValidationError('Código de operador deve ser positivo')
    if value > 999999:
        raise ValidationError('Código de operador muito grande')


def validate_pause_name(value: str):
    """Valida nome de pausa."""
    if not value or not value.strip():
        raise ValidationError('Nome da pausa não pode ser vazio')
    
    if len(value.strip()) < 2:
        raise ValidationError('Nome da pausa deve ter pelo menos 2 caracteres')


def validate_source_name(value: str):
    """Valida nome de fonte."""
    if value and len(value) > 30:
        raise ValidationError('Nome da fonte não pode exceder 30 caracteres')
