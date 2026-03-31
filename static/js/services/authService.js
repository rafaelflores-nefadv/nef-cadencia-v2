import { api } from './api.js';
import { storage } from '../utils/storage.js';

class AuthService {
  constructor() {
    this.endpoints = {
      login: '/api/auth/login',
      logout: '/api/auth/logout',
      refresh: '/api/auth/refresh',
      me: '/api/auth/me',
      workspaces: '/api/workspaces',
    };
  }

  async login(username, password, rememberMe = false) {
    try {
      storage.setRememberMe(rememberMe);

      const result = await api.post(this.endpoints.login, {
        username,
        password,
      });

      if (result.success) {
        storage.setAuthToken(result.data.token);
        storage.set('refresh_token', result.data.refresh);
        storage.setUser(result.data.user);
        storage.set('workspaces', result.data.workspaces);

        if (rememberMe) {
          storage.set('remembered_username', username);
        }

        return {
          success: true,
          message: 'Login realizado com sucesso',
          user: result.data.user,
          workspaces: result.data.workspaces,
          token: result.data.token,
        };
      }

      return {
        success: false,
        error: result.error || 'Erro ao realizar login',
        status: result.status || 401,
      };
    } catch (error) {
      console.error('Login error:', error);
      return {
        success: false,
        error: 'Erro ao conectar com o servidor',
        status: 500,
      };
    }
  }

  async logout() {
    try {
      const refreshToken = storage.get('refresh_token');

      await api.post(this.endpoints.logout, {
        refresh: refreshToken,
      });

      storage.clearAuth();
      storage.remove('refresh_token');
      storage.remove('workspaces');

      window.location.href = '/login';

      return {
        success: true,
        message: 'Logout realizado com sucesso',
      };
    } catch (error) {
      console.error('Logout error:', error);

      storage.clearAuth();
      storage.remove('refresh_token');
      storage.remove('workspaces');
      window.location.href = '/login';

      return {
        success: false,
        error: 'Erro ao realizar logout',
      };
    }
  }

  async getMe() {
    try {
      const result = await api.get(this.endpoints.me);

      if (result.success) {
        storage.setUser(result.data.user);
        storage.set('workspaces', result.data.workspaces);
      }

      return result;
    } catch (error) {
      console.error('Get me error:', error);
      return {
        success: false,
        error: 'Erro ao obter dados do usuario',
      };
    }
  }

  async getUserWorkspaces() {
    try {
      const result = await api.get(this.endpoints.workspaces);

      if (result.success) {
        storage.set('workspaces', result.data.workspaces);
        return {
          success: true,
          workspaces: result.data.workspaces,
        };
      }

      return result;
    } catch (error) {
      console.error('Get workspaces error:', error);
      return {
        success: false,
        error: 'Erro ao obter workspaces',
      };
    }
  }

  async refreshToken() {
    try {
      const refreshToken = storage.get('refresh_token');

      if (!refreshToken) {
        throw new Error('Refresh token nao encontrado');
      }

      const result = await api.post(this.endpoints.refresh, {
        refresh: refreshToken,
      });

      if (result.success) {
        storage.setAuthToken(result.data.access);
        return {
          success: true,
          token: result.data.access,
        };
      }

      return result;
    } catch (error) {
      console.error('Refresh token error:', error);

      storage.clearAuth();
      window.location.href = '/login';

      return {
        success: false,
        error: 'Sessao expirada',
      };
    }
  }

  isAuthenticated() {
    const hasSessionCookie =
      document.cookie.includes('sessionid') ||
      document.cookie.includes('nef_sessionid');
    const token = storage.getAuthToken();
    const user = storage.getUser();

    return hasSessionCookie || !!(token && user);
  }

  getUser() {
    return storage.getUser();
  }

  _getCsrfToken() {
    const name = 'csrftoken';
    const cookies = document.cookie.split(';');

    for (let cookie of cookies) {
      const trimmed = cookie.trim();
      if (trimmed.startsWith(name + '=')) {
        return trimmed.substring(name.length + 1);
      }
    }

    const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
    if (csrfInput) {
      return csrfInput.value;
    }

    return '';
  }

  validateCredentials(username, password) {
    const errors = [];

    if (!username || username.trim().length === 0) {
      errors.push('Usuario e obrigatorio');
    }

    if (!password || password.length === 0) {
      errors.push('Senha e obrigatoria');
    }

    if (password && password.length < 3) {
      errors.push('Senha deve ter no minimo 3 caracteres');
    }

    return {
      valid: errors.length === 0,
      errors,
    };
  }
}

export const authService = new AuthService();
