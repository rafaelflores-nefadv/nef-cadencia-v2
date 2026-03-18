"""
Selectors para Workspace.

Responsabilidade: Queries de leitura otimizadas.
Não contém lógica de negócio, apenas busca de dados.
"""
from django.db.models import Count, Q, Prefetch
from .models import Workspace, UserWorkspace


def get_user_workspaces(user, include_inactive=False):
    """
    Retorna todos os workspaces de um usuário.
    
    Args:
        user: Instância de User
        include_inactive: Se deve incluir workspaces inativos
    
    Returns:
        QuerySet de Workspace
    """
    queryset = user.workspaces.select_related('default_for_users')
    
    if not include_inactive:
        queryset = queryset.filter(is_active=True)
    
    # Adicionar contagem de membros
    queryset = queryset.annotate(
        members_count=Count('members')
    )
    
    # Adicionar role do usuário
    queryset = queryset.prefetch_related(
        Prefetch(
            'userworkspace_set',
            queryset=UserWorkspace.objects.filter(user=user),
            to_attr='user_membership'
        )
    )
    
    return queryset.order_by('name')


def get_workspace_by_id(workspace_id):
    """
    Retorna workspace por ID.
    
    Args:
        workspace_id: ID do workspace
    
    Returns:
        Workspace ou None
    """
    try:
        return Workspace.objects.select_related().get(id=workspace_id, is_active=True)
    except Workspace.DoesNotExist:
        return None


def get_workspace_by_slug(slug):
    """
    Retorna workspace por slug.
    
    Args:
        slug: Slug do workspace
    
    Returns:
        Workspace ou None
    """
    try:
        return Workspace.objects.select_related().get(slug=slug, is_active=True)
    except Workspace.DoesNotExist:
        return None


def get_workspace_members(workspace, role=None):
    """
    Retorna membros de um workspace.
    
    Args:
        workspace: Instância de Workspace
        role: Filtrar por role específico (opcional)
    
    Returns:
        QuerySet de User
    """
    queryset = workspace.members.select_related('default_workspace')
    
    if role:
        queryset = queryset.filter(userworkspace__role=role)
    
    # Adicionar role do usuário
    queryset = queryset.prefetch_related(
        Prefetch(
            'userworkspace_set',
            queryset=UserWorkspace.objects.filter(workspace=workspace),
            to_attr='workspace_membership'
        )
    )
    
    return queryset.order_by('username')


def get_workspace_admins(workspace):
    """
    Retorna admins de um workspace.
    
    Args:
        workspace: Instância de Workspace
    
    Returns:
        QuerySet de User
    """
    return get_workspace_members(workspace, role=UserWorkspace.Role.ADMIN)


def user_has_workspace_access(user, workspace):
    """
    Verifica se usuário tem acesso a um workspace.
    
    Args:
        user: Instância de User
        workspace: Instância de Workspace
    
    Returns:
        bool
    """
    return UserWorkspace.objects.filter(
        user=user,
        workspace=workspace,
        workspace__is_active=True
    ).exists()


def get_user_role_in_workspace(user, workspace):
    """
    Retorna o role do usuário em um workspace.
    
    Args:
        user: Instância de User
        workspace: Instância de Workspace
    
    Returns:
        str (role) ou None
    """
    try:
        membership = UserWorkspace.objects.get(user=user, workspace=workspace)
        return membership.role
    except UserWorkspace.DoesNotExist:
        return None


def get_workspaces_for_api(user):
    """
    Retorna workspaces formatados para API.
    
    Args:
        user: Instância de User
    
    Returns:
        list de dict
    """
    workspaces = get_user_workspaces(user)
    
    result = []
    for workspace in workspaces:
        # Obter role do usuário
        role = None
        if hasattr(workspace, 'user_membership') and workspace.user_membership:
            role = workspace.user_membership[0].role
        
        result.append({
            'id': workspace.id,
            'name': workspace.name,
            'slug': workspace.slug,
            'description': workspace.description,
            'role': role,
            'members_count': workspace.members_count if hasattr(workspace, 'members_count') else workspace.get_members_count(),
            'is_default': workspace.id == user.default_workspace_id if user.default_workspace_id else False
        })
    
    return result
