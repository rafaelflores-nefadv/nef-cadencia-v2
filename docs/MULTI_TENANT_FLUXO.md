# Fluxo Multi-Tenant - NEF Cadência

**Data:** 18 de Março de 2026  
**Objetivo:** Implementar seleção de workspace multi-tenant  
**Status:** ✅ IMPLEMENTADO

---

## VISÃO GERAL

Sistema multi-tenant onde um usuário pode pertencer a múltiplos workspaces e precisa selecionar qual workspace deseja acessar após o login.

---

## FLUXO COMPLETO

### Cenário 1: Usuário com 1 Workspace

```
1. Usuário faz login
   ↓
2. Backend retorna workspaces do usuário
   ↓
3. Frontend detecta apenas 1 workspace
   ↓
4. Seleciona automaticamente
   ↓
5. Salva no authContext e storage
   ↓
6. Redireciona para /dashboard
```

### Cenário 2: Usuário com Múltiplos Workspaces

```
1. Usuário faz login
   ↓
2. Backend retorna workspaces do usuário
   ↓
3. Frontend detecta múltiplos workspaces
   ↓
4. Redireciona para /select-workspace
   ↓
5. Usuário vê lista de workspaces
   ↓
6. Usuário clica em um workspace
   ↓
7. Salva no authContext e storage
   ↓
8. Redireciona para /dashboard
```

### Cenário 3: Usuário sem Workspaces

```
1. Usuário faz login
   ↓
2. Backend retorna lista vazia
   ↓
3. Frontend mostra erro
   ↓
4. "Você não possui acesso a nenhum workspace"
   ↓
5. Usuário deve contatar administrador
```

---

## ARQUIVOS CRIADOS/MODIFICADOS

### 1. `templates/pages/select_workspace.html` (CRIADO)
**Página de Seleção de Workspace**

**Características:**
- ✅ Layout elegante e profissional
- ✅ Cards de workspace com informações
- ✅ Ícones personalizados por workspace
- ✅ Badge de role (Admin, Membro, Visualizador)
- ✅ Contagem de membros
- ✅ Loading states
- ✅ Error states
- ✅ Empty state
- ✅ Animações suaves
- ✅ Responsivo

**Estados:**
- Loading - Carregando workspaces
- List - Lista de workspaces
- Error - Erro ao carregar
- Empty - Sem workspaces

---

### 2. `static/js/services/authService.js` (ATUALIZADO)
**Adicionado método `getUserWorkspaces()`**

```javascript
async getUserWorkspaces() {
  // TODO: Implementar endpoint real
  // const result = await api.get('/api/workspaces');
  
  // MOCK: Retorna dados de exemplo
  return {
    success: true,
    workspaces: [...]
  };
}
```

---

### 3. `static/js/pages/login.js` (ATUALIZADO)
**Adicionado lógica de verificação de workspaces**

**Novo método:** `handleWorkspaceRedirect()`

```javascript
async handleWorkspaceRedirect() {
  // Buscar workspaces
  const result = await authService.getUserWorkspaces();
  
  if (workspaces.length === 0) {
    // Mostrar erro
  } else if (workspaces.length === 1) {
    // Selecionar automaticamente
    auth.selectWorkspace(workspaces[0]);
    window.location.href = '/dashboard';
  } else {
    // Redirecionar para seleção
    window.location.href = '/select-workspace';
  }
}
```

---

### 4. `apps/core/views.py` (ATUALIZADO)
**Adicionada view `SelectWorkspaceView`**

```python
class SelectWorkspaceView(LoginRequiredMixin, TemplateView):
    template_name = 'pages/select_workspace.html'
    login_url = 'login'
```

---

### 5. `apps/core/urls.py` (ATUALIZADO)
**Adicionada rota `/select-workspace/`**

```python
path('select-workspace/', SelectWorkspaceView.as_view(), name='select-workspace')
```

---

## ESTRUTURA DE WORKSPACE

### Modelo de Dados

```javascript
{
  id: 1,
  name: 'Workspace Principal',
  slug: 'principal',
  description: 'Ambiente principal de produção',
  role: 'admin',           // Role do usuário neste workspace
  members_count: 15,       // Quantidade de membros
  icon: 'briefcase'        // Ícone do workspace
}
```

### Roles Disponíveis

1. **admin** - Administrador
   - Acesso total
   - Pode gerenciar membros
   - Pode alterar configurações

2. **member** - Membro
   - Acesso completo às funcionalidades
   - Não pode gerenciar membros
   - Não pode alterar configurações

3. **viewer** - Visualizador
   - Apenas leitura
   - Não pode criar/editar
   - Não pode deletar

