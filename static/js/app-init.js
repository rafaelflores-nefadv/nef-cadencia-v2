/**
 * Inicialização da Aplicação
 * 
 * Este arquivo é carregado em todas as páginas e:
 * - Inicializa o contexto de autenticação
 * - Configura listeners globais
 * - Prepara a aplicação
 */

import { authContext } from './context/authContext.js';
import { useAuth } from './hooks/useAuth.js';
import { AuthGuard } from './guards/authGuard.js';
import { RoleManager } from './rbac/roleManager.js';
import { themeManager } from './theme/themeManager.js';

/**
 * Inicializar aplicação
 */
async function initApp() {
  console.log('[NEF] Inicializando aplicação...');

  // Inicializar tema (primeiro para evitar flash)
  themeManager.init();

  // Inicializar AuthGuard
  AuthGuard.init();

  // Inicializar RoleManager
  RoleManager.init();

  // Aguardar inicialização do auth
  const auth = useAuth();
  await auth.waitForInit();

  console.log('[NEF] Auth inicializado:', {
    isAuthenticated: auth.isAuthenticated,
    user: auth.user,
    workspace: auth.workspace
  });

  // Configurar listeners globais
  setupGlobalListeners();

  // Inicializar controles de UI baseados em role
  if (auth.isAuthenticated) {
    RoleManager.initRoleBasedUI();
  }

  // Adicionar botão de toggle de tema (se não existir)
  if (!document.querySelector('.theme-toggle-btn')) {
    const toggleBtn = themeManager.createToggleButton();
    toggleBtn.classList.add('theme-toggle-fixed');
    document.body.appendChild(toggleBtn);
  }

  // Atualizar UI baseado no estado de auth
  updateAuthUI(auth.state);

  console.log('[NEF] Aplicação pronta!');
}

/**
 * Configurar listeners globais
 */
function setupGlobalListeners() {
  // Escutar mudanças de autenticação
  window.addEventListener('auth:state-change', (event) => {
    console.log('[NEF] Auth state changed:', event.detail);
    updateAuthUI(event.detail);
  });

  // Escutar logout de botões
  document.querySelectorAll('[data-logout-btn]').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      e.preventDefault();
      const auth = useAuth();
      await auth.logout();
    });
  });

  // Escutar seleção de workspace
  document.querySelectorAll('[data-workspace-select]').forEach(select => {
    select.addEventListener('change', (e) => {
      const auth = useAuth();
      const workspaceId = e.target.value;
      
      // Buscar dados do workspace (implementar conforme necessário)
      const workspace = {
        id: workspaceId,
        name: e.target.options[e.target.selectedIndex].text
      };
      
      auth.selectWorkspace(workspace);
    });
  });
}

/**
 * Atualizar UI baseado no estado de auth
 */
function updateAuthUI(state) {
  // Atualizar elementos que mostram nome do usuário
  document.querySelectorAll('[data-user-name]').forEach(el => {
    if (state.user && state.user.username) {
      el.textContent = state.user.username;
    }
  });

  // Atualizar elementos que mostram workspace
  document.querySelectorAll('[data-workspace-name]').forEach(el => {
    if (state.workspace && state.workspace.name) {
      el.textContent = state.workspace.name;
    }
  });

  // Mostrar/ocultar elementos baseado em autenticação
  document.querySelectorAll('[data-auth-required]').forEach(el => {
    el.style.display = state.isAuthenticated ? '' : 'none';
  });

  document.querySelectorAll('[data-guest-only]').forEach(el => {
    el.style.display = !state.isAuthenticated ? '' : 'none';
  });

  // Mostrar/ocultar elementos baseado em permissões
  document.querySelectorAll('[data-staff-only]').forEach(el => {
    el.style.display = (state.user?.is_staff) ? '' : 'none';
  });
}

/**
 * Expor auth globalmente para uso em scripts inline
 */
window.NEF = window.NEF || {};
window.NEF.auth = useAuth();
window.NEF.authContext = authContext;

// Inicializar quando DOM estiver pronto
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initApp);
} else {
  initApp();
}

// Exportar para uso em módulos
export { initApp };
