"""
Models para sistema multi-tenant com workspaces.

Arquitetura:
- Um usuário pode pertencer a múltiplos workspaces
- Um workspace pode ter múltiplos usuários
- UserWorkspace define o role do usuário no workspace
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.core.exceptions import ValidationError

User = get_user_model()


class WorkspaceManager(models.Manager):
    """Manager customizado para Workspace."""
    
    def get_by_slug(self, slug):
        """Obter workspace por slug."""
        return self.get(slug=slug)
    
    def get_user_workspaces(self, user):
        """Obter todos os workspaces de um usuário."""
        return self.filter(members=user)


class Workspace(models.Model):
    """
    Workspace (Tenant) do sistema.
    
    Representa um ambiente isolado onde usuários podem trabalhar.
    Cada workspace tem seus próprios dados e configurações.
    """
    
    name = models.CharField(
        'Nome',
        max_length=100,
        help_text='Nome do workspace'
    )
    
    slug = models.SlugField(
        'Slug',
        max_length=100,
        unique=True,
        help_text='Identificador único do workspace (URL-friendly)'
    )
    
    description = models.TextField(
        'Descrição',
        blank=True,
        help_text='Descrição do workspace'
    )
    
    is_active = models.BooleanField(
        'Ativo',
        default=True,
        help_text='Se o workspace está ativo'
    )
    
    # Relacionamento many-to-many com User através de UserWorkspace
    members = models.ManyToManyField(
        User,
        through='UserWorkspace',
        related_name='workspaces',
        verbose_name='Membros'
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        'Criado em',
        auto_now_add=True
    )
    
    updated_at = models.DateTimeField(
        'Atualizado em',
        auto_now=True
    )
    
    objects = WorkspaceManager()
    
    class Meta:
        db_table = 'workspaces'
        verbose_name = 'Workspace'
        verbose_name_plural = 'Workspaces'
        ordering = ['name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_active']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        """Override save para gerar slug automaticamente."""
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def clean(self):
        """Validações customizadas."""
        super().clean()
        
        # Validar slug único
        if self.slug:
            qs = Workspace.objects.filter(slug=self.slug)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError({'slug': 'Já existe um workspace com este slug.'})
    
    def get_members_count(self):
        """Retorna quantidade de membros."""
        return self.members.count()
    
    def get_admins(self):
        """Retorna usuários admin do workspace."""
        return self.members.filter(
            userworkspace__role=UserWorkspace.Role.ADMIN
        )
    
    def get_user_role(self, user):
        """Retorna o role de um usuário neste workspace."""
        try:
            membership = self.userworkspace_set.get(user=user)
            return membership.role
        except UserWorkspace.DoesNotExist:
            return None
    
    def has_member(self, user):
        """Verifica se usuário é membro do workspace."""
        return self.members.filter(pk=user.pk).exists()
    
    def add_member(self, user, role=None):
        """Adiciona um membro ao workspace."""
        if role is None:
            role = UserWorkspace.Role.MEMBER
        
        UserWorkspace.objects.get_or_create(
            workspace=self,
            user=user,
            defaults={'role': role}
        )
    
    def remove_member(self, user):
        """Remove um membro do workspace."""
        UserWorkspace.objects.filter(
            workspace=self,
            user=user
        ).delete()


class UserWorkspace(models.Model):
    """
    Relacionamento entre User e Workspace.
    
    Define o role (permissão) do usuário dentro do workspace.
    """
    
    class Role(models.TextChoices):
        """Roles disponíveis no workspace."""
        ADMIN = 'admin', 'Administrador'
        MEMBER = 'member', 'Membro'
        MANAGER = 'manager', 'Gerente'
        ANALYST = 'analyst', 'Analista'
        VIEWER = 'viewer', 'Visualizador'
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Usuário'
    )
    
    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        verbose_name='Workspace'
    )
    
    role = models.CharField(
        'Role',
        max_length=20,
        choices=Role.choices,
        default=Role.MEMBER,
        help_text='Permissão do usuário no workspace'
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        'Criado em',
        auto_now_add=True
    )
    
    class Meta:
        db_table = 'user_workspaces'
        verbose_name = 'Membro do Workspace'
        verbose_name_plural = 'Membros dos Workspaces'
        unique_together = [['user', 'workspace']]
        ordering = ['workspace', 'user']
        indexes = [
            models.Index(fields=['user', 'workspace']),
            models.Index(fields=['workspace', 'role']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f'{self.user.username} - {self.workspace.name} ({self.get_role_display()})'
    
    def clean(self):
        """Validações customizadas."""
        super().clean()
        
        # Validar que workspace está ativo
        if self.workspace and not self.workspace.is_active:
            raise ValidationError('Não é possível adicionar membros a um workspace inativo.')
    
    def is_admin(self):
        """Verifica se é admin."""
        return self.role == self.Role.ADMIN
    
    def is_member(self):
        """Verifica se é membro."""
        return self.role == self.Role.MEMBER
    
    def is_viewer(self):
        """Verifica se é visualizador."""
        return self.role == self.Role.VIEWER
    
    def can_edit(self):
        """Verifica se pode editar."""
        return self.role in [self.Role.ADMIN, self.Role.MEMBER]
    
    def can_delete(self):
        """Verifica se pode deletar."""
        return self.role == self.Role.ADMIN
    
    def can_manage_members(self):
        """Verifica se pode gerenciar membros."""
        return self.role == self.Role.ADMIN
