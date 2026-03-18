"""
Services para autenticação.

Responsabilidade: Lógica de negócio de autenticação.
"""
from django.contrib.auth import get_user_model, authenticate
from django.core.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken
from apps.workspaces import selectors as workspace_selectors

User = get_user_model()


class AuthService:
    """Serviço de autenticação."""
    
    @staticmethod
    def authenticate_user(username, password):
        """
        Autentica usuário com username/email e senha.
        
        Args:
            username: Username ou email
            password: Senha em texto plano
        
        Returns:
            User autenticado ou None
        
        Raises:
            ValidationError: Se credenciais inválidas
        """
        # Tentar autenticar com username
        user = authenticate(username=username, password=password)
        
        # Se falhar, tentar com email
        if not user:
            try:
                user_by_email = User.objects.get(email=username)
                user = authenticate(username=user_by_email.username, password=password)
            except User.DoesNotExist:
                pass
        
        if not user:
            raise ValidationError('Credenciais inválidas')
        
        if not user.is_active:
            raise ValidationError('Usuário inativo')
        
        return user
    
    @staticmethod
    def generate_tokens(user):
        """
        Gera tokens JWT para o usuário.
        
        Args:
            user: Instância de User
        
        Returns:
            dict com 'access' e 'refresh' tokens
        """
        refresh = RefreshToken.for_user(user)
        
        # Adicionar claims customizados
        refresh['username'] = user.username
        refresh['email'] = user.email
        refresh['is_staff'] = user.is_staff
        
        return {
            'access': str(refresh.access_token),
            'refresh': str(refresh)
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
            ValidationError: Se credenciais inválidas
        """
        # Autenticar usuário
        user = AuthService.authenticate_user(username, password)
        
        # Gerar tokens
        tokens = AuthService.generate_tokens(user)
        
        # Buscar workspaces do usuário
        workspaces = workspace_selectors.get_workspaces_for_api(user)
        
        return {
            'token': tokens['access'],
            'refresh': tokens['refresh'],
            'user': user,
            'workspaces': workspaces
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
            ValidationError: Se refresh token inválido
        """
        try:
            refresh = RefreshToken(refresh_token)
            return {
                'access': str(refresh.access_token)
            }
        except Exception as e:
            raise ValidationError(f'Refresh token inválido: {str(e)}')
    
    @staticmethod
    def verify_token(token):
        """
        Verifica se token JWT é válido.
        
        Args:
            token: Access token JWT
        
        Returns:
            dict com dados do token
        
        Raises:
            ValidationError: Se token inválido
        """
        from rest_framework_simplejwt.tokens import AccessToken
        
        try:
            access_token = AccessToken(token)
            return {
                'user_id': access_token['user_id'],
                'username': access_token.get('username'),
                'email': access_token.get('email'),
                'is_staff': access_token.get('is_staff', False)
            }
        except Exception as e:
            raise ValidationError(f'Token inválido: {str(e)}')
