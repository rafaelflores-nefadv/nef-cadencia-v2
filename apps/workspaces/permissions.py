"""
Permissions para Workspace.

Responsabilidade: Verificar permissões de acesso.
"""
from django.core.exceptions import PermissionDenied
from .models import UserWorkspace
from . import selectors


class WorkspacePermission:
    """Classe base para permissões de workspace."""
    
    @staticmethod
    def check_workspace_access(user, workspace):
        """
        Verifica se usuário tem acesso ao workspace.
        
        Raises:
            PermissionDenied: Se não tem acesso
        """
        if not selectors.user_has_workspace_access(user, workspace):
            raise PermissionDenied('Você não tem acesso a este workspace')
    
    @staticmethod
    def check_workspace_admin(user, workspace):
        """
        Verifica se usuário é admin do workspace.
        
        Raises:
            PermissionDenied: Se não é admin
        """
        WorkspacePermission.check_workspace_access(user, workspace)
        
        role = selectors.get_user_role_in_workspace(user, workspace)
        if role != UserWorkspace.Role.ADMIN:
            raise PermissionDenied('Apenas admins podem realizar esta ação')
    
    @staticmethod
    def check_can_edit(user, workspace):
        """
        Verifica se usuário pode editar no workspace.
        
        Raises:
            PermissionDenied: Se não pode editar
        """
        WorkspacePermission.check_workspace_access(user, workspace)
        
        role = selectors.get_user_role_in_workspace(user, workspace)
        if role not in [UserWorkspace.Role.ADMIN, UserWorkspace.Role.MEMBER]:
            raise PermissionDenied('Você não tem permissão para editar')
    
    @staticmethod
    def check_can_delete(user, workspace):
        """
        Verifica se usuário pode deletar no workspace.
        
        Raises:
            PermissionDenied: Se não pode deletar
        """
        WorkspacePermission.check_workspace_admin(user, workspace)
    
    @staticmethod
    def can_view(user, workspace):
        """Verifica se pode visualizar (não lança exceção)."""
        return selectors.user_has_workspace_access(user, workspace)
    
    @staticmethod
    def can_edit(user, workspace):
        """Verifica se pode editar (não lança exceção)."""
        if not selectors.user_has_workspace_access(user, workspace):
            return False
        
        role = selectors.get_user_role_in_workspace(user, workspace)
        return role in [UserWorkspace.Role.ADMIN, UserWorkspace.Role.MEMBER]
    
    @staticmethod
    def can_delete(user, workspace):
        """Verifica se pode deletar (não lança exceção)."""
        if not selectors.user_has_workspace_access(user, workspace):
            return False
        
        role = selectors.get_user_role_in_workspace(user, workspace)
        return role == UserWorkspace.Role.ADMIN
    
    @staticmethod
    def can_manage_members(user, workspace):
        """Verifica se pode gerenciar membros (não lança exceção)."""
        return WorkspacePermission.can_delete(user, workspace)


class RequireWorkspaceAccessMixin:
    """Mixin para views que requerem acesso ao workspace."""
    
    def dispatch(self, request, *args, **kwargs):
        workspace_id = kwargs.get('workspace_id') or kwargs.get('pk')
        
        if workspace_id:
            workspace = selectors.get_workspace_by_id(workspace_id)
            if not workspace:
                from django.http import Http404
                raise Http404('Workspace não encontrado')
            
            WorkspacePermission.check_workspace_access(request.user, workspace)
            request.workspace = workspace
        
        return super().dispatch(request, *args, **kwargs)


class RequireWorkspaceAdminMixin:
    """Mixin para views que requerem admin do workspace."""
    
    def dispatch(self, request, *args, **kwargs):
        workspace_id = kwargs.get('workspace_id') or kwargs.get('pk')
        
        if workspace_id:
            workspace = selectors.get_workspace_by_id(workspace_id)
            if not workspace:
                from django.http import Http404
                raise Http404('Workspace não encontrado')
            
            WorkspacePermission.check_workspace_admin(request.user, workspace)
            request.workspace = workspace
        
        return super().dispatch(request, *args, **kwargs)
