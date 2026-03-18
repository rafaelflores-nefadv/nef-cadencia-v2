"""
Permissões do app monitoring.
"""
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.shortcuts import redirect
from apps.core.permissions import BasePermissionMixin


class CanViewDashboard(LoginRequiredMixin):
    """Permissão para visualizar dashboards."""
    pass  # Todos os usuários logados podem ver


class CanManageAgents(BasePermissionMixin):
    """Permissão para gerenciar agentes."""
    
    permission_denied_message = 'Você não tem permissão para gerenciar agentes.'
    
    def test_func(self):
        return self.request.user.is_staff or \
               self.request.user.has_perm('monitoring.change_agent')


class CanRebuildStats(BasePermissionMixin):
    """Permissão para rebuild de estatísticas."""
    
    permission_denied_message = 'Apenas administradores podem rebuild estatísticas.'
    
    def test_func(self):
        return self.request.user.is_staff


class CanManagePauseClassification(BasePermissionMixin):
    """Permissão para gerenciar classificação de pausas."""
    
    permission_denied_message = 'Você não tem permissão para gerenciar classificações de pausas.'
    
    def test_func(self):
        return self.request.user.is_staff or \
               self.request.user.has_perm('monitoring.change_pauseclassification')


class CanViewJobRuns(LoginRequiredMixin):
    """Permissão para visualizar execuções de jobs."""
    pass  # Todos os usuários logados podem ver
