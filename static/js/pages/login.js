/**
 * Lógica da página de login
 * 
 * Responsabilidades:
 * - Gerenciar interações do formulário
 * - Validar campos
 * - Chamar serviço de autenticação
 * - Exibir feedback visual
 * - Gerenciar loading states
 */

import { useAuth } from '../hooks/useAuth.js';

class LoginPage {
  constructor() {
    this.form = document.getElementById('loginForm');
    this.submitButton = null;
    this.usernameInput = null;
    this.passwordInput = null;
    this.rememberMeCheckbox = null;
    this.errorContainer = null;
    this.auth = useAuth();
    
    this.init();
  }

  init() {
    if (!this.form) {
      console.warn('Login form not found');
      return;
    }

    this.submitButton = this.form.querySelector('button[type="submit"]');
    this.usernameInput = this.form.querySelector('[name="username"]');
    this.passwordInput = this.form.querySelector('[name="password"]');
    this.rememberMeCheckbox = this.form.querySelector('[name="remember_me"]');
    
    this.bindEvents();
    this.restoreRememberMe();
  }

  bindEvents() {
    // Prevenir submit padrão e usar nossa lógica
    this.form.addEventListener('submit', (e) => {
      e.preventDefault();
      this.handleSubmit();
    });

    // Limpar erro ao digitar
    if (this.usernameInput) {
      this.usernameInput.addEventListener('input', () => this.clearError());
    }
    if (this.passwordInput) {
      this.passwordInput.addEventListener('input', () => this.clearError());
    }
  }

  /**
   * Restaurar preferência de "lembrar de mim"
   */
  restoreRememberMe() {
    if (this.rememberMeCheckbox) {
      const user = this.auth.user;
      if (user && user.username) {
        this.rememberMeCheckbox.checked = true;
        if (this.usernameInput) {
          this.usernameInput.value = user.username;
        }
      }
    }
  }

  /**
   * Processar submit do formulário
   */
  async handleSubmit() {
    const username = this.usernameInput?.value.trim() || '';
    const password = this.passwordInput?.value || '';
    const rememberMe = this.rememberMeCheckbox?.checked || false;

    // Validar campos
    if (!username || !password) {
      this.showError('Por favor, preencha todos os campos');
      return;
    }

    // Mostrar loading
    this.setLoading(true);
    this.clearError();

    // Chamar contexto de autenticação (que usa authService internamente)
    const result = await this.auth.login(username, password, rememberMe);

    if (result.success) {
      // Login bem-sucedido
      this.showSuccess('Login realizado com sucesso!');
      
      // Verificar workspaces do usuário
      // O resultado já contém workspaces da API
      await this.handleWorkspaceRedirect(result.workspaces);

    } else {
      // Login falhou
      this.setLoading(false);
      this.showError(result.error || 'Erro ao realizar login');
      
      // Limpar senha
      if (this.passwordInput) {
        this.passwordInput.value = '';
        this.passwordInput.focus();
      }
    }
  }

  /**
   * Mostrar estado de loading
   */
  setLoading(loading) {
    if (!this.submitButton) return;

    if (loading) {
      this.submitButton.disabled = true;
      this.submitButton.classList.add('loading');
      
      // Salvar texto original
      this.submitButton.dataset.originalText = this.submitButton.textContent;
      
      // Adicionar spinner
      this.submitButton.innerHTML = `
        <svg class="animate-spin h-5 w-5 mx-auto" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        <span class="ml-2">Entrando...</span>
      `;
    } else {
      this.submitButton.disabled = false;
      this.submitButton.classList.remove('loading');
      
      // Restaurar texto original
      const originalText = this.submitButton.dataset.originalText || 'Entrar';
      this.submitButton.textContent = originalText;
    }
  }

  /**
   * Mostrar mensagem de erro
   */
  showError(message) {
    this.clearError();

    // Criar container de erro se não existir
    if (!this.errorContainer) {
      this.errorContainer = document.createElement('div');
      this.errorContainer.className = 'error-message bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-800 dark:text-red-200 px-4 py-3 rounded-lg text-sm mb-4 flex items-start gap-3';
      this.errorContainer.setAttribute('role', 'alert');
      
      // Inserir no início do form
      this.form.insertBefore(this.errorContainer, this.form.firstChild);
    }

    this.errorContainer.innerHTML = `
      <svg class="w-5 h-5 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
      </svg>
      <span class="flex-1">${message}</span>
    `;

    this.errorContainer.style.display = 'flex';

    // Adicionar animação
    this.errorContainer.style.animation = 'slideDown 0.3s ease-out';
  }

  /**
   * Mostrar mensagem de sucesso
   */
  showSuccess(message) {
    this.clearError();

    // Criar container de sucesso
    const successContainer = document.createElement('div');
    successContainer.className = 'success-message bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 text-green-800 dark:text-green-200 px-4 py-3 rounded-lg text-sm mb-4 flex items-start gap-3';
    successContainer.setAttribute('role', 'status');
    
    successContainer.innerHTML = `
      <svg class="w-5 h-5 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
      </svg>
      <span class="flex-1">${message}</span>
    `;

    // Inserir no início do form
    this.form.insertBefore(successContainer, this.form.firstChild);

    // Adicionar animação
    successContainer.style.animation = 'slideDown 0.3s ease-out';
  }

  /**
   * Limpar mensagens de erro
   */
  clearError() {
    if (this.errorContainer) {
      this.errorContainer.style.display = 'none';
    }

    // Remover mensagens de sucesso também
    const successMessages = this.form.querySelectorAll('.success-message');
    successMessages.forEach(msg => msg.remove());
  }

  /**
   * Lidar com redirecionamento baseado em workspaces
   */
  async handleWorkspaceRedirect(workspaces) {
    try {
      // Workspaces já vêm da resposta de login
      if (!workspaces || !Array.isArray(workspaces)) {
        console.warn('No workspaces in login response, redirecting to dashboard');
        setTimeout(() => {
          window.location.href = '/dashboard';
        }, 500);
        return;
      }

      if (workspaces.length === 0) {
        // Sem workspaces, mostrar erro
        this.setLoading(false);
        this.showError('Você não possui acesso a nenhum workspace. Entre em contato com o administrador.');
        return;
      }

      if (workspaces.length === 1) {
        // Apenas 1 workspace, selecionar automaticamente
        this.auth.selectWorkspace(workspaces[0]);
        
        setTimeout(() => {
          window.location.href = '/dashboard';
        }, 500);
      } else {
        // Múltiplos workspaces, redirecionar para seleção
        setTimeout(() => {
          window.location.href = '/select-workspace';
        }, 500);
      }

    } catch (error) {
      console.error('Workspace redirect error:', error);
      
      // Em caso de erro, redirecionar para dashboard
      setTimeout(() => {
        window.location.href = '/dashboard';
      }, 500);
    }
  }

  /**
   * Obter CSRF token
   */
  _getCsrfToken() {
    const csrfInput = this.form.querySelector('[name=csrfmiddlewaretoken]');
    if (csrfInput) {
      return csrfInput.value;
    }

    // Tentar obter do cookie
    const name = 'csrftoken';
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
      const trimmed = cookie.trim();
      if (trimmed.startsWith(name + '=')) {
        return trimmed.substring(name.length + 1);
      }
    }

    return '';
  }
}

// Inicializar quando DOM estiver pronto
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    new LoginPage();
  });
} else {
  new LoginPage();
}

// Exportar para uso externo se necessário
export { LoginPage };
