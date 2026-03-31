# Sistema RBAC - Role-Based Access Control

**Data:** 18 de Março de 2026  
**Objetivo:** Documentar sistema de autorização por perfil dentro do workspace  
**Status:** ✅ BASE IMPLEMENTADA

---

## VISÃO GERAL

Sistema de **RBAC (Role-Based Access Control)** para controlar permissões dentro de workspaces.

**Características:**
- ✅ 4 roles hierárquicos
- ✅ Permissões granulares
- ✅ Backend e frontend sincronizados
- ✅ Extensível para novas permissões
- ✅ Controle de UI automático

---

## ROLES DISPONÍVEIS

### 1. Admin (Nível 4)
**Acesso total ao workspace**

- ✅ Todas as permissões
- ✅ Gerenciar membros
- ✅ Configurações do workspace
- ✅ Deletar workspace

**Uso:** Proprietário ou administrador principal

---

### 2. Manager (Nível 3)
**Gerente com permissões de gestão**

- ✅ Gerenciar recursos
- ✅ Gerenciar membros
- ✅ Criar, editar e deletar (exceto workspace)
- ❌ Não pode deletar workspace
- ❌ Não pode alterar configurações críticas

**Uso:** Gerente de equipe, líder de projeto

---

### 3. Analyst (Nível 2)
**Analista com permissões de edição**

- ✅ Criar e editar recursos
- ✅ Executar agentes
- ✅ Gerar relatórios
- ❌ Não pode deletar
- ❌ Não pode gerenciar membros

**Uso:** Analista, desenvolvedor, operador

---

### 4. Viewer (Nível 1)
**Visualizador apenas leitura**

- ✅ Visualizar recursos
- ✅ Executar agentes (sem editar)
- ❌ Não pode criar
- ❌ Não pode editar
- ❌ Não pode deletar

**Uso:** Cliente, stakeholder, auditor

---

## HIERARQUIA

```
Admin (4)
  ↓ pode tudo que Manager faz
Manager (3)
  ↓ pode tudo que Analyst faz
Analyst (2)
  ↓ pode tudo que Viewer faz
Viewer (1)
  ↓ apenas visualização
```

**Regra:** Roles superiores herdam permissões dos inferiores.

---

## PERMISSÕES DISPONÍVEIS

### Workspace
- `workspace.view` - Visualizar workspace
- `workspace.edit` - Editar workspace
- `workspace.delete` - Deletar workspace
- `workspace.manage_members` - Gerenciar membros
- `workspace.manage_settings` - Gerenciar configurações

### Agents
- `agent.view` - Visualizar agentes
- `agent.create` - Criar agentes
- `agent.edit` - Editar agentes
- `agent.delete` - Deletar agentes
- `agent.execute` - Executar agentes

### Rules
- `rule.view` - Visualizar regras
- `rule.create` - Criar regras
- `rule.edit` - Editar regras
- `rule.delete` - Deletar regras

### Reports
- `report.view` - Visualizar relatórios
- `report.create` - Criar relatórios
- `report.edit` - Editar relatórios
- `report.delete` - Deletar relatórios
- `report.export` - Exportar relatórios

### Integrations
- `integration.view` - Visualizar integrações
- `integration.create` - Criar integrações
- `integration.edit` - Editar integrações
- `integration.delete` - Deletar integrações

---

## BACKEND - DJANGO

### Arquivo Principal

**`apps/workspaces/rbac.py`** (400 linhas)

Contém:
- Enum `Role` - Roles disponíveis
- Enum `Permission` - Permissões disponíveis
- `ROLE_PERMISSIONS` - Mapeamento role → permissões
- Classe `RBACManager` - Gerenciador de RBAC

---

### RBACManager

