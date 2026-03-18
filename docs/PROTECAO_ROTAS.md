# Proteção de Rotas - NEF Cadência

**Data:** 18 de Março de 2026  
**Objetivo:** Documentar sistema de proteção de rotas frontend e backend  
**Status:** ✅ IMPLEMENTADO

---

## VISÃO GERAL

Sistema completo de proteção de rotas com:
- **Frontend:** AuthGuard para rotas JavaScript
- **Backend:** Mixins e permissions para views Django
- **Reutilizável:** Fácil aplicar em novas rotas
- **Extensível:** Preparado para permissões por role

---

## FRONTEND - AUTH GUARD

### Arquivo Principal

**`static/js/guards/authGuard.js`**

Classe singleton que gerencia proteção de rotas no frontend.

### Métodos Principais

#### 1. `protect(options)`
Protege uma rota com opções customizáveis.

```javascript
import { AuthGuard } from './guards/authGuard.js';

// Proteger rota simples
AuthGuard.protect({
  requireAuth: true,
  requireWorkspace: false
});
```

**Opções:**
- `requireAuth` (boolean) - Requer autenticação (default: true)
- `requireWorkspace` (boolean) - Requer workspace selecionado (default: false)
- `redirectTo` (string) - URL customizada de redirecionamento

---

#### 2. `protectPage(options)`
Protege página inteira. Lança exceção se acesso negado.

```javascript
// No início do script da página
try {
  AuthGuard.protectPage({
    requireAuth: true,
    requireWorkspace: true
  });
} catch (error) {
  // Página será redirecionada automaticamente
}
```

---

#### 3. `hasRole(role)`
Verifica se usuário tem role específico.

```javascript
if (AuthGuard.hasRole('admin')) {
  // Mostrar opções de admin
}
```

**Roles disponíveis:**
- `admin` - Administrador (nível 3)
- `member` - Membro (nível 2)
- `viewer` - Visualizador (nível 1)

**Hierarquia:** Admin pode fazer tudo que Member faz, Member pode fazer tudo que Viewer faz.

---

#### 4. `requireRole(role, message)`
Protege ação que requer role específico.

```javascript
function deleteItem() {
  if (!AuthGuard.requireRole('admin', 'Apenas admins podem deletar')) {
    return;
  }
  
  // Executar ação
}
```

---

#### 5. Helpers de Role

```javascript
// Verificar se é admin
if (AuthGuard.isAdmin()) {
  // ...
}

// Verificar se pode editar (admin ou member)
if (AuthGuard.canEdit()) {
  // ...
}

// Verificar se é apenas viewer
if (AuthGuard.isViewer()) {
  // ...
}
```

---

### Uso em Páginas

#### Dashboard (Requer Auth + Workspace)

**`static/js/pages/dashboard-guard.js`**

```javascript
import { AuthGuard } from '../guards/authGuard.js';

try {
  AuthGuard.protectPage({
    requireAuth: true,
    requireWorkspace: true
  });
} catch (error) {
  // Redirecionado automaticamente
}
```

**Incluir no HTML:**

```html
<!-- templates/dashboard.html -->
<script type="module" src="{% static 'js/pages/dashboard-guard.js' %}"></script>
<script type="module" src="{% static 'js/pages/dashboard.js' %}"></script>
```

---

#### Seleção de Workspace (Requer Auth)

**`static/js/pages/workspace-selection-guard.js`**

```javascript
import { AuthGuard } from '../guards/authGuard.js';

try {
  AuthGuard.protectPage({
    requireAuth: true,
    requireWorkspace: false  // Não requer workspace pois é onde seleciona
  });
} catch (error) {
  // Redirecionado automaticamente
}
```

---

#### Login (Rota Pública)

```javascript
import { AuthGuard } from '../guards/authGuard.js';

// Redirecionar se já autenticado
AuthGuard.redirectAuthenticatedUser();
```

---

### Inicialização Global

**`static/js/app-init.js`**

```javascript
import { AuthGuard } from './guards/authGuard.js';

async function initApp() {
  // Inicializar AuthGuard
  AuthGuard.init();
  
  // ... resto da inicialização
}
```

