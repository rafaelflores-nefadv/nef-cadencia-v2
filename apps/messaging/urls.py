"""
URLs do app messaging.
"""
from django.urls import path
from .views import (
    TemplateListView,
    TemplateCreateView,
    TemplateUpdateView,
    TemplatePreviewView,
)

urlpatterns = [
    path('templates/', TemplateListView.as_view(), name='template-list'),
    path('templates/novo/', TemplateCreateView.as_view(), name='template-create'),
    path('templates/<int:pk>/editar/', TemplateUpdateView.as_view(), name='template-edit'),
    path('templates/<int:pk>/preview/', TemplatePreviewView.as_view(), name='template-preview'),
]