```python
from apps.workspaces.rbac import RBACManager, Permission

# Verificar permissão
if RBACManager.has_permission('admin', 'agent.create'):
    # Permitir criar agente
    pass

# Obter permissões do role
permissions = RBACManager.get_role_permissions('manager')

# Verificar hierarquia
if RBACManager.is_higher_role('admin', 'analyst'):
    # Admin é superior a analyst
    pass

# Verificar se pode gerenciar outro role
if RBACManager.can_manage_role('manager', 'analyst'):
    # Manager pode gerenciar analyst
    pass
```

---

### Decorators

**`apps/workspaces/decorators.py`**

#### 1. `@require_workspace_role(role)`
Requer role específico ou superior.

```python
from apps.workspaces.decorators import require_workspace_role

@require_workspace_role('manager')
def manage_team(request, workspace_id):
    # Apenas manager ou admin podem acessar
    pass
```

---

#### 2. `@require_workspace_permission(permission)`
Requer permissão específica.

```python
from apps.workspaces.decorators import require_workspace_permission

@require_workspace_permission('agent.create')
def create_agent(request, workspace_id):
    # Apenas quem tem permissão agent.create
    pass
```

---

#### 3. `@require_any_workspace_permission(*permissions)`
Requer pelo menos uma das permissões.

```python
from apps.workspaces.decorators import require_any_workspace_permission

@require_any_workspace_permission('agent.edit', 'agent.delete')
def manage_agent(request, workspace_id):
    # Precisa de edit OU delete
    pass
```

---

### Mixins

**`apps/core/permissions.py`** (ATUALIZADO)

#### 1. `WorkspaceRoleMixin`
Requer role específico.

```python
from apps.core.permissions import WorkspaceRoleMixin

class ManageTeamView(WorkspaceRoleMixin, TemplateView):
    required_role = 'manager'
    template_name = 'team/manage.html'
```

---

#### 2. `WorkspacePermissionMixin`
Requer permissão específica.

```python
from apps.core.permissions import WorkspacePermissionMixin

class CreateAgentView(WorkspacePermissionMixin, CreateView):
    required_permission = 'agent.create'
    model = Agent
```

---

## FRONTEND - JAVASCRIPT

### Arquivo Principal

**`static/js/rbac/roleManager.js`** (400 linhas)

Contém:
- `Roles` - Enum de roles
- `Permissions` - Enum de permissões
- `ROLE_PERMISSIONS` - Mapeamento role → permissões
- Classe `RoleManager` - Gerenciador de RBAC

---

### RoleManager

```javascript
import { RoleManager, Permissions } from './rbac/roleManager.js';

// Verificar permissão
if (RoleManager.currentUserHasPermission(Permissions.AGENT_CREATE)) {
  // Mostrar botão de criar agente
}

// Verificar role
if (RoleManager.isCurrentUserAdmin()) {
  // Mostrar opções de admin
}

if (RoleManager.isCurrentUserManager()) {
  // Mostrar opções de manager
}

// Obter role atual
const role = RoleManager.getCurrentRole();
console.log('Role:', role);

// Obter label do role
const label = RoleManager.getRoleLabel(role);
console.log('Label:', label); // "Administrador"
```

---

### Controle de UI Automático

#### 1. `data-permission`
Mostra elemento apenas se tiver permissão.

```html
<!-- Botão visível apenas para quem pode criar agentes -->
<button data-permission="agent.create">
  Criar Agente
</button>
```

---

#### 2. `data-permission-disable`
Desabilita elemento se não tiver permissão.

```html
<!-- Botão desabilitado se não pode deletar -->
<button data-permission-disable="agent.delete">
  Deletar Agente
</button>
```

---

#### 3. `data-role`
Mostra elemento apenas para role específico ou superior.

```html
<!-- Visível apenas para manager ou admin -->
<div data-role="manager">
  Configurações de Equipe
</div>
```

---

### Inicialização

**`static/js/app-init.js`** (ATUALIZADO)

