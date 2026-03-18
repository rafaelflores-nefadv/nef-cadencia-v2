# Arquitetura Backend Django - NEF Cadência

**Data:** 18 de Março de 2026  
**Objetivo:** Documentar arquitetura limpa e profissional do backend  
**Status:** ✅ IMPLEMENTADO

---

## VISÃO GERAL

Arquitetura em **camadas** seguindo princípios de **Clean Architecture** e **Domain-Driven Design** adaptados para Django.

---

## ESTRUTURA DE CAMADAS

```
┌─────────────────────────────────────────────────┐
│              PRESENTATION LAYER                 │
│  Views, Templates, Forms, Serializers           │
├─────────────────────────────────────────────────┤
│              APPLICATION LAYER                  │
│  Services (Business Logic)                      │
├─────────────────────────────────────────────────┤
│              DOMAIN LAYER                       │
│  Models, Validators, Business Rules             │
├─────────────────────────────────────────────────┤
│              DATA ACCESS LAYER                  │
│  Selectors (Read), Repositories (Write)         │
├─────────────────────────────────────────────────┤
│              INFRASTRUCTURE LAYER               │
│  Database, Cache, External APIs                 │
└─────────────────────────────────────────────────┘
```

---

## ORGANIZAÇÃO POR APP

### Estrutura Padrão de um App

```
apps/workspaces/
├── __init__.py
├── apps.py                # Configuração do app
├── models.py              # Domain Layer - Entidades
├── admin.py               # Admin interface
├── views.py               # Presentation Layer - Views
├── urls.py                # Routing
├── forms.py               # Presentation Layer - Forms
├── serializers.py         # Presentation Layer - API
├── services.py            # Application Layer - Business Logic
├── selectors.py           # Data Access Layer - Read queries
├── permissions.py         # Authorization
├── middlewares.py         # Request/Response processing
├── validators.py          # Domain validation
├── signals.py             # Event handlers
├── management/            # Commands
│   └── commands/
│       └── seed_workspaces.py
└── tests/                 # Tests
    ├── test_models.py
    ├── test_services.py
    ├── test_selectors.py
    └── test_views.py
```

---

## CAMADAS DETALHADAS

### 1. MODELS (Domain Layer)

**Responsabilidade:** Definir entidades e regras de negócio

```python
# apps/workspaces/models.py
class Workspace(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    
    def clean(self):
        # Validações de domínio
        pass
    
    def get_admins(self):
        # Lógica de domínio
        return self.members.filter(userworkspace__role='admin')
```

**Regras:**
- ✅ Apenas definição de campos
- ✅ Validações de domínio
- ✅ Métodos de consulta simples
- ❌ Não fazer queries complexas
- ❌ Não chamar APIs externas
- ❌ Não ter lógica de negócio complexa

---

### 2. SELECTORS (Data Access Layer - Read)

**Responsabilidade:** Queries de leitura otimizadas

```python
# apps/workspaces/selectors.py
def get_user_workspaces(user, include_inactive=False):
    queryset = user.workspaces.select_related('default_for_users')
    
    if not include_inactive:
        queryset = queryset.filter(is_active=True)
    
    queryset = queryset.annotate(
        members_count=Count('members')
    )
    
    return queryset.order_by('name')
```

**Regras:**
- ✅ Apenas queries de leitura (SELECT)
- ✅ Otimizações (select_related, prefetch_related)
- ✅ Filtros e ordenação
- ✅ Agregações
- ❌ Não modificar dados
- ❌ Não ter lógica de negócio

---

### 3. SERVICES (Application Layer)

**Responsabilidade:** Lógica de negócio e operações de escrita

```python
# apps/workspaces/services.py
class WorkspaceService:
    @staticmethod
    @transaction.atomic
    def create_workspace(name, slug, description='', created_by=None):
        # Validar
        if Workspace.objects.filter(slug=slug).exists():
            raise ValidationError('Slug já existe')
        
        # Criar
        workspace = Workspace.objects.create(
            name=name,
            slug=slug,
            description=description
        )
        
        # Adicionar criador como admin
        if created_by:
            workspace.add_member(created_by, 'admin')
        
        return workspace
```

