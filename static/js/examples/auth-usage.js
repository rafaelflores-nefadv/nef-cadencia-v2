/**
 * Exemplos de Uso do AuthContext
 * 
 * Este arquivo demonstra como usar o contexto de autenticação
 * em diferentes cenários
 */

import { useAuth } from '../hooks/useAuth.js';
import { authContext } from '../context/authContext.js';

// ============================================
// EXEMPLO 1: Verificar Autenticação
// ============================================

function checkAuth() {
  const auth = useAuth();
  
  console.log('Usuário autenticado?', auth.isAuthenticated);
  console.log('Usuário:', auth.user);
  console.log('Workspace:', auth.workspace);
  console.log('Loading?', auth.loading);
}

// ============================================
// EXEMPLO 2: Proteger Rota
// ============================================

async function protectedPage() {
  const auth = useAuth();
  
  // Aguardar inicialização
  await auth.waitForInit();
  
  // Verificar autenticação
  if (!auth.isAuthenticated) {
    const currentPath = window.location.pathname;
    window.location.href = `/login?next=${encodeURIComponent(currentPath)}`;
    return;
  }
  
  // Usuário autenticado, continuar
  console.log('Página protegida carregada para:', auth.user.username);
}

// ============================================
// EXEMPLO 3: Verificar Permissões
// ============================================

function checkPermissions() {
  const auth = useAuth();
  
  if (auth.isStaff()) {
    console.log('Usuário é staff');
    // Mostrar menu admin
    document.getElementById('adminMenu').style.display = 'block';
  }
  
  if (auth.isSuperuser()) {
    console.log('Usuário é superuser');
    // Mostrar opções avançadas
    document.getElementById('advancedOptions').style.display = 'block';
  }
}

// ============================================
// EXEMPLO 4: Escutar Mudanças de Estado
// ============================================

function listenToAuthChanges() {
  const auth = useAuth();
  
  // Registrar observer
  const unsubscribe = auth.onStateChange((state) => {
    console.log('Auth state mudou:', state);
    
    if (state.isAuthenticated) {
      console.log('Usuário logou:', state.user);
      // Atualizar UI
      updateUserInfo(state.user);
    } else {
      console.log('Usuário deslogou');
      // Redirecionar para login
      window.location.href = '/login';
    }
  });
  
  // Cancelar inscrição quando não precisar mais
  // unsubscribe();
}

// ============================================
// EXEMPLO 5: Fazer Logout
// ============================================

async function handleLogout() {
  const auth = useAuth();
  
  const confirmLogout = confirm('Deseja realmente sair?');
  if (!confirmLogout) return;
  
  const result = await auth.logout();
  
  if (result.success) {
    console.log('Logout realizado com sucesso');
    // authContext já redireciona automaticamente
  } else {
    console.error('Erro ao fazer logout:', result.error);
  }
}

// ============================================
// EXEMPLO 6: Selecionar Workspace
// ============================================

function handleWorkspaceChange(workspaceId, workspaceName) {
  const auth = useAuth();
  
  const workspace = {
    id: workspaceId,
    name: workspaceName
  };
  
  const result = auth.selectWorkspace(workspace);
  
  if (result.success) {
    console.log('Workspace selecionado:', workspace);
    // Recarregar dados do dashboard
    reloadDashboard();
  } else {
    console.error('Erro ao selecionar workspace:', result.error);
  }
}

// ============================================
// EXEMPLO 7: Usar em Event Listener
// ============================================

document.addEventListener('DOMContentLoaded', async () => {
  const auth = useAuth();
  
  // Aguardar inicialização
  await auth.waitForInit();
  
  // Configurar botão de logout
  const logoutBtn = document.getElementById('logoutBtn');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', async (e) => {
      e.preventDefault();
      await auth.logout();
    });
  }
  
  // Configurar seletor de workspace
  const workspaceSelect = document.getElementById('workspaceSelect');
  if (workspaceSelect) {
    workspaceSelect.addEventListener('change', (e) => {
      const option = e.target.options[e.target.selectedIndex];
      handleWorkspaceChange(e.target.value, option.text);
    });
  }
});

// ============================================
// EXEMPLO 8: Usar com Fetch API
// ============================================

async function fetchProtectedData() {
  const auth = useAuth();
  
  if (!auth.isAuthenticated) {
    console.error('Usuário não autenticado');
    return;
  }
  
  try {
    const response = await fetch('/api/protected-endpoint', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCsrfToken()
      },
      credentials: 'same-origin'
    });
    
    const data = await response.json();
    console.log('Dados protegidos:', data);
  } catch (error) {
    console.error('Erro ao buscar dados:', error);
  }
}

// ============================================
// EXEMPLO 9: Usar Globalmente (window.NEF)
// ============================================

// Em scripts inline ou não-módulos
function useAuthGlobally() {
  // Acessar via window.NEF
  const auth = window.NEF.auth;
  
  if (auth.isAuthenticated) {
    console.log('Usuário:', auth.user.username);
  }
}

// ============================================
// EXEMPLO 10: Escutar Evento Global
// ============================================

window.addEventListener('auth:state-change', (event) => {
  const state = event.detail;
  console.log('Auth mudou:', state);
  
  // Atualizar UI
  if (state.isAuthenticated) {
    document.getElementById('userName').textContent = state.user.username;
  }
});

// ============================================
// HELPERS
// ============================================

function getCsrfToken() {
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

function updateUserInfo(user) {
  document.querySelectorAll('[data-user-name]').forEach(el => {
    el.textContent = user.username;
  });
}

function reloadDashboard() {
  window.location.reload();
}

// Exportar exemplos
export {
  checkAuth,
  protectedPage,
  checkPermissions,
  listenToAuthChanges,
  handleLogout,
  handleWorkspaceChange
};
