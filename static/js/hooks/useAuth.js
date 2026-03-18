/**
 * Hook useAuth
 * 
 * Helper para acessar o contexto de autenticação
 * Similar ao hook useAuth do React
 * 
 * Uso:
 * import { useAuth } from './hooks/useAuth.js';
 * 
 * const auth = useAuth();
 * console.log(auth.user);
 * console.log(auth.isAuthenticated);
 * 
 * auth.onStateChange((state) => {
 *   console.log('Auth state changed:', state);
 * });
 */

import { authContext } from '../context/authContext.js';

/**
 * Hook para acessar contexto de autenticação
 * 
 * @returns {Object} Objeto com estado e métodos de auth
 */
export function useAuth() {
  return {
    // Estado atual
    get state() {
      return authContext.getState();
    },

    // Propriedades individuais
    get user() {
      return authContext.state.user;
    },

    get token() {
      return authContext.state.token;
    },

    get loading() {
      return authContext.state.loading;
    },

    get isAuthenticated() {
      return authContext.state.isAuthenticated;
    },

    get workspace() {
      return authContext.state.workspace;
    },

    // Métodos
    async login(username, password, rememberMe = false) {
      return await authContext.login(username, password, rememberMe);
    },

    async logout() {
      return await authContext.logout();
    },

    selectWorkspace(workspace) {
      return authContext.selectWorkspace(workspace);
    },

    hasPermission(permission) {
      return authContext.hasPermission(permission);
    },

    isStaff() {
      return authContext.isStaff();
    },

    isSuperuser() {
      return authContext.isSuperuser();
    },

    // Observar mudanças de estado
    onStateChange(callback) {
      return authContext.subscribe(callback);
    },

    // Aguardar inicialização
    async waitForInit() {
      return new Promise((resolve) => {
        if (!authContext.state.loading) {
          resolve(authContext.state);
          return;
        }

        const unsubscribe = authContext.subscribe((state) => {
          if (!state.loading) {
            unsubscribe();
            resolve(state);
          }
        });
      });
    }
  };
}

/**
 * Helper para proteger rotas
 * Redireciona para login se não autenticado
 */
export function requireAuth() {
  const auth = useAuth();

  if (!auth.loading && !auth.isAuthenticated) {
    const currentPath = window.location.pathname;
    const loginUrl = `/login?next=${encodeURIComponent(currentPath)}`;
    window.location.href = loginUrl;
    return false;
  }

  return true;
}

/**
 * Helper para proteger rotas de staff
 */
export function requireStaff() {
  const auth = useAuth();

  if (!auth.loading && !auth.isStaff()) {
    window.location.href = '/dashboard';
    return false;
  }

  return true;
}

/**
 * Helper para redirecionar se já autenticado
 */
export function redirectIfAuthenticated(redirectTo = '/dashboard') {
  const auth = useAuth();

  if (!auth.loading && auth.isAuthenticated) {
    window.location.href = redirectTo;
    return true;
  }

  return false;
}
