"""API views de autenticacao."""

import logging

from django.conf import settings
from django.contrib.auth import login as django_login, logout as django_logout
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import OperationalError
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.workspaces import selectors as workspace_selectors

from .serializers import LoginSerializer, UserSerializer
from .services import AuthService

logger = logging.getLogger(__name__)


class LoginAPIView(APIView):
    """Endpoint de login."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        username = serializer.validated_data["username"]
        password = serializer.validated_data["password"]

        try:
            result = AuthService.login(username, password)

            # Also open Django session for server-rendered pages (/dashboard etc.)
            django_login(request, result["user"])

            workspace_id = result["user"].default_workspace_id
            if not workspace_id and result["workspaces"]:
                workspace_id = result["workspaces"][0].get("id")
            if workspace_id:
                request.session["workspace_id"] = workspace_id

            response_data = {
                "token": result["token"],
                "refresh": result["refresh"],
                "user": UserSerializer(result["user"]).data,
                "workspaces": result["workspaces"],
            }
            return Response(response_data, status=status.HTTP_200_OK)

        except DjangoValidationError as exc:
            message = exc.messages[0] if getattr(exc, "messages", None) else str(exc)
            return Response(
                {"success": False, "error": message},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        except OperationalError:
            logger.exception("Falha de banco durante login")
            return Response(
                {
                    "success": False,
                    "error": "Servico temporariamente indisponivel. Verifique a conexao com o banco.",
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        except Exception as exc:  # pragma: no cover - protecao de borda
            logger.exception("Erro inesperado ao realizar login")
            return Response(
                {
                    "success": False,
                    "error": str(exc) if settings.DEBUG else "Erro ao realizar login",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class RefreshTokenAPIView(APIView):
    """Endpoint para refresh de token."""

    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.data.get("refresh")

        if not refresh_token:
            return Response(
                {"error": "Refresh token e obrigatorio"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            result = AuthService.refresh_token(refresh_token)
            return Response(result, status=status.HTTP_200_OK)

        except DjangoValidationError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_401_UNAUTHORIZED)


class VerifyTokenAPIView(APIView):
    """Endpoint para verificar token."""

    permission_classes = [AllowAny]

    def post(self, request):
        token = request.data.get("token")

        if not token:
            return Response(
                {"error": "Token e obrigatorio"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            token_data = AuthService.verify_token(token)
            return Response({"valid": True, **token_data}, status=status.HTTP_200_OK)

        except DjangoValidationError as exc:
            return Response(
                {"valid": False, "error": str(exc)},
                status=status.HTTP_401_UNAUTHORIZED,
            )


class MeAPIView(APIView):
    """Endpoint para obter dados do usuario autenticado."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        user_data = UserSerializer(user).data
        workspaces = workspace_selectors.get_workspaces_for_api(user)

        return Response(
            {"user": user_data, "workspaces": workspaces},
            status=status.HTTP_200_OK,
        )


class LogoutAPIView(APIView):
    """Endpoint para logout."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")

            if refresh_token:
                from rest_framework_simplejwt.tokens import RefreshToken

                token = RefreshToken(refresh_token)
                token.blacklist()

            django_logout(request)

            return Response(
                {"message": "Logout realizado com sucesso"},
                status=status.HTTP_200_OK,
            )

        except Exception:
            logger.exception("Erro ao realizar logout")
            return Response(
                {"error": "Erro ao realizar logout"},
                status=status.HTTP_400_BAD_REQUEST,
            )
