"""
Views refatoradas do app messaging usando arquitetura em camadas.

Este módulo demonstra o padrão de views enxutas com separação de responsabilidades.
"""
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DetailView

from apps.core.views import StaffPageMixin, FormMessageMixin
from apps.core.messages import Messages
from .models import MessageTemplate
from .forms import MessageTemplateForm
from .permissions import CanManageTemplates
from .selectors import get_active_templates, get_template_by_type_and_channel
from .services.template_service import render_template, validate_template_syntax


class TemplateListView(CanManageTemplates, StaffPageMixin, ListView):
    """
    View de listagem de templates de mensagens.
    
    Camadas:
    - Apresentação: Esta view
    - Permissão: CanManageTemplates
    - Consulta: get_active_templates (selector)
    """
    model = MessageTemplate
    template_name = 'messaging/template_list.html'
    context_object_name = 'templates'
    paginate_by = 20
    
    page_title = 'Templates de Mensagens'
    page_subtitle = 'Gerencie os templates de notificações'
    
    breadcrumbs = [
        {'label': 'Dashboard', 'url': '/dashboard'},
        {'label': 'Templates', 'url': None},
    ]
    
    def get_queryset(self):
        qs = super().get_queryset()
        
        # Filtros opcionais
        template_type = self.request.GET.get('type')
        if template_type:
            qs = qs.filter(template_type=template_type)
        
        channel = self.request.GET.get('channel')
        if channel:
            qs = qs.filter(channel=channel)
        
        return qs.order_by('-updated_at')


class TemplateCreateView(CanManageTemplates, FormMessageMixin, StaffPageMixin, CreateView):
    """
    View de criação de template.
    
    Camadas:
    - Apresentação: Esta view
    - Permissão: CanManageTemplates
    - Validação: MessageTemplateForm
    - Serviço: validate_template_syntax
    - Mensagens: FormMessageMixin
    """
    model = MessageTemplate
    form_class = MessageTemplateForm
    template_name = 'messaging/template_form.html'
    success_url = reverse_lazy('template-list')
    
    page_title = 'Novo Template'
    success_message = 'Template criado com sucesso.'
    
    breadcrumbs = [
        {'label': 'Dashboard', 'url': '/dashboard'},
        {'label': 'Templates', 'url': reverse_lazy('template-list')},
        {'label': 'Novo', 'url': None},
    ]
    
    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        return super().form_valid(form)


class TemplateUpdateView(CanManageTemplates, FormMessageMixin, StaffPageMixin, UpdateView):
    """
    View de edição de template.
    
    Camadas:
    - Apresentação: Esta view
    - Permissão: CanManageTemplates
    - Validação: MessageTemplateForm
    - Mensagens: FormMessageMixin
    """
    model = MessageTemplate
    form_class = MessageTemplateForm
    template_name = 'messaging/template_form.html'
    success_url = reverse_lazy('template-list')
    
    page_title = 'Editar Template'
    success_message = 'Template atualizado com sucesso.'
    
    def get_breadcrumbs(self):
        return [
            {'label': 'Dashboard', 'url': '/dashboard'},
            {'label': 'Templates', 'url': reverse_lazy('template-list')},
            {'label': 'Editar', 'url': None},
        ]
    
    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        return super().form_valid(form)


class TemplatePreviewView(CanManageTemplates, StaffPageMixin, DetailView):
    """
    View de preview de template.
    
    Camadas:
    - Apresentação: Esta view
    - Permissão: CanManageTemplates
    - Serviço: render_template (para renderizar com contexto de exemplo)
    """
    model = MessageTemplate
    template_name = 'messaging/template_preview.html'
    
    page_title = 'Preview de Template'
    
    def get_breadcrumbs(self):
        return [
            {'label': 'Dashboard', 'url': '/dashboard'},
            {'label': 'Templates', 'url': reverse_lazy('template-list')},
            {'label': 'Preview', 'url': None},
        ]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Contexto de exemplo para preview
        sample_context = {
            'nome_agente': 'João Silva',
            'cd_operador': '12345',
            'tempo_pausa': '45 minutos',
            'data': '18/03/2026',
        }
        
        # Renderizar template com contexto de exemplo
        rendered = render_template(self.object, sample_context)
        
        context['rendered_subject'] = rendered['subject']
        context['rendered_body'] = rendered['body']
        context['sample_context'] = sample_context
        
        return context
