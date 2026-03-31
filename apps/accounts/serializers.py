"""
Serializers para API de autenticação.

Responsabilidade: Serialização de dados para API REST.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from apps.workspaces.models import Workspace, UserWorkspace

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer para User."""
    
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'full_name',
            'phone',
            'avatar',
            'bio',
            'is_staff',
            'is_active',
            'date_joined',
        ]
        read_only_fields = ['id', 'date_joined']
    
    def get_full_name(self, obj):
        """Retorna nome completo."""
        return obj.get_full_name() or obj.username


class WorkspaceSerializer(serializers.ModelSerializer):
    """Serializer para Workspace."""
    
    members_count = serializers.IntegerField(read_only=True)
    role = serializers.SerializerMethodField()
    is_default = serializers.SerializerMethodField()
    
    class Meta:
        model = Workspace
        fields = [
            'id',
            'name',
            'slug',
            'description',
            'role',
            'members_count',
            'is_default',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_role(self, obj):
        """Retorna role do usuário no workspace."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        
        try:
            membership = UserWorkspace.objects.get(
                user=request.user,
                workspace=obj
            )
            return membership.role
        except UserWorkspace.DoesNotExist:
            return None
    
    def get_is_default(self, obj):
        """Verifica se é o workspace padrão do usuário."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        
        return obj.id == request.user.default_workspace_id


class LoginSerializer(serializers.Serializer):
    """Serializer para login."""
    
    username = serializers.CharField(
        required=True,
        help_text='Username ou email'
    )
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'},
        help_text='Senha do usuário'
    )
    
    def validate(self, attrs):
        """Validar credenciais."""
        username = attrs.get('username')
        password = attrs.get('password')
        
        if not username or not password:
            raise serializers.ValidationError('Username e senha são obrigatórios')
        
        return attrs


class LoginResponseSerializer(serializers.Serializer):
    """Serializer para resposta de login."""
    
    token = serializers.CharField(help_text='JWT access token')
    refresh = serializers.CharField(help_text='JWT refresh token')
    user = UserSerializer(help_text='Dados do usuário autenticado')
    workspaces = WorkspaceSerializer(many=True, help_text='Workspaces do usuário')
    
    class Meta:
        fields = ['token', 'refresh', 'user', 'workspaces']
