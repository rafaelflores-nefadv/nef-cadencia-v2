"""
Sistema avançado de permissões e controle de acesso.

Este módulo implementa mixins, decorators e helpers para controle
granular de acesso baseado em perfis e permissões do Django.
"""
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.contrib.auth.views import redirect_to_login
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse_lazy
from functools import wraps


# ============================================================================
# MIXINS DE PERMISSÃO
# ============================================================================

class PermissionRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin base para verificação de permissões.
    
    Uso:
        class MyView(PermissionRequiredMixin, View):
            permission_required = 'app.permission_name'
            # ou
            permission_required = ['app.perm1', 'app.perm2']
    """
    permission_required = None
    permission_denied_message = 'Você não tem permissão para acessar esta página.'
    redirect_url = reverse_lazy('dashboard-productivity')
    
    def test_func(self):
        """Testa se o usuário tem as permissões necessárias."""
        if not self.permission_required:
            return True
        
        user = self.request.user
        
        # Se for lista de permissões, verificar todas
        if isinstance(self.permission_required, (list, tuple)):
            return user.has_perms(self.permission_required)
        
        # Se for string única
        return user.has_perm(self.permission_required)
    
    def handle_no_permission(self):
        """Trata quando usuário não tem permissão."""
        messages.error(self.request, self.permission_denied_message)
        return redirect(self.redirect_url)


class DashboardAccessMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin para acesso ao dashboard e visualizações operacionais.
    
    Permite acesso a:
    - Usuários staff
    - Usuários com permissão 'monitoring.view_dashboard'
    - Usuários do grupo 'Operadores'
    """
    permission_denied_message = 'Você não tem permissão para visualizar o dashboard.'
    redirect_url = reverse_lazy('login')
    
    def test_func(self):
        user = self.request.user
        return (
            user.is_staff or
            user.has_perm('monitoring.view_dashboard') or
            user.groups.filter(name='Operadores').exists()
        )
    
    def handle_no_permission(self):
        messages.error(self.request, self.permission_denied_message)
        return redirect(self.redirect_url)


class ConfigurationAccessMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin para acesso às configurações do sistema.
    
    Permite acesso a:
    - Usuários staff
    - Usuários com permissão 'core.manage_settings'
    - Usuários do grupo 'Administradores'
    """
    permission_denied_message = 'Você não tem permissão para gerenciar configurações.'
    redirect_url = reverse_lazy('dashboard-productivity')
    
    def test_func(self):
        user = self.request.user
        return (
            user.is_staff or
            user.has_perm('core.manage_settings') or
            user.groups.filter(name='Administradores').exists()
        )
    
    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect_to_login(
                self.request.get_full_path(),
                self.get_login_url(),
                self.get_redirect_field_name(),
            )
        messages.error(self.request, self.permission_denied_message)
        return redirect(self.redirect_url)


class IntegrationManagementMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin para gerenciamento de integrações.
    
    Permite acesso a:
    - Usuários staff
    - Usuários com permissão 'integrations.change_integration'
    - Usuários do grupo 'Administradores'
    """
    permission_denied_message = 'Você não tem permissão para gerenciar integrações.'
    redirect_url = reverse_lazy('settings-hub')
    
    def test_func(self):
        user = self.request.user
        return (
            user.is_staff or
            user.has_perm('integrations.change_integration') or
            user.groups.filter(name='Administradores').exists()
        )
    
    def handle_no_permission(self):
        messages.error(self.request, self.permission_denied_message)
        return redirect(self.redirect_url)


class RulesManagementMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin para gerenciamento de regras operacionais.
    
    Permite acesso a:
    - Usuários staff
    - Usuários com permissão 'rules.change_systemconfig'
    - Usuários do grupo 'Administradores'
    """
    permission_denied_message = 'Você não tem permissão para gerenciar regras.'
    redirect_url = reverse_lazy('settings-hub')
    
    def test_func(self):
        user = self.request.user
        return (
            user.is_staff or
            user.has_perm('rules.change_systemconfig') or
            user.groups.filter(name='Administradores').exists()
        )
    
    def handle_no_permission(self):
        messages.error(self.request, self.permission_denied_message)
        return redirect(self.redirect_url)


class UserManagementMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin para gerenciamento de usuários.
    
    Permite acesso a:
    - Superusuários
    - Usuários com permissão 'auth.change_user'
    - Usuários do grupo 'Administradores de Sistema'
    """
    permission_denied_message = 'Você não tem permissão para gerenciar usuários.'
    redirect_url = reverse_lazy('settings-hub')
    
    def test_func(self):
        user = self.request.user
        return (
            user.is_superuser or
            user.has_perm('auth.change_user') or
            user.groups.filter(name='Administradores de Sistema').exists()
        )
    
    def handle_no_permission(self):
        messages.error(self.request, self.permission_denied_message)
        return redirect(self.redirect_url)


class AssistantManagementMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin para gerenciamento do assistente IA.
    
    Permite acesso a:
    - Usuários staff
    - Usuários com permissão 'assistant.manage_assistant'
    - Usuários do grupo 'Administradores'
    """
    permission_denied_message = 'Você não tem permissão para gerenciar o assistente.'
    redirect_url = reverse_lazy('settings-hub')
    
    def test_func(self):
        user = self.request.user
        return (
            user.is_staff or
            user.has_perm('assistant.manage_assistant') or
            user.groups.filter(name='Administradores').exists()
        )
    
    def handle_no_permission(self):
        messages.error(self.request, self.permission_denied_message)
        return redirect(self.redirect_url)


class ReportsAccessMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin para acesso a relatórios.
    
    Permite acesso a:
    - Usuários staff
    - Usuários com permissão 'reports.view_reports'
    - Usuários dos grupos 'Gestores' ou 'Analistas'
    """
    permission_denied_message = 'Você não tem permissão para acessar relatórios.'
    redirect_url = reverse_lazy('dashboard-productivity')
    
    def test_func(self):
        user = self.request.user
        return (
            user.is_staff or
            user.has_perm('reports.view_reports') or
            user.groups.filter(name__in=['Gestores', 'Analistas']).exists()
        )
    
    def handle_no_permission(self):
        messages.error(self.request, self.permission_denied_message)
        return redirect(self.redirect_url)


class MonitoringAccessMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin para acesso ao monitoramento operacional.
    
    Permite acesso a:
    - Usuários staff
    - Usuários com permissão 'monitoring.view_agent'
    - Usuários dos grupos 'Operadores', 'Gestores' ou 'Supervisores'
    """
    permission_denied_message = 'Você não tem permissão para acessar o monitoramento.'
    redirect_url = reverse_lazy('dashboard-productivity')
    
    def test_func(self):
        user = self.request.user
        return (
            user.is_staff or
            user.has_perm('monitoring.view_agent') or
            user.groups.filter(name__in=['Operadores', 'Gestores', 'Supervisores']).exists()
        )
    
    def handle_no_permission(self):
        messages.error(self.request, self.permission_denied_message)
        return redirect(self.redirect_url)


# ============================================================================
# DECORATORS DE PERMISSÃO
# ============================================================================

def permission_required(permission, redirect_url='dashboard', message=None):
    """
    Decorator para verificar permissão em function-based views.
    
    Args:
        permission: String ou lista de permissões
        redirect_url: URL para redirecionar se não tiver permissão
        message: Mensagem de erro customizada
    
    Uso:
        @permission_required('app.permission_name')
        def my_view(request):
            pass
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            
            # Verificar permissão
            has_permission = False
            if isinstance(permission, (list, tuple)):
                has_permission = request.user.has_perms(permission)
            else:
                has_permission = request.user.has_perm(permission)
            
            if not has_permission:
                error_message = message or 'Você não tem permissão para acessar esta página.'
                messages.error(request, error_message)
                return redirect(redirect_url)
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def dashboard_access_required(view_func):
    """
    Decorator para exigir acesso ao dashboard.
    
    Uso:
        @dashboard_access_required
        def my_view(request):
            pass
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        user = request.user
        has_access = (
            user.is_staff or
            user.has_perm('monitoring.view_dashboard') or
            user.groups.filter(name='Operadores').exists()
        )
        
        if not has_access:
            messages.error(request, 'Você não tem permissão para visualizar o dashboard.')
            return redirect('login')
        
        return view_func(request, *args, **kwargs)
    return wrapper


def configuration_access_required(view_func):
    """
    Decorator para exigir acesso às configurações.
    
    Uso:
        @configuration_access_required
        def my_view(request):
            pass
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        user = request.user
        has_access = (
            user.is_staff or
            user.has_perm('core.manage_settings') or
            user.groups.filter(name='Administradores').exists()
        )
        
        if not has_access:
            messages.error(request, 'Você não tem permissão para gerenciar configurações.')
            return redirect('dashboard')
        
        return view_func(request, *args, **kwargs)
    return wrapper


