"""
Service para gerenciamento de configurações do sistema.

Este service adiciona lógica de negócio sobre as configurações,
complementando o system_config.py existente.
"""
from typing import Dict, List, Any
from django.core.exceptions import ValidationError
from ..models import SystemConfig, SystemConfigValueType
import json


def get_configs_grouped_by_category() -> Dict[str, List[SystemConfig]]:
    """
    Retorna configurações agrupadas por categoria (prefixo).
    
    Returns:
        Dicionário com categorias e suas configurações
    """
    configs = SystemConfig.objects.all().order_by('config_key')
    grouped = {}
    
    for config in configs:
        # Extrair categoria do prefixo (antes do primeiro ponto)
        if '.' in config.config_key:
            category = config.config_key.split('.')[0]
        else:
            category = 'geral'
        
        if category not in grouped:
            grouped[category] = []
        
        grouped[category].append(config)
    
    return grouped


def update_config(config_key: str, new_value: str, updated_by=None) -> SystemConfig:
    """
    Atualiza uma configuração com validação.
    
    Args:
        config_key: Chave da configuração
        new_value: Novo valor
        updated_by: Usuário que está atualizando
    
    Returns:
        SystemConfig atualizado
    
    Raises:
        ValidationError: Se validação falhar
    """
    try:
        config = SystemConfig.objects.get(config_key=config_key)
    except SystemConfig.DoesNotExist:
        raise ValidationError(f'Configuração {config_key} não encontrada')
    
    # Validar valor baseado no tipo
    validate_config_value(new_value, config.value_type)
    
    # Atualizar
    config.config_value = new_value
    if updated_by:
        config.updated_by = updated_by
    config.save()
    
    return config


def validate_config_value(value: str, value_type: str) -> None:
    """
    Valida valor de configuração baseado no tipo.
    
    Args:
        value: Valor a validar
        value_type: Tipo do valor
    
    Raises:
        ValidationError: Se validação falhar
    """
    if value_type == SystemConfigValueType.INT:
        try:
            int(value)
        except ValueError:
            raise ValidationError('Valor deve ser um número inteiro')
    
    elif value_type == SystemConfigValueType.BOOL:
        if value.lower() not in ['true', 'false', '1', '0', 'yes', 'no']:
            raise ValidationError('Valor deve ser true ou false')
    
    elif value_type == SystemConfigValueType.JSON:
        try:
            json.loads(value)
        except json.JSONDecodeError:
            raise ValidationError('Valor deve ser um JSON válido')
    
    elif value_type == SystemConfigValueType.TIME:
        # Validar formato HH:MM
        import re
        if not re.match(r'^\d{2}:\d{2}$', value):
            raise ValidationError('Valor deve estar no formato HH:MM')


def get_config_value_typed(config_key: str, default: Any = None) -> Any:
    """
    Retorna valor da configuração convertido para o tipo correto.
    
    Args:
        config_key: Chave da configuração
        default: Valor padrão se não encontrar
    
    Returns:
        Valor convertido para o tipo apropriado
    """
    try:
        config = SystemConfig.objects.get(config_key=config_key)
    except SystemConfig.DoesNotExist:
        return default
    
    value = config.config_value
    value_type = config.value_type
    
    # Converter baseado no tipo
    if value_type == SystemConfigValueType.INT:
        return int(value)
    elif value_type == SystemConfigValueType.BOOL:
        return value.lower() in ['true', '1', 'yes']
    elif value_type == SystemConfigValueType.JSON:
        return json.loads(value)
    else:
        return value
