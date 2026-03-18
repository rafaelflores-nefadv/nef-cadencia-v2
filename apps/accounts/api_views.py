"""
API Views para autenticação.

Responsabilidade: Controllers da API REST.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError

from .serializers import (
    LoginSerializer,
    LoginResponseSerializer,
    UserSerializer,
    WorkspaceSerializer
)
from .services import AuthService
from apps.workspaces import selectors as workspace_selectors


class LoginAPIView(APIView):
    """
    Endpoint de login.
    
    POST /api/auth/login
    
    Body:
    {
        "username": "admin",
        "password": "admin123"
    }
    
    Response:
    {
        "token": "eyJ...",
        "refresh": "eyJ...",
        "user": {...},
        "workspaces": [...]
    }
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Realizar login."""
        # Validar entrada
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']
        
        try:
            # Chamar service de autenticação
            result = AuthService.login(username, password)
            
            # Serializar resposta
            response_data = {
                'token': result['token'],
                'refresh': result['refresh'],
                'user': UserSerializer(result['user']).data,
                'workspaces': result['workspaces']
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except DjangoValidationError as e:
            return Response(
                {
                    'success': False,
                    'error': str(e.message) if hasattr(e, 'message') else str(e)
                },
                status=status.HTTP_401_UNAUTHORIZED
            )
        except Exception as e:
            return Response(
                {
                    'success': False,
                    'error': 'Erro ao realizar login'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RefreshTokenAPIView(APIView):
    """
    Endpoint para refresh de token.
    
    POST /api/auth/refresh
    
    Body:
    {
        "refresh": "eyJ..."
    }
    
    Response:
    {
        "token": "eyJ..."
    }
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Atualizar access token."""
        refresh_token = request.data.get('refresh')
        
        if not refresh_token:
            return Response(
                {'error': 'Refresh token é obrigatório'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            result = AuthService.refresh_token(refresh_token)
            return Response(result, status=status.HTTP_200_OK)
            
        except DjangoValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_401_UNAUTHORIZED
            )


class VerifyTokenAPIView(APIView):
    """
    Endpoint para verificar token.
    
    POST /api/auth/verify
    
    Body:
    {
        "token": "eyJ..."
    }
    
    Response:
    {
        "valid": true,
        "user_id": 1,
        "username": "admin"
    }
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Verificar token."""
        token = request.data.get('token')
        
        if not token:
            return Response(
                {'error': 'Token é obrigatório'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            token_data = AuthService.verify_token(token)
            return Response(
                {
                    'valid': True,
                    **token_data
                },
                status=status.HTTP_200_OK
            )
            
        except DjangoValidationError as e:
            return Response(
                {
                    'valid': False,
                    'error': str(e)
                },
                status=status.HTTP_401_UNAUTHORIZED
            )


class MeAPIView(APIView):
    """
    Endpoint para obter dados do usuário autenticado.
    
    GET /api/auth/me
    
    Response:
    {
        "user": {...},
        "workspaces": [...]
    }
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Obter dados do usuário autenticado."""
        user = request.user
        
        # Serializar user
        user_data = UserSerializer(user).data
        
        # Buscar workspaces
        workspaces = workspace_selectors.get_workspaces_for_api(user)
        
        return Response(
            {
                'user': user_data,
                'workspaces': workspaces
            },
            status=status.HTTP_200_OK
        )


class LogoutAPIView(APIView):
    """
    Endpoint para logout.
    
    POST /api/auth/logout
    
    Body:
    {
        "refresh": "eyJ..."
    }
    
    Response:
    {
        "message": "Logout realizado com sucesso"
    }
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Realizar logout."""
        try:
            refresh_token = request.data.get('refresh')
            
            if refresh_token:
                # Blacklist do refresh token
                from rest_framework_simplejwt.tokens import RefreshToken
                token = RefreshToken(refresh_token)
                token.blacklist()
            
            return Response(
                {'message': 'Logout realizado com sucesso'},
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            return Response(
                {'error': 'Erro ao realizar logout'},
                status=status.HTTP_400_BAD_REQUEST
            )