**Regras:**
- ✅ Lógica de negócio
- ✅ Operações de escrita (INSERT, UPDATE, DELETE)
- ✅ Validações complexas
- ✅ Transações
- ✅ Chamar selectors para leitura
- ❌ Não fazer queries diretas complexas
- ❌ Não acessar request diretamente

---

### 4. PERMISSIONS (Authorization)

**Responsabilidade:** Verificar permissões de acesso

```python
# apps/workspaces/permissions.py
class WorkspacePermission:
    @staticmethod
    def check_workspace_admin(user, workspace):
        if not user.is_workspace_admin(workspace):
            raise PermissionDenied('Apenas admins')
    
    @staticmethod
    def can_edit(user, workspace):
        role = selectors.get_user_role_in_workspace(user, workspace)
        return role in ['admin', 'member']
```

**Regras:**
- ✅ Verificações de permissão
- ✅ Métodos check_* lançam exceção
- ✅ Métodos can_* retornam bool
- ❌ Não ter lógica de negócio
- ❌ Não modificar dados

---

### 5. VIEWS (Presentation Layer)

**Responsabilidade:** Receber requests e retornar responses

```python
# apps/workspaces/views.py
class WorkspaceListView(LoginRequiredMixin, ListView):
    template_name = 'workspaces/list.html'
    
    def get_queryset(self):
        # Usar selector
        return selectors.get_user_workspaces(self.request.user)

class WorkspaceCreateView(LoginRequiredMixin, CreateView):
    def form_valid(self, form):
        # Usar service
        workspace = WorkspaceService.create_workspace(
            name=form.cleaned_data['name'],
            slug=form.cleaned_data['slug'],
            created_by=self.request.user
        )
        return redirect('workspace-detail', pk=workspace.id)
```

**Regras:**
- ✅ Receber request
- ✅ Validar entrada (forms)
- ✅ Chamar services/selectors
- ✅ Retornar response
- ❌ Não ter lógica de negócio
- ❌ Não fazer queries diretas

---

### 6. MIDDLEWARES

**Responsabilidade:** Processar request/response globalmente

```python
# apps/workspaces/middlewares.py
class WorkspaceMiddleware:
    def __call__(self, request):
        # Anexar workspace ao request
        self._attach_workspace(request)
        
        response = self.get_response(request)
        return response
```

**Regras:**
- ✅ Processar todos os requests
- ✅ Adicionar contexto ao request
- ✅ Validações globais
- ❌ Não ter lógica de negócio específica

---

## FLUXO DE DADOS

### Read (Consulta)

```
Request → View → Selector → Model → Database
                    ↓
                Response ← Template ← Context
```

**Exemplo:**
```python
# View
def workspace_list(request):
    workspaces = selectors.get_user_workspaces(request.user)
    return render(request, 'list.html', {'workspaces': workspaces})
```

---

### Write (Modificação)

```
Request → View → Form → Service → Model → Database
                          ↓
                      Selector (se precisar ler)
                          ↓
                Response ← Redirect
```

**Exemplo:**
```python
# View
def workspace_create(request):
    if request.method == 'POST':
        form = WorkspaceForm(request.POST)
        if form.is_valid():
            workspace = WorkspaceService.create_workspace(
                name=form.cleaned_data['name'],
                created_by=request.user
            )
            return redirect('workspace-detail', pk=workspace.id)
    else:
        form = WorkspaceForm()
    
    return render(request, 'create.html', {'form': form})
```

---

## COMPARAÇÃO COM NODE.JS

### Node.js (Express)

