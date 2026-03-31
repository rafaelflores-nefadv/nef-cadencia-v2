"""
Views base e mixins para páginas do sistema.
"""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.views.generic import TemplateView


class BasePageMixin:
    """
    Mixin base para todas as páginas do sistema.
    
    Adiciona metadados, breadcrumbs e contexto padrão.
    """
    page_title = None
    page_subtitle = None
    breadcrumbs = []
    
    def get_page_title(self):
        """Retorna o título da página."""
        return self.page_title or "NEF Cadência"
    
    def get_page_subtitle(self):
        """Retorna o subtítulo da página."""
        return self.page_subtitle
    
    def get_breadcrumbs(self):
        """
        Retorna lista de breadcrumbs.
        
        Formato: [
            {'label': 'Home', 'url': '/'},
            {'label': 'Dashboard', 'url': '/dashboard'},
            {'label': 'Atual', 'url': None},  # None = página atual
        ]
        """
        return self.breadcrumbs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = self.get_page_title()
        context['page_subtitle'] = self.get_page_subtitle()
        context['breadcrumbs'] = self.get_breadcrumbs()
        return context


class AuthenticatedPageMixin(LoginRequiredMixin, BasePageMixin):
    """
    Mixin para páginas que requerem autenticação.
    
    Combina LoginRequiredMixin com metadados de página.
    """
    login_url = 'login'
    redirect_field_name = 'next'


class StaffPageMixin(UserPassesTestMixin, AuthenticatedPageMixin):
    """
    Mixin para páginas administrativas (requer staff).
    """
    permission_denied_message = 'Você não tem permissão para acessar esta página.'
    
    def test_func(self):
        return self.request.user.is_staff
    
    def handle_no_permission(self):
        messages.error(self.request, self.permission_denied_message)
        return redirect('dashboard-productivity')


class SuperuserPageMixin(UserPassesTestMixin, AuthenticatedPageMixin):
    """
    Mixin para páginas que requerem superusuário.
    """
    permission_denied_message = 'Apenas administradores podem acessar esta página.'
    
    def test_func(self):
        return self.request.user.is_superuser
    
    def handle_no_permission(self):
        messages.error(self.request, self.permission_denied_message)
        return redirect('dashboard-productivity')


class FormMessageMixin:
    """
    Mixin para adicionar mensagens automáticas em forms.
    """
    success_message = None
    error_message = 'Ocorreu um erro ao processar o formulário.'
    
    def get_success_message(self):
        """Retorna mensagem de sucesso."""
        return self.success_message
    
    def form_valid(self, form):
        response = super().form_valid(form)
        success_msg = self.get_success_message()
        if success_msg:
            messages.success(self.request, success_msg)
        return response
    
    def form_invalid(self, form):
        messages.error(self.request, self.error_message)
        return super().form_invalid(form)


class DeleteConfirmMixin:
    """
    Mixin para views de deleção com confirmação.
    """
    delete_success_message = 'Item removido com sucesso.'
    delete_error_message = 'Não foi possível remover o item.'
    
    def delete(self, request, *args, **kwargs):
        try:
            response = super().delete(request, *args, **kwargs)
            messages.success(request, self.delete_success_message)
            return response
        except Exception as e:
            messages.error(request, self.delete_error_message)
            return redirect(self.get_success_url())


class AjaxResponseMixin:
    """
    Mixin para views que respondem JSON em requisições AJAX.
    """
    def is_ajax(self):
        return self.request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    def get_ajax_data(self):
        """Override para retornar dados JSON."""
        return {}
    
    def render_to_response(self, context, **response_kwargs):
        if self.is_ajax():
            from django.http import JsonResponse
            return JsonResponse(self.get_ajax_data())
        return super().render_to_response(context, **response_kwargs)


class SelectWorkspaceView(LoginRequiredMixin, TemplateView):
    """
    View para seleção de workspace em ambiente multi-tenant.
    
    Redireciona automaticamente para o workspace principal.
    """
    login_url = 'login'
    
    def get(self, request, *args, **kwargs):
        return redirect('dashboard-productivity')
