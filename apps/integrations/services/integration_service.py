"""
Service para gerenciamento de integrações externas.

Este service contém lógica de negócio para configuração e
teste de integrações.
"""
from typing import Dict, Optional
from django.core.exceptions import ValidationError
from ..models import Integration
import json


def validate_integration_config(integration: Integration) -> None:
    """
    Valida configuração de uma integração.
    
    Args:
        integration: Integração a validar
    
    Raises:
        ValidationError: Se configuração inválida
    """
    config = integration.config_json
    
    # Validar que é um dicionário
    if not isinstance(config, dict):
        raise ValidationError('Configuração deve ser um dicionário')
    
    # Validações específicas por canal
    if integration.channel == 'EMAIL':
        required_fields = ['smtp_host', 'smtp_port', 'from_email']
        for field in required_fields:
            if field not in config:
                raise ValidationError(f'Campo obrigatório ausente: {field}')
    
    elif integration.channel == 'SMS':
        required_fields = ['api_key', 'api_url']
        for field in required_fields:
            if field not in config:
                raise ValidationError(f'Campo obrigatório ausente: {field}')
    
    elif integration.channel == 'WHATSAPP':
        required_fields = ['api_token', 'phone_number_id']
        for field in required_fields:
            if field not in config:
                raise ValidationError(f'Campo obrigatório ausente: {field}')


def test_integration_connection(integration: Integration) -> Dict[str, any]:
    """
    Testa conexão com a integração.
    
    Args:
        integration: Integração a testar
    
    Returns:
        Dicionário com resultado do teste
    """
    if not integration.enabled:
        return {
            'success': False,
            'message': 'Integração está desabilitada',
        }
    
    try:
        # Validar configuração
        validate_integration_config(integration)
        
        # Aqui seria implementada a lógica real de teste
        # Por enquanto, apenas validamos a configuração
        
        return {
            'success': True,
            'message': 'Configuração válida',
        }
    
    except ValidationError as e:
        return {
            'success': False,
            'message': str(e),
        }
    except Exception as e:
        return {
            'success': False,
            'message': f'Erro ao testar conexão: {str(e)}',
        }


def get_integration_by_channel(channel: str) -> Optional[Integration]:
    """
    Busca integração habilitada por canal.
    
    Args:
        channel: Canal da integração
    
    Returns:
        Integration ou None
    """
    return Integration.objects.filter(
        channel=channel,
        enabled=True
    ).first()


def update_integration_config(
    integration: Integration,
    new_config: Dict,
    updated_by=None
) -> Integration:
    """
    Atualiza configuração de uma integração.
    
    Args:
        integration: Integração a atualizar
        new_config: Nova configuração
        updated_by: Usuário que está atualizando
    
    Returns:
        Integration atualizada
    
    Raises:
        ValidationError: Se configuração inválida
    """
    # Atualizar config
    integration.config_json = new_config
    
    # Validar
    validate_integration_config(integration)
    
    # Salvar
    integration.save()
    
    return integration