```javascript
// Controller
app.post('/workspaces', async (req, res) => {
  const workspace = await workspaceService.create(req.body);
  res.json(workspace);
});

// Service
class WorkspaceService {
  async create(data) {
    return await workspaceRepository.create(data);
  }
}

// Repository
class WorkspaceRepository {
  async create(data) {
    return await db.workspaces.create(data);
  }
}
```

### Django (Nossa Implementação)

```python
# View (Controller)
class WorkspaceCreateView(CreateView):
    def form_valid(self, form):
        workspace = WorkspaceService.create_workspace(
            name=form.cleaned_data['name']
        )
        return redirect('workspace-detail', pk=workspace.id)

# Service
class WorkspaceService:
    @staticmethod
    def create_workspace(name):
        return Workspace.objects.create(name=name)

# Selector (Repository - Read)
def get_workspace_by_id(workspace_id):
    return Workspace.objects.get(id=workspace_id)
```

**Mesma separação, mesma clareza!**

---

## BOAS PRÁTICAS IMPLEMENTADAS

### 1. Separação de Responsabilidades

- ✅ Views não têm lógica de negócio
- ✅ Services não fazem queries complexas
- ✅ Selectors não modificam dados
- ✅ Models não têm lógica de apresentação

### 2. Transações

```python
@transaction.atomic
def create_workspace(name, created_by):
    workspace = Workspace.objects.create(name=name)
    workspace.add_member(created_by, 'admin')
    return workspace
```

### 3. Validações em Camadas

```python
# Model (domínio)
def clean(self):
    if not self.slug:
        raise ValidationError('Slug obrigatório')

# Form (apresentação)
def clean_slug(self):
    slug = self.cleaned_data['slug']
    if Workspace.objects.filter(slug=slug).exists():
        raise ValidationError('Slug já existe')
    return slug

# Service (negócio)
def create_workspace(slug):
    if len(slug) < 3:
        raise ValidationError('Slug muito curto')
```

### 4. Query Optimization

```python
# ❌ N+1 queries
workspaces = Workspace.objects.all()
for ws in workspaces:
    print(ws.members.count())

# ✅ Otimizado
workspaces = Workspace.objects.annotate(
    members_count=Count('members')
)
for ws in workspaces:
    print(ws.members_count)
```

### 5. Permissions

```python
# Mixin para views
class RequireWorkspaceAdminMixin:
    def dispatch(self, request, *args, **kwargs):
        WorkspacePermission.check_workspace_admin(
            request.user,
            request.workspace
        )
        return super().dispatch(request, *args, **kwargs)
```

---

## ESTRUTURA COMPLETA DO PROJETO

```
nef-cadencia-v2/
├── apps/
│   ├── accounts/              # Autenticação e usuários
│   │   ├── models.py         # User customizado
│   │   ├── admin.py          # Admin do User
│   │   ├── views.py          # Views de auth
│   │   ├── forms.py          # Forms de login/registro
│   │   └── permissions.py    # Permissões de user
│   │
│   ├── workspaces/            # ✨ NOVO - Multi-tenant
│   │   ├── models.py         # Workspace, UserWorkspace
│   │   ├── admin.py          # Admin de workspaces
│   │   ├── selectors.py      # Queries de leitura
│   │   ├── services.py       # Lógica de negócio
│   │   ├── permissions.py    # Permissões de workspace
│   │   ├── middlewares.py    # Middleware de workspace
│   │   └── management/
│   │       └── commands/
│   │           └── seed_workspaces.py
│   │
│   ├── monitoring/            # Monitoramento de agentes
│   ├── assistant/             # IA Assistant
│   ├── rules/                 # Regras de negócio
│   ├── messaging/             # Mensagens
│   ├── integrations/          # Integrações externas
│   ├── reports/               # Relatórios
│   └── core/                  # Funcionalidades core
│
├── alive_platform/            # Configurações Django
│   ├── settings.py           # Settings (AUTH_USER_MODEL)
│   ├── urls.py               # URLs principais
│   └── wsgi.py
│
├── templates/                 # Templates Django
├── static/                    # Assets estáticos
└── docs/                      # Documentação
```

