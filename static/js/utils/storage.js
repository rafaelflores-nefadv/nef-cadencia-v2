/**
 * LocalStorage manager for auth/session data.
 */
class StorageManager {
  static KEYS = {
    AUTH_TOKEN: 'auth_token',
    REFRESH_TOKEN: 'refresh_token',
    USER: 'user',
    ACTIVE_WORKSPACE: 'active_workspace',
    REMEMBER_ME: 'remember_me',
    REMEMBERED_USERNAME: 'remembered_username',
    WORKSPACES: 'workspaces',
    RETURN_URL: 'return_url',
  };

  constructor() {
    this.prefix = 'nef_';
  }

  _getKey(key) {
    return `${this.prefix}${key}`;
  }

  set(key, value) {
    try {
      localStorage.setItem(this._getKey(key), JSON.stringify(value));
      return true;
    } catch (error) {
      console.error('Storage set error:', error);
      return false;
    }
  }

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

  remove(key) {
    try {
      localStorage.removeItem(this._getKey(key));
      return true;
    } catch (error) {
      console.error('Storage remove error:', error);
      return false;
    }
  }

  clear() {
    try {
      const keys = Object.keys(localStorage);
      keys.forEach((key) => {
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

  has(key) {
    return localStorage.getItem(this._getKey(key)) !== null;
  }

  setAuthToken(token) {
    return this.set(StorageManager.KEYS.AUTH_TOKEN, token);
  }

  getAuthToken() {
    return this.get(StorageManager.KEYS.AUTH_TOKEN);
  }

  removeAuthToken() {
    return this.remove(StorageManager.KEYS.AUTH_TOKEN);
  }

  setUser(user) {
    return this.set(StorageManager.KEYS.USER, user);
  }

  getUser() {
    return this.get(StorageManager.KEYS.USER);
  }

  removeUser() {
    return this.remove(StorageManager.KEYS.USER);
  }

  setActiveWorkspace(workspace) {
    return this.set(StorageManager.KEYS.ACTIVE_WORKSPACE, workspace);
  }

  getActiveWorkspace() {
    return this.get(StorageManager.KEYS.ACTIVE_WORKSPACE);
  }

  removeActiveWorkspace() {
    return this.remove(StorageManager.KEYS.ACTIVE_WORKSPACE);
  }

  setRememberMe(remember) {
    return this.set(StorageManager.KEYS.REMEMBER_ME, remember);
  }

  getRememberMe() {
    return this.get(StorageManager.KEYS.REMEMBER_ME, false);
  }

  clearAuth() {
    this.removeAuthToken();
    this.remove(StorageManager.KEYS.REFRESH_TOKEN);
    this.remove(StorageManager.KEYS.WORKSPACES);
    this.removeUser();
    this.removeActiveWorkspace();
    return true;
  }
}

export const storage = new StorageManager();
