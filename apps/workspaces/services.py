"""
Services para Workspace.

Responsabilidade: Lógica de negócio e operações de escrita.
"""
from django.db import transaction
from django.core.exceptions import ValidationError, PermissionDenied
from .models import Workspace, UserWorkspace
from . import selectors


class WorkspaceService:
    """Serviço para operações de workspace."""
    
    @staticmethod
    @transaction.atomic
    def create_workspace(name, slug, description='', created_by=None):
        """
        Cria um novo workspace.
        
        Args:
            name: Nome do workspace
            slug: Slug único
            description: Descrição
            created_by: Usuário criador (será admin)
        
        Returns:
            Workspace criado
        """
        # Validar slug único
        if Workspace.objects.filter(slug=slug).exists():
            raise ValidationError(f'Já existe um workspace com o slug "{slug}"')
        
        # Criar workspace
        workspace = Workspace.objects.create(
            name=name,
            slug=slug,
            description=description,
            is_active=True
        )
        
        # Adicionar criador como admin
        if created_by:
            workspace.add_member(created_by, UserWorkspace.Role.ADMIN)
            created_by.set_default_workspace(workspace)
        
        return workspace
    
    @staticmethod
    @transaction.atomic
    def update_workspace(workspace, name=None, description=None, is_active=None):
        """
        Atualiza um workspace.
        
        Args:
            workspace: Instância de Workspace
            name: Novo nome (opcional)
            description: Nova descrição (opcional)
            is_active: Novo status (opcional)
        
        Returns:
            Workspace atualizado
        """
        if name is not None:
            workspace.name = name
        
        if description is not None:
            workspace.description = description
        
        if is_active is not None:
            workspace.is_active = is_active
        
        workspace.save()
        return workspace
    
    @staticmethod
    @transaction.atomic
    def delete_workspace(workspace, deleted_by):
        """
        Deleta um workspace.
        
        Args:
            workspace: Instância de Workspace
            deleted_by: Usuário que está deletando
        
        Raises:
            PermissionDenied: Se usuário não é admin
        """
        # Verificar permissão
        if not deleted_by.is_workspace_admin(workspace):
            raise PermissionDenied('Apenas admins podem deletar workspaces')
        
        # Soft delete
        workspace.is_active = False
        workspace.save()
    
    @staticmethod
    @transaction.atomic
    def add_member(workspace, user, role, added_by):
        """
        Adiciona um membro ao workspace.
        
        Args:
            workspace: Instância de Workspace
            user: Usuário a ser adicionado
            role: Role do usuário
            added_by: Usuário que está adicionando
        
        Raises:
            PermissionDenied: Se usuário não tem permissão
        """
        # Verificar permissão
        if not added_by.is_workspace_admin(workspace):
            raise PermissionDenied('Apenas admins podem adicionar membros')
        
        # Adicionar membro
        workspace.add_member(user, role)
    
    @staticmethod
    @transaction.atomic
    def remove_member(workspace, user, removed_by):
        """
        Remove um membro do workspace.
        
        Args:
            workspace: Instância de Workspace
            user: Usuário a ser removido
            removed_by: Usuário que está removendo
        
        Raises:
            PermissionDenied: Se usuário não tem permissão
            ValidationError: Se tentar remover último admin
        """
        # Verificar permissão
        if not removed_by.is_workspace_admin(workspace):
            raise PermissionDenied('Apenas admins podem remover membros')
        
        # Não permitir remover último admin
        admins_count = workspace.get_admins().count()
        is_removing_admin = user.is_workspace_admin(workspace)
        
        if is_removing_admin and admins_count <= 1:
            raise ValidationError('Não é possível remover o último admin do workspace')
        
        # Remover membro
        workspace.remove_member(user)
    
    @staticmethod
    @transaction.atomic
    def change_member_role(workspace, user, new_role, changed_by):
        """
        Altera o role de um membro.
        
        Args:
            workspace: Instância de Workspace
            user: Usuário a ter role alterado
            new_role: Novo role
            changed_by: Usuário que está alterando
        
        Raises:
            PermissionDenied: Se usuário não tem permissão
            ValidationError: Se tentar remover último admin
        """
        # Verificar permissão
        if not changed_by.is_workspace_admin(workspace):
            raise PermissionDenied('Apenas admins podem alterar roles')
        
        # Obter membership
        try:
            membership = UserWorkspace.objects.get(user=user, workspace=workspace)
        except UserWorkspace.DoesNotExist:
            raise ValidationError('Usuário não é membro deste workspace')
        
        # Não permitir remover último admin
        if membership.role == UserWorkspace.Role.ADMIN and new_role != UserWorkspace.Role.ADMIN:
            admins_count = workspace.get_admins().count()
            if admins_count <= 1:
                raise ValidationError('Não é possível remover o último admin do workspace')
        
        # Alterar role
        membership.role = new_role
        membership.save()
        
        return membership
