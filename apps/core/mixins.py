"""
Mixins reutilizáveis para views.
"""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.urls import reverse


class StaffRequiredMixin(UserPassesTestMixin):
    """Mixin que requer usuário staff."""
    
    def test_func(self):
        return self.request.user.is_staff
    
    def handle_no_permission(self):
        messages.error(self.request, 'Você não tem permissão para acessar esta página.')
        return redirect('dashboard-productivity')


class AjaxResponseMixin:
    """Mixin para views que respondem JSON em requisições AJAX."""
    
    def is_ajax(self):
        return self.request.headers.get('X-Requested-With') == 'XMLHttpRequest'


class FormMessageMixin:
    """Mixin que adiciona mensagens de sucesso/erro em forms."""
    
    success_message = None
    error_message = None
    
    def form_valid(self, form):
        if self.success_message:
            messages.success(self.request, self.success_message)
        return super().form_valid(form)
    
    def form_invalid(self, form):
        if self.error_message:
            messages.error(self.request, self.error_message)
        return super().form_invalid(form)
