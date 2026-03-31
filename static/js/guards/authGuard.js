/**
 * Auth Guard - Proteção de Rotas
 * 
 * Responsabilidades:
 * - Verificar autenticação antes de acessar rotas protegidas
 * - Redirecionar usuários não autenticados para login
 * - Verificar permissões de workspace
 * - Prevenir acesso não autorizado
 */

import { authContext } from '../context/authContext.js';
import { storage } from '../utils/storage.js';

class AuthGuard {
  /**
   * Verificar se usuário está autenticado
   */
  static isAuthenticated() {
    const token = storage.getAuthToken();
    const user = storage.getUser();
    
    return !!(token && user);
  }

  /**
   * Verificar se usuário tem workspace selecionado
   */
  static hasWorkspace() {
    const workspace = storage.getActiveWorkspace();
    return !!workspace;
  }

  /**
   * Redirecionar para login
   */
  static redirectToLogin(returnUrl = null) {
    const currentUrl = returnUrl || window.location.pathname + window.location.search;
    
    // Salvar URL de retorno
    if (currentUrl !== '/login') {
      storage.set('return_url', currentUrl);
    }
    
    window.location.href = '/login';
  }

  /**
   * Redirecionar para seleção de workspace
   */
  static redirectToWorkspaceSelection() {
    window.location.href = '/select-workspace';
  }

  /**
   * Redirecionar para dashboard
   */
  static redirectToDashboard() {
    window.location.href = '/dashboard';
  }

  /**
   * Obter URL de retorno salva
   */
  static getReturnUrl() {
    const returnUrl = storage.get('return_url');
    storage.remove('return_url');
    return returnUrl || '/dashboard';
  }

  /**
   * Proteger rota - requer autenticação
   * 
   * @param {Object} options - Opções de proteção
   * @param {boolean} options.requireAuth - Requer autenticação (default: true)
   * @param {boolean} options.requireWorkspace - Requer workspace selecionado (default: false)
   * @param {string} options.redirectTo - URL de redirecionamento customizado
   * @returns {boolean} - true se acesso permitido, false caso contrário
   */
  static protect(options = {}) {
    const {
      requireAuth = true,
      requireWorkspace = false,
      redirectTo = null
    } = options;

    // Verificar autenticação
    if (requireAuth && !this.isAuthenticated()) {
      console.warn('AuthGuard: Usuário não autenticado, redirecionando para login');
      this.redirectToLogin(redirectTo);
      return false;
    }

    // Verificar workspace
    if (requireWorkspace && !this.hasWorkspace()) {
      console.warn('AuthGuard: Workspace não selecionado, redirecionando para seleção');
      this.redirectToWorkspaceSelection();
      return false;
    }

    return true;
  }

  /**
   * Proteger página inteira
   * Deve ser chamado no início do script da página
   */
  static protectPage(options = {}) {
    // Executar proteção
    const allowed = this.protect(options);
    
    if (!allowed) {
      // Prevenir execução do resto do script
      throw new Error('Access denied');
    }
    
    return true;
  }

  /**
   * Verificar se usuário pode acessar rota pública
   * (ex: login, registro - não deve acessar se já autenticado)
   */
  static isPublicRoute() {
    const publicRoutes = ['/login', '/register', '/forgot-password', '/reset-password'];
    const currentPath = window.location.pathname;
    
    return publicRoutes.some(route => currentPath.startsWith(route));
  }

  /**
   * Redirecionar usuário autenticado de rotas públicas
   */
  static redirectAuthenticatedUser() {
    if (this.isAuthenticated() && this.isPublicRoute()) {
      console.log('AuthGuard: Usuário já autenticado, redirecionando para dashboard');
      this.redirectToDashboard();
      return true;
    }
    return false;
  }

  /**
   * Verificar permissão de role
   * 
   * @param {string} requiredRole - Role necessário (admin, member, viewer)
   * @returns {boolean}
   */
  static hasRole(requiredRole) {
    const workspace = storage.getActiveWorkspace();
    
    if (!workspace || !workspace.role) {
      return false;
    }

    const roleHierarchy = {
      'admin': 3,
      'member': 2,
      'viewer': 1
    };

    const userRoleLevel = roleHierarchy[workspace.role] || 0;
    const requiredRoleLevel = roleHierarchy[requiredRole] || 0;

    return userRoleLevel >= requiredRoleLevel;
  }

  /**
   * Proteger ação que requer role específico
   */
  static requireRole(requiredRole, errorMessage = null) {
    if (!this.hasRole(requiredRole)) {
      const message = errorMessage || `Esta ação requer permissão de ${requiredRole}`;
      console.warn('AuthGuard:', message);
      alert(message);
      return false;
    }
    return true;
  }

  /**
   * Verificar se é admin
   */
  static isAdmin() {
    return this.hasRole('admin');
  }

  /**
   * Verificar se pode editar
   */
  static canEdit() {
    return this.hasRole('member');
  }

  /**
   * Verificar se pode apenas visualizar
   */
  static isViewer() {
    const workspace = storage.getActiveWorkspace();
    return workspace && workspace.role === 'viewer';
  }

  /**
   * Inicializar guard global
   * Deve ser chamado no app-init.js
   */
  static init() {
    // Escutar mudanças de autenticação
    window.addEventListener('auth:state-change', (event) => {
      const { isAuthenticated } = event.detail;
      
      // Se deslogou, redirecionar para login
      if (!isAuthenticated && !this.isPublicRoute()) {
        this.redirectToLogin();
      }
    });

    // Escutar mudanças de workspace
    window.addEventListener('workspace:changed', (event) => {
      console.log('AuthGuard: Workspace changed', event.detail);
    });

    console.log('AuthGuard: Initialized');
  }
}

// Exportar
export { AuthGuard };

// Tornar disponível globalmente
window.AuthGuard = AuthGuard;