---

## INTERFACE DA PÁGINA

### Layout

```
┌─────────────────────────────────────────────────┐
│  [Logo] NEF Cadência                            │
│  Selecione seu Workspace                        │
│  Escolha o ambiente de trabalho                 │
├─────────────────────────────────────────────────┤
│                                                 │
│  ┌───────────────────────────────────────────┐ │
│  │ [Icon] Workspace Principal          Admin │ │
│  │ Ambiente principal de produção            │ │
│  │ 👥 15 membros  🛡️ Administrador      →   │ │
│  └───────────────────────────────────────────┘ │
│                                                 │
│  ┌───────────────────────────────────────────┐ │
│  │ [Icon] Workspace de Testes                │ │
│  │ Ambiente de testes e desenvolvimento      │ │
│  │ 👥 8 membros   🛡️ Membro              →   │ │
│  └───────────────────────────────────────────┘ │
│                                                 │
│  ┌───────────────────────────────────────────┐ │
│  │ [Icon] Workspace Comercial                │ │
│  │ Equipe comercial e vendas                 │ │
│  │ 👥 23 membros  🛡️ Visualizador        →   │ │
│  └───────────────────────────────────────────┘ │
│                                                 │
└─────────────────────────────────────────────────┘
```

### Interações

**Hover:**
- Card eleva (translateY -2px)
- Borda muda para azul
- Cursor pointer

**Click:**
- Loading spinner aparece
- Card fica disabled
- Workspace é selecionado
- Redirect para dashboard

---

## INTEGRAÇÃO COM BACKEND

### Endpoint Necessário (TODO)

```
GET /api/workspaces
Authorization: Session (Cookie)

Response:
{
  "success": true,
  "workspaces": [
    {
      "id": 1,
      "name": "Workspace Principal",
      "slug": "principal",
      "description": "...",
      "role": "admin",
      "members_count": 15
    }
  ]
}
```

### Implementação Django (Exemplo)

```python
# apps/core/api_views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

class UserWorkspacesAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Buscar workspaces do usuário
        workspaces = request.user.workspaces.all()
        
        data = [
            {
                'id': ws.id,
                'name': ws.name,
                'slug': ws.slug,
                'description': ws.description,
                'role': ws.get_user_role(request.user),
                'members_count': ws.members.count()
            }
            for ws in workspaces
        ]
        
        return Response({
            'success': True,
            'workspaces': data
        })
```

---

## PERSISTÊNCIA DE WORKSPACE

### LocalStorage

```javascript
// Salvar workspace selecionado
storage.setActiveWorkspace({
  id: 1,
  name: 'Workspace Principal',
  slug: 'principal'
});

// Recuperar workspace
const workspace = storage.getActiveWorkspace();
```

### AuthContext

```javascript
// Estado global
authContext.state.workspace = {
  id: 1,
  name: 'Workspace Principal',
  slug: 'principal'
};

// Acessar via hook
const auth = useAuth();
console.log(auth.workspace);
```

---

## FILTRAR DADOS POR WORKSPACE

### No Frontend

```javascript
import { useAuth } from './hooks/useAuth.js';
import { api } from './services/api.js';

async function loadAgents() {
  const auth = useAuth();
  
  if (!auth.workspace) {
    console.warn('Nenhum workspace selecionado');
    return;
  }
  
  // Buscar dados do workspace ativo
  const result = await api.get(`/api/agents?workspace=${auth.workspace.id}`);
  
  if (result.success) {
    renderAgents(result.data);
  }
}
```

### No Backend

```python
# apps/monitoring/views.py
from django.views.generic import ListView

class AgentListView(LoginRequiredMixin, ListView):
    model = Agent
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtrar por workspace ativo
        workspace_id = self.request.session.get('workspace_id')
        if workspace_id:
            queryset = queryset.filter(workspace_id=workspace_id)
        
        return queryset
```

---

## TROCAR DE WORKSPACE

### Durante a Sessão

```javascript
// Usuário quer trocar de workspace
const auth = useAuth();

// Selecionar novo workspace
auth.selectWorkspace({
  id: 2,
  name: 'Workspace de Testes'
});

// Recarregar página para aplicar mudanças
window.location.reload();
```

### Componente de Seletor

```html
<!-- Seletor no topbar -->
<select id="workspaceSelect" data-workspace-select>
  <option value="1">Workspace Principal</option>
  <option value="2">Workspace de Testes</option>
  <option value="3">Workspace Comercial</option>
</select>

<script>
  // app-init.js já configura automaticamente
  // Escuta mudanças e chama auth.selectWorkspace()
</script>
```

---