O `AuthGuard.init()` configura:
- Listener para mudanças de autenticação
- Listener para mudanças de workspace
- Redirecionamento automático ao deslogar

---

## BACKEND - DJANGO PERMISSIONS

### Mixins Disponíveis

**`apps/core/permissions.py`**

#### 1. `StaffPermissionMixin`
Requer usuário staff.

```python
from apps.core.permissions import StaffPermissionMixin

class AdminDashboardView(StaffPermissionMixin, TemplateView):
    template_name = 'admin/dashboard.html'
```

---

#### 2. `SuperuserPermissionMixin`
Requer superusuário.

```python
from apps.core.permissions import SuperuserPermissionMixin

class SystemConfigView(SuperuserPermissionMixin, UpdateView):
    # ...
```

---

#### 3. `WorkspaceAccessMixin` ✨ NOVO
Requer acesso ao workspace.

```python
from apps.core.permissions import WorkspaceAccessMixin

class WorkspaceDetailView(WorkspaceAccessMixin, DetailView):
    model = Workspace
    
    # workspace_id virá de kwargs ou sessão
```

**Verifica:**
- Usuário autenticado
- Usuário é membro do workspace
- Workspace está ativo

---

#### 4. `WorkspaceAdminMixin` ✨ NOVO
Requer ser admin do workspace.

```python
from apps.core.permissions import WorkspaceAdminMixin

class WorkspaceSettingsView(WorkspaceAdminMixin, UpdateView):
    model = Workspace
    
    # Apenas admins do workspace podem acessar
```

---

### API REST - DRF Permissions

**Django REST Framework já está configurado com JWT.**

**`alive_platform/settings_jwt.py`**

```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}
```

**Todas as API views requerem autenticação por padrão.**

Para rotas públicas:

```python
from rest_framework.permissions import AllowAny

class PublicAPIView(APIView):
    permission_classes = [AllowAny]
```

---

### Workspace Permissions (API)

**`apps/workspaces/permissions.py`** (já criado anteriormente)

```python
from apps.workspaces.permissions import WorkspacePermission

class WorkspaceAPIView(APIView):
    def get(self, request, workspace_id):
        workspace = get_object_or_404(Workspace, id=workspace_id)
        
        # Verificar acesso
        WorkspacePermission.check_workspace_access(request.user, workspace)
        
        # ... resto da lógica
```

**Métodos disponíveis:**
- `check_workspace_access()` - Lança exceção se sem acesso
- `check_workspace_admin()` - Lança exceção se não admin
- `can_view()` - Retorna bool
- `can_edit()` - Retorna bool
- `can_delete()` - Retorna bool

---

## FLUXO DE PROTEÇÃO

### Frontend

```
1. Usuário acessa /dashboard
   ↓
2. dashboard-guard.js executa
   ↓
3. AuthGuard.protectPage() verifica:
   - Token JWT existe?
   - User no storage?
   - Workspace selecionado?
   ↓
4a. ✅ Acesso permitido → Carrega página
4b. ❌ Sem auth → Redireciona para /login
4c. ❌ Sem workspace → Redireciona para /select-workspace
```

---

### Backend (Django Views)

```
1. Request para view protegida
   ↓
2. Mixin verifica permissão
   ↓
3. test_func() retorna True/False
   ↓
4a. ✅ True → Processa view
4b. ❌ False → handle_no_permission()
   ↓
5. Redireciona com mensagem de erro
```

---

### Backend (API REST)

```
1. Request para API endpoint
   ↓
2. JWTAuthentication verifica token
   ↓
3. Token válido?
   ↓
4a. ✅ Válido → Processa request
4b. ❌ Inválido → 401 Unauthorized
   ↓
5. Frontend detecta 401 → Tenta refresh
   ↓
6a. ✅ Refresh ok → Retry request
6b. ❌ Refresh falhou → Redireciona para login
```

---

## EXEMPLOS DE USO

### Proteger Nova Página

**1. Criar guard:**

