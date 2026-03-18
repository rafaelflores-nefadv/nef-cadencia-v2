"""
Views para páginas filhas de Configurações.

Este módulo contém views específicas para cada seção de configurações,
permitindo navegação detalhada e gerenciamento granular.
"""
from django.views.generic import TemplateView
from django.urls import reverse_lazy

from apps.core.views import StaffPageMixin
from apps.core.selectors_settings import (
    get_system_configs_stats,
    get_integrations_stats,
    get_message_templates_stats,
    get_pause_classification_stats,
    get_assistant_stats,
    get_users_stats,
    get_operational_rules_stats,
    get_recent_config_changes,
)


class SettingsGeneralView(StaffPageMixin, TemplateView):
    """
    Página de configurações gerais do sistema.
    
    Exibe todas as configurações do sistema com opções de filtro e edição.
    """
    template_name = 'core/settings/general.html'
    
    page_title = 'Configurações Gerais'
    page_subtitle = 'Gerencie as configurações do sistema'
    
    def get_breadcrumbs(self):
        return [
            {'label': 'Dashboard', 'url': '/dashboard'},
            {'label': 'Configurações', 'url': reverse_lazy('settings-hub')},
            {'label': 'Gerais', 'url': None},
        ]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Estatísticas
        context['stats'] = get_system_configs_stats()
        
        # Alterações recentes
        context['recent_changes'] = get_recent_config_changes(limit=10)
        
        return context


class SettingsRulesView(StaffPageMixin, TemplateView):
    """
    Página de regras operacionais.
    
    Exibe e permite editar regras operacionais como thresholds e limites.
    """
    template_name = 'core/settings/rules.html'
    
    page_title = 'Regras Operacionais'
    page_subtitle = 'Configure thresholds, limites e alertas'
    
    def get_breadcrumbs(self):
        return [
            {'label': 'Dashboard', 'url': '/dashboard'},
            {'label': 'Configurações', 'url': reverse_lazy('settings-hub')},
            {'label': 'Regras', 'url': None},
        ]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Estatísticas
        context['stats'] = get_operational_rules_stats()
        
        return context


class SettingsIntegrationsView(StaffPageMixin, TemplateView):
    """
    Página de integrações.
    
    Exibe status e permite gerenciar integrações externas.
    """
    template_name = 'core/settings/integrations.html'
    
    page_title = 'Integrações'
    page_subtitle = 'Gerencie integrações com serviços externos'
    
    def get_breadcrumbs(self):
        return [
            {'label': 'Dashboard', 'url': '/dashboard'},
            {'label': 'Configurações', 'url': reverse_lazy('settings-hub')},
            {'label': 'Integrações', 'url': None},
        ]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Estatísticas
        context['stats'] = get_integrations_stats()
        
        return context


class SettingsTemplatesView(StaffPageMixin, TemplateView):
    """
    Página de templates de mensagens.
    
    Exibe e permite gerenciar templates de notificações.
    """
    template_name = 'core/settings/templates.html'
    
    page_title = 'Templates de Mensagens'
    page_subtitle = 'Gerencie templates de email, SMS e notificações'
    
    def get_breadcrumbs(self):
        return [
            {'label': 'Dashboard', 'url': '/dashboard'},
            {'label': 'Configurações', 'url': reverse_lazy('settings-hub')},
            {'label': 'Templates', 'url': None},
        ]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Estatísticas
        context['stats'] = get_message_templates_stats()
        
        return context


class SettingsAssistantView(StaffPageMixin, TemplateView):
    """
    Página de configurações do assistente IA.
    
    Exibe e permite configurar o assistente Eustácio.
    """
    template_name = 'core/settings/assistant.html'
    
    page_title = 'Assistente IA'
    page_subtitle = 'Configure o assistente Eustácio'
    
    def get_breadcrumbs(self):
        return [
            {'label': 'Dashboard', 'url': '/dashboard'},
            {'label': 'Configurações', 'url': reverse_lazy('settings-hub')},
            {'label': 'Assistente', 'url': None},
        ]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Estatísticas
        context['stats'] = get_assistant_stats()
        
        return context


class SettingsPauseClassificationView(StaffPageMixin, TemplateView):
    """
    Página de classificação de pausas.
    
    Exibe e permite gerenciar classificações de pausas operacionais.
    """
    template_name = 'core/settings/pause_classification.html'
    
    page_title = 'Classificação de Pausas'
    page_subtitle = 'Gerencie categorias e regras de pausas'
    
    def get_breadcrumbs(self):
        return [
            {'label': 'Dashboard', 'url': '/dashboard'},
            {'label': 'Configurações', 'url': reverse_lazy('settings-hub')},
            {'label': 'Pausas', 'url': None},
        ]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Estatísticas
        context['stats'] = get_pause_classification_stats()
        
        return context


class SettingsUsersView(StaffPageMixin, TemplateView):
    """
    Página de gestão de usuários.
    
    Exibe e permite gerenciar usuários e agentes do sistema.
    """
    template_name = 'core/settings/users.html'
    
    page_title = 'Gestão de Usuários'
    page_subtitle = 'Gerencie usuários, perfis e agentes'
    
    def get_breadcrumbs(self):
        return [
            {'label': 'Dashboard', 'url': '/dashboard'},
            {'label': 'Configurações', 'url': reverse_lazy('settings-hub')},
            {'label': 'Usuários', 'url': None},
        ]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Estatísticas
        context['stats'] = get_users_stats()
        
        return context
