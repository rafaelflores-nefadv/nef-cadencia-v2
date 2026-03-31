"""
Middleware para gerenciar workspace ativo na sessão.

Responsabilidade:
- Anexar workspace ativo ao request
- Validar acesso ao workspace
- Filtrar dados automaticamente por workspace
"""
from django.shortcuts import redirect
from django.urls import reverse
from .models import Workspace
from . import selectors


class WorkspaceMiddleware:
    """
    Middleware para gerenciar workspace ativo.
    
    Anexa o workspace ativo ao request baseado na sessão.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # URLs que não requerem workspace
        self.exempt_urls = [
            '/login',
            '/logout',
            '/select-workspace',
            '/admin',
            '/static',
            '/media',
        ]
    
    def __call__(self, request):
        # Processar request
        self._attach_workspace(request)
        
        # Validar workspace para URLs protegidas
        if request.user.is_authenticated and self._requires_workspace(request):
            if not hasattr(request, 'workspace') or request.workspace is None:
                # Redirecionar para seleção de workspace
                return redirect('select-workspace')
        
        response = self.get_response(request)
        return response
    
    def _attach_workspace(self, request):
        """Anexa workspace ativo ao request."""
        request.workspace = None
        
        if not request.user.is_authenticated:
            return
        
        # Obter workspace_id da sessão
        workspace_id = request.session.get('workspace_id')
        
        if workspace_id:
            # Buscar workspace
            workspace = selectors.get_workspace_by_id(workspace_id)
            
            if workspace:
                # Verificar se usuário tem acesso
                if selectors.user_has_workspace_access(request.user, workspace):
                    request.workspace = workspace
                    
                    # Atualizar default_workspace do usuário
                    if request.user.default_workspace_id != workspace_id:
                        request.user.set_default_workspace(workspace)
                else:
                    # Usuário não tem acesso, limpar sessão
                    del request.session['workspace_id']
        
        # Se não tem workspace na sessão, tentar usar default_workspace
        if not request.workspace and request.user.default_workspace:
            workspace = request.user.default_workspace
            if selectors.user_has_workspace_access(request.user, workspace):
                request.workspace = workspace
                request.session['workspace_id'] = workspace.id
    
    def _requires_workspace(self, request):
        """Verifica se a URL requer workspace."""
        path = request.path
        
        # Verificar URLs isentas
        for exempt_url in self.exempt_urls:
            if path.startswith(exempt_url):
                return False
        
        # Superuser não precisa de workspace
        if request.user.is_superuser:
            return False
        
        return True


class WorkspaceAccessMiddleware:
    """
    Middleware para validar acesso ao workspace.
    
    Garante que usuário só acesse dados do workspace ativo.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        return response
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        """Valida acesso antes de processar view."""
        
        # Apenas para usuários autenticados
        if not request.user.is_authenticated:
            return None
        
        # Superuser tem acesso a tudo
        if request.user.is_superuser:
            return None
        
        # Se tem workspace_id nos kwargs, validar acesso
        workspace_id = view_kwargs.get('workspace_id')
        if workspace_id:
            workspace = selectors.get_workspace_by_id(workspace_id)
            
            if not workspace:
                from django.http import Http404
                raise Http404('Workspace não encontrado')
            
            if not selectors.user_has_workspace_access(request.user, workspace):
                from django.core.exceptions import PermissionDenied
                raise PermissionDenied('Você não tem acesso a este workspace')
        
        return None
