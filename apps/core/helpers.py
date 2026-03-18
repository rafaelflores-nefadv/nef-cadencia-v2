"""
Funções auxiliares compartilhadas.
"""
from datetime import datetime, timedelta


def format_seconds_to_hhmm(seconds):
    """
    Formata segundos para HH:MM.
    
    Args:
        seconds: Número de segundos
        
    Returns:
        String no formato HH:MM
    """
    if seconds is None:
        return "00:00"
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    return f"{hours:02d}:{minutes:02d}"


def format_duration_hhmm(start_time, end_time):
    """
    Calcula e formata duração entre dois datetimes.
    
    Args:
        start_time: Datetime de início
        end_time: Datetime de fim
        
    Returns:
        String no formato HH:MM
    """
    if not start_time or not end_time:
        return "00:00"
    
    duration = end_time - start_time
    return format_seconds_to_hhmm(duration.total_seconds())


def safe_divide(numerator, denominator, default=0):
    """
    Divisão segura que retorna default se denominador for zero.
    
    Args:
        numerator: Numerador
        denominator: Denominador
        default: Valor padrão se denominador for zero
        
    Returns:
        Resultado da divisão ou default
    """
    if denominator == 0:
        return default
    return numerator / denominator


def percentage(part, total, decimals=2):
    """
    Calcula percentual.
    
    Args:
        part: Parte
        total: Total
        decimals: Número de casas decimais
        
    Returns:
        Percentual arredondado
    """
    if total == 0:
        return 0
    return round((part / total) * 100, decimals)
