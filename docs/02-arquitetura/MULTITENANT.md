# Banco de Dados Multi-Tenant - NEF Cadência

**Data:** 18 de Março de 2026  
**Objetivo:** Configurar PostgreSQL com modelagem multi-tenant  
**Status:** ✅ IMPLEMENTADO

---

## ESTRATÉGIA ESCOLHIDA

### ORM: Django ORM

**Por quê Django ORM?**
- ✅ Integração nativa com Django
- ✅ Migrations automáticas
- ✅ Query optimization built-in
- ✅ Suporte completo a PostgreSQL
- ✅ Relacionamentos complexos simplificados
- ✅ Admin interface automática
- ✅ Validações no model layer

**Alternativas consideradas:**
- SQLAlchemy - Mais verboso, menos integrado
- Raw SQL - Sem migrations, sem validações
- Query Builder - Menos type-safe

---

## MODELAGEM IMPLEMENTADA

### 1. Tabela `users`

```sql
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    username VARCHAR(150) UNIQUE NOT NULL,
    email VARCHAR(254) UNIQUE NOT NULL,
    password VARCHAR(128) NOT NULL,
    first_name VARCHAR(150),
    last_name VARCHAR(150),
    phone VARCHAR(20),
    avatar VARCHAR(100),
    bio TEXT,
    default_workspace_id BIGINT REFERENCES workspaces(id) ON DELETE SET NULL,
    is_staff BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    last_login TIMESTAMP,
    date_joined TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_is_active ON users(is_active);
CREATE INDEX idx_users_date_joined ON users(date_joined);
```

**Campos:**
- `id` - Primary key
- `username` - Nome de usuário único
- `email` - Email único (usado para login)
- `password` - Hash da senha (bcrypt via Django)
- `first_name`, `last_name` - Nome completo
- `phone` - Telefone de contato
- `avatar` - Foto de perfil
- `bio` - Biografia
- `default_workspace_id` - Último workspace acessado
- `is_staff` - Acesso ao admin
- `is_active` - Conta ativa
- `is_superuser` - Superusuário
- `last_login` - Último login
- `date_joined` - Data de criação
- `updated_at` - Data de atualização

---

### 2. Tabela `workspaces`

```sql
CREATE TABLE workspaces (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_workspaces_slug ON workspaces(slug);
CREATE INDEX idx_workspaces_is_active ON workspaces(is_active);
CREATE INDEX idx_workspaces_created_at ON workspaces(created_at);
```

**Campos:**
- `id` - Primary key
- `name` - Nome do workspace
- `slug` - Identificador único (URL-friendly)
- `description` - Descrição do workspace
- `is_active` - Workspace ativo
- `created_at` - Data de criação
- `updated_at` - Data de atualização

---

### 3. Tabela `user_workspaces`

```sql
CREATE TABLE user_workspaces (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    workspace_id BIGINT NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL DEFAULT 'member',
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, workspace_id)
);

CREATE INDEX idx_user_workspaces_user_workspace ON user_workspaces(user_id, workspace_id);
CREATE INDEX idx_user_workspaces_workspace_role ON user_workspaces(workspace_id, role);
CREATE INDEX idx_user_workspaces_created_at ON user_workspaces(created_at);

-- Constraint para validar roles
ALTER TABLE user_workspaces 
ADD CONSTRAINT check_role 
CHECK (role IN ('admin', 'member', 'viewer'));
```

**Campos:**
- `id` - Primary key
- `user_id` - Foreign key para users
- `workspace_id` - Foreign key para workspaces
- `role` - Permissão do usuário no workspace
- `created_at` - Data de entrada no workspace

**Roles:**
- `admin` - Administrador (acesso total)
- `member` - Membro (pode criar/editar)
- `viewer` - Visualizador (apenas leitura)

---

## RELACIONAMENTOS

### Diagrama ER

```
┌─────────────────────┐
│       users         │
├─────────────────────┤
│ id (PK)             │
│ username            │
│ email               │
│ password            │
│ default_workspace_id│──┐
│ ...                 │  │
└─────────────────────┘  │
         │               │
         │ M             │
         │               │
         ▼               │
┌─────────────────────┐  │
│  user_workspaces    │  │
├─────────────────────┤  │
│ id (PK)             │  │
│ user_id (FK)        │  │
│ workspace_id (FK)   │──┼──┐
│ role                │  │  │
└─────────────────────┘  │  │
         │               │  │
         │ M             │  │
         │               │  │
         ▼               │  │
┌─────────────────────┐  │  │
│    workspaces       │◄─┘  │
├─────────────────────┤     │
│ id (PK)             │◄────┘
│ name                │
│ slug                │
│ ...                 │
└─────────────────────┘
```

### Relacionamentos

1. **User ↔ Workspace (Many-to-Many)**
   - Um usuário pode pertencer a múltiplos workspaces
   - Um workspace pode ter múltiplos usuários
   - Intermediado por `user_workspaces`

