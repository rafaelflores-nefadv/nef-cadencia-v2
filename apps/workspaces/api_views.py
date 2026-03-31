"""
API Views para workspaces.

Responsabilidade: Controllers da API REST de workspaces.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from apps.accounts.serializers import WorkspaceSerializer
from . import selectors


class UserWorkspacesAPIView(APIView):
    """
    Endpoint para listar workspaces do usuário.
    
    GET /api/workspaces
    
    Response:
    {
        "success": true,
        "workspaces": [...]
    }
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Listar workspaces do usuário autenticado."""
        user = request.user
        
        # Buscar workspaces
        workspaces = selectors.get_workspaces_for_api(user)
        
        return Response(
            {
                'success': True,
                'workspaces': workspaces
            },
            status=status.HTTP_200_OK
        )


class SelectWorkspaceAPIView(APIView):
    """
    Endpoint para selecionar workspace ativo.
    
    POST /api/workspaces/select
    
    Body:
    {
        "workspace_id": 1
    }
    
    Response:
    {
        "success": true,
        "workspace": {...}
    }
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Selecionar workspace ativo."""
        workspace_id = request.data.get('workspace_id')
        
        if not workspace_id:
            return Response(
                {'error': 'workspace_id é obrigatório'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Buscar workspace
        workspace = selectors.get_workspace_by_id(workspace_id)
        
        if not workspace:
            return Response(
                {'error': 'Workspace não encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Verificar acesso
        if not selectors.user_has_workspace_access(request.user, workspace):
            return Response(
                {'error': 'Você não tem acesso a este workspace'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Salvar na sessão
        request.session['workspace_id'] = workspace.id
        
        # Atualizar default_workspace
        request.user.set_default_workspace(workspace)
        
        # Serializar workspace
        serializer = WorkspaceSerializer(workspace, context={'request': request})
        
        return Response(
            {
                'success': True,
                'workspace': serializer.data
            },
            status=status.HTTP_200_OK
        )
