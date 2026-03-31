"""
URLs da API de autenticação.
"""
from django.urls import path
from .api_views import (
    LoginAPIView,
    RefreshTokenAPIView,
    VerifyTokenAPIView,
    MeAPIView,
    LogoutAPIView
)

urlpatterns = [
    path('login', LoginAPIView.as_view(), name='api-login'),
    path('refresh', RefreshTokenAPIView.as_view(), name='api-refresh'),
    path('verify', VerifyTokenAPIView.as_view(), name='api-verify'),
    path('me', MeAPIView.as_view(), name='api-me'),
    path('logout', LogoutAPIView.as_view(), name='api-logout'),
]
