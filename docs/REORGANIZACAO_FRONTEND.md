# Reorganização do Frontend - NEF Cadência

**Data:** 18 de Março de 2026  
**Objetivo:** Reorganizar frontend Django para arquitetura profissional e escalável  
**Status:** 📋 PLANEJAMENTO - Aguardando aprovação

---

## ÍNDICE

1. [Análise da Estrutura Atual](#1-análise-da-estrutura-atual)
2. [Nova Estrutura Proposta](#2-nova-estrutura-proposta)
3. [Mapeamento de Arquivos](#3-mapeamento-de-arquivos)
4. [Componentes a Criar](#4-componentes-a-criar)
5. [JavaScript Modularizado](#5-javascript-modularizado)
6. [Plano de Migração](#6-plano-de-migração)
7. [Cuidados e Riscos](#7-cuidados-e-riscos)

---

## 1. ANÁLISE DA ESTRUTURA ATUAL

### 1.1 Templates Existentes (27 arquivos)

```
templates/
├── accounts/
│   └── login.html                    # Página de login (172 linhas)
│
├── admin/                             # Django Admin customizado
│   ├── base.html
│   ├── base_site.html
│   ├── index.html
│   ├── app_list.html
│   ├── partials/
│   │   └── sidebar_menu.html
│   └── includes/
│       └── sidebar_apps.html
│
├── assistant/
│   ├── page.html                      # Página do assistente
│   └── _assistant_widget.html         # Widget (partial)
│
├── core/
│   └── settings_hub.html              # Central de configurações
│
├── monitoring/                        # 12 templates
│   ├── dashboard_executive.html       # Dashboard principal
│   ├── dashboard_productivity.html
│   ├── dashboard_risk.html
│   ├── dashboard_pipeline.html
│   ├── dashboard_day_detail.html
│   ├── agents_list.html
│   ├── agent_detail.html
│   ├── runs_list.html
│   ├── run_detail.html
│   ├── pause_classification.html
│   ├── _dashboard_nav.html            # Partial
│   └── _dashboard_filters.html        # Partial
│
├── layouts/
│   ├── base.html                      # Layout principal (188 linhas)
│   └── auth.html                      # Layout autenticação (141 linhas)
│
├── partials/
│   └── sidebar.html                   # Menu lateral
│
├── base.html                          # Wrapper (7 linhas)
└── dashboard.html                     # Dashboard (72KB!)
```

### 1.2 Static Files Existentes

```
static/
├── css/
│   ├── app.css                        # TailwindCSS compilado (49KB)
│   └── admin_custom.css               # Admin styles (20KB)
│
├── js/
│   ├── app.js                         # JavaScript principal (304 linhas)
│   └── admin_ui.js                    # Admin UI (4.8KB)
│
└── assistant/                         # Assets do assistente
    ├── assistant_widget.css
    ├── assistant_widget.js
    ├── assistant_processing_ui.js
    └── assistant_message_rendering.js
```

### 1.3 Problemas Identificados

**Templates:**
- ❌ `dashboard.html` com 72KB (gigante!)
- ❌ Poucos partials reutilizáveis
- ❌ Código HTML duplicado
- ❌ Sem componentização clara
- ❌ Estilos inline em alguns templates

**JavaScript:**
- ❌ `app.js` com 304 linhas (tudo em um arquivo)
- ❌ Sem modularização
- ❌ Código duplicado (fetch, validações)
- ❌ Sem separação de responsabilidades

**CSS:**
- ✅ TailwindCSS bem usado
- ⚠️ Alguns estilos customizados poderiam ser componentes

---

## 2. NOVA ESTRUTURA PROPOSTA

### 2.1 Templates Reorganizados

```
templates/
├── components/                        # ✨ NOVO - Componentes reutilizáveis
│   ├── ui/                            # Componentes de UI genéricos
│   │   ├── button.html                # Botões padronizados
│   │   ├── input.html                 # Inputs padronizados
│   │   ├── card.html                  # Cards
│   │   ├── badge.html                 # Badges/tags
│   │   ├── alert.html                 # Alertas
│   │   ├── modal.html                 # Modais
│   │   ├── table.html                 # Tabelas
│   │   ├── pagination.html            # Paginação
│   │   ├── breadcrumb.html            # Breadcrumbs
│   │   └── loading.html               # Loading states
│   │
│   ├── auth/                          # Componentes de autenticação
│   │   ├── login_form.html            # Form de login
│   │   ├── auth_header.html           # Header do login
│   │   └── auth_footer.html           # Footer do login
│   │
│   ├── navigation/                    # Componentes de navegação
│   │   ├── sidebar.html               # Menu lateral
│   │   ├── topbar.html                # Barra superior
│   │   ├── profile_menu.html          # Menu de perfil
│   │   └── mobile_drawer.html         # Drawer mobile
│   │
│   ├── dashboard/                     # Componentes de dashboard
│   │   ├── kpi_card.html              # Card de KPI
│   │   ├── chart_card.html            # Card com gráfico
│   │   ├── filters.html               # Filtros
│   │   ├── nav_tabs.html              # Abas de navegação
│   │   └── stats_grid.html            # Grid de estatísticas
│   │
│   └── assistant/                     # Componentes do assistente
│       ├── widget.html                # Widget
│       ├── chat_message.html          # Mensagem de chat
│       └── chat_input.html            # Input de chat
│
├── pages/                             # ✨ NOVO - Páginas completas
│   ├── auth/
│   │   ├── login.html                 # Página de login
│   │   └── logout.html                # Página de logout
│   │
│   ├── dashboard/
│   │   ├── executive.html             # Dashboard executivo
│   │   ├── productivity.html          # Dashboard produtividade
│   │   ├── risk.html                  # Dashboard risco
│   │   ├── pipeline.html              # Dashboard pipeline
│   │   └── day_detail.html            # Detalhe do dia
│   │
│   ├── monitoring/
│   │   ├── agents_list.html           # Lista de agentes
│   │   ├── agent_detail.html          # Detalhe do agente
│   │   ├── runs_list.html             # Lista de execuções
│   │   ├── run_detail.html            # Detalhe de execução
│   │   └── pause_classification.html  # Classificação de pausas
│   │
│   ├── settings/
│   │   └── hub.html                   # Central de configurações
│   │
│   └── assistant/
│       └── page.html                  # Página do assistente
│
├── layouts/                           # Layouts base (mantidos)
│   ├── base.html                      # Layout principal
│   ├── auth.html                      # Layout autenticação
│   └── admin.html                     # ✨ NOVO - Layout admin
│
└── admin/                             # Admin customizado (mantido)
    └── ... (estrutura atual mantida)
```

### 2.2 Static Files Reorganizados

```
static/
├── js/
│   ├── components/                    # ✨ NOVO - Componentes JS
│   │   ├── modal.js                   # Lógica de modais
│   │   ├── dropdown.js                # Dropdowns
│   │   ├── tabs.js                    # Tabs
│   │   └── theme-switcher.js          # Alternador de tema
│   │
│   ├── services/                      # ✨ NOVO - Serviços
│   │   ├── api.js                     # Cliente API genérico
│   │   ├── auth.js                    # Serviço de autenticação
│   │   ├── dashboard.js               # Serviço de dashboard
│   │   └── assistant.js               # Serviço do assistente
│   │
│   ├── utils/                         # ✨ NOVO - Utilitários
│   │   ├── storage.js                 # LocalStorage helper
│   │   ├── validators.js              # Validações
│   │   ├── formatters.js              # Formatação de dados
│   │   └── dom.js                     # Helpers DOM
│   │
│   ├── pages/                         # ✨ NOVO - Scripts por página
│   │   ├── login.js                   # Lógica da página de login
│   │   ├── dashboard.js               # Lógica do dashboard
│   │   └── agents.js                  # Lógica de agentes
│   │
│   ├── app.js                         # Core app (refatorado)
│   └── admin_ui.js                    # Admin (mantido)
│
├── css/
│   ├── components/                    # ✨ NOVO - Estilos de componentes
│   │   ├── button.css                 # Estilos de botões
│   │   ├── card.css                   # Estilos de cards
│   │   ├── form.css                   # Estilos de forms
│   │   └── table.css                  # Estilos de tabelas
│   │
│   ├── layouts/                       # ✨ NOVO - Estilos de layouts
│   │   ├── auth.css                   # Layout de autenticação
│   │   └── dashboard.css              # Layout de dashboard
│   │
│   ├── theme.css                      # ✨ NOVO - Variáveis de tema
│   ├── app.css                        # TailwindCSS compilado (mantido)
│   └── admin_custom.css               # Admin (mantido)
│
└── assistant/                         # Assistente (mantido)
    └── ... (estrutura atual mantida)
```

---

## 3. MAPEAMENTO DE ARQUIVOS

### 3.1 Arquivos a MOVER

#### Templates

| Origem | Destino | Ação |
|--------|---------|------|
| `accounts/login.html` | `pages/auth/login.html` | Mover + Refatorar |
| `monitoring/dashboard_executive.html` | `pages/dashboard/executive.html` | Mover |
| `monitoring/dashboard_productivity.html` | `pages/dashboard/productivity.html` | Mover |
| `monitoring/dashboard_risk.html` | `pages/dashboard/risk.html` | Mover |
| `monitoring/dashboard_pipeline.html` | `pages/dashboard/pipeline.html` | Mover |
| `monitoring/dashboard_day_detail.html` | `pages/dashboard/day_detail.html` | Mover |
| `monitoring/agents_list.html` | `pages/monitoring/agents_list.html` | Mover |
| `monitoring/agent_detail.html` | `pages/monitoring/agent_detail.html` | Mover |
| `monitoring/runs_list.html` | `pages/monitoring/runs_list.html` | Mover |
| `monitoring/run_detail.html` | `pages/monitoring/run_detail.html` | Mover |
| `monitoring/pause_classification.html` | `pages/monitoring/pause_classification.html` | Mover |
| `core/settings_hub.html` | `pages/settings/hub.html` | Mover |
| `assistant/page.html` | `pages/assistant/page.html` | Mover |
| `partials/sidebar.html` | `components/navigation/sidebar.html` | Mover |
| `monitoring/_dashboard_nav.html` | `components/dashboard/nav_tabs.html` | Mover + Renomear |
| `monitoring/_dashboard_filters.html` | `components/dashboard/filters.html` | Mover + Renomear |
| `assistant/_assistant_widget.html` | `components/assistant/widget.html` | Mover + Renomear |

#### JavaScript

| Origem | Destino | Ação |
|--------|---------|------|
| `js/app.js` (linhas 1-40) | `js/services/api.js` | Extrair |
| `js/app.js` (linhas 41-73) | `js/components/theme-switcher.js` | Extrair |
| `js/app.js` (linhas 74-193) | `js/components/profile-menu.js` | Extrair |
| `js/app.js` (linhas 194-261) | `js/components/mobile-drawer.js` | Extrair |
| `js/app.js` (linhas 262-296) | `js/components/sidebar.js` | Extrair |
| `assistant/assistant_widget.js` | `services/assistant.js` | Refatorar |

### 3.2 Arquivos a MANTER (sem alteração)

**Templates:**
- `layouts/base.html` - Layout principal (apenas ajustar includes)
- `layouts/auth.html` - Layout auth (apenas ajustar includes)
- `admin/*` - Admin customizado (manter como está)
- `base.html` - Wrapper (manter)
- `dashboard.html` - Dashboard (manter temporariamente, refatorar depois)

**Static:**
- `css/app.css` - TailwindCSS compilado
- `css/admin_custom.css` - Admin styles
- `js/admin_ui.js` - Admin UI
- `assistant/*.css` - Estilos do assistente
- `assistant/assistant_processing_ui.js` - Processing UI
- `assistant/assistant_message_rendering.js` - Message rendering

---

## 4. COMPONENTES A CRIAR

### 4.1 Componentes UI Genéricos

#### `components/ui/button.html`
```django
{# Componente de botão reutilizável #}
{% comment %}
Uso:
  {% include "components/ui/button.html" with 
     text="Salvar" 
     type="primary" 
     size="md" 
     icon="save" 
     disabled=False 
  %}
{% endcomment %}

<button 
  type="{{ button_type|default:'button' }}"
  class="btn btn-{{ type|default:'primary' }} btn-{{ size|default:'md' }} 
         {% if disabled %}opacity-50 cursor-not-allowed{% endif %}
         {% if full_width %}w-full{% endif %}"
  {% if disabled %}disabled{% endif %}
  {% if onclick %}onclick="{{ onclick }}"{% endif %}
>
  {% if icon %}
    <i data-lucide="{{ icon }}" class="btn-icon"></i>
  {% endif %}
  <span>{{ text }}</span>
  {% if loading %}
    <svg class="animate-spin h-4 w-4 ml-2" fill="none" viewBox="0 0 24 24">
      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
    </svg>
  {% endif %}
</button>
```

#### `components/ui/input.html`
```django
{# Componente de input reutilizável #}
{% comment %}
Uso:
  {% include "components/ui/input.html" with 
     name="email" 
     label="E-mail" 
     type="email" 
     placeholder="Digite seu e-mail"
     required=True
     error=form.email.errors
  %}
{% endcomment %}

<div class="form-group">
  {% if label %}
    <label for="id_{{ name }}" class="form-label">
      {{ label }}
      {% if required %}<span class="text-red-500">*</span>{% endif %}
    </label>
  {% endif %}
  
  <input
    type="{{ type|default:'text' }}"
    name="{{ name }}"
    id="id_{{ name }}"
    class="form-input {% if error %}border-red-500{% endif %}"
    {% if placeholder %}placeholder="{{ placeholder }}"{% endif %}
    {% if value %}value="{{ value }}"{% endif %}
    {% if required %}required{% endif %}
    {% if disabled %}disabled{% endif %}
  >
  
  {% if error %}
    <p class="form-error">{{ error.0 }}</p>
  {% endif %}
  
  {% if help_text %}
    <p class="form-help">{{ help_text }}</p>
  {% endif %}
</div>
```

#### `components/ui/card.html`
```django
{# Componente de card reutilizável #}
{% comment %}
Uso:
  {% include "components/ui/card.html" with 
     title="Título do Card" 
     subtitle="Subtítulo"
     icon="activity"
  %}
    <p>Conteúdo do card</p>
  {% endinclude %}
{% endcomment %}

<div class="card {{ class|default:'' }}">
  {% if title or icon %}
    <div class="card-header">
      {% if icon %}
        <i data-lucide="{{ icon }}" class="card-icon"></i>
      {% endif %}
      <div class="flex-1">
        {% if title %}
          <h3 class="card-title">{{ title }}</h3>
        {% endif %}
        {% if subtitle %}
          <p class="card-subtitle">{{ subtitle }}</p>
        {% endif %}
      </div>
      {% if actions %}
        <div class="card-actions">
          {{ actions }}
        </div>
      {% endif %}
    </div>
  {% endif %}
  
  <div class="card-body">
    {{ content|default:'' }}
  </div>
  
  {% if footer %}
    <div class="card-footer">
      {{ footer }}
    </div>
  {% endif %}
</div>
```

### 4.2 Componentes de Autenticação

#### `components/auth/login_form.html`
```django
{# Form de login componentizado #}
<form method="post" id="loginForm" class="space-y-6">
  {% csrf_token %}
  
  {% if next %}
    <input type="hidden" name="next" value="{{ next }}">
  {% endif %}
  
  {% if form.errors %}
    {% include "components/ui/alert.html" with 
       type="error" 
       title="Erro ao fazer login"
       message="Usuário ou senha inválidos."
    %}
  {% endif %}
  
  {% include "components/ui/input.html" with 
     name="username" 
     label="Usuário ou E-mail"
     type="text"
     placeholder="Digite seu usuário ou e-mail"
     required=True
     autofocus=True
  %}
  
  {% include "components/ui/input.html" with 
     name="password" 
     label="Senha"
     type="password"
     placeholder="Digite sua senha"
     required=True
     show_toggle=True
  %}
  
  <div class="flex items-center justify-between">
    <label class="flex items-center gap-2">
      <input type="checkbox" name="remember_me" class="form-checkbox">
      <span class="text-sm">Lembrar de mim</span>
    </label>
    <a href="#" class="text-sm text-blue-600 hover:text-blue-700">
      Esqueci minha senha
    </a>
  </div>
  
  {% include "components/ui/button.html" with 
     text="Entrar"
     type="primary"
     full_width=True
     button_type="submit"
  %}
</form>
```

### 4.3 Componentes de Dashboard

#### `components/dashboard/kpi_card.html`
```django
{# Card de KPI #}
<div class="kpi-card">
  <div class="kpi-header">
    <span class="kpi-label">{{ label }}</span>
    {% if trend %}
      <span class="kpi-trend kpi-trend-{{ trend }}">
        <i data-lucide="trending-{{ trend }}"></i>
        {{ trend_value }}%
      </span>
    {% endif %}
  </div>
  <div class="kpi-value">{{ value }}</div>
  {% if subtitle %}
    <div class="kpi-subtitle">{{ subtitle }}</div>
  {% endif %}
</div>
```

---

## 5. JAVASCRIPT MODULARIZADO

### 5.1 Estrutura de Serviços

#### `static/js/services/api.js`
```javascript
/**
 * Cliente API genérico para comunicação com backend Django
 */
class ApiService {
  constructor() {
    this.baseURL = '';
    this.csrfToken = this.getCsrfToken();
  }

  getCsrfToken() {
    const cookie = document.cookie
      .split('; ')
      .find(row => row.startsWith('csrftoken='));
    return cookie ? cookie.split('=')[1] : '';
  }

  async request(url, options = {}) {
    const config = {
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': this.csrfToken,
        ...options.headers
      },
      ...options
    };

    try {
      const response = await fetch(this.baseURL + url, config);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('API Error:', error);
      throw error;
    }
  }

  get(url, options = {}) {
    return this.request(url, { ...options, method: 'GET' });
  }

  post(url, data, options = {}) {
    return this.request(url, {
      ...options,
      method: 'POST',
      body: JSON.stringify(data)
    });
  }

  put(url, data, options = {}) {
    return this.request(url, {
      ...options,
      method: 'PUT',
      body: JSON.stringify(data)
    });
  }

  delete(url, options = {}) {
    return this.request(url, { ...options, method: 'DELETE' });
  }
}

// Exportar instância singleton
export const api = new ApiService();
```

#### `static/js/services/auth.js`
```javascript
/**
 * Serviço de autenticação
 */
import { api } from './api.js';
import { storage } from '../utils/storage.js';

class AuthService {
  async login(username, password, rememberMe = false) {
    try {
      const response = await api.post('/login', {
        username,
        password,
        remember_me: rememberMe
      });

      if (response.success) {
        if (rememberMe) {
          storage.set('user', response.user);
        }
      }

      return response;
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  }

  async logout() {
    try {
      await api.post('/logout');
      storage.remove('user');
      window.location.href = '/login';
    } catch (error) {
      console.error('Logout error:', error);
    }
  }

  getUser() {
    return storage.get('user');
  }

  isAuthenticated() {
    return !!this.getUser();
  }
}

export const auth = new AuthService();
```

### 5.2 Estrutura de Utilitários

#### `static/js/utils/storage.js`
```javascript
/**
 * Helper para LocalStorage
 */
class StorageService {
  set(key, value) {
    try {
      const serialized = JSON.stringify(value);
      localStorage.setItem(key, serialized);
    } catch (error) {
      console.error('Storage set error:', error);
    }
  }

  get(key, defaultValue = null) {
    try {
      const item = localStorage.getItem(key);
      return item ? JSON.parse(item) : defaultValue;
    } catch (error) {
      console.error('Storage get error:', error);
      return defaultValue;
    }
  }

  remove(key) {
    try {
      localStorage.removeItem(key);
    } catch (error) {
      console.error('Storage remove error:', error);
    }
  }

  clear() {
    try {
      localStorage.clear();
    } catch (error) {
      console.error('Storage clear error:', error);
    }
  }
}

export const storage = new StorageService();
```

#### `static/js/utils/validators.js`
```javascript
/**
 * Validadores de formulário
 */
export const validators = {
  required(value) {
    return value && value.trim().length > 0;
  },

  email(value) {
    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return regex.test(value);
  },

  minLength(value, min) {
    return value && value.length >= min;
  },

  maxLength(value, max) {
    return value && value.length <= max;
  },

  password(value) {
    // Mínimo 8 caracteres, 1 maiúscula, 1 minúscula, 1 número
    const regex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d@$!%*?&]{8,}$/;
    return regex.test(value);
  }
};
```

### 5.3 Estrutura de Componentes

#### `static/js/components/theme-switcher.js`
```javascript
/**
 * Componente de alternância de tema
 */
import { storage } from '../utils/storage.js';

class ThemeSwitcher {
  constructor() {
    this.storageKey = 'nef_theme_preference';
    this.themes = ['blue', 'dark', 'light'];
    this.init();
  }

  init() {
    this.applyTheme(this.getCurrentTheme());
    this.bindEvents();
  }

  getCurrentTheme() {
    const saved = storage.get(this.storageKey);
    return this.themes.includes(saved) ? saved : 'blue';
  }

  applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    document.body.setAttribute('data-theme', theme);
    
    // Atualizar botões
    document.querySelectorAll('[data-theme-option]').forEach(button => {
      const isActive = button.getAttribute('data-theme-option') === theme;
      button.classList.toggle('is-active', isActive);
      button.setAttribute('aria-pressed', isActive ? 'true' : 'false');
    });

    // Salvar preferência
    storage.set(this.storageKey, theme);

    // Disparar evento
    document.dispatchEvent(new CustomEvent('theme-change', { 
      detail: { theme } 
    }));
  }

  bindEvents() {
    document.querySelectorAll('[data-theme-option]').forEach(button => {
      button.addEventListener('click', () => {
        const theme = button.getAttribute('data-theme-option');
        this.applyTheme(theme);
      });
    });
  }
}

// Inicializar automaticamente
new ThemeSwitcher();
```

---

## 6. PLANO DE MIGRAÇÃO

### Fase 1: Preparação (Dia 1)
**Objetivo:** Criar estrutura sem quebrar nada

**Ações:**
1. ✅ Criar pastas vazias:
   - `templates/components/`
   - `templates/pages/`
   - `static/js/components/`
   - `static/js/services/`
   - `static/js/utils/`
   - `static/css/components/`

2. ✅ Criar arquivo de configuração:
   - `docs/REORGANIZACAO_FRONTEND.md` (este documento)

**Risco:** Nenhum (apenas criar pastas)

---

### Fase 2: Componentes UI (Dias 2-3)
**Objetivo:** Criar componentes reutilizáveis

**Ações:**
1. Criar componentes UI genéricos:
   - `components/ui/button.html`
   - `components/ui/input.html`
   - `components/ui/card.html`
   - `components/ui/alert.html`
   - `components/ui/badge.html`
   - `components/ui/modal.html`

2. Criar estilos de componentes:
   - `static/css/components/button.css`
   - `static/css/components/form.css`
   - `static/css/components/card.css`

3. Testar componentes em página isolada

**Risco:** Baixo (componentes novos, não afetam código existente)

---

### Fase 3: Modularizar JavaScript (Dias 3-4)
**Objetivo:** Separar `app.js` em módulos

**Ações:**
1. Extrair serviços:
   - `services/api.js`
   - `services/auth.js`

2. Extrair utilitários:
   - `utils/storage.js`
   - `utils/validators.js`
   - `utils/dom.js`

3. Extrair componentes:
   - `components/theme-switcher.js`
   - `components/profile-menu.js`
   - `components/mobile-drawer.js`
   - `components/sidebar.js`

4. Refatorar `app.js` para importar módulos

**Risco:** Médio (alterar JavaScript existente)
**Mitigação:** Testar cada módulo individualmente

---

### Fase 4: Migrar Partials (Dia 5)
**Objetivo:** Mover partials para `components/`

**Ações:**
1. Mover partials:
   - `partials/sidebar.html` → `components/navigation/sidebar.html`
   - `monitoring/_dashboard_nav.html` → `components/dashboard/nav_tabs.html`
   - `monitoring/_dashboard_filters.html` → `components/dashboard/filters.html`
   - `assistant/_assistant_widget.html` → `components/assistant/widget.html`

2. Atualizar includes nos templates que usam esses partials

3. Testar todas as páginas que usam esses componentes

**Risco:** Médio (alterar includes)
**Mitigação:** Buscar todos os `{% include %}` antes de mover

---

### Fase 5: Migrar Páginas (Dias 6-7)
**Objetivo:** Reorganizar páginas em `pages/`

**Ações:**
1. Mover páginas de autenticação:
   - `accounts/login.html` → `pages/auth/login.html`

2. Mover páginas de dashboard:
   - `monitoring/dashboard_*.html` → `pages/dashboard/*.html`

3. Mover páginas de monitoramento:
   - `monitoring/*.html` → `pages/monitoring/*.html`

4. Mover outras páginas:
   - `core/settings_hub.html` → `pages/settings/hub.html`
   - `assistant/page.html` → `pages/assistant/page.html`

5. Atualizar `template_name` nas views

**Risco:** Alto (alterar caminhos de templates)
**Mitigação:** 
- Fazer um de cada vez
- Testar após cada mudança
- Commit após cada página migrada

---

### Fase 6: Refatorar Login (Dia 8)
**Objetivo:** Componentizar página de login

**Ações:**
1. Extrair componentes do login:
   - `components/auth/login_form.html`
   - `components/auth/auth_header.html`
   - `components/auth/auth_footer.html`

2. Refatorar `pages/auth/login.html` para usar componentes

3. Extrair JavaScript do login:
   - `pages/login.js`

4. Testar login completo

**Risco:** Médio (página crítica)
**Mitigação:** Testar extensivamente

---

### Fase 7: Documentação (Dia 9)
**Objetivo:** Documentar nova estrutura

**Ações:**
1. Criar guia de componentes
2. Documentar padrões de uso
3. Criar exemplos
4. Atualizar README

**Risco:** Nenhum

---

## 7. CUIDADOS E RISCOS

### 7.1 Cuidados Essenciais

#### ⚠️ Ao Mover Templates

**Problema:** Django busca templates por caminho relativo
**Solução:** Atualizar `template_name` nas views

**Exemplo:**
```python
# ANTES
class LoginView(DjangoLoginView):
    template_name = 'accounts/login.html'

# DEPOIS
class LoginView(DjangoLoginView):
    template_name = 'pages/auth/login.html'
```

#### ⚠️ Ao Mover Partials

**Problema:** `{% include %}` usa caminho relativo
**Solução:** Buscar e substituir todos os includes

**Comando para buscar:**
```bash
grep -r "{% include 'partials/sidebar.html'" templates/
```

**Substituir:**
```django
{# ANTES #}
{% include 'partials/sidebar.html' %}

{# DEPOIS #}
{% include 'components/navigation/sidebar.html' %}
```

#### ⚠️ Ao Modularizar JavaScript

**Problema:** Navegadores antigos não suportam ES6 modules
**Solução:** Usar `type="module"` nos scripts

**Exemplo:**
```html
<!-- ANTES -->
<script src="{% static 'js/app.js' %}"></script>

<!-- DEPOIS -->
<script type="module" src="{% static 'js/app.js' %}"></script>
```

### 7.2 Riscos por Fase

| Fase | Risco | Impacto | Mitigação |
|------|-------|---------|-----------|
| 1. Preparação | Nenhum | Nenhum | - |
| 2. Componentes UI | Baixo | Baixo | Testar isoladamente |
| 3. Modularizar JS | Médio | Médio | Testar cada módulo |
| 4. Migrar Partials | Médio | Alto | Buscar todos includes |
| 5. Migrar Páginas | Alto | Alto | Um de cada vez |
| 6. Refatorar Login | Médio | Alto | Testar extensivamente |
| 7. Documentação | Nenhum | Nenhum | - |

### 7.3 Checklist de Segurança

Antes de cada mudança:
- [ ] Fazer backup do arquivo original
- [ ] Buscar todas as referências ao arquivo
- [ ] Testar em ambiente local
- [ ] Verificar console do navegador
- [ ] Testar funcionalidade completa
- [ ] Commit com mensagem descritiva

Após cada mudança:
- [ ] Verificar se nada quebrou
- [ ] Testar navegação completa
- [ ] Verificar logs do Django
- [ ] Testar em diferentes navegadores
- [ ] Documentar mudança

### 7.4 Rollback Plan

Se algo quebrar:
1. Reverter último commit: `git revert HEAD`
2. Restaurar arquivo específico: `git checkout HEAD~1 -- arquivo`
3. Voltar para branch anterior: `git checkout main`

---

## 8. BENEFÍCIOS ESPERADOS

### 8.1 Organização

**Antes:**
- Templates espalhados
- JavaScript em um arquivo
- Difícil encontrar código

**Depois:**
- Estrutura clara por tipo
- Módulos separados
- Fácil navegação

### 8.2 Reutilização

**Antes:**
- Código HTML duplicado
- Estilos inline
- Lógica repetida

**Depois:**
- Componentes reutilizáveis
- Estilos consistentes
- Lógica centralizada

### 8.3 Manutenibilidade

**Antes:**
- Difícil alterar UI
- Mudanças em múltiplos lugares
- Risco de quebrar

**Depois:**
- Alterar em um lugar
- Propaga automaticamente
- Menor risco

### 8.4 Escalabilidade

**Antes:**
- Adicionar features é difícil
- Código cresce desordenado
- Performance degrada

**Depois:**
- Fácil adicionar componentes
- Estrutura mantém-se organizada
- Performance otimizada

---

## 9. PRÓXIMOS PASSOS

### Após Esta Reorganização

1. **Componentizar Dashboard** (72KB)
   - Extrair KPIs
   - Extrair gráficos
   - Extrair tabelas

2. **Criar Design System**
   - Documentar componentes
   - Criar Storybook/guia visual
   - Padronizar cores e espaçamentos

3. **Otimizar Performance**
   - Lazy loading de componentes
   - Code splitting
   - Cache de templates

4. **Adicionar Testes**
   - Testes de componentes
   - Testes de integração
   - Testes E2E

---

## RESUMO EXECUTIVO

### O Que Será Feito

✅ Reorganizar templates em `components/`, `pages/`, `layouts/`
✅ Modularizar JavaScript em `services/`, `utils/`, `components/`
✅ Criar componentes UI reutilizáveis
✅ Extrair lógica de negócio para serviços
✅ Manter sistema funcionando durante migração

### O Que NÃO Será Feito

❌ Migrar para React/TypeScript
❌ Reescrever código do zero
❌ Alterar backend Django
❌ Implementar JWT/API REST
❌ Quebrar funcionalidades existentes

### Tempo Estimado

**Total:** 9 dias úteis
- Preparação: 1 dia
- Componentes: 2 dias
- JavaScript: 2 dias
- Migração: 3 dias
- Documentação: 1 dia

### Risco Geral

**Médio** - Mitigado com:
- Migração incremental
- Testes constantes
- Commits frequentes
- Rollback plan

---

**Status:** 📋 AGUARDANDO APROVAÇÃO

**Próximo Passo:** Aguardar confirmação do usuário para iniciar Fase 1.

---

**Documento criado em:** 18 de Março de 2026  
**Nenhuma alteração foi feita no código durante este planejamento.**
