"""
URLs da API REST.

Centraliza todas as rotas da API.
"""
from django.urls import path, include

urlpatterns = [
    # Autenticação
    path('auth/', include('apps.accounts.urls_api')),
    
    # Workspaces
    path('workspaces/', include('apps.workspaces.urls_api')),
]
