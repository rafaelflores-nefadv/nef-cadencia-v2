"""
Permissões do app integrations.
"""
from apps.core.permissions import BasePermissionMixin


class CanManageIntegrations(BasePermissionMixin):
    """Permissão para gerenciar integrações."""
    
    permission_denied_message = 'Você não tem permissão para gerenciar integrações.'
    
    def test_func(self):
        return self.request.user.is_staff or \
               self.request.user.has_perm('integrations.change_integration')
