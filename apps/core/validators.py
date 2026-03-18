"""
Validadores compartilhados.
"""
from django.core.exceptions import ValidationError
from datetime import date, timedelta


def validate_positive_integer(value):
    """Valida que o valor é um inteiro positivo."""
    if value <= 0:
        raise ValidationError('O valor deve ser um número positivo.')


def validate_date_not_future(value):
    """Valida que a data não está no futuro."""
    if value > date.today():
        raise ValidationError('A data não pode estar no futuro.')


def validate_date_range(start_date, end_date, max_days=None):
    """
    Valida um range de datas.
    
    Args:
        start_date: Data inicial
        end_date: Data final
        max_days: Número máximo de dias permitido (opcional)
    """
    if start_date > end_date:
        raise ValidationError('A data inicial deve ser menor ou igual à data final.')
    
    if max_days:
        delta = (end_date - start_date).days
        if delta > max_days:
            raise ValidationError(f'O período não pode exceder {max_days} dias.')


def validate_email_or_phone(email, phone):
    """Valida que pelo menos email ou telefone está preenchido."""
    if not email and not phone:
        raise ValidationError('Informe pelo menos email ou telefone.')
