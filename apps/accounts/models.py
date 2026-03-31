"""
Models customizados para autenticação e usuários.

Estende o User model do Django para adicionar campos customizados.
"""
from django.db import models
from django.contrib.auth.models import AbstractUser, UserManager as DjangoUserManager
from django.utils.translation import gettext_lazy as _


class UserManager(DjangoUserManager):
    """Mantem o email unico mesmo sem valor explicito no create_user."""

    def _build_fallback_email(self, username: str) -> str:
        base_username = (username or "user").strip() or "user"
        normalized_base = "".join(
            char if char.isalnum() or char in {"-", "_", "."} else "-"
            for char in base_username.lower()
        ).strip("-") or "user"
        candidate = f"{normalized_base}@local.invalid"
        suffix = 1

        while self.model._default_manager.filter(email=candidate).exists():
            suffix += 1
            candidate = f"{normalized_base}-{suffix}@local.invalid"

        return candidate

    def _create_user(self, username, email, password, **extra_fields):
        normalized_email = self.normalize_email(email) if email else ""
        if not normalized_email:
            normalized_email = self._build_fallback_email(username)
        return super()._create_user(username, normalized_email, password, **extra_fields)


class User(AbstractUser):
    """
    User model customizado.
    
    Estende o AbstractUser do Django para adicionar campos adicionais
    necessários para o sistema multi-tenant.
    
    Campos herdados do AbstractUser:
    - username
    - first_name
    - last_name
    - email
    - password
    - is_staff
    - is_active
    - is_superuser
    - last_login
    - date_joined
    """
    
    # Sobrescrever email para tornar obrigatório e único
    email = models.EmailField(
        _('email address'),
        unique=True,
        help_text='Email do usuário (usado para login)'
    )
    
    # Campos adicionais
    phone = models.CharField(
        'Telefone',
        max_length=20,
        blank=True,
        help_text='Telefone de contato'
    )
    
    avatar = models.ImageField(
        'Avatar',
        upload_to='avatars/',
        blank=True,
        null=True,
        help_text='Foto de perfil do usuário'
    )
    
    bio = models.TextField(
        'Biografia',
        blank=True,
        help_text='Breve descrição sobre o usuário'
    )
    
    # Workspace padrão (último acessado)
    default_workspace = models.ForeignKey(
        'workspaces.Workspace',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='default_for_users',
        verbose_name='Workspace Padrão',
        help_text='Último workspace acessado pelo usuário'
    )
    
    # Timestamps customizados
    updated_at = models.DateTimeField(
        'Atualizado em',
        auto_now=True
    )

    objects = UserManager()
    
    class Meta:
        db_table = 'users'
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'
        ordering = ['username']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['is_active']),
            models.Index(fields=['date_joined']),
        ]
    
    def __str__(self):
        return self.get_full_name() or self.username
    
    def get_workspaces(self):
        """Retorna todos os workspaces do usuário."""
        return self.workspaces.filter(is_active=True)
    
    def get_workspace_role(self, workspace):
        """Retorna o role do usuário em um workspace específico."""
        try:
            from apps.workspaces.models import UserWorkspace
            membership = UserWorkspace.objects.get(user=self, workspace=workspace)
            return membership.role
        except UserWorkspace.DoesNotExist:
            return None
    
    def is_workspace_admin(self, workspace):
        """Verifica se é admin de um workspace."""
        from apps.workspaces.models import UserWorkspace
        return self.userworkspace_set.filter(
            workspace=workspace,
            role=UserWorkspace.Role.ADMIN
        ).exists()
    
    def has_workspace_access(self, workspace):
        """Verifica se tem acesso a um workspace."""
        return self.workspaces.filter(pk=workspace.pk, is_active=True).exists()
    
    def set_default_workspace(self, workspace):
        """Define o workspace padrão."""
        if self.has_workspace_access(workspace):
            self.default_workspace = workspace
            self.save(update_fields=['default_workspace', 'updated_at'])
