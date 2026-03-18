"""
Decorators para proteção de views por role.
"""
from functools import wraps
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from .models import Workspace, UserWorkspace
from .rbac import RBACManager, Permission


def require_workspace_role(required_role: str):
    """
    Decorator que requer role específico no workspace.
    
    Usage:
        @require_workspace_role('admin')
        def my_view(request, workspace_id):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Obter workspace_id
            workspace_id = kwargs.get('workspace_id') or request.session.get('workspace_id')
            
            if not workspace_id:
                raise PermissionDenied('Workspace não especificado')
            
            # Verificar se usuário tem role necessário
            try:
                membership = UserWorkspace.objects.get(
                    user=request.user,
                    workspace_id=workspace_id,
                    workspace__is_active=True
                )
                
                # Verificar se role é suficiente
                user_level = RBACManager.get_role_level(membership.role)
                required_level = RBACManager.get_role_level(required_role)
                
                if user_level < required_level:
                    raise PermissionDenied(f'Esta ação requer role {required_role}')
                
            except UserWorkspace.DoesNotExist:
                raise PermissionDenied('Você não tem acesso a este workspace')
            
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator


def require_workspace_permission(permission: str):
    """
    Decorator que requer permissão específica no workspace.
    
    Usage:
        @require_workspace_permission('agent.create')
        def create_agent(request, workspace_id):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Obter workspace_id
            workspace_id = kwargs.get('workspace_id') or request.session.get('workspace_id')
            
            if not workspace_id:
                raise PermissionDenied('Workspace não especificado')
            
            # Verificar se usuário tem permissão
            try:
                membership = UserWorkspace.objects.get(
                    user=request.user,
                    workspace_id=workspace_id,
                    workspace__is_active=True
                )
                
                if not RBACManager.has_permission(membership.role, permission):
                    raise PermissionDenied(f'Você não tem permissão: {permission}')
                
            except UserWorkspace.DoesNotExist:
                raise PermissionDenied('Você não tem acesso a este workspace')
            
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator


def require_any_workspace_permission(*permissions):
    """
    Decorator que requer pelo menos uma das permissões.
    
    Usage:
        @require_any_workspace_permission('agent.edit', 'agent.delete')
        def manage_agent(request, workspace_id):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Obter workspace_id
            workspace_id = kwargs.get('workspace_id') or request.session.get('workspace_id')
            
            if not workspace_id:
                raise PermissionDenied('Workspace não especificado')
            
            # Verificar se usuário tem pelo menos uma permissão
            try:
                membership = UserWorkspace.objects.get(
                    user=request.user,
                    workspace_id=workspace_id,
                    workspace__is_active=True
                )
                
                if not RBACManager.has_any_permission(membership.role, list(permissions)):
                    raise PermissionDenied(f'Você não tem nenhuma das permissões necessárias')
                
            except UserWorkspace.DoesNotExist:
                raise PermissionDenied('Você não tem acesso a este workspace')
            
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator
