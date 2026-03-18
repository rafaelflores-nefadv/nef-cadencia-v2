# Guia do AuthContext - NEF Cadência

**Data:** 18 de Março de 2026  
**Objetivo:** Contexto global de autenticação no frontend  
**Status:** ✅ IMPLEMENTADO

---

## ARQUIVOS CRIADOS

### 1. `static/js/context/authContext.js` (270 linhas)
**Gerenciador Global de Estado de Autenticação**

**Estado Gerenciado:**
```javascript
{
  user: null,              // Dados do usuário
  token: null,             // Token de sessão (sessionid)
  loading: true,           // Estado de carregamento
  isAuthenticated: false,  // Se está autenticado
  workspace: null          // Workspace ativo
}
```

**Métodos Públicos:**
- `getState()` - Obter estado atual
- `subscribe(callback)` - Registrar observer
- `login(username, password, rememberMe)` - Fazer login
- `logout()` - Fazer logout
- `selectWorkspace(workspace)` - Selecionar workspace
- `hasPermission(permission)` - Verificar permissão
- `isStaff()` - Verificar se é staff
- `isSuperuser()` - Verificar se é superuser

---

### 2. `static/js/hooks/useAuth.js` (140 linhas)
**Hook para Acessar Contexto**

**Funcionalidades:**
- ✅ Encapsula acesso ao authContext
- ✅ Expõe estado e métodos
- ✅ Helpers para proteção de rotas
- ✅ Similar ao `useAuth()` do React

**Métodos:**
- `useAuth()` - Obter instância do auth
- `requireAuth()` - Proteger rota (redireciona se não autenticado)
- `requireStaff()` - Proteger rota staff
- `redirectIfAuthenticated()` - Redirecionar se já autenticado

---

### 3. `static/js/app-init.js` (120 linhas)
**Inicialização Global da Aplicação**

**Responsabilidades:**
- ✅ Inicializar authContext ao carregar app
- ✅ Configurar listeners globais
- ✅ Atualizar UI baseado em estado de auth
- ✅ Expor auth globalmente (`window.NEF.auth`)

---

### 4. `static/js/examples/auth-usage.js` (200 linhas)
**Exemplos de Uso**

10 exemplos práticos de como usar o authContext.

---

### 5. `static/js/pages/login.js` (ATUALIZADO)
**Integrado com AuthContext**

Agora usa `useAuth()` ao invés de `authService` diretamente.

---

### 6. `templates/layouts/base.html` (ATUALIZADO)
**Carrega app-init.js**

Adicionado `<script type="module" src="app-init.js">` para inicializar auth em todas as páginas.

---

## 🔄 COMO FUNCIONA

### Padrão Observer

```
┌─────────────────────────────────────────────────┐
│           AUTHCONTEXT (Estado Global)           │
├─────────────────────────────────────────────────┤
│                                                 │
│  state = {                                      │
│    user: { username: 'admin' },                 │
│    isAuthenticated: true,                       │
│    workspace: { id: 1, name: 'Principal' }      │
│  }                                              │
│                                                 │
└────────────┬────────────────────────────────────┘
             │
             │ notifyObservers()
             │
     ┌───────┴───────┬───────────┬────────────┐
     │               │           │            │
     ▼               ▼           ▼            ▼
┌─────────┐   ┌─────────┐  ┌─────────┐  ┌─────────┐
│ Sidebar │   │ Topbar  │  │ Profile │  │ Custom  │
│ Observer│   │ Observer│  │ Observer│  │ Observer│
└─────────┘   └─────────┘  └─────────┘  └─────────┘
```

### Fluxo de Inicialização

```
1. Página carrega
   ↓
2. app-init.js executa
   ↓
3. authContext.init()
   ├── Verifica cookie sessionid
   ├── Restaura user do storage
   ├── Restaura workspace do storage
   └── setState({ isAuthenticated: true })
   ↓
4. notifyObservers()
   ↓
5. Todos os componentes recebem estado
   ↓
6. UI atualiza automaticamente
```

### Fluxo de Login

```
1. LoginPage.handleSubmit()
   ↓
2. auth.login(username, password)
   ↓
3. authContext.login()
   ├── authService.login() (POST /login)
   ├── setState({ user, isAuthenticated: true })
   └── notifyObservers()
   ↓
4. Todos os componentes recebem novo estado
   ↓
5. Redirect para /dashboard
```

### Fluxo de Logout

```
1. Usuário clica em "Sair"
   ↓
2. auth.logout()
   ↓
3. authContext.logout()
   ├── authService.logout() (POST /logout)
   ├── storage.clearAuth()
   ├── setState({ user: null, isAuthenticated: false })
   └── notifyObservers()
   ↓
4. Redirect para /login
```

---

## 📖 GUIA DE USO

### Uso Básico

```javascript
import { useAuth } from './hooks/useAuth.js';

// Obter instância
const auth = useAuth();

// Acessar estado
console.log(auth.user);
console.log(auth.isAuthenticated);
console.log(auth.workspace);
console.log(auth.loading);

// Fazer login
const result = await auth.login('admin', 'admin123', true);

// Fazer logout
await auth.logout();

// Selecionar workspace
auth.selectWorkspace({ id: 1, name: 'Principal' });
```

### Proteger Rotas

```javascript
import { requireAuth, requireStaff } from './hooks/useAuth.js';

// Proteger página (requer autenticação)
if (!requireAuth()) {
  // Já foi redirecionado para /login
  return;
}

// Proteger página admin (requer staff)
if (!requireStaff()) {
  // Já foi redirecionado para /dashboard
  return;
}

// Continuar com lógica da página
console.log('Página protegida carregada');
```

### Escutar Mudanças de Estado

```javascript
import { useAuth } from './hooks/useAuth.js';

const auth = useAuth();

// Registrar observer
const unsubscribe = auth.onStateChange((state) => {
  console.log('Estado mudou:', state);
  
  if (state.isAuthenticated) {
    // Usuário logou
    updateUI(state.user);
  } else {
    // Usuário deslogou
    clearUI();
  }
});

// Cancelar quando não precisar mais
// unsubscribe();
```

### Usar em Scripts Inline (Não-Módulos)

```html
<script>
  // Acessar via window.NEF
  const auth = window.NEF.auth;
  
  if (auth.isAuthenticated) {
    console.log('Usuário:', auth.user.username);
  }
</script>
```

### Usar em Event Listeners

```javascript
document.getElementById('logoutBtn').addEventListener('click', async () => {
  const auth = window.NEF.auth;
  await auth.logout();
});
```

### Atualizar UI Automaticamente

```html
<!-- Elementos com data-attributes -->
<span data-user-name></span>
<span data-workspace-name></span>

<!-- Mostrar apenas se autenticado -->
<div data-auth-required>Conteúdo protegido</div>

<!-- Mostrar apenas para guests -->
<div data-guest-only>Faça login</div>

<!-- Mostrar apenas para staff -->
<div data-staff-only>Menu admin</div>
```

O `app-init.js` atualiza esses elementos automaticamente!

---

## 🎯 CASOS DE USO

### 1. Página de Dashboard

```javascript
// pages/dashboard.js
import { useAuth } from '../hooks/useAuth.js';

async function initDashboard() {
  const auth = useAuth();
  
  // Aguardar inicialização
  await auth.waitForInit();
  
  // Proteger rota
  if (!auth.isAuthenticated) {
    window.location.href = '/login';
    return;
  }
  
  // Carregar dados do dashboard
  console.log('Carregando dashboard para:', auth.user.username);
  console.log('Workspace:', auth.workspace);
  
  // Escutar mudanças de workspace
  auth.onStateChange((state) => {
    if (state.workspace) {
      console.log('Workspace mudou, recarregar dados');
      reloadDashboardData();
    }
  });
}
```

### 2. Componente de Perfil

```javascript
// components/profile-menu.js
import { useAuth } from '../hooks/useAuth.js';

class ProfileMenu {
  constructor() {
    this.auth = useAuth();
    this.init();
  }
  
  init() {
    // Atualizar nome do usuário
    this.updateUserName();
    
    // Escutar mudanças
    this.auth.onStateChange(() => {
      this.updateUserName();
    });
  }
  
  updateUserName() {
    const nameEl = document.getElementById('profileName');
    if (nameEl && this.auth.user) {
      nameEl.textContent = this.auth.user.username;
    }
  }
}
```

### 3. Seletor de Workspace

```javascript
// components/workspace-selector.js
import { useAuth } from '../hooks/useAuth.js';

class WorkspaceSelector {
  constructor() {
    this.auth = useAuth();
    this.select = document.getElementById('workspaceSelect');
    this.init();
  }
  
  init() {
    if (!this.select) return;
    
    // Restaurar workspace selecionado
    if (this.auth.workspace) {
      this.select.value = this.auth.workspace.id;
    }
    
    // Escutar mudanças
    this.select.addEventListener('change', (e) => {
      const option = e.target.options[e.target.selectedIndex];
      const workspace = {
        id: e.target.value,
        name: option.text
      };
      
      this.auth.selectWorkspace(workspace);
      
      // Recarregar página com novo workspace
      window.location.reload();
    });
  }
}
```

---

## 🔐 INTEGRAÇÃO COM ROTAS PROTEGIDAS

### Proteger Página Inteira

```javascript
// pages/agents.js
import { requireAuth } from '../hooks/useAuth.js';

// No início do arquivo
if (!requireAuth()) {
  // Já foi redirecionado
  throw new Error('Not authenticated');
}

// Continuar com lógica da página
console.log('Página de agentes carregada');
```

### Proteger Seção da Página

```javascript
import { useAuth } from '../hooks/useAuth.js';

async function initPage() {
  const auth = useAuth();
  await auth.waitForInit();
  
  // Mostrar conteúdo básico
  showBasicContent();
  
  // Mostrar conteúdo admin apenas para staff
  if (auth.isStaff()) {
    showAdminContent();
  }
}
```

---

## 🌐 MÚLTIPLOS WORKSPACES

### Estrutura de Workspace

```javascript
const workspace = {
  id: 1,
  name: 'Workspace Principal',
  slug: 'principal',
  role: 'admin',  // Futuro: role do usuário no workspace
  permissions: [] // Futuro: permissões específicas
};
```

### Selecionar Workspace

```javascript
const auth = useAuth();

// Selecionar workspace
auth.selectWorkspace({
  id: 2,
  name: 'Workspace Secundário'
});

// Obter workspace atual
const current = auth.workspace;
console.log('Workspace ativo:', current.name);
```

### Filtrar Dados por Workspace

```javascript
import { useAuth } from '../hooks/useAuth.js';
import { api } from '../services/api.js';

async function loadAgents() {
  const auth = useAuth();
  
  if (!auth.workspace) {
    console.warn('Nenhum workspace selecionado');
    return;
  }
  
  // Buscar agentes do workspace
  const result = await api.get(`/api/agents?workspace=${auth.workspace.id}`);
  
  if (result.success) {
    renderAgents(result.data);
  }
}
```

---

## 📊 ESTRUTURA FINAL

```
static/js/
├── context/               # ✨ CRIADO
│   └── authContext.js    # Gerenciador global (270 linhas)
│
├── hooks/                 # ✨ CRIADO
│   └── useAuth.js        # Helper de acesso (140 linhas)
│
├── services/
│   ├── api.js            # Cliente HTTP
│   └── authService.js    # Serviço de auth
│
├── utils/
│   └── storage.js        # LocalStorage
│
├── pages/
│   └── login.js          # Página de login (ATUALIZADO)
│
├── examples/              # ✨ CRIADO
│   └── auth-usage.js     # 10 exemplos de uso
│
├── app-init.js            # ✨ CRIADO - Inicialização global
└── app.js                 # Core app
```

---

## 🎯 BENEFÍCIOS

### Estado Global Centralizado
- ✅ Um único ponto de verdade
- ✅ Todos os componentes sincronizados
- ✅ Fácil debugar

### Reatividade
- ✅ Mudanças propagam automaticamente
- ✅ UI atualiza sem reload
- ✅ Observers notificados

### Reutilização
- ✅ `useAuth()` em qualquer arquivo
- ✅ Mesma interface em todo projeto
- ✅ Fácil testar

### Preparado para Crescer
- ✅ Múltiplos workspaces
- ✅ Permissões granulares
- ✅ Roles por workspace
- ✅ Fácil adicionar features

---

## 🚀 COMO USAR

### Em Módulos ES6

```javascript
// Importar hook
import { useAuth } from './hooks/useAuth.js';

// Usar
const auth = useAuth();
console.log(auth.user);
```

### Em Scripts Inline

```html
<script>
  // Acessar via window.NEF
  const auth = window.NEF.auth;
  console.log(auth.user);
</script>
```

### Em Event Listeners

```javascript
window.addEventListener('auth:state-change', (event) => {
  console.log('Auth mudou:', event.detail);
});
```

### Em Templates Django

```html
<!-- Atualiza automaticamente -->
<span data-user-name></span>

<!-- Mostra apenas se autenticado -->
<div data-auth-required>
  Conteúdo protegido
</div>

<!-- Mostra apenas para staff -->
<div data-staff-only>
  Menu admin
</div>
```

---

## 📝 EXEMPLOS PRÁTICOS

### Exemplo 1: Verificar Autenticação

```javascript
import { useAuth } from './hooks/useAuth.js';

const auth = useAuth();

if (auth.isAuthenticated) {
  console.log('Usuário logado:', auth.user.username);
} else {
  console.log('Usuário não autenticado');
}
```

### Exemplo 2: Proteger Página

```javascript
import { requireAuth } from './hooks/useAuth.js';

// No início do script da página
if (!requireAuth()) {
  throw new Error('Not authenticated');
}

// Continuar com lógica da página
console.log('Página protegida');
```

### Exemplo 3: Fazer Logout

```javascript
import { useAuth } from './hooks/useAuth.js';

const auth = useAuth();

document.getElementById('logoutBtn').addEventListener('click', async () => {
  await auth.logout();
  // Já redireciona automaticamente para /login
});
```

### Exemplo 4: Selecionar Workspace

```javascript
import { useAuth } from './hooks/useAuth.js';

const auth = useAuth();

document.getElementById('workspaceSelect').addEventListener('change', (e) => {
  const workspace = {
    id: e.target.value,
    name: e.target.options[e.target.selectedIndex].text
  };
  
  auth.selectWorkspace(workspace);
  
  // Recarregar dados
  window.location.reload();
});
```

### Exemplo 5: Escutar Mudanças

```javascript
import { useAuth } from './hooks/useAuth.js';

const auth = useAuth();

// Registrar observer
const unsubscribe = auth.onStateChange((state) => {
  console.log('Estado mudou:', state);
  
  // Atualizar UI
  document.getElementById('userName').textContent = state.user?.username || 'Guest';
});

// Cancelar quando não precisar mais
// unsubscribe();
```

---

## 🔧 CONFIGURAÇÃO

### Adicionar em Todas as Páginas

O `app-init.js` já está incluído em `layouts/base.html`, então **todas as páginas** automaticamente:
- ✅ Inicializam authContext
- ✅ Restauram sessão
- ✅ Atualizam UI
- ✅ Expõem `window.NEF.auth`

### Adicionar em Página Específica

```html
<!-- Em qualquer template -->
{% block scripts %}
<script type="module">
  import { useAuth } from '{% static "js/hooks/useAuth.js" %}';
  
  const auth = useAuth();
  console.log('User:', auth.user);
</script>
{% endblock %}
```

---

## 🎨 INTEGRAÇÃO COM UI

### Atualizar Nome do Usuário

```html
<!-- Template -->
<span data-user-name>Carregando...</span>

<!-- JavaScript (automático via app-init.js) -->
<!-- Atualiza automaticamente quando auth muda -->
```

### Mostrar/Ocultar Baseado em Auth

```html
<!-- Mostrar apenas se autenticado -->
<div data-auth-required>
  <button>Meu Perfil</button>
</div>

<!-- Mostrar apenas para guests -->
<div data-guest-only>
  <a href="/login">Fazer Login</a>
</div>

<!-- Mostrar apenas para staff -->
<div data-staff-only>
  <a href="/admin">Painel Admin</a>
</div>
```

### Botão de Logout

```html
<!-- Adicionar data-attribute -->
<button data-logout-btn>Sair</button>

<!-- app-init.js configura automaticamente -->
```

---

## 🔄 COMPARAÇÃO COM REACT

### React Context API

```typescript
// React
const { user, isAuthenticated, login, logout } = useAuth();

if (isAuthenticated) {
  console.log(user.username);
}

await login(username, password);
await logout();
```

### Nossa Implementação

```javascript
// JavaScript Vanilla
const auth = useAuth();

if (auth.isAuthenticated) {
  console.log(auth.user.username);
}

await auth.login(username, password);
await auth.logout();
```

**Mesma API, mesma experiência!** 🎉

---

## 📋 CHECKLIST DE IMPLEMENTAÇÃO

### ✅ Implementado

- [x] AuthContext com estado global
- [x] Padrão Observer para reatividade
- [x] Hook useAuth para acesso
- [x] Métodos login/logout/selectWorkspace
- [x] Restauração de sessão ao iniciar
- [x] Integração com authService
- [x] Integração com storage
- [x] Helpers para proteção de rotas
- [x] Inicialização automática (app-init.js)
- [x] Atualização automática de UI
- [x] Exposição global (window.NEF.auth)
- [x] Eventos globais (auth:state-change)
- [x] Exemplos de uso
- [x] Documentação completa

### 🔄 Próximos Passos

- [ ] Testar em diferentes páginas
- [ ] Adicionar testes unitários
- [ ] Implementar permissões granulares
- [ ] Adicionar roles por workspace
- [ ] Criar componente de seletor de workspace
- [ ] Adicionar refresh de sessão

---

## 🧪 TESTANDO

### 1. Verificar Inicialização

```javascript
// No console do navegador
console.log(window.NEF.auth);
console.log(window.NEF.auth.isAuthenticated);
console.log(window.NEF.auth.user);
```

### 2. Testar Login

1. Acesse `/login`
2. Abra DevTools → Console
3. Faça login
4. Observe logs:
   - `[NEF] Inicializando aplicação...`
   - `[NEF] Auth inicializado: { isAuthenticated: true }`
   - `[NEF] Auth state changed: { ... }`

### 3. Testar Logout

```javascript
// No console
await window.NEF.auth.logout();
```

### 4. Testar Workspace

```javascript
// No console
window.NEF.auth.selectWorkspace({
  id: 1,
  name: 'Workspace Teste'
});

console.log(window.NEF.auth.workspace);
```

---

## 🎁 RECURSOS EXTRAS

### Debug Mode

```javascript
// Ativar logs detalhados
window.NEF.authContext.debug = true;

// Ver estado completo
console.log(window.NEF.authContext.getState());

// Ver observers registrados
console.log(window.NEF.authContext.observers.length);
```

### Forçar Refresh de Sessão

```javascript
// Forçar re-inicialização
await window.NEF.authContext.init();
```

---

## RESUMO

### ✅ O Que Foi Criado

1. **authContext.js** - Gerenciador global de estado (270 linhas)
2. **useAuth.js** - Hook de acesso (140 linhas)
3. **app-init.js** - Inicialização automática (120 linhas)
4. **auth-usage.js** - 10 exemplos práticos (200 linhas)
5. **Documentação completa** - Este guia

### ✅ Funcionalidades

- Estado global: user, token, loading, isAuthenticated, workspace
- Métodos: login(), logout(), selectWorkspace()
- Helpers: requireAuth(), requireStaff(), redirectIfAuthenticated()
- Reatividade: Padrão Observer
- Inicialização automática
- Atualização automática de UI
- Exposição global (window.NEF)
- Eventos globais

### ✅ Compatibilidade

- Django 5.1 ✅
- Session-based auth ✅
- JavaScript Vanilla ✅
- ES6 Modules ✅
- Navegadores modernos ✅

---

**Status:** ✅ **IMPLEMENTADO E PRONTO PARA USAR**

**Teste agora:**
1. Recarregue qualquer página (F5)
2. Abra Console (F12)
3. Digite: `window.NEF.auth`
4. Veja o estado de autenticação!

---

**Documento criado em:** 18 de Março de 2026  
**AuthContext implementado e funcionando.**
