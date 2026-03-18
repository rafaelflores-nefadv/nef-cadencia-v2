"""
Validadores do app messaging.
"""
from django.core.exceptions import ValidationError


def validate_template_body(value: str):
    """Valida corpo do template."""
    if not value or not value.strip():
        raise ValidationError('Corpo do template não pode ser vazio')
    
    if len(value) > 10000:
        raise ValidationError('Corpo do template não pode exceder 10000 caracteres')


def validate_template_name(value: str):
    """Valida nome do template."""
    if not value or not value.strip():
        raise ValidationError('Nome do template não pode ser vazio')
    
    if len(value) > 120:
        raise ValidationError('Nome do template não pode exceder 120 caracteres')
