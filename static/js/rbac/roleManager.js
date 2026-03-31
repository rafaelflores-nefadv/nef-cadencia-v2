/**
 * Role Manager - Gerenciamento de Roles e Permissões
 * 
 * Responsabilidades:
 * - Definir roles e permissões
 * - Verificar permissões do usuário
 * - Controlar UI baseado em role
 */

// Roles disponíveis
export const Roles = {
  ADMIN: 'admin',
  MANAGER: 'manager',
  ANALYST: 'analyst',
  VIEWER: 'viewer'
};

// Permissões disponíveis
export const Permissions = {
  // Workspace
  WORKSPACE_VIEW: 'workspace.view',
  WORKSPACE_EDIT: 'workspace.edit',
  WORKSPACE_DELETE: 'workspace.delete',
  WORKSPACE_MANAGE_MEMBERS: 'workspace.manage_members',
  WORKSPACE_MANAGE_SETTINGS: 'workspace.manage_settings',
  
  // Agents
  AGENT_VIEW: 'agent.view',
  AGENT_CREATE: 'agent.create',
  AGENT_EDIT: 'agent.edit',
  AGENT_DELETE: 'agent.delete',
  AGENT_EXECUTE: 'agent.execute',
  
  // Rules
  RULE_VIEW: 'rule.view',
  RULE_CREATE: 'rule.create',
  RULE_EDIT: 'rule.edit',
  RULE_DELETE: 'rule.delete',
  
  // Reports
  REPORT_VIEW: 'report.view',
  REPORT_CREATE: 'report.create',
  REPORT_EDIT: 'report.edit',
  REPORT_DELETE: 'report.delete',
  REPORT_EXPORT: 'report.export',
  
  // Integrations
  INTEGRATION_VIEW: 'integration.view',
  INTEGRATION_CREATE: 'integration.create',
  INTEGRATION_EDIT: 'integration.edit',
  INTEGRATION_DELETE: 'integration.delete'
};

// Mapeamento de roles para permissões
const ROLE_PERMISSIONS = {
  [Roles.ADMIN]: [
    // Admin tem todas as permissões
    Permissions.WORKSPACE_VIEW,
    Permissions.WORKSPACE_EDIT,
    Permissions.WORKSPACE_DELETE,
    Permissions.WORKSPACE_MANAGE_MEMBERS,
    Permissions.WORKSPACE_MANAGE_SETTINGS,
    Permissions.AGENT_VIEW,
    Permissions.AGENT_CREATE,
    Permissions.AGENT_EDIT,
    Permissions.AGENT_DELETE,
    Permissions.AGENT_EXECUTE,
    Permissions.RULE_VIEW,
    Permissions.RULE_CREATE,
    Permissions.RULE_EDIT,
    Permissions.RULE_DELETE,
    Permissions.REPORT_VIEW,
    Permissions.REPORT_CREATE,
    Permissions.REPORT_EDIT,
    Permissions.REPORT_DELETE,
    Permissions.REPORT_EXPORT,
    Permissions.INTEGRATION_VIEW,
    Permissions.INTEGRATION_CREATE,
    Permissions.INTEGRATION_EDIT,
    Permissions.INTEGRATION_DELETE
  ],
  
  [Roles.MANAGER]: [
    // Manager pode gerenciar mas não deletar workspace
    Permissions.WORKSPACE_VIEW,
    Permissions.WORKSPACE_EDIT,
    Permissions.WORKSPACE_MANAGE_MEMBERS,
    Permissions.AGENT_VIEW,
    Permissions.AGENT_CREATE,
    Permissions.AGENT_EDIT,
    Permissions.AGENT_DELETE,
    Permissions.AGENT_EXECUTE,
    Permissions.RULE_VIEW,
    Permissions.RULE_CREATE,
    Permissions.RULE_EDIT,
    Permissions.RULE_DELETE,
    Permissions.REPORT_VIEW,
    Permissions.REPORT_CREATE,
    Permissions.REPORT_EDIT,
    Permissions.REPORT_DELETE,
    Permissions.REPORT_EXPORT,
    Permissions.INTEGRATION_VIEW,
    Permissions.INTEGRATION_CREATE,
    Permissions.INTEGRATION_EDIT,
    Permissions.INTEGRATION_DELETE
  ],
  
  [Roles.ANALYST]: [
    // Analyst pode criar e editar mas não deletar
    Permissions.WORKSPACE_VIEW,
    Permissions.AGENT_VIEW,
    Permissions.AGENT_CREATE,
    Permissions.AGENT_EDIT,
    Permissions.AGENT_EXECUTE,
    Permissions.RULE_VIEW,
    Permissions.RULE_CREATE,
    Permissions.RULE_EDIT,
    Permissions.REPORT_VIEW,
    Permissions.REPORT_CREATE,
    Permissions.REPORT_EDIT,
    Permissions.REPORT_EXPORT,
    Permissions.INTEGRATION_VIEW
  ],
  
  [Roles.VIEWER]: [
    // Viewer apenas visualiza
    Permissions.WORKSPACE_VIEW,
    Permissions.AGENT_VIEW,
    Permissions.AGENT_EXECUTE,
    Permissions.RULE_VIEW,
    Permissions.REPORT_VIEW,
    Permissions.INTEGRATION_VIEW
  ]
};