```javascript
// static/js/pages/minha-pagina-guard.js
import { AuthGuard } from '../guards/authGuard.js';

try {
  AuthGuard.protectPage({
    requireAuth: true,
    requireWorkspace: true
  });
} catch (error) {
  // Redirecionado
}
```

**2. Incluir no template:**

```html
<!-- templates/minha-pagina.html -->
<script type="module" src="{% static 'js/pages/minha-pagina-guard.js' %}"></script>
<script type="module" src="{% static 'js/pages/minha-pagina.js' %}"></script>
```

---

### Proteger Ação Específica

```javascript
// Botão de deletar (apenas admin)
deleteButton.addEventListener('click', () => {
  if (!AuthGuard.requireRole('admin', 'Apenas admins podem deletar')) {
    return;
  }
  
  // Executar delete
  deleteItem();
});
```

---

### Proteger View Django

```python
from apps.core.permissions import WorkspaceAccessMixin
from django.views.generic import ListView

class MyProtectedView(WorkspaceAccessMixin, ListView):
    model = MyModel
    template_name = 'my_template.html'
    
    # Automaticamente protegido
    # Requer acesso ao workspace
```

---

### Proteger API Endpoint

```python
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from apps.workspaces.permissions import WorkspacePermission

class MyAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, workspace_id):
        workspace = get_object_or_404(Workspace, id=workspace_id)
        
        # Verificar acesso
        WorkspacePermission.check_workspace_access(request.user, workspace)
        
        # Processar
        return Response({'status': 'ok'})
```

---

## ROTAS PROTEGIDAS ATUALMENTE

### Frontend

| Rota | Requer Auth | Requer Workspace | Guard |
|------|-------------|------------------|-------|
| `/login` | ❌ | ❌ | Redireciona se autenticado |
| `/select-workspace` | ✅ | ❌ | workspace-selection-guard.js |
| `/dashboard` | ✅ | ✅ | dashboard-guard.js |

---

### Backend (API)

| Endpoint | Autenticação | Permissão |
|----------|--------------|-----------|
| `POST /api/auth/login` | ❌ Público | AllowAny |
| `POST /api/auth/refresh` | ❌ Público | AllowAny |
| `GET /api/auth/me` | ✅ JWT | IsAuthenticated |
| `POST /api/auth/logout` | ✅ JWT | IsAuthenticated |
| `GET /api/workspaces` | ✅ JWT | IsAuthenticated |
| `POST /api/workspaces/select` | ✅ JWT | IsAuthenticated |

---

## ADICIONAR PROTEÇÃO EM NOVAS ROTAS

### Checklist Frontend

- [ ] Criar guard file (ex: `minha-pagina-guard.js`)
- [ ] Importar `AuthGuard`
- [ ] Chamar `AuthGuard.protectPage()`
- [ ] Incluir guard no template HTML
- [ ] Testar acesso sem autenticação
- [ ] Testar acesso sem workspace (se aplicável)

---

### Checklist Backend (Views)

- [ ] Importar mixin apropriado
- [ ] Adicionar mixin à view
- [ ] Testar acesso sem autenticação
- [ ] Testar acesso sem permissão
- [ ] Verificar mensagem de erro

---

### Checklist Backend (API)

- [ ] Adicionar `permission_classes`
- [ ] Verificar workspace access (se aplicável)
- [ ] Testar com token inválido
- [ ] Testar com token expirado
- [ ] Testar sem token

---

## PERMISSÕES POR ROLE

### Hierarquia

```
Admin (nível 3)
  ↓ pode tudo que Member faz
Member (nível 2)
  ↓ pode tudo que Viewer faz
Viewer (nível 1)
  ↓ apenas visualização
```

### Verificação

**Frontend:**

```javascript
// Verificar role
if (AuthGuard.hasRole('member')) {
  // Mostrar botão de editar
}

// Proteger ação
if (!AuthGuard.requireRole('admin')) {
  return; // Bloqueado
}
```

**Backend:**

```python
# Verificar role
from apps.workspaces import selectors

role = selectors.get_user_role_in_workspace(user, workspace)

if role == 'admin':
    # Permitir
    pass
```

