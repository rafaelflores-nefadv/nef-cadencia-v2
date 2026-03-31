"""
Permissões do app accounts.
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from apps.core.permissions import BasePermissionMixin


class CanEditProfile(LoginRequiredMixin):
    """Permissão para editar próprio perfil."""
    pass  # Todos os usuários logados podem editar seu perfil


class CanChangePassword(LoginRequiredMixin):
    """Permissão para mudar própria senha."""
    pass  # Todos os usuários logados podem mudar sua senha
