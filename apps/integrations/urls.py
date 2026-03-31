"""
URLs do app integrations.
"""
from django.urls import path
from .views import (
    IntegrationListView,
    IntegrationCreateView,
    IntegrationUpdateView,
    IntegrationTestView,
)

urlpatterns = [
    path('integracoes/', IntegrationListView.as_view(), name='integration-list'),
    path('integracoes/nova/', IntegrationCreateView.as_view(), name='integration-create'),
    path('integracoes/<int:pk>/editar/', IntegrationUpdateView.as_view(), name='integration-edit'),
    path('integracoes/<int:pk>/testar/', IntegrationTestView.as_view(), name='integration-test'),
]
