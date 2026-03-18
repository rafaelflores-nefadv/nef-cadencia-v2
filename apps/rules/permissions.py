"""
Permissões do app rules.
"""
from apps.core.permissions import BasePermissionMixin


class CanManageConfigs(BasePermissionMixin):
    """Permissão para gerenciar configurações do sistema."""
    
    permission_denied_message = 'Você não tem permissão para gerenciar configurações.'
    
    def test_func(self):
        return self.request.user.is_staff or \
               self.request.user.has_perm('rules.change_systemconfig')
