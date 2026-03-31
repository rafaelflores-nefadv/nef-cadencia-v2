"""
Context processors do app core.

Context processors adicionam variáveis globais ao contexto de todos os templates.
"""
from django.conf import settings
from .permissions_advanced import get_user_permissions_summary


def system_info(request):
    """
    Adiciona informações do sistema ao contexto.
    
    Returns:
        Dict com informações do sistema
    """
    return {
        'system_name': 'NEF Cadência',
        'system_version': '2.0',
    }


def user_permissions(request):
    """
    Adiciona permissões completas do usuário ao contexto.
    
    Usa o helper get_user_permissions_summary para obter todas
    as permissões do usuário de forma centralizada.
    
    Returns:
        Dict com flags de permissão do usuário
    """
    if not request.user.is_authenticated:
        return {
            'user_permissions': {},
            'can_access_dashboard': False,
            'can_manage_settings': False,
            'can_manage_integrations': False,
            'can_manage_rules': False,
            'can_manage_users': False,
            'can_manage_assistant': False,
            'can_view_reports': False,
            'can_access_monitoring': False,
        }
    
    # Obter resumo completo de permissões
    permissions = get_user_permissions_summary(request.user)
    
    # Retornar tanto o dict completo quanto flags individuais
    # para facilitar uso nos templates
    return {
        'user_permissions': permissions,
        **permissions,  # Desempacotar para acesso direto
        'can_manage_templates': request.user.is_staff or request.user.has_perm('messaging.change_messagetemplate'),
        'can_manage_integrations': request.user.is_staff or request.user.has_perm('integrations.change_integration'),
    }
