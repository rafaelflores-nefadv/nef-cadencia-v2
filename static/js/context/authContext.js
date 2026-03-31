/**
 * Contexto Global de AutenticaÃ§Ã£o
 * 
 * ImplementaÃ§Ã£o de contexto similar ao React Context API
 * usando JavaScript Vanilla com padrÃ£o Observer
 * 
 * Responsabilidades:
 * - Gerenciar estado global de autenticaÃ§Ã£o
 * - Controlar user, loading, workspace
 * - Prover mÃ©todos login/logout/selectWorkspace
 * - Notificar componentes sobre mudanÃ§as de estado
 * - Restaurar sessÃ£o ao iniciar aplicaÃ§Ã£o
 */

import { authService } from '../services/authService.js';
import { storage } from '../utils/storage.js';

class AuthContext {
  constructor() {
    // Estado inicial
    this.state = {
      user: null,
      token: null,
      loading: true,
      isAuthenticated: false,
      workspace: null
    };

    // Observers (componentes que escutam mudanÃ§as)
    this.observers = [];

    // Inicializar
    this.init();
  }

  /**
   * Inicializar contexto
   * Restaurar sessÃ£o se existir
   */
  async init() {
    this.setState({ loading: true });

    try {
      // Verificar se hÃ¡ sessÃ£o ativa
      const isAuth = authService.isAuthenticated();
      
      if (isAuth) {
        // Restaurar dados do storage
        const user = storage.getUser();
        const workspace = storage.getActiveWorkspace();

        this.setState({
          user: user,
          token: storage.getAuthToken() || this._getSessionToken(),
          isAuthenticated: true,
          workspace: workspace,
          loading: false
        });

        // Tentar obter perfil atualizado do servidor (futuro)
        // const profile = await authService.getProfile();
        // if (profile.success) {
        //   this.setState({ user: profile.data });
        // }
      } else {
        // Sem sessÃ£o
        this.setState({
          user: null,
          token: null,
          isAuthenticated: false,
          workspace: null,
          loading: false
        });
      }
    } catch (error) {
      console.error('Auth init error:', error);
      this.setState({ loading: false });
    }
  }

  /**
   * Atualizar estado e notificar observers
   */
  setState(newState) {
    this.state = {
      ...this.state,
      ...newState
    };

    // Notificar todos os observers
    this.notifyObservers();
  }

  /**
   * Obter estado atual
   */
  getState() {
    return { ...this.state };
  }

  /**
   * Registrar observer (componente que quer escutar mudanÃ§as)
   */
  subscribe(callback) {
    this.observers.push(callback);

    // Retornar funÃ§Ã£o para cancelar inscriÃ§Ã£o
    return () => {
      this.observers = this.observers.filter(obs => obs !== callback);
    };
  }

  /**
   * Notificar todos os observers sobre mudanÃ§a de estado
   */
  notifyObservers() {
    this.observers.forEach(callback => {
      try {
        callback(this.state);
      } catch (error) {
        console.error('Observer error:', error);
      }
    });

    // Disparar evento global
    window.dispatchEvent(new CustomEvent('auth:state-change', {
      detail: this.state
    }));
  }

  /**
   * Fazer login
   */
  async login(username, password, rememberMe = false) {
    this.setState({ loading: true });

    try {
      const result = await authService.login(username, password, rememberMe);

      if (result.success) {
        // Dados jÃ¡ estÃ£o no storage, pegar de lÃ¡
        const user = storage.getUser();
        const token = storage.getAuthToken();
        const workspaces = result.workspaces || [];

        this.setState({
          user,
          token,
          isAuthenticated: true,
          loading: false
        });

        return {
          success: true,
          user,
          workspaces,
          token
        };
      }

      this.setState({ loading: false });

      return {
        success: false,
        error: result.error || 'Erro ao realizar login'
      };

    } catch (error) {
      console.error('AuthContext login error:', error);

      this.setState({ loading: false });

      return {
        success: false,
        error: 'Erro ao realizar login'
      };
    }
  }

  /**
   * Realizar logout
   */
  async logout() {
    this.setState({ loading: true });

    try {
      await authService.logout();

      // Limpar estado
      this.setState({
        user: null,
        token: null,
        isAuthenticated: false,
        workspace: null,
        loading: false
      });

      return { success: true };
    } catch (error) {
      console.error('Logout error:', error);
      
      // Mesmo com erro, limpar estado local
      this.setState({
        user: null,
        token: null,
        isAuthenticated: false,
        workspace: null,
        loading: false
      });

      return {
        success: false,
        error: 'Erro ao realizar logout'
      };
    }
  }

  /**
   * Selecionar workspace
   */
  selectWorkspace(workspace) {
    if (!this.state.isAuthenticated) {
      console.warn('User not authenticated');
      return { success: false, error: 'UsuÃ¡rio nÃ£o autenticado' };
    }

    try {
      // Salvar workspace no storage
      storage.setActiveWorkspace(workspace);

      // Atualizar estado
      this.setState({ workspace });

      return { success: true };
    } catch (error) {
      console.error('Select workspace error:', error);
      return {
        success: false,
        error: 'Erro ao selecionar workspace'
      };
    }
  }

  /**
   * Obter token de sessÃ£o do cookie
   */
  _getSessionToken() {
    const names = ['sessionid', 'nef_sessionid'];
    const cookies = document.cookie.split(';');
    
    for (let cookie of cookies) {
      const trimmed = cookie.trim();
      for (const name of names) {
        if (trimmed.startsWith(name + '=')) {
          return trimmed.substring(name.length + 1);
        }
      }
    }
    
    return null;
  }

  /**
   * Verificar se usuÃ¡rio tem permissÃ£o
   */
  hasPermission(permission) {
    if (!this.state.isAuthenticated || !this.state.user) {
      return false;
    }

    // Implementar lÃ³gica de permissÃµes aqui
    // Por enquanto, retornar true se autenticado
    return true;
  }

  /**
   * Verificar se usuÃ¡rio Ã© staff
   */
  isStaff() {
    return this.state.user?.is_staff || false;
  }

  /**
   * Verificar se usuÃ¡rio Ã© superuser
   */
  isSuperuser() {
    return this.state.user?.is_superuser || false;
  }
}

// Criar instÃ¢ncia singleton
const authContext = new AuthContext();

// Exportar
export { authContext };

