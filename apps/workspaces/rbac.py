"""
RBAC - Role-Based Access Control

Sistema de controle de acesso baseado em roles dentro de workspaces.

Roles disponíveis:
- admin: Administrador total do workspace
- manager: Gerente com permissões de gestão
- analyst: Analista com permissões de edição
- viewer: Visualizador apenas leitura
"""

from enum import Enum
from typing import List, Set


class Role(str, Enum):
    """Roles disponíveis no sistema."""
    ADMIN = 'admin'
    MANAGER = 'manager'
    ANALYST = 'analyst'
    VIEWER = 'viewer'


class Permission(str, Enum):
    """Permissões disponíveis no sistema."""
    
    # Workspace
    WORKSPACE_VIEW = 'workspace.view'
    WORKSPACE_EDIT = 'workspace.edit'
    WORKSPACE_DELETE = 'workspace.delete'
    WORKSPACE_MANAGE_MEMBERS = 'workspace.manage_members'
    WORKSPACE_MANAGE_SETTINGS = 'workspace.manage_settings'
    
    # Agents
    AGENT_VIEW = 'agent.view'
    AGENT_CREATE = 'agent.create'
    AGENT_EDIT = 'agent.edit'
    AGENT_DELETE = 'agent.delete'
    AGENT_EXECUTE = 'agent.execute'
    
    # Rules
    RULE_VIEW = 'rule.view'
    RULE_CREATE = 'rule.create'
    RULE_EDIT = 'rule.edit'
    RULE_DELETE = 'rule.delete'
    
    # Reports
    REPORT_VIEW = 'report.view'
    REPORT_CREATE = 'report.create'
    REPORT_EDIT = 'report.edit'
    REPORT_DELETE = 'report.delete'
    REPORT_EXPORT = 'report.export'
    
    # Integrations
    INTEGRATION_VIEW = 'integration.view'
    INTEGRATION_CREATE = 'integration.create'
    INTEGRATION_EDIT = 'integration.edit'
    INTEGRATION_DELETE = 'integration.delete'


# Mapeamento de roles para permissões
ROLE_PERMISSIONS: dict[Role, Set[Permission]] = {
    Role.ADMIN: {
        # Admin tem todas as permissões
        Permission.WORKSPACE_VIEW,
        Permission.WORKSPACE_EDIT,
        Permission.WORKSPACE_DELETE,
        Permission.WORKSPACE_MANAGE_MEMBERS,
        Permission.WORKSPACE_MANAGE_SETTINGS,
        Permission.AGENT_VIEW,
        Permission.AGENT_CREATE,
        Permission.AGENT_EDIT,
        Permission.AGENT_DELETE,
        Permission.AGENT_EXECUTE,
        Permission.RULE_VIEW,
        Permission.RULE_CREATE,
        Permission.RULE_EDIT,
        Permission.RULE_DELETE,
        Permission.REPORT_VIEW,
        Permission.REPORT_CREATE,
        Permission.REPORT_EDIT,
        Permission.REPORT_DELETE,
        Permission.REPORT_EXPORT,
        Permission.INTEGRATION_VIEW,
        Permission.INTEGRATION_CREATE,
        Permission.INTEGRATION_EDIT,
        Permission.INTEGRATION_DELETE,
    },
    
    Role.MANAGER: {
        # Manager pode gerenciar mas não deletar workspace
        Permission.WORKSPACE_VIEW,
        Permission.WORKSPACE_EDIT,
        Permission.WORKSPACE_MANAGE_MEMBERS,
        Permission.AGENT_VIEW,
        Permission.AGENT_CREATE,
        Permission.AGENT_EDIT,
        Permission.AGENT_DELETE,
        Permission.AGENT_EXECUTE,
        Permission.RULE_VIEW,
        Permission.RULE_CREATE,
        Permission.RULE_EDIT,
        Permission.RULE_DELETE,
        Permission.REPORT_VIEW,
        Permission.REPORT_CREATE,
        Permission.REPORT_EDIT,
        Permission.REPORT_DELETE,
        Permission.REPORT_EXPORT,
        Permission.INTEGRATION_VIEW,
        Permission.INTEGRATION_CREATE,
        Permission.INTEGRATION_EDIT,
        Permission.INTEGRATION_DELETE,
    },
    
    Role.ANALYST: {
        # Analyst pode criar e editar mas não deletar
        Permission.WORKSPACE_VIEW,
        Permission.AGENT_VIEW,
        Permission.AGENT_CREATE,
        Permission.AGENT_EDIT,
        Permission.AGENT_EXECUTE,
        Permission.RULE_VIEW,
        Permission.RULE_CREATE,
        Permission.RULE_EDIT,
        Permission.REPORT_VIEW,
        Permission.REPORT_CREATE,
        Permission.REPORT_EDIT,
        Permission.REPORT_EXPORT,
        Permission.INTEGRATION_VIEW,
    },
    
    Role.VIEWER: {
        # Viewer apenas visualiza
        Permission.WORKSPACE_VIEW,
        Permission.AGENT_VIEW,
        Permission.AGENT_EXECUTE,
        Permission.RULE_VIEW,
        Permission.REPORT_VIEW,
        Permission.INTEGRATION_VIEW,
    },
}


