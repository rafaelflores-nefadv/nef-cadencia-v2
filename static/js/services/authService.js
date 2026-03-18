/**
 * Serviço de Autenticação
 * 
 * Responsabilidades:
 * - Gerenciar login/logout
 * - Gerenciar sessão do usuário
 * - Integrar com backend Django
 * - Gerenciar tokens e preferências
 */

import { api } from './api.js';
import { storage } from '../utils/storage.js';

class AuthService {
  constructor() {
    this.endpoints = {
      login: '/api/auth/login',
      logout: '/api/auth/logout',
      refresh: '/api/auth/refresh',
      me: '/api/auth/me',
      workspaces: '/api/workspaces'
    };
  }

  /**
   * Realizar login via API REST
   * 
   * @param {string} username - Usuário ou email
   * @param {string} password - Senha
   * @param {boolean} rememberMe - Lembrar de mim
   * @returns {Promise<Object>} Resultado do login com token, user e workspaces
   */
  async login(username, password, rememberMe = false) {
    try {
      // Salvar preferência de "lembrar de mim"
      storage.setRememberMe(rememberMe);

      // Chamar API REST (JSON)
      const result = await api.post(this.endpoints.login, {
        username,
        password
      });

      if (result.success) {
        // Salvar tokens
        storage.setAuthToken(result.data.token);
        storage.set('refresh_token', result.data.refresh);
        
        // Salvar dados do usuário
        storage.setUser(result.data.user);
        
        // Salvar workspaces
        storage.set('workspaces', result.data.workspaces);
        
        // Salvar username se "lembrar de mim"
        if (rememberMe) {
          storage.set('remembered_username', username);
        }

        return {
          success: true,
          message: 'Login realizado com sucesso',
          user: result.data.user,
          workspaces: result.data.workspaces,
          token: result.data.token
        };
      }

      return {
        success: false,
        error: result.error || 'Erro ao realizar login',
        status: result.status || 401
      };

    } catch (error) {
      console.error('Login error:', error);
      
      return {
        success: false,
        error: 'Erro ao conectar com o servidor',
        status: 500
      };
    }
  }

  /**
   * Realizar logout via API REST
   */
  async logout() {
    try {
      const refreshToken = storage.get('refresh_token');
      
      // Chamar API de logout
      await api.post(this.endpoints.logout, {
        refresh: refreshToken
      });

      // Limpar dados locais
      storage.clearAuth();
      storage.remove('refresh_token');
      storage.remove('workspaces');

      // Redirecionar para login
      window.location.href = '/login';

      return {
        success: true,
        message: 'Logout realizado com sucesso'
      };

    } catch (error) {
      console.error('Logout error:', error);
      
      // Mesmo com erro, limpar dados locais
      storage.clearAuth();
      storage.remove('refresh_token');
      storage.remove('workspaces');
      window.location.href = '/login';

      return {
        success: false,
        error: 'Erro ao realizar logout'
      };
    }
  }

  /**
   * Obter dados do usuário autenticado
   */
  async getMe() {
    try {
      const result = await api.get(this.endpoints.me);
      
      if (result.success) {
        storage.setUser(result.data.user);
        storage.set('workspaces', result.data.workspaces);
        return result;
      }

      return result;

    } catch (error) {
      console.error('Get me error:', error);
      
      return {
        success: false,
        error: 'Erro ao obter dados do usuário'
      };
    }
  }

  /**
   * Obter workspaces do usuário via API REST
   */
  async getUserWorkspaces() {
    try {
      const result = await api.get(this.endpoints.workspaces);
      
      if (result.success) {
        storage.set('workspaces', result.data.workspaces);
        return {
          success: true,
          workspaces: result.data.workspaces
        };
      }

      return result;

    } catch (error) {
      console.error('Get workspaces error:', error);
      
      return {
        success: false,
        error: 'Erro ao obter workspaces'
      };
    }
  }

  /**
   * Atualizar access token usando refresh token
   */
  async refreshToken() {
    try {
      const refreshToken = storage.get('refresh_token');
      
      if (!refreshToken) {
        throw new Error('Refresh token não encontrado');
      }

      const result = await api.post(this.endpoints.refresh, {
        refresh: refreshToken
      });

      if (result.success) {
        storage.setAuthToken(result.data.access);
        return {
          success: true,
          token: result.data.access
        };
      }

      return result;

    } catch (error) {
      console.error('Refresh token error:', error);
      
      // Se refresh falhar, fazer logout
      storage.clearAuth();
      window.location.href = '/login';
      
      return {
        success: false,
        error: 'Sessão expirada'
      };
    }
  }

  /**
   * Verificar se usuário está autenticado
   */
  isAuthenticated() {
    // Em Django session-based, verificar se há cookie de sessão
    return document.cookie.includes('sessionid');
  }

  /**
   * Obter usuário do storage
   */
  getUser() {
    return storage.getUser();
  }

  /**
   * Obter CSRF token do cookie
   */
  _getCsrfToken() {
    const name = 'csrftoken';
    const cookies = document.cookie.split(';');
    
    for (let cookie of cookies) {
      const trimmed = cookie.trim();
      if (trimmed.startsWith(name + '=')) {
        return trimmed.substring(name.length + 1);
      }
    }
    
    // Tentar obter do input hidden
    const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
    if (csrfInput) {
      return csrfInput.value;
    }
    
    return '';
  }

  /**
   * Validar credenciais localmente antes de enviar
   */
  validateCredentials(username, password) {
    const errors = [];

    if (!username || username.trim().length === 0) {
      errors.push('Usuário é obrigatório');
    }

    if (!password || password.length === 0) {
      errors.push('Senha é obrigatória');
    }

    if (password && password.length < 3) {
      errors.push('Senha deve ter no mínimo 3 caracteres');
    }

    return {
      valid: errors.length === 0,
      errors: errors
    };
  }
}

// Exportar instância singleton
export const authService = new AuthService();
