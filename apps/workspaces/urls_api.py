"""
URLs da API de workspaces.
"""
from django.urls import path
from .api_views import (
    UserWorkspacesAPIView,
    SelectWorkspaceAPIView
)

urlpatterns = [
    path('', UserWorkspacesAPIView.as_view(), name='api-workspaces-list'),
    path('select', SelectWorkspaceAPIView.as_view(), name='api-workspaces-select'),
]