---

## SEGURANÇA

### ✅ Implementado

1. **JWT Tokens**
   - Access token: 1 hora
   - Refresh token: 7 dias
   - Auto-refresh em 401

2. **Bcrypt**
   - Senhas hasheadas
   - Salt automático

3. **CORS**
   - Origens permitidas configuradas
   - Credentials habilitado

4. **CSRF**
   - Token em todas as requisições
   - Validação no backend

5. **Workspace Isolation**
   - Verificação de acesso
   - Queries filtradas por workspace

---

### ⚠️ Recomendações Futuras

1. **Rate Limiting**
   - Limitar tentativas de login
   - Throttle em API endpoints

2. **2FA**
   - Two-factor authentication
   - TOTP ou SMS

3. **Audit Log**
   - Registrar acessos
   - Rastrear mudanças

4. **IP Whitelist**
   - Restringir IPs permitidos
   - Geolocalização

5. **Session Management**
   - Logout em todas as abas
   - Timeout de inatividade

---

## TROUBLESHOOTING

### Problema: Redirecionamento infinito

**Causa:** Guard protegendo página de login

**Solução:** Não proteger rotas públicas

```javascript
// ❌ Errado
// login.js
AuthGuard.protectPage({ requireAuth: true });

// ✅ Correto
// login.js
AuthGuard.redirectAuthenticatedUser();
```

---

### Problema: 401 em todas as requisições

**Causa:** Token não está sendo enviado

**Solução:** Verificar se `api.js` adiciona header

```javascript
// api.js
const token = this.getAuthToken();
if (token) {
  headers['Authorization'] = `Bearer ${token}`;
}
```

---

### Problema: Workspace não encontrado

**Causa:** Workspace não está no storage

**Solução:** Selecionar workspace após login

```javascript
// Após login
const workspaces = result.workspaces;
if (workspaces.length === 1) {
  authContext.selectWorkspace(workspaces[0]);
}
```

---

## TESTES

### Testar Proteção Frontend

```javascript
// 1. Limpar storage
localStorage.clear();

// 2. Tentar acessar /dashboard
// Deve redirecionar para /login

// 3. Fazer login
// Deve permitir acesso

// 4. Limpar workspace
localStorage.removeItem('nef_active_workspace');

// 5. Tentar acessar /dashboard
// Deve redirecionar para /select-workspace
```

---

### Testar Proteção Backend

```bash
# 1. Tentar acessar API sem token
curl http://localhost:8000/api/auth/me

# Deve retornar 401

# 2. Fazer login
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' \
  | jq -r '.token')

# 3. Acessar com token
curl http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer $TOKEN"

# Deve retornar dados do usuário
```

---

## RESUMO

### ✅ Implementado

- [x] AuthGuard frontend
- [x] Guards para páginas específicas
- [x] Mixins Django para views
- [x] JWT authentication no DRF
- [x] Workspace permissions
- [x] Role-based access control
- [x] Auto-refresh de token
- [x] Redirecionamento automático

### 📊 Arquivos Criados

**Frontend:**
1. `static/js/guards/authGuard.js` - Sistema de proteção
2. `static/js/pages/dashboard-guard.js` - Guard do dashboard
3. `static/js/pages/workspace-selection-guard.js` - Guard de seleção

**Backend:**
4. `apps/core/permissions.py` - Mixins atualizados (WorkspaceAccessMixin, WorkspaceAdminMixin)

**Documentação:**
5. `docs/PROTECAO_ROTAS.md` - Este documento

### 🎯 Próximos Passos

1. Aplicar guards em todas as páginas protegidas
2. Adicionar testes automatizados
3. Implementar rate limiting
4. Adicionar audit log
5. Configurar 2FA (futuro)

---

**Status:** ✅ **PROTEÇÃO DE ROTAS IMPLEMENTADA**

O sistema está protegido tanto no frontend quanto no backend. Basta aplicar os guards nas páginas e mixins nas views!

---

**Documento criado em:** 18 de Março de 2026  
**Sistema de proteção de rotas implementado com sucesso.**