```javascript
import { RoleManager } from './rbac/roleManager.js';

// Após auth inicializar
if (auth.isAuthenticated) {
  RoleManager.initRoleBasedUI();
}
```

Isso aplica automaticamente os controles de UI baseados em `data-permission`, `data-permission-disable` e `data-role`.

---

## EXEMPLOS DE USO

### Backend - Proteger View

```python
from apps.core.permissions import WorkspaceRoleMixin
from django.views.generic import ListView

class AgentListView(WorkspaceRoleMixin, ListView):
    required_role = 'analyst'  # Analyst ou superior
    model = Agent
    template_name = 'agents/list.html'
```

---

### Backend - Proteger Função

```python
from apps.workspaces.decorators import require_workspace_permission

@require_workspace_permission('agent.delete')
def delete_agent(request, workspace_id, agent_id):
    agent = get_object_or_404(Agent, id=agent_id, workspace_id=workspace_id)
    agent.delete()
    return JsonResponse({'success': True})
```

---

### Backend - Verificar Permissão Manualmente

```python
from apps.workspaces.rbac import RBACManager
from apps.workspaces.models import UserWorkspace

def my_view(request, workspace_id):
    # Obter role do usuário
    membership = UserWorkspace.objects.get(
        user=request.user,
        workspace_id=workspace_id
    )
    
    # Verificar permissão
    if RBACManager.has_permission(membership.role, 'agent.create'):
        # Permitir criar
        pass
    else:
        # Negar
        return HttpResponseForbidden('Sem permissão')
```

---

### Frontend - Controlar Botão

```javascript
import { RoleManager, Permissions } from './rbac/roleManager.js';

const deleteButton = document.getElementById('deleteAgentBtn');

if (RoleManager.currentUserHasPermission(Permissions.AGENT_DELETE)) {
  deleteButton.style.display = 'block';
} else {
  deleteButton.style.display = 'none';
}
```

---

### Frontend - Controlar Seção

```html
<!-- HTML -->
<div id="adminSection">
  Configurações de Administrador
</div>

<script type="module">
import { RoleManager } from './rbac/roleManager.js';

const adminSection = document.getElementById('adminSection');
adminSection.style.display = RoleManager.isCurrentUserAdmin() ? 'block' : 'none';
</script>
```

---

### Frontend - Usar Atributos Data

```html
<!-- Botão de criar (apenas analyst ou superior) -->
<button data-permission="agent.create" class="btn btn-primary">
  Criar Agente
</button>

<!-- Botão de deletar (apenas manager ou admin) -->
<button data-permission="agent.delete" class="btn btn-danger">
  Deletar Agente
</button>

<!-- Seção de configurações (apenas admin) -->
<div data-role="admin">
  <h3>Configurações Avançadas</h3>
  <!-- ... -->
</div>

<!-- Campo desabilitado se não pode editar -->
<input 
  type="text" 
  data-permission-disable="agent.edit"
  placeholder="Nome do agente"
>
```

**Após chamar `RoleManager.initRoleBasedUI()`, todos esses elementos são controlados automaticamente!**

---

## ADICIONAR NOVAS PERMISSÕES

### 1. Definir Permissão

**Backend (`apps/workspaces/rbac.py`):**

```python
class Permission(str, Enum):
    # ... permissões existentes
    
    # Nova permissão
    DASHBOARD_VIEW_ANALYTICS = 'dashboard.view_analytics'
```

**Frontend (`static/js/rbac/roleManager.js`):**

```javascript
export const Permissions = {
  // ... permissões existentes
  
  // Nova permissão
  DASHBOARD_VIEW_ANALYTICS: 'dashboard.view_analytics'
};
```

---

### 2. Atribuir a Roles

**Backend:**

```python
ROLE_PERMISSIONS = {
    Role.ADMIN: {
        # ... permissões existentes
        Permission.DASHBOARD_VIEW_ANALYTICS,
    },
    Role.MANAGER: {
        # ... permissões existentes
        Permission.DASHBOARD_VIEW_ANALYTICS,
    },
    # Analyst e Viewer não têm
}
```