---

## PADRÕES IMPLEMENTADOS

### 1. Service Layer Pattern

**Objetivo:** Centralizar lógica de negócio

```python
# services.py
class WorkspaceService:
    @staticmethod
    @transaction.atomic
    def create_workspace(name, slug, created_by):
        # Validação
        # Criação
        # Lógica adicional
        return workspace
```

**Usado em:**
- `apps/workspaces/services.py`

---

### 2. Repository Pattern (Selectors)

**Objetivo:** Abstrair acesso a dados

```python
# selectors.py
def get_user_workspaces(user):
    return user.workspaces.select_related().filter(is_active=True)
```

**Usado em:**
- `apps/workspaces/selectors.py`

---

### 3. Permission Pattern

**Objetivo:** Centralizar verificações de permissão

```python
# permissions.py
class WorkspacePermission:
    @staticmethod
    def check_workspace_admin(user, workspace):
        if not user.is_workspace_admin(workspace):
            raise PermissionDenied()
```

**Usado em:**
- `apps/workspaces/permissions.py`

---

### 4. Middleware Pattern

**Objetivo:** Processar requests globalmente

```python
# middlewares.py
class WorkspaceMiddleware:
    def __call__(self, request):
        self._attach_workspace(request)
        return self.get_response(request)
```

**Usado em:**
- `apps/workspaces/middlewares.py`

---

## MULTI-TENANT IMPLEMENTADO

### Estratégia: Shared Database, Shared Schema

**Características:**
- ✅ Um banco de dados
- ✅ Um schema
- ✅ Dados isolados por `workspace_id`
- ✅ Middleware anexa workspace ao request
- ✅ Queries filtradas automaticamente

**Alternativas:**
- Database per Tenant - Banco separado por workspace
- Schema per Tenant - Schema separado por workspace

**Por que Shared Database?**
- Mais simples
- Mais econômico
- Suficiente para maioria dos casos
- Fácil migrar para outras estratégias depois

---

## SEGURANÇA

### 1. Isolamento de Dados

```python
# Middleware anexa workspace
request.workspace = workspace

# Manager filtra automaticamente
class WorkspaceScopedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(
            workspace=self.workspace
        )
```

### 2. Validação de Acesso

```python
# Antes de qualquer operação
WorkspacePermission.check_workspace_access(user, workspace)
```

### 3. Row Level Security (Futuro)

```sql
-- PostgreSQL RLS
ALTER TABLE agents ENABLE ROW LEVEL SECURITY;

CREATE POLICY workspace_isolation ON agents
FOR ALL
USING (workspace_id IN (
    SELECT workspace_id FROM user_workspaces
    WHERE user_id = current_user_id()
));
```

---

## ESCALABILIDADE

### 1. Connection Pooling

```python
DATABASES = {
    'default': {
        'CONN_MAX_AGE': 600,  # 10 minutos
    }
}
```

### 2. Query Optimization

```python
# Select related
workspaces = Workspace.objects.select_related('default_for_users')

# Prefetch related
workspaces = Workspace.objects.prefetch_related('members')

# Annotate
workspaces = Workspace.objects.annotate(
    members_count=Count('members')
)
```

### 3. Caching (Futuro)

```python
from django.core.cache import cache

def get_user_workspaces(user):
    cache_key = f'user_workspaces_{user.id}'
    workspaces = cache.get(cache_key)
    
    if not workspaces:
        workspaces = list(user.workspaces.all())
        cache.set(cache_key, workspaces, 300)  # 5 min
    
    return workspaces
```

---

## TESTES

### Estrutura de Testes

```python
# tests/test_services.py
class WorkspaceServiceTest(TestCase):
    def test_create_workspace(self):
        user = User.objects.create_user('test', 'test@example.com')
        workspace = WorkspaceService.create_workspace(
            name='Test',
            slug='test',
            created_by=user
        )
        
        self.assertEqual(workspace.name, 'Test')
        self.assertTrue(user.is_workspace_admin(workspace))
```