# ============================================================================
# HELPERS DE AUTORIZAÇÃO
# ============================================================================

def user_can_access_dashboard(user) -> bool:
    """Verifica se usuário pode acessar o dashboard."""
    return (
        user.is_authenticated and (
            user.is_staff or
            user.has_perm('monitoring.view_dashboard') or
            user.groups.filter(name='Operadores').exists()
        )
    )


def user_can_manage_settings(user) -> bool:
    """Verifica se usuário pode gerenciar configurações."""
    return (
        user.is_authenticated and (
            user.is_staff or
            user.has_perm('core.manage_settings') or
            user.groups.filter(name='Administradores').exists()
        )
    )


def user_can_manage_integrations(user) -> bool:
    """Verifica se usuário pode gerenciar integrações."""
    return (
        user.is_authenticated and (
            user.is_staff or
            user.has_perm('integrations.change_integration') or
            user.groups.filter(name='Administradores').exists()
        )
    )


def user_can_manage_rules(user) -> bool:
    """Verifica se usuário pode gerenciar regras."""
    return (
        user.is_authenticated and (
            user.is_staff or
            user.has_perm('rules.change_systemconfig') or
            user.groups.filter(name='Administradores').exists()
        )
    )


def user_can_manage_users(user) -> bool:
    """Verifica se usuário pode gerenciar usuários."""
    return (
        user.is_authenticated and (
            user.is_superuser or
            user.has_perm('auth.change_user') or
            user.groups.filter(name='Administradores de Sistema').exists()
        )
    )


def user_can_manage_assistant(user) -> bool:
    """Verifica se usuário pode gerenciar o assistente."""
    return (
        user.is_authenticated and (
            user.is_staff or
            user.has_perm('assistant.manage_assistant') or
            user.groups.filter(name='Administradores').exists()
        )
    )


def user_can_view_reports(user) -> bool:
    """Verifica se usuário pode visualizar relatórios."""
    return (
        user.is_authenticated and (
            user.is_staff or
            user.has_perm('reports.view_reports') or
            user.groups.filter(name__in=['Gestores', 'Analistas']).exists()
        )
    )


def user_can_access_monitoring(user) -> bool:
    """Verifica se usuário pode acessar monitoramento."""
    return (
        user.is_authenticated and (
            user.is_staff or
            user.has_perm('monitoring.view_agent') or
            user.groups.filter(name__in=['Operadores', 'Gestores', 'Supervisores']).exists()
        )
    )


def get_user_permissions_summary(user) -> dict:
    """
    Retorna resumo de todas as permissões do usuário.
    
    Args:
        user: Usuário do Django
    
    Returns:
        Dict com booleanos indicando cada permissão
    """
    return {
        'can_access_dashboard': user_can_access_dashboard(user),
        'can_manage_settings': user_can_manage_settings(user),
        'can_manage_integrations': user_can_manage_integrations(user),
        'can_manage_rules': user_can_manage_rules(user),
        'can_manage_users': user_can_manage_users(user),
        'can_manage_assistant': user_can_manage_assistant(user),
        'can_view_reports': user_can_view_reports(user),
        'can_access_monitoring': user_can_access_monitoring(user),
        'is_staff': user.is_staff,
        'is_superuser': user.is_superuser,
    }