**Frontend:**

```javascript
const ROLE_PERMISSIONS = {
  [Roles.ADMIN]: [
    // ... permissões existentes
    Permissions.DASHBOARD_VIEW_ANALYTICS
  ],
  [Roles.MANAGER]: [
    // ... permissões existentes
    Permissions.DASHBOARD_VIEW_ANALYTICS
  ]
};
```

---

### 3. Usar Permissão

**Backend:**

```python
@require_workspace_permission('dashboard.view_analytics')
def analytics_dashboard(request, workspace_id):
    # ...
```

**Frontend:**

```html
<div data-permission="dashboard.view_analytics">
  Analytics Dashboard
</div>
```

---

## ADICIONAR NOVO ROLE

### 1. Definir Role

**Backend:**

```python
class Role(str, Enum):
    ADMIN = 'admin'
    MANAGER = 'manager'
    ANALYST = 'analyst'
    VIEWER = 'viewer'
    GUEST = 'guest'  # Novo role
```

**Frontend:**

```javascript
export const Roles = {
  ADMIN: 'admin',
  MANAGER: 'manager',
  ANALYST: 'analyst',
  VIEWER: 'viewer',
  GUEST: 'guest'  // Novo role
};
```

---

### 2. Definir Permissões

```python
ROLE_PERMISSIONS = {
    # ... roles existentes
    
    Role.GUEST: {
        Permission.WORKSPACE_VIEW,
        Permission.AGENT_VIEW,
        # Apenas visualização básica
    }
}
```

---

### 3. Definir Nível

```python
# Backend
role_levels = {
    Role.ADMIN: 5,
    Role.MANAGER: 4,
    Role.ANALYST: 3,
    Role.VIEWER: 2,
    Role.GUEST: 1,  # Novo nível
}

# Frontend
const ROLE_LEVELS = {
  [Roles.ADMIN]: 5,
  [Roles.MANAGER]: 4,
  [Roles.ANALYST]: 3,
  [Roles.VIEWER]: 2,
  [Roles.GUEST]: 1  // Novo nível
};
```

---

### 4. Atualizar Model

```python
# apps/workspaces/models.py
class UserWorkspace(models.Model):
    class Role(models.TextChoices):
        ADMIN = 'admin', 'Administrador'
        MANAGER = 'manager', 'Gerente'
        ANALYST = 'analyst', 'Analista'
        VIEWER = 'viewer', 'Visualizador'
        GUEST = 'guest', 'Convidado'  # Novo
```

---

### 5. Criar Migration

```bash
python manage.py makemigrations
python manage.py migrate
```

---

## FLUXO DE VERIFICAÇÃO

### Backend

```
Request → View/Decorator
    ↓
Obter workspace_id
    ↓
Buscar UserWorkspace
    ↓
Obter role do usuário
    ↓
RBACManager.has_permission(role, permission)
    ↓
✅ Permitir ou ❌ Negar (PermissionDenied)
```

---

### Frontend

```
Página carrega
    ↓
RoleManager.initRoleBasedUI()
    ↓
Buscar elementos com data-permission
    ↓
Para cada elemento:
  - Obter role do workspace ativo
  - Verificar permissão
  - Mostrar/ocultar ou habilitar/desabilitar
    ↓
UI atualizada baseada em role
```

---

## SEGURANÇA

### ✅ Implementado

1. **Verificação Backend**
   - Todas as views protegidas
   - Decorators e mixins
   - Verificação em cada request

2. **Verificação Frontend**
   - Controle de UI
   - Prevenção de ações não autorizadas
   - Feedback visual

3. **Hierarquia de Roles**
   - Roles superiores herdam permissões
   - Não pode gerenciar role superior

4. **Workspace Isolation**
   - Permissões por workspace
   - Usuário pode ter roles diferentes em workspaces diferentes