// Níveis hierárquicos dos roles
const ROLE_LEVELS = {
  [Roles.ADMIN]: 4,
  [Roles.MANAGER]: 3,
  [Roles.ANALYST]: 2,
  [Roles.VIEWER]: 1
};

/**
 * Gerenciador de Roles e Permissões
 */
class RoleManager {
  /**
   * Obter permissões de um role
   */
  static getRolePermissions(role) {
    return ROLE_PERMISSIONS[role] || [];
  }
  
  /**
   * Verificar se role tem permissão específica
   */
  static hasPermission(role, permission) {
    const permissions = this.getRolePermissions(role);
    return permissions.includes(permission);
  }
  
  /**
   * Verificar se role tem pelo menos uma das permissões
   */
  static hasAnyPermission(role, permissions) {
    return permissions.some(permission => this.hasPermission(role, permission));
  }
  
  /**
   * Verificar se role tem todas as permissões
   */
  static hasAllPermissions(role, permissions) {
    return permissions.every(permission => this.hasPermission(role, permission));
  }
  
  /**
   * Obter nível hierárquico do role
   */
  static getRoleLevel(role) {
    return ROLE_LEVELS[role] || 0;
  }
  
  /**
   * Verificar se role1 é superior a role2
   */
  static isHigherRole(role1, role2) {
    return this.getRoleLevel(role1) > this.getRoleLevel(role2);
  }
  
  /**
   * Verificar se manager pode gerenciar target
   */
  static canManageRole(managerRole, targetRole) {
    return this.isHigherRole(managerRole, targetRole);
  }
  
  /**
   * Obter role do workspace ativo
   */
  static getCurrentRole() {
    const workspace = this.getCurrentWorkspace();
    return workspace?.role || null;
  }
  
  /**
   * Obter workspace ativo do storage
   */
  static getCurrentWorkspace() {
    try {
      const workspaceStr = localStorage.getItem('nef_active_workspace');
      return workspaceStr ? JSON.parse(workspaceStr) : null;
    } catch (error) {
      console.error('Error getting current workspace:', error);
      return null;
    }
  }
  
  /**
   * Verificar se usuário atual tem permissão
   */
  static currentUserHasPermission(permission) {
    const role = this.getCurrentRole();
    return role ? this.hasPermission(role, permission) : false;
  }
  
  /**
   * Verificar se usuário atual é admin
   */
  static isCurrentUserAdmin() {
    return this.getCurrentRole() === Roles.ADMIN;
  }
  
  /**
   * Verificar se usuário atual é manager ou superior
   */
  static isCurrentUserManager() {
    const role = this.getCurrentRole();
    return role && this.getRoleLevel(role) >= ROLE_LEVELS[Roles.MANAGER];
  }
  
