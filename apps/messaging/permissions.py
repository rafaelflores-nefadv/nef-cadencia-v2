"""
Permissões do app messaging.
"""
from apps.core.permissions import BasePermissionMixin


class CanManageTemplates(BasePermissionMixin):
    """Permissão para gerenciar templates de mensagens."""
    
    permission_denied_message = 'Você não tem permissão para gerenciar templates de mensagens.'
    
    def test_func(self):
        return self.request.user.is_staff or \
               self.request.user.has_perm('messaging.change_messagetemplate')