## SEGURANÇA

### Validação Backend

**Sempre validar no backend:**
```python
def get_queryset(self):
    queryset = super().get_queryset()
    
    # Verificar se usuário tem acesso ao workspace
    workspace_id = self.request.session.get('workspace_id')
    if workspace_id:
        # Verificar permissão
        if not self.request.user.has_workspace_access(workspace_id):
            raise PermissionDenied
        
        queryset = queryset.filter(workspace_id=workspace_id)
    
    return queryset
```

### Middleware de Workspace

```python
# middleware/workspace.py
class WorkspaceMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        if request.user.is_authenticated:
            workspace_id = request.session.get('workspace_id')
            if workspace_id:
                # Anexar workspace ao request
                request.workspace = Workspace.objects.get(id=workspace_id)
        
        response = self.get_response(request)
        return response
```

---

## TESTES

### Testar Fluxo Completo

1. **Login com 1 workspace:**
   - Fazer login
   - Verificar redirect direto para /dashboard
   - Verificar workspace salvo no storage

2. **Login com múltiplos workspaces:**
   - Fazer login
   - Verificar redirect para /select-workspace
   - Clicar em workspace
   - Verificar redirect para /dashboard
   - Verificar workspace salvo

3. **Trocar workspace:**
   - Selecionar outro workspace
   - Verificar atualização do contexto
   - Verificar dados filtrados

---

## MOCK DE DESENVOLVIMENTO

### Alterar Quantidade de Workspaces

**Em `select_workspace.html`:**

```javascript
getMockWorkspaces() {
  // Retornar 1 workspace (teste auto-select)
  return [
    { id: 1, name: 'Único Workspace', ... }
  ];
  
  // Retornar múltiplos (teste seleção manual)
  return [
    { id: 1, name: 'Workspace 1', ... },
    { id: 2, name: 'Workspace 2', ... },
    { id: 3, name: 'Workspace 3', ... }
  ];
  
  // Retornar vazio (teste empty state)
  return [];
}
```

**Em `authService.js`:**

```javascript
async getUserWorkspaces() {
  return {
    success: true,
    workspaces: [
      // Adicionar/remover workspaces aqui
    ]
  };
}
```

---

## PRÓXIMOS PASSOS

### Backend (TODO)

1. **Criar modelo Workspace**
```python
class Workspace(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    members = models.ManyToManyField(User, through='WorkspaceMember')
```

2. **Criar modelo WorkspaceMember**
```python
class WorkspaceMember(models.Model):
    workspace = models.ForeignKey(Workspace)
    user = models.ForeignKey(User)
    role = models.CharField(choices=ROLES)
```

3. **Criar endpoint `/api/workspaces`**

4. **Adicionar filtro de workspace em todas as queries**

5. **Criar middleware de workspace**

### Frontend (Melhorias)

1. **Adicionar busca de workspaces**
2. **Adicionar favoritos**
3. **Adicionar workspaces recentes**
4. **Melhorar animações**
5. **Adicionar skeleton loading**

---

## RESUMO

### ✅ Implementado

- [x] Página de seleção de workspace
- [x] Lógica de redirecionamento baseado em quantidade
- [x] Seleção automática (1 workspace)
- [x] Seleção manual (múltiplos workspaces)
- [x] Persistência no authContext
- [x] Persistência no storage
- [x] UI elegante e profissional
- [x] Loading/Error/Empty states
- [x] Integração com authContext
- [x] Rota Django `/select-workspace/`
- [x] Mock de dados para desenvolvimento

### 🔄 Pendente (Backend)

- [ ] Modelo Workspace no Django
- [ ] Modelo WorkspaceMember
- [ ] Endpoint `/api/workspaces`
- [ ] Filtro de workspace em queries
- [ ] Middleware de workspace
- [ ] Validação de permissões

### 📊 Fluxo Funcional

```
Login → Verificar Workspaces → Decisão
                                    ↓
                    ┌───────────────┴───────────────┐
                    │                               │
                1 workspace                  Múltiplos
                    │                               │
                    ↓                               ↓
            Auto-selecionar                 /select-workspace
                    │                               │
                    ↓                               ↓
            Salvar contexto                 Usuário escolhe
                    │                               │
                    ↓                               ↓
                /dashboard  ←───────────────  Salvar contexto
```

---

**Status:** ✅ **IMPLEMENTADO E PRONTO PARA BACKEND**

O fluxo multi-tenant está completo no frontend. Basta implementar os endpoints e modelos no backend para funcionar em produção!

---

**Documento criado em:** 18 de Março de 2026  
**Fluxo multi-tenant implementado com sucesso.**
