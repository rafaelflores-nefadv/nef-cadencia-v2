import { useAuth } from '../hooks/useAuth.js';
import { storage } from '../utils/storage.js';

class LoginPage {
  constructor() {
    this.form = document.getElementById('loginForm');
    this.submitButton = null;
    this.usernameInput = null;
    this.passwordInput = null;
    this.rememberMeCheckbox = null;
    this.errorContainer = null;
    this.successContainer = null;
    this.auth = useAuth();

    this.init();
  }

  init() {
    if (!this.form) {
      return;
    }

    this.submitButton = this.form.querySelector('button[type="submit"]');
    this.usernameInput = this.form.querySelector('[name="username"]');
    this.passwordInput = this.form.querySelector('[name="password"]');
    this.rememberMeCheckbox = this.form.querySelector('[name="remember_me"]');

    this.resetStaleAuthState();
    this.bindEvents();
    this.restoreRememberMe();
  }

  resetStaleAuthState() {
    storage.removeAuthToken();
    storage.remove('refresh_token');
    storage.remove('workspaces');
    storage.remove('active_workspace');
  }

  bindEvents() {
    this.form.addEventListener('submit', (event) => {
      event.preventDefault();
      this.handleSubmit();
    });

    if (this.usernameInput) {
      this.usernameInput.addEventListener('input', () => this.clearAlerts());
    }

    if (this.passwordInput) {
      this.passwordInput.addEventListener('input', () => this.clearAlerts());
    }
  }

  restoreRememberMe() {
    const rememberedUsername = storage.get('remembered_username');
    const rememberMe = storage.getRememberMe();

    if (this.rememberMeCheckbox) {
      this.rememberMeCheckbox.checked = Boolean(rememberMe && rememberedUsername);
    }

    if (rememberedUsername && this.usernameInput) {
      this.usernameInput.value = rememberedUsername;
    }
  }

  async handleSubmit() {
    const username = this.usernameInput?.value.trim() || '';
    const password = this.passwordInput?.value || '';
    const rememberMe = this.rememberMeCheckbox?.checked || false;

    if (!username || !password) {
      this.showError('Preencha usuario e senha para continuar.');
      return;
    }

    this.setLoading(true);
    this.clearAlerts();

    const result = await this.auth.login(username, password, rememberMe);

    if (!result.success) {
      this.setLoading(false);
      this.showError(result.error || 'Nao foi possivel realizar o login.');

      if (this.passwordInput) {
        this.passwordInput.value = '';
        this.passwordInput.focus();
      }

      return;
    }

    this.showSuccess('Login realizado com sucesso. Redirecionando...');
    await this.handleWorkspaceRedirect(result.workspaces);
  }

  setLoading(isLoading) {
    if (!this.submitButton) {
      return;
    }

    if (isLoading) {
      this.submitButton.disabled = true;
      this.submitButton.classList.add('is-loading');
      this.submitButton.dataset.originalText = this.submitButton.textContent.trim();
      this.submitButton.innerHTML =
        '<span class="auth-btn-spinner" aria-hidden="true"></span><span>Entrando...</span>';
      return;
    }

    this.submitButton.disabled = false;
    this.submitButton.classList.remove('is-loading');
    this.submitButton.textContent = this.submitButton.dataset.originalText || 'Entrar';
  }

  createAlert(type, message, role) {
    const container = document.createElement('div');
    container.className = `auth-alert auth-alert--${type}`;
    container.setAttribute('role', role);

    const icon = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    icon.setAttribute('viewBox', '0 0 24 24');
    icon.setAttribute('fill', 'none');
    icon.setAttribute('stroke', 'currentColor');
    icon.setAttribute('aria-hidden', 'true');
    icon.setAttribute('class', 'auth-alert__icon');

    const pathA = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    pathA.setAttribute('stroke-linecap', 'round');
    pathA.setAttribute('stroke-linejoin', 'round');
    pathA.setAttribute('stroke-width', '2');

    const pathB = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    pathB.setAttribute('stroke-linecap', 'round');
    pathB.setAttribute('stroke-linejoin', 'round');
    pathB.setAttribute('stroke-width', '2');

    if (type === 'success') {
      pathA.setAttribute('d', 'M9 12l2 2 4-4');
      pathB.setAttribute('d', 'M21 12a9 9 0 11-18 0 9 9 0 0118 0z');
    } else {
      pathA.setAttribute('d', 'M12 8v4m0 4h.01');
      pathB.setAttribute('d', 'M21 12a9 9 0 11-18 0 9 9 0 0118 0z');
    }

    icon.append(pathA, pathB);

    const content = document.createElement('div');
    const title = document.createElement('strong');
    title.textContent = type === 'success' ? 'Tudo certo' : 'Nao foi possivel entrar';
    const text = document.createElement('p');
    text.textContent = message;
    content.append(title, text);

    container.append(icon, content);
    return container;
  }

  showError(message) {
    this.clearAlerts();
    this.errorContainer = this.createAlert('error', message, 'alert');
    this.form.insertBefore(this.errorContainer, this.form.firstChild);
  }

  showSuccess(message) {
    this.clearAlerts();
    this.successContainer = this.createAlert('success', message, 'status');
    this.form.insertBefore(this.successContainer, this.form.firstChild);
  }

  clearAlerts() {
    if (this.errorContainer) {
      this.errorContainer.remove();
      this.errorContainer = null;
    }

    if (this.successContainer) {
      this.successContainer.remove();
      this.successContainer = null;
    }
  }

  async handleWorkspaceRedirect(workspaces) {
    try {
      if (!Array.isArray(workspaces)) {
        setTimeout(() => {
          window.location.href = '/dashboard';
        }, 320);
        return;
      }

      if (workspaces.length === 0) {
        this.setLoading(false);
        this.showError('Seu usuario nao possui acesso a nenhum workspace ativo.');
        return;
      }

      if (workspaces.length === 1) {
        this.auth.selectWorkspace(workspaces[0]);
        setTimeout(() => {
          window.location.href = '/dashboard';
        }, 320);
        return;
      }

      setTimeout(() => {
        window.location.href = '/select-workspace';
      }, 320);
    } catch (error) {
      console.error('Workspace redirect error:', error);
      setTimeout(() => {
        window.location.href = '/dashboard';
      }, 320);
    }
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    new LoginPage();
  });
} else {
  new LoginPage();
}

export { LoginPage };
