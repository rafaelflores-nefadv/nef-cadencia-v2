"""
Views refatoradas do app rules usando arquitetura em camadas.

Este módulo demonstra o padrão de views enxutas com separação de responsabilidades.
"""
from django.urls import reverse_lazy
from django.views.generic import ListView, UpdateView

from apps.core.views import StaffPageMixin, FormMessageMixin
from apps.core.messages import Messages
from .models import SystemConfig
from .forms import SystemConfigForm
from .permissions import CanManageConfigs
from .selectors import get_all_configs, get_config_by_key
from .services.config_service import get_configs_grouped_by_category, update_config


class ConfigListView(CanManageConfigs, StaffPageMixin, ListView):
    """
    View de listagem de configurações do sistema.
    
    Camadas:
    - Apresentação: Esta view
    - Permissão: CanManageConfigs
    - Consulta: get_configs_grouped_by_category (service)
    """
    model = SystemConfig
    template_name = 'rules/config_list.html'
    context_object_name = 'configs'
    
    page_title = 'Configurações do Sistema'
    page_subtitle = 'Gerencie as configurações da aplicação'
    
    breadcrumbs = [
        {'label': 'Dashboard', 'url': '/dashboard'},
        {'label': 'Configurações', 'url': None},
    ]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Usar service para agrupar configurações
        context['grouped_configs'] = get_configs_grouped_by_category()
        return context


class ConfigEditView(CanManageConfigs, FormMessageMixin, StaffPageMixin, UpdateView):
    """
    View de edição de configuração.
    
    Camadas:
    - Apresentação: Esta view
    - Permissão: CanManageConfigs
    - Validação: SystemConfigForm
    - Serviço: update_config (para lógica de negócio)
    - Mensagens: FormMessageMixin
    """
    model = SystemConfig
    form_class = SystemConfigForm
    template_name = 'rules/config_edit.html'
    success_url = reverse_lazy('config-list')
    
    page_title = 'Editar Configuração'
    success_message = 'Configuração atualizada com sucesso.'
    
    def get_breadcrumbs(self):
        return [
            {'label': 'Dashboard', 'url': '/dashboard'},
            {'label': 'Configurações', 'url': reverse_lazy('config-list')},
            {'label': 'Editar', 'url': None},
        ]
    
    def form_valid(self, form):
        # Atualizar updated_by
        form.instance.updated_by = self.request.user
        return super().form_valid(form)
