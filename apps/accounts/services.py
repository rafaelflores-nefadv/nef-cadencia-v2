"""
Services para autenticacao.

Responsabilidade: logica de negocio de autenticacao.
"""

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.core.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken

from apps.workspaces import selectors as workspace_selectors

User = get_user_model()


class AuthService:
    """Servico de autenticacao."""

    @staticmethod
    def _ensure_development_admin():
        """
        Garante usuario admin e workspace principal no ambiente de desenvolvimento.

        So deve ser usado em DEBUG para facilitar bootstrap local.
        """
        from apps.workspaces.models import UserWorkspace, Workspace

        user, _ = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@example.com",
                "first_name": "Admin",
                "last_name": "Sistema",
                "is_staff": True,
                "is_superuser": True,
                "is_active": True,
            },
        )

        user.email = "admin@example.com"
        user.first_name = "Admin"
        user.last_name = "Sistema"
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.set_password("admin123")
        user.save()

        workspace, _ = Workspace.objects.get_or_create(
            slug="principal",
            defaults={
                "name": "Workspace Principal",
                "description": "Ambiente principal de desenvolvimento",
                "is_active": True,
            },
        )

        if not workspace.is_active:
            workspace.is_active = True
            workspace.save(update_fields=["is_active"])

        UserWorkspace.objects.get_or_create(
            workspace=workspace,
            user=user,
            defaults={"role": UserWorkspace.Role.ADMIN},
        )

        if user.default_workspace_id != workspace.id:
            user.default_workspace = workspace
            user.save()

        return user

    @staticmethod
    def authenticate_user(username, password):
        """
        Autentica usuario com username/email e senha.

        Args:
            username: Username ou email
            password: Senha em texto plano

        Returns:
            User autenticado

        Raises:
            ValidationError: Se credenciais invalidas
        """
        username = (username or "").strip()
        password = password or ""

        # Tentar autenticar com username
        user = authenticate(username=username, password=password)

        # Se falhar, tentar com email
        if not user:
            try:
                user_by_email = User.objects.get(email=username)
                user = authenticate(username=user_by_email.username, password=password)
            except User.DoesNotExist:
                pass

        # Bootstrap automatico da conta de desenvolvimento
        if (
            not user
            and settings.DEBUG
            and username.lower() in {"admin", "admin@example.com"}
            and password == "admin123"
        ):
            dev_user = AuthService._ensure_development_admin()
            user = authenticate(username=dev_user.username, password=password)

        if not user:
            raise ValidationError("Credenciais invalidas")

        if not user.is_active:
            raise ValidationError("Usuario inativo")

        return user

    @staticmethod
    def generate_tokens(user):
        """
        Gera tokens JWT para o usuario.

        Args:
            user: Instancia de User

        Returns:
            dict com 'access' e 'refresh'
        """
        refresh = RefreshToken.for_user(user)

        # Claims customizados
        refresh["username"] = user.username
        refresh["email"] = user.email
        refresh["is_staff"] = user.is_staff

        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }

    @staticmethod
    def login(username, password):
        """
        Realiza login completo.

        Args:
            username: Username ou email
            password: Senha

        Returns:
            dict com token, user e workspaces

        Raises:
            ValidationError: Se credenciais invalidas
        """
        user = AuthService.authenticate_user(username, password)
        tokens = AuthService.generate_tokens(user)
        workspaces = workspace_selectors.get_workspaces_for_api(user)

        return {
            "token": tokens["access"],
            "refresh": tokens["refresh"],
            "user": user,
            "workspaces": workspaces,
        }

    @staticmethod
    def refresh_token(refresh_token):
        """
        Atualiza access token usando refresh token.

        Args:
            refresh_token: Refresh token JWT

        Returns:
            dict com novo access token

        Raises:
            ValidationError: Se refresh token invalido
        """
        try:
            refresh = RefreshToken(refresh_token)
            return {"access": str(refresh.access_token)}
        except Exception as exc:
            raise ValidationError(f"Refresh token invalido: {str(exc)}")

    @staticmethod
    def verify_token(token):
        """
        Verifica se token JWT e valido.

        Args:
            token: Access token JWT

        Returns:
            dict com dados do token

        Raises:
            ValidationError: Se token invalido
        """
        from rest_framework_simplejwt.tokens import AccessToken

        try:
            access_token = AccessToken(token)
            return {
                "user_id": access_token["user_id"],
                "username": access_token.get("username"),
                "email": access_token.get("email"),
                "is_staff": access_token.get("is_staff", False),
            }
        except Exception as exc:
            raise ValidationError(f"Token invalido: {str(exc)}")