  /**
   * Verificar se usuário atual é analyst ou superior
   */
  static isCurrentUserAnalyst() {
    const role = this.getCurrentRole();
    return role && this.getRoleLevel(role) >= ROLE_LEVELS[Roles.ANALYST];
  }
  
  /**
   * Obter label do role
   */
  static getRoleLabel(role) {
    const labels = {
      [Roles.ADMIN]: 'Administrador',
      [Roles.MANAGER]: 'Gerente',
      [Roles.ANALYST]: 'Analista',
      [Roles.VIEWER]: 'Visualizador'
    };
    return labels[role] || role;
  }
  
  /**
   * Obter descrição do role
   */
  static getRoleDescription(role) {
    const descriptions = {
      [Roles.ADMIN]: 'Acesso total ao workspace',
      [Roles.MANAGER]: 'Pode gerenciar recursos e membros',
      [Roles.ANALYST]: 'Pode criar e editar recursos',
      [Roles.VIEWER]: 'Apenas visualização'
    };
    return descriptions[role] || '';
  }
  
  /**
   * Obter lista de roles disponíveis
   */
  static getAvailableRoles() {
    return [
      {
        value: Roles.ADMIN,
        label: this.getRoleLabel(Roles.ADMIN),
        description: this.getRoleDescription(Roles.ADMIN),
        level: ROLE_LEVELS[Roles.ADMIN]
      },
      {
        value: Roles.MANAGER,
        label: this.getRoleLabel(Roles.MANAGER),
        description: this.getRoleDescription(Roles.MANAGER),
        level: ROLE_LEVELS[Roles.MANAGER]
      },
      {
        value: Roles.ANALYST,
        label: this.getRoleLabel(Roles.ANALYST),
        description: this.getRoleDescription(Roles.ANALYST),
        level: ROLE_LEVELS[Roles.ANALYST]
      },
      {
        value: Roles.VIEWER,
        label: this.getRoleLabel(Roles.VIEWER),
        description: this.getRoleDescription(Roles.VIEWER),
        level: ROLE_LEVELS[Roles.VIEWER]
      }
    ];
  }
  
  /**
   * Controlar visibilidade de elemento baseado em permissão
   */
  static controlElementVisibility(element, permission) {
    if (!element) return;
    
    const hasPermission = this.currentUserHasPermission(permission);
    element.style.display = hasPermission ? '' : 'none';
  }
  
  /**
   * Controlar estado de elemento baseado em permissão
   */
  static controlElementState(element, permission) {
    if (!element) return;
    
    const hasPermission = this.currentUserHasPermission(permission);
    element.disabled = !hasPermission;
    
    if (!hasPermission) {
      element.title = 'Você não tem permissão para esta ação';
      element.classList.add('disabled');
    }
  }
  
  /**
   * Inicializar controles de UI baseados em role
   */
  static initRoleBasedUI() {
    // Controlar elementos com data-permission
    document.querySelectorAll('[data-permission]').forEach(element => {
      const permission = element.dataset.permission;
      this.controlElementVisibility(element, permission);
    });
    
    // Controlar elementos com data-permission-disable
    document.querySelectorAll('[data-permission-disable]').forEach(element => {
      const permission = element.dataset.permissionDisable;
      this.controlElementState(element, permission);
    });
    
    // Controlar elementos com data-role
    document.querySelectorAll('[data-role]').forEach(element => {
      const requiredRole = element.dataset.role;
      const currentRole = this.getCurrentRole();
      const hasRole = currentRole && this.getRoleLevel(currentRole) >= this.getRoleLevel(requiredRole);
      element.style.display = hasRole ? '' : 'none';
    });
    
    console.log('RoleManager: UI initialized for role', this.getCurrentRole());
  }
}

// Exportar
export { RoleManager };

// Tornar disponível globalmente
window.RoleManager = RoleManager;