class RBACManager:
    """Gerenciador de RBAC."""
    
    @staticmethod
    def get_role_permissions(role: str) -> Set[Permission]:
        """
        Retorna permissões de um role.
        
        Args:
            role: Role do usuário
        
        Returns:
            Set de permissões
        """
        try:
            role_enum = Role(role)
            return ROLE_PERMISSIONS.get(role_enum, set())
        except ValueError:
            return set()
    
    @staticmethod
    def has_permission(role: str, permission: str) -> bool:
        """
        Verifica se role tem permissão específica.
        
        Args:
            role: Role do usuário
            permission: Permissão a verificar
        
        Returns:
            bool
        """
        try:
            role_enum = Role(role)
            permission_enum = Permission(permission)
            permissions = ROLE_PERMISSIONS.get(role_enum, set())
            return permission_enum in permissions
        except ValueError:
            return False
    
    @staticmethod
    def has_any_permission(role: str, permissions: List[str]) -> bool:
        """
        Verifica se role tem pelo menos uma das permissões.
        
        Args:
            role: Role do usuário
            permissions: Lista de permissões
        
        Returns:
            bool
        """
        for permission in permissions:
            if RBACManager.has_permission(role, permission):
                return True
        return False
    
    @staticmethod
    def has_all_permissions(role: str, permissions: List[str]) -> bool:
        """
        Verifica se role tem todas as permissões.
        
        Args:
            role: Role do usuário
            permissions: Lista de permissões
        
        Returns:
            bool
        """
        for permission in permissions:
            if not RBACManager.has_permission(role, permission):
                return False
        return True
    
    @staticmethod
    def get_role_level(role: str) -> int:
        """
        Retorna nível hierárquico do role.
        
        Args:
            role: Role do usuário
        
        Returns:
            int (maior = mais permissões)
        """
        role_levels = {
            Role.ADMIN: 4,
            Role.MANAGER: 3,
            Role.ANALYST: 2,
            Role.VIEWER: 1,
        }
        
        try:
            role_enum = Role(role)
            return role_levels.get(role_enum, 0)
        except ValueError:
            return 0
    
    @staticmethod
    def is_higher_role(role1: str, role2: str) -> bool:
        """
        Verifica se role1 é superior a role2.
        
        Args:
            role1: Primeiro role
            role2: Segundo role
        
        Returns:
            bool
        """
        return RBACManager.get_role_level(role1) > RBACManager.get_role_level(role2)
    
    @staticmethod
    def can_manage_role(manager_role: str, target_role: str) -> bool:
        """
        Verifica se manager pode gerenciar target.
        
        Regra: Só pode gerenciar roles de nível inferior.
        
        Args:
            manager_role: Role do gerenciador
            target_role: Role alvo
        
        Returns:
            bool
        """
        return RBACManager.is_higher_role(manager_role, target_role)
    
    @staticmethod
    def get_available_roles() -> List[dict]:
        """
        Retorna lista de roles disponíveis.
        
        Returns:
            List de dicts com info dos roles
        """
        return [
            {
                'value': Role.ADMIN.value,
                'label': 'Administrador',
                'description': 'Acesso total ao workspace',
                'level': 4
            },
            {
                'value': Role.MANAGER.value,
                'label': 'Gerente',
                'description': 'Pode gerenciar recursos e membros',
                'level': 3
            },
            {
                'value': Role.ANALYST.value,
                'label': 'Analista',
                'description': 'Pode criar e editar recursos',
                'level': 2
            },
            {
                'value': Role.VIEWER.value,
                'label': 'Visualizador',
                'description': 'Apenas visualização',
                'level': 1
            },
        ]


# Atalhos para verificações comuns
def has_permission(role: str, permission: str) -> bool:
    """Atalho para RBACManager.has_permission"""
    return RBACManager.has_permission(role, permission)


def get_role_permissions(role: str) -> Set[Permission]:
    """Atalho para RBACManager.get_role_permissions"""
    return RBACManager.get_role_permissions(role)


def can_manage_role(manager_role: str, target_role: str) -> bool:
    """Atalho para RBACManager.can_manage_role"""
    return RBACManager.can_manage_role(manager_role, target_role)
