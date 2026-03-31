"""
Permissões do app assistant.
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from apps.core.permissions import BasePermissionMixin


class CanUseAssistant(LoginRequiredMixin):
    """Permissão para usar o assistente."""
    pass  # Todos os usuários logados podem usar


class CanManageConversations(BasePermissionMixin):
    """Permissão para gerenciar conversas."""
    
    permission_denied_message = 'Você não tem permissão para gerenciar conversas.'
    
    def test_func(self):
        # Usuários podem gerenciar suas próprias conversas
        return True


class CanViewAuditLogs(BasePermissionMixin):
    """Permissão para visualizar logs de auditoria."""
    
    permission_denied_message = 'Você não tem permissão para visualizar logs de auditoria.'
    
    def test_func(self):
        return self.request.user.is_staff
