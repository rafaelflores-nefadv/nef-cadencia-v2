"""
Classes de permissão base compartilhadas.
"""
from django.contrib.auth.mixins import PermissionRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.shortcuts import redirect


class BasePermissionMixin(UserPassesTestMixin):
    """Classe base para permissões customizadas."""
    
    permission_denied_message = 'Você não tem permissão para acessar esta página.'
    redirect_url = 'dashboard'
    
    def handle_no_permission(self):
        messages.error(self.request, self.permission_denied_message)
        return redirect(self.redirect_url)


class StaffPermissionMixin(BasePermissionMixin):
    """Permissão que requer usuário staff."""
    
    def test_func(self):
        return self.request.user.is_staff


class SuperuserPermissionMixin(BasePermissionMixin):
    """Permissão que requer superusuário."""
    
    permission_denied_message = 'Apenas administradores podem acessar esta página.'
    
    def test_func(self):
        return self.request.user.is_superuser


class WorkspaceAccessMixin(BasePermissionMixin):
    """Permissão que requer acesso ao workspace."""
    
    permission_denied_message = 'Você não tem acesso a este workspace.'
    
    def test_func(self):
        # Verificar se usuário está autenticado
        if not self.request.user.is_authenticated:
            return False
        
        # Obter workspace_id dos kwargs ou da sessão
        workspace_id = self.kwargs.get('workspace_id') or self.request.session.get('workspace_id')
        
        if not workspace_id:
            return False
        
        # Verificar se usuário tem acesso ao workspace
        from apps.workspaces.models import UserWorkspace
        return UserWorkspace.objects.filter(
            user=self.request.user,
            workspace_id=workspace_id,
            workspace__is_active=True
        ).exists()


class WorkspaceAdminMixin(BasePermissionMixin):
    """Permissão que requer ser admin do workspace."""
    
    permission_denied_message = 'Apenas administradores do workspace podem acessar esta página.'
    
    def test_func(self):
        # Verificar se usuário está autenticado
        if not self.request.user.is_authenticated:
            return False
        
        # Obter workspace_id dos kwargs ou da sessão
        workspace_id = self.kwargs.get('workspace_id') or self.request.session.get('workspace_id')
        
        if not workspace_id:
            return False
        
        # Verificar se usuário é admin do workspace
        from apps.workspaces.models import UserWorkspace
        try:
            membership = UserWorkspace.objects.get(
                user=self.request.user,
                workspace_id=workspace_id,
                workspace__is_active=True
            )
            return membership.role == UserWorkspace.Role.ADMIN
        except UserWorkspace.DoesNotExist:
            return False


class WorkspaceRoleMixin(BasePermissionMixin):
    """Permissão que requer role específico no workspace."""
    
    required_role = None  # Deve ser definido na subclasse
    permission_denied_message = 'Você não tem permissão suficiente neste workspace.'
    
    def test_func(self):
        # Verificar se usuário está autenticado
        if not self.request.user.is_authenticated:
            return False
        
        # Verificar se required_role foi definido
        if not self.required_role:
            raise ValueError('required_role deve ser definido')
        
        # Obter workspace_id dos kwargs ou da sessão
        workspace_id = self.kwargs.get('workspace_id') or self.request.session.get('workspace_id')
        
        if not workspace_id:
            return False
        
        # Verificar role do usuário
        from apps.workspaces.models import UserWorkspace
        from apps.workspaces.rbac import RBACManager
        
        try:
            membership = UserWorkspace.objects.get(
                user=self.request.user,
                workspace_id=workspace_id,
                workspace__is_active=True
            )
            
            # Verificar se role é suficiente (hierárquico)
            user_level = RBACManager.get_role_level(membership.role)
            required_level = RBACManager.get_role_level(self.required_role)
            
            return user_level >= required_level
            
        except UserWorkspace.DoesNotExist:
            return False


class WorkspacePermissionMixin(BasePermissionMixin):
    """Permissão que requer permissão específica no workspace."""
    
    required_permission = None  # Deve ser definido na subclasse
    permission_denied_message = 'Você não tem esta permissão neste workspace.'
    
    def test_func(self):
        # Verificar se usuário está autenticado
        if not self.request.user.is_authenticated:
            return False
        
        # Verificar se required_permission foi definido
        if not self.required_permission:
            raise ValueError('required_permission deve ser definido')
        
        # Obter workspace_id dos kwargs ou da sessão
        workspace_id = self.kwargs.get('workspace_id') or self.request.session.get('workspace_id')
        
        if not workspace_id:
            return False
        
        # Verificar permissão do usuário
        from apps.workspaces.models import UserWorkspace
        from apps.workspaces.rbac import RBACManager
        
        try:
            membership = UserWorkspace.objects.get(
                user=self.request.user,
                workspace_id=workspace_id,
                workspace__is_active=True
            )
            
            return RBACManager.has_permission(membership.role, self.required_permission)
            
        except UserWorkspace.DoesNotExist:
            return False
