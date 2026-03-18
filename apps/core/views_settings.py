"""
View de Configurações - Hub central de configurações do sistema.

Esta view substitui a navegação para o Django Admin, oferecendo uma
experiência integrada de gerenciamento de configurações.
"""
from django.views.generic import TemplateView

from apps.core.views import StaffPageMixin
from apps.core.services import (
    get_settings_dashboard_data,
    get_settings_health_overview,
    get_settings_alerts,
)


class SettingsHubView(StaffPageMixin, TemplateView):
    """
    Hub central de configurações do sistema.
    
    Exibe cards com resumo de cada área de configuração e ações rápidas.
    Usa services para buscar dados reais do sistema.
    """
    template_name = 'core/settings_hub.html'
    
    page_title = 'Configurações'
    page_subtitle = 'Central de gerenciamento e configurações do sistema'
    
    breadcrumbs = [
        {'label': 'Dashboard', 'url': '/dashboard'},
        {'label': 'Configurações', 'url': None},
    ]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Usar service para buscar todos os dados
        dashboard_data = get_settings_dashboard_data()
        
        # Adicionar dados ao contexto
        context.update(dashboard_data)
        
        # Adicionar visão geral de saúde
        context['health_overview'] = get_settings_health_overview()
        
        # Adicionar alertas
        context['alerts'] = get_settings_alerts()
        
        return context