### Cobertura de Testes

```bash
# Instalar coverage
pip install coverage

# Rodar testes com coverage
coverage run --source='apps' manage.py test

# Ver relatório
coverage report

# Gerar HTML
coverage html
```

---

## DOCUMENTAÇÃO DA API (Futuro)

### Django REST Framework

```python
# serializers.py
class WorkspaceSerializer(serializers.ModelSerializer):
    members_count = serializers.IntegerField(read_only=True)
    role = serializers.SerializerMethodField()
    
    class Meta:
        model = Workspace
        fields = ['id', 'name', 'slug', 'description', 'members_count', 'role']
    
    def get_role(self, obj):
        user = self.context['request'].user
        return selectors.get_user_role_in_workspace(user, obj)

# views.py (API)
class WorkspaceViewSet(viewsets.ModelViewSet):
    serializer_class = WorkspaceSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return selectors.get_user_workspaces(self.request.user)
    
    def perform_create(self, serializer):
        WorkspaceService.create_workspace(
            name=serializer.validated_data['name'],
            slug=serializer.validated_data['slug'],
            created_by=self.request.user
        )
```

---

## COMPARAÇÃO: DJANGO vs NODE.JS

### Equivalências

| Django | Node.js | Responsabilidade |
|--------|---------|------------------|
| Views | Controllers | Presentation |
| Services | Services | Business Logic |
| Selectors | Repositories (Read) | Data Access |
| Models | Models/Entities | Domain |
| Middlewares | Middlewares | Request Processing |
| Permissions | Guards/Policies | Authorization |
| Forms | DTOs/Validators | Input Validation |
| Serializers | Serializers | Output Formatting |

### Exemplo Comparativo

**Node.js:**
```javascript
// controller
app.post('/workspaces', async (req, res) => {
  const workspace = await workspaceService.create(req.body);
  res.json(workspace);
});

// service
class WorkspaceService {
  async create(data) {
    return await workspaceRepository.create(data);
  }
}
```

**Django:**
```python
# view
class WorkspaceCreateView(CreateView):
    def form_valid(self, form):
        workspace = WorkspaceService.create_workspace(
            name=form.cleaned_data['name']
        )
        return redirect('workspace-detail', pk=workspace.id)

# service
class WorkspaceService:
    @staticmethod
    def create_workspace(name):
        return Workspace.objects.create(name=name)
```

**Mesma arquitetura, linguagem diferente!**

---

## PRÓXIMOS PASSOS

### Imediato

1. ✅ Rodar migrations
2. ✅ Criar seed
3. ✅ Testar no admin

### Curto Prazo

4. Criar API REST com DRF
5. Adicionar middleware de workspace
6. Filtrar dados por workspace em todos os apps
7. Adicionar testes

### Médio Prazo

8. Implementar cache
9. Adicionar auditoria
10. Otimizar queries
11. Adicionar monitoring

---

## RESUMO

### ✅ Arquitetura Implementada

- **Models** - Domain Layer
- **Selectors** - Data Access (Read)
- **Services** - Business Logic
- **Permissions** - Authorization
- **Middlewares** - Request Processing
- **Views** - Presentation
- **Admin** - Interface administrativa

### ✅ Padrões Aplicados

- Service Layer Pattern
- Repository Pattern (Selectors)
- Permission Pattern
- Middleware Pattern
- Transaction Management
- Query Optimization

### ✅ Multi-Tenant

- Workspace model
- UserWorkspace (many-to-many)
- Role-based access
- Middleware de workspace
- Isolamento de dados

---

**Status:** ✅ **ARQUITETURA BACKEND PROFISSIONAL**

O backend Django está estruturado de forma limpa, escalável e profissional, equivalente às melhores práticas de Node.js/TypeScript!

---

**Documento criado em:** 18 de Março de 2026  
**Arquitetura backend implementada com sucesso.**