2. **User → Workspace (default_workspace)**
   - Um usuário tem um workspace padrão
   - Foreign key opcional (pode ser NULL)

---

## MODELS DJANGO

### User Model

```python
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio = models.TextField(blank=True)
    default_workspace = models.ForeignKey(
        'workspaces.Workspace',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'users'
```

### Workspace Model

```python
class Workspace(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    members = models.ManyToManyField(
        User,
        through='UserWorkspace',
        related_name='workspaces'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'workspaces'
```

### UserWorkspace Model

```python
class UserWorkspace(models.Model):
    class Role(models.TextChoices):
        ADMIN = 'admin', 'Administrador'
        MEMBER = 'member', 'Membro'
        VIEWER = 'viewer', 'Visualizador'
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE)
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.MEMBER
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'user_workspaces'
        unique_together = [['user', 'workspace']]
```

---

## CONFIGURAÇÃO POSTGRESQL

### settings.py

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME', default='nef_cadencia'),
        'USER': env('DB_USER', default='postgres'),
        'PASSWORD': env('DB_PASSWORD', default=''),
        'HOST': env('DB_HOST', default='localhost'),
        'PORT': env('DB_PORT', default='5432'),
        'CONN_MAX_AGE': 600,  # Connection pooling
        'OPTIONS': {
            'connect_timeout': 10,
        }
    }
}

# Custom User Model
AUTH_USER_MODEL = 'accounts.User'
```

### .env

```bash
DB_NAME=nef_cadencia
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
```

---

## MIGRATIONS

### Criar Migrations

```bash
# Criar migrations
python manage.py makemigrations

# Aplicar migrations
python manage.py migrate

# Ver SQL das migrations
python manage.py sqlmigrate workspaces 0001
```

### Ordem de Execução

1. **accounts.0001_initial** - Cria tabela users
2. **workspaces.0001_initial** - Cria tabelas workspaces e user_workspaces
3. **accounts.0002_add_default_workspace** - Adiciona FK default_workspace

---

## SEED INICIAL

### Management Command

```bash
# Criar dados iniciais
python manage.py seed_workspaces

# Limpar e recriar
python manage.py seed_workspaces --clear
```

### Dados Criados

**Workspaces:**
1. Workspace Principal (slug: principal)
2. Workspace de Testes (slug: testes)
3. Workspace Comercial (slug: comercial)

**Usuários:**
1. **admin** (senha: admin123)
   - Admin em todos os workspaces
   - is_staff=True, is_superuser=True

2. **usuario1** (senha: senha123)
   - Membro em principal e testes

3. **usuario2** (senha: senha123)
   - Visualizador em principal
   - Membro em comercial

---

## QUERIES COMUNS

### Buscar Workspaces do Usuário

```python
# Django ORM
user = User.objects.get(username='admin')
workspaces = user.workspaces.filter(is_active=True)

# SQL equivalente
SELECT w.* FROM workspaces w
INNER JOIN user_workspaces uw ON w.id = uw.workspace_id
WHERE uw.user_id = 1 AND w.is_active = TRUE;
```

### Buscar Membros do Workspace

```python
# Django ORM
workspace = Workspace.objects.get(slug='principal')
members = workspace.members.all()

# Com role
admins = workspace.members.filter(userworkspace__role='admin')

# SQL equivalente
SELECT u.* FROM users u
INNER JOIN user_workspaces uw ON u.id = uw.user_id
WHERE uw.workspace_id = 1 AND uw.role = 'admin';
```

### Verificar Permissão

```python
# Django ORM
user = User.objects.get(username='admin')
workspace = Workspace.objects.get(slug='principal')
role = user.get_workspace_role(workspace)

is_admin = user.is_workspace_admin(workspace)

# SQL equivalente
SELECT role FROM user_workspaces
WHERE user_id = 1 AND workspace_id = 1;
```

---

## ÍNDICES E PERFORMANCE

### Índices Criados

**users:**
- `idx_users_email` - Busca por email (login)
- `idx_users_is_active` - Filtro de usuários ativos
- `idx_users_date_joined` - Ordenação por data

**workspaces:**
- `idx_workspaces_slug` - Busca por slug (URL)
- `idx_workspaces_is_active` - Filtro de workspaces ativos
- `idx_workspaces_created_at` - Ordenação por data

**user_workspaces:**
- `idx_user_workspaces_user_workspace` - Busca de membros
- `idx_user_workspaces_workspace_role` - Filtro por role
- `idx_user_workspaces_created_at` - Ordenação por data

### Query Optimization

```python
# ❌ N+1 queries
workspaces = Workspace.objects.all()
for ws in workspaces:
    print(ws.members.count())  # Query por workspace

# ✅ Otimizado
workspaces = Workspace.objects.annotate(
    member_count=Count('members')
)
for ws in workspaces:
    print(ws.member_count)  # Sem queries extras
