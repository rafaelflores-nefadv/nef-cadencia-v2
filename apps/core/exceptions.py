"""
Exception handlers customizados para API.

Responsabilidade: Tratamento global de erros.
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.exceptions import PermissionDenied
from django.http import Http404


def custom_exception_handler(exc, context):
    """
    Handler customizado para exceções da API.
    
    Padroniza formato de erro:
    {
        "success": false,
        "error": "mensagem de erro",
        "details": {...}  # opcional
    }
    """
    # Chamar handler padrão do DRF
    response = exception_handler(exc, context)
    
    # Se DRF já tratou, formatar resposta
    if response is not None:
        custom_response = {
            'success': False,
            'error': _get_error_message(response.data),
            'status_code': response.status_code
        }
        
        # Adicionar detalhes se houver
        if isinstance(response.data, dict) and len(response.data) > 1:
            custom_response['details'] = response.data
        
        response.data = custom_response
        return response
    
    # Tratar exceções do Django não tratadas pelo DRF
    if isinstance(exc, DjangoValidationError):
        return Response(
            {
                'success': False,
                'error': _get_error_message(exc.message_dict if hasattr(exc, 'message_dict') else str(exc)),
                'status_code': status.HTTP_400_BAD_REQUEST
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if isinstance(exc, PermissionDenied):
        return Response(
            {
                'success': False,
                'error': str(exc) or 'Você não tem permissão para realizar esta ação',
                'status_code': status.HTTP_403_FORBIDDEN
            },
            status=status.HTTP_403_FORBIDDEN
        )
    
    if isinstance(exc, Http404):
        return Response(
            {
                'success': False,
                'error': 'Recurso não encontrado',
                'status_code': status.HTTP_404_NOT_FOUND
            },
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Erro não tratado
    return Response(
        {
            'success': False,
            'error': 'Erro interno do servidor',
            'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )


def _get_error_message(data):
    """Extrai mensagem de erro de diferentes formatos."""
    if isinstance(data, str):
        return data
    
    if isinstance(data, list):
        return data[0] if data else 'Erro desconhecido'
    
    if isinstance(data, dict):
        # Tentar pegar primeira mensagem
        for key, value in data.items():
            if isinstance(value, list):
                return f'{key}: {value[0]}'
            elif isinstance(value, str):
                return f'{key}: {value}'
        
        return str(data)
    
    return 'Erro desconhecido'