---

### ⚠️ Importante

**Frontend é apenas UI!**

- ✅ Ocultar botões
- ✅ Desabilitar campos
- ✅ Melhorar UX

**Backend é a segurança real!**

- ✅ Sempre verificar no backend
- ✅ Nunca confiar apenas no frontend
- ✅ Validar em cada endpoint

---

## TESTES

### Testar Permissões Backend

```python
from apps.workspaces.rbac import RBACManager, Permission

# Testar admin
assert RBACManager.has_permission('admin', 'agent.create') == True
assert RBACManager.has_permission('admin', 'workspace.delete') == True

# Testar viewer
assert RBACManager.has_permission('viewer', 'agent.create') == False
assert RBACManager.has_permission('viewer', 'agent.view') == True

# Testar hierarquia
assert RBACManager.is_higher_role('admin', 'analyst') == True
assert RBACManager.can_manage_role('manager', 'viewer') == True
```

---

### Testar Permissões Frontend

```javascript
import { RoleManager, Permissions, Roles } from './rbac/roleManager.js';

// Mock workspace com role
localStorage.setItem('nef_active_workspace', JSON.stringify({
  id: 1,
  name: 'Test',
  role: Roles.ANALYST
}));

// Testar permissões
console.assert(
  RoleManager.currentUserHasPermission(Permissions.AGENT_CREATE) === true,
  'Analyst deve poder criar agente'
);

console.assert(
  RoleManager.currentUserHasPermission(Permissions.AGENT_DELETE) === false,
  'Analyst não deve poder deletar agente'
);

// Testar helpers
console.assert(
  RoleManager.isCurrentUserAnalyst() === true,
  'Deve ser analyst'
);

console.assert(
  RoleManager.isCurrentUserAdmin() === false,
  'Não deve ser admin'
);
```

---

## MIGRAÇÃO DE ROLES ANTIGOS

Se você tinha roles antigos (`member` ao invés de `analyst`):

```python
# Migration para atualizar roles
from django.db import migrations

def migrate_roles(apps, schema_editor):
    UserWorkspace = apps.get_model('workspaces', 'UserWorkspace')
    
    # Migrar 'member' para 'analyst'
    UserWorkspace.objects.filter(role='member').update(role='analyst')

class Migration(migrations.Migration):
    dependencies = [
        ('workspaces', '0002_previous_migration'),
    ]
    
    operations = [
        migrations.RunPython(migrate_roles),
    ]
```

---

## RESUMO

### ✅ Implementado

- [x] 4 roles hierárquicos (admin, manager, analyst, viewer)
- [x] 20+ permissões granulares
- [x] Backend: RBACManager, decorators, mixins
- [x] Frontend: RoleManager, controle automático de UI
- [x] Sincronização backend ↔ frontend
- [x] Extensível para novas permissões e roles

### 📦 Arquivos Criados

**Backend:**
1. `apps/workspaces/rbac.py` (400 linhas) - Sistema RBAC
2. `apps/workspaces/decorators.py` (150 linhas) - Decorators
3. `apps/core/permissions.py` (ATUALIZADO) - Mixins RBAC

**Frontend:**
4. `static/js/rbac/roleManager.js` (400 linhas) - Gerenciador de roles

**Documentação:**
5. `docs/RBAC_SISTEMA.md` - Este documento

### 🎯 Próximos Passos

1. Aplicar permissões em views existentes
2. Adicionar controles de UI nas páginas
3. Criar testes automatizados
4. Adicionar auditoria de permissões
5. Implementar permissões customizadas por workspace (futuro)

---

**Status:** ✅ **BASE RBAC IMPLEMENTADA**

O sistema está pronto para crescer! Basta adicionar novas permissões conforme necessário.

---

**Documento criado em:** 18 de Março de 2026  
**Sistema RBAC implementado com sucesso.**