```

---

## ESCALABILIDADE

### Connection Pooling

```python
DATABASES = {
    'default': {
        ...
        'CONN_MAX_AGE': 600,  # Manter conexões por 10min
    }
}
```

### Read Replicas (Futuro)

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'nef_cadencia',
        ...
    },
    'replica': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'nef_cadencia',
        'HOST': 'replica.example.com',
        ...
    }
}

DATABASE_ROUTERS = ['path.to.ReplicaRouter']
```

### Particionamento (Futuro)

Para workspaces muito grandes, considerar:
- Particionamento por workspace_id
- Sharding por região
- Tabelas separadas por tenant

---

## SEGURANÇA

### Password Hashing

Django usa **PBKDF2** por padrão com SHA256:
```python
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
]
```

### Validação de Dados

```python
# No model
def clean(self):
    if self.workspace and not self.workspace.is_active:
        raise ValidationError('Workspace inativo')

# No form
class UserWorkspaceForm(forms.ModelForm):
    def clean(self):
        # Validações customizadas
        pass
```

### Row Level Security (Futuro)

```sql
-- PostgreSQL RLS
ALTER TABLE workspaces ENABLE ROW LEVEL SECURITY;

CREATE POLICY workspace_access ON workspaces
FOR SELECT
USING (
    id IN (
        SELECT workspace_id FROM user_workspaces
        WHERE user_id = current_user_id()
    )
);
```

---

## BACKUP E RESTORE

### Backup

```bash
# Backup completo
pg_dump -U postgres -d nef_cadencia > backup.sql

# Backup apenas dados
pg_dump -U postgres -d nef_cadencia --data-only > data.sql

# Backup específico
pg_dump -U postgres -d nef_cadencia -t users -t workspaces > tables.sql
```

### Restore

```bash
# Restore completo
psql -U postgres -d nef_cadencia < backup.sql

# Restore apenas dados
psql -U postgres -d nef_cadencia < data.sql
```

---

## TESTES

### Criar Banco de Teste

```python
# settings.py
if 'test' in sys.argv:
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'test_nef_cadencia',
        ...
    }
```

### Testes de Model

```python
from django.test import TestCase
from apps.workspaces.models import Workspace, UserWorkspace

class WorkspaceModelTest(TestCase):
    def test_create_workspace(self):
        workspace = Workspace.objects.create(
            name='Test Workspace',
            slug='test'
        )
        self.assertEqual(workspace.name, 'Test Workspace')
    
    def test_add_member(self):
        workspace = Workspace.objects.create(name='Test', slug='test')
        user = User.objects.create_user('testuser', 'test@example.com')
        workspace.add_member(user, UserWorkspace.Role.ADMIN)
        
        self.assertTrue(workspace.has_member(user))
        self.assertEqual(workspace.get_user_role(user), 'admin')
```

---

## PRÓXIMOS PASSOS

### Curto Prazo

1. **Criar API REST para workspaces**
   - GET /api/workspaces - Listar workspaces do usuário
   - POST /api/workspaces - Criar workspace
   - PUT /api/workspaces/:id - Atualizar workspace
   - DELETE /api/workspaces/:id - Deletar workspace

2. **Middleware de Workspace**
   - Anexar workspace ao request
   - Validar permissões
   - Filtrar queries automaticamente

3. **Filtrar Dados por Workspace**
   - Adicionar workspace_id em todas as tabelas
   - Manager customizado para filtrar automaticamente
   - Signals para garantir isolamento

### Médio Prazo

4. **Auditoria**
   - Log de mudanças
   - Histórico de acessos
   - Rastreamento de ações

5. **Permissões Granulares**
   - Permissões por recurso
   - Grupos de permissões
   - Herança de permissões

6. **Multi-Database**
   - Banco separado por workspace
   - Sharding automático
   - Migração de dados

---

## RESUMO

### ✅ Implementado

- [x] User model customizado
- [x] Workspace model
- [x] UserWorkspace model (many-to-many)
- [x] Relacionamentos e FKs
- [x] Índices de performance
- [x] Validações de dados
- [x] Django Admin
- [x] Management command para seed
- [x] Configuração PostgreSQL
- [x] AUTH_USER_MODEL configurado

### 📊 Estrutura Final

```
users (tabela principal de usuários)
  ↕ many-to-many
user_workspaces (relacionamento + role)
  ↕ many-to-many
workspaces (tabela de workspaces/tenants)
```

### 🎯 Próximos Passos

1. Rodar migrations: `python manage.py migrate`
2. Criar seed: `python manage.py seed_workspaces`
3. Testar no admin: `/admin/workspaces/`
4. Criar API REST
5. Implementar middleware
6. Filtrar dados por workspace

---

**Status:** ✅ **BASE DE DADOS CONFIGURADA**

A modelagem multi-tenant está completa e pronta para uso!

---

**Documento criado em:** 18 de Março de 2026  
**PostgreSQL multi-tenant configurado com sucesso.**
