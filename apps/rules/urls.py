"""
URLs do app rules.
"""
from django.urls import path
from .views import ConfigListView, ConfigEditView

urlpatterns = [
    path('configuracoes/', ConfigListView.as_view(), name='config-list'),
    path('configuracoes/<int:pk>/editar/', ConfigEditView.as_view(), name='config-edit'),
]
