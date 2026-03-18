/**
 * Gerenciador de LocalStorage
 * 
 * Responsabilidades:
 * - Salvar e recuperar dados do localStorage
 * - Serializar/deserializar JSON automaticamente
 * - Tratar erros de forma segura
 * - Gerenciar tokens e preferências do usuário
 */

class StorageManager {
  constructor() {
    this.prefix = 'nef_';
  }

  /**
   * Gera chave com prefixo
   */
  _getKey(key) {
    return `${this.prefix}${key}`;
  }

  /**
   * Salvar item no localStorage
   */
  set(key, value) {
    try {
      const serialized = JSON.stringify(value);
      localStorage.setItem(this._getKey(key), serialized);
      return true;
    } catch (error) {
      console.error('Storage set error:', error);
      return false;
    }
  }

  /**
   * Recuperar item do localStorage
   */
  get(key, defaultValue = null) {
    try {
      const item = localStorage.getItem(this._getKey(key));
      if (item === null) {
        return defaultValue;
      }
      return JSON.parse(item);
    } catch (error) {
      console.error('Storage get error:', error);
      return defaultValue;
    }
  }

  /**
   * Remover item do localStorage
   */
  remove(key) {
    try {
      localStorage.removeItem(this._getKey(key));
      return true;
    } catch (error) {
      console.error('Storage remove error:', error);
      return false;
    }
  }

  /**
   * Limpar todos os itens com prefixo
   */
  clear() {
    try {
      const keys = Object.keys(localStorage);
      keys.forEach(key => {
        if (key.startsWith(this.prefix)) {
          localStorage.removeItem(key);
        }
      });
      return true;
    } catch (error) {
      console.error('Storage clear error:', error);
      return false;
    }
  }

  /**
   * Verificar se item existe
   */
  has(key) {
    return localStorage.getItem(this._getKey(key)) !== null;
  }

  // ============================================
  // Métodos específicos para autenticação
  // ============================================

  /**
   * Salvar token de autenticação
   */
  setAuthToken(token) {
    return this.set('auth_token', token);
  }

  /**
   * Recuperar token de autenticação
   */
  getAuthToken() {
    return this.get(StorageManager.KEYS.AUTH_TOKEN);
  }

  /**
   * Remover token de autenticação
   */
  removeAuthToken() {
    return this.remove(StorageManager.KEYS.AUTH_TOKEN);
  }

  /**
   * Salvar dados do usuário
   */
  setUser(user) {
    return this.set(StorageManager.KEYS.USER, user);
  }

  /**
   * Recuperar dados do usuário
   */
  getUser() {
    return this.get(StorageManager.KEYS.USER);
    return this.get('user');
  }

  /**
   * Remover dados do usuário
   */
  removeUser() {
    return this.remove('user');
  }

  /**
   * Salvar workspace ativo
   */
  setActiveWorkspace(workspace) {
    return this.set('active_workspace', workspace);
  }

  /**
   * Recuperar workspace ativo
   */
  getActiveWorkspace() {
    return this.get('active_workspace');
  }

  /**
   * Remover workspace ativo
   */
  removeActiveWorkspace() {
    return this.remove('active_workspace');
  }

  /**
   * Salvar preferência de "lembrar de mim"
   */
  setRememberMe(remember) {
    return this.set('remember_me', remember);
  }

  /**
   * Verificar se "lembrar de mim" está ativo
   */
  getRememberMe() {
    return this.get('remember_me', false);
  }

  /**
   * Limpar todos os dados de autenticação
   */
  clearAuth() {
    this.removeAuthToken();
    this.removeUser();
    this.removeActiveWorkspace();
    return true;
  }
}

// Exportar instância singleton
export const storage = new StorageManager();
