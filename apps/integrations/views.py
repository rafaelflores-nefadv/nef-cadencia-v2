"""
Views refatoradas do app integrations usando arquitetura em camadas.

Este módulo demonstra o padrão de views enxutas com separação de responsabilidades.
"""
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, View
from django.http import JsonResponse

from apps.core.views import StaffPageMixin, FormMessageMixin, AjaxResponseMixin
from apps.core.messages import Messages
from .models import Integration
from .forms import IntegrationForm
from .permissions import CanManageIntegrations
from .selectors import get_enabled_integrations, get_integrations_by_channel
from .services.integration_service import test_integration_connection, validate_integration_config


class IntegrationListView(CanManageIntegrations, StaffPageMixin, ListView):
    """
    View de listagem de integrações.
    
    Camadas:
    - Apresentação: Esta view
    - Permissão: CanManageIntegrations
    - Consulta: get_enabled_integrations (selector)
    """
    model = Integration
    template_name = 'integrations/integration_list.html'
    context_object_name = 'integrations'
    
    page_title = 'Integrações'
    page_subtitle = 'Gerencie as integrações externas'
    
    breadcrumbs = [
        {'label': 'Dashboard', 'url': '/dashboard'},
        {'label': 'Integrações', 'url': None},
    ]
    
    def get_queryset(self):
        qs = super().get_queryset()
        
        # Filtro opcional por canal
        channel = self.request.GET.get('channel')
        if channel:
            qs = qs.filter(channel=channel)
        
        return qs.order_by('channel', 'name')


class IntegrationCreateView(CanManageIntegrations, FormMessageMixin, StaffPageMixin, CreateView):
    """
    View de criação de integração.
    
    Camadas:
    - Apresentação: Esta view
    - Permissão: CanManageIntegrations
    - Validação: IntegrationForm
    - Serviço: validate_integration_config
    - Mensagens: FormMessageMixin
    """
    model = Integration
    form_class = IntegrationForm
    template_name = 'integrations/integration_form.html'
    success_url = reverse_lazy('integration-list')
    
    page_title = 'Nova Integração'
    success_message = 'Integração criada com sucesso.'
    
    breadcrumbs = [
        {'label': 'Dashboard', 'url': '/dashboard'},
        {'label': 'Integrações', 'url': reverse_lazy('integration-list')},
        {'label': 'Nova', 'url': None},
    ]


class IntegrationUpdateView(CanManageIntegrations, FormMessageMixin, StaffPageMixin, UpdateView):
    """
    View de edição de integração.
    
    Camadas:
    - Apresentação: Esta view
    - Permissão: CanManageIntegrations
    - Validação: IntegrationForm
    - Mensagens: FormMessageMixin
    """
    model = Integration
    form_class = IntegrationForm
    template_name = 'integrations/integration_form.html'
    success_url = reverse_lazy('integration-list')
    
    page_title = 'Editar Integração'
    success_message = 'Integração atualizada com sucesso.'
    
    def get_breadcrumbs(self):
        return [
            {'label': 'Dashboard', 'url': '/dashboard'},
            {'label': 'Integrações', 'url': reverse_lazy('integration-list')},
            {'label': 'Editar', 'url': None},
        ]


class IntegrationTestView(CanManageIntegrations, AjaxResponseMixin, View):
    """
    View para testar conexão de integração (AJAX).
    
    Camadas:
    - Apresentação: Esta view
    - Permissão: CanManageIntegrations
    - Serviço: test_integration_connection
    """
    
    def post(self, request, pk):
        """Testa conexão com a integração."""
        try:
            integration = Integration.objects.get(pk=pk)
            result = test_integration_connection(integration)
            
            return JsonResponse(result)
        
        except Integration.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Integração não encontrada'
            }, status=404)
        
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erro ao testar integração: {str(e)}'
            }, status=500)
