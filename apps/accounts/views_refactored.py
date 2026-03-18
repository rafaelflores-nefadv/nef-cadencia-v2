"""
Views refatoradas do app accounts usando arquitetura em camadas.

Este módulo demonstra o padrão de views enxutas com separação de responsabilidades.
"""
from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import UpdateView, TemplateView

from apps.core.views import AuthenticatedPageMixin, FormMessageMixin
from apps.core.messages import Messages
from .forms import CustomLoginForm, UserProfileForm, CustomPasswordChangeForm
from .permissions import CanEditProfile


class LoginView(DjangoLoginView):
    """
    View de login usando form customizado.
    
    Camadas:
    - Apresentação: Esta view
    - Validação: CustomLoginForm
    """
    template_name = 'accounts/login.html'
    form_class = CustomLoginForm
    redirect_authenticated_user = True
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Login - NEF Cadência'
        return context


class ProfileView(CanEditProfile, FormMessageMixin, AuthenticatedPageMixin, UpdateView):
    """
    View de edição de perfil do usuário.
    
    Camadas:
    - Apresentação: Esta view
    - Permissão: CanEditProfile
    - Validação: UserProfileForm
    - Mensagens: FormMessageMixin
    """
    template_name = 'accounts/profile.html'
    form_class = UserProfileForm
    success_url = reverse_lazy('profile')
    
    page_title = 'Meu Perfil'
    page_subtitle = 'Edite suas informações pessoais'
    success_message = 'Perfil atualizado com sucesso.'
    
    breadcrumbs = [
        {'label': 'Dashboard', 'url': '/dashboard'},
        {'label': 'Meu Perfil', 'url': None},
    ]
    
    def get_object(self, queryset=None):
        """Retorna o usuário atual."""
        return self.request.user


class ChangePasswordView(CanEditProfile, FormMessageMixin, AuthenticatedPageMixin, TemplateView):
    """
    View de mudança de senha.
    
    Camadas:
    - Apresentação: Esta view
    - Permissão: CanEditProfile
    - Validação: CustomPasswordChangeForm
    - Mensagens: FormMessageMixin
    """
    template_name = 'accounts/change_password.html'
    form_class = CustomPasswordChangeForm
    success_url = reverse_lazy('profile')
    
    page_title = 'Alterar Senha'
    page_subtitle = 'Altere sua senha de acesso'
    success_message = 'Senha alterada com sucesso.'
    
    breadcrumbs = [
        {'label': 'Dashboard', 'url': '/dashboard'},
        {'label': 'Meu Perfil', 'url': '/profile'},
        {'label': 'Alterar Senha', 'url': None},
    ]
