# Setup do Banco de Dados - NEF Cadência

**Data:** 18 de Março de 2026  
**Objetivo:** Guia completo para configurar PostgreSQL multi-tenant  
**Status:** ✅ PRONTO PARA EXECUTAR

---

## PASSO A PASSO

### 1. Verificar PostgreSQL

```bash
# Verificar se PostgreSQL está instalado
psql --version

# Verificar se está rodando (Windows)
Get-Service -Name postgresql*
```

Se não estiver instalado:
- Download: https://www.postgresql.org/download/windows/
- Ou use Docker: `docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=postgres postgres:15`

---

### 2. Criar Banco de Dados

```bash
# Conectar ao PostgreSQL
psql -U postgres

# Criar banco
CREATE DATABASE nef_cadencia;

# Criar usuário (opcional)
CREATE USER nef_user WITH PASSWORD 'sua_senha_segura';

# Dar permissões
GRANT ALL PRIVILEGES ON DATABASE nef_cadencia TO nef_user;

# Sair
\q
```

---

### 3. Configurar .env

Edite o arquivo `.env` na raiz do projeto:

```bash
# Database
DB_NAME=nef_cadencia
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=127.0.0.1
DB_PORT=5432

# Django
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

# OpenAI
OPENAI_API_KEY=your-openai-key
OPENAI_MODEL=gpt-4.1-mini
```

---

### 4. Criar Migrations

```bash
# Criar migrations para o novo User model e Workspaces
python manage.py makemigrations accounts
python manage.py makemigrations workspaces

# Verificar SQL das migrations
python manage.py sqlmigrate accounts 0001
python manage.py sqlmigrate workspaces 0001
```

---

### 5. Aplicar Migrations

```bash
# Aplicar todas as migrations
python manage.py migrate

# Verificar status
python manage.py showmigrations
```

**Saída esperada:**
```
accounts
 [X] 0001_initial
workspaces
 [X] 0001_initial
...
```

---

### 6. Criar Dados Iniciais

```bash
# Criar workspaces e usuários de teste
python manage.py seed_workspaces

# Ou limpar e recriar
python manage.py seed_workspaces --clear
```

**Saída esperada:**
```
✓ Workspace criado: Workspace Principal
✓ Workspace criado: Workspace de Testes
✓ Workspace criado: Workspace Comercial
✓ Usuário admin criado (senha: admin123)
✓ Usuário usuario1 criado (senha: senha123)
✓ Usuário usuario2 criado (senha: senha123)

Workspaces criados:
  • Workspace Principal (principal)
  • Workspace de Testes (testes)
  • Workspace Comercial (comercial)

Usuários:
  • admin (admin em todos os workspaces)
  • usuario1 (membro em principal e testes)
  • usuario2 (visualizador em principal, membro em comercial)
```

---

### 7. Verificar no Admin

```bash
# Criar superuser (se não usou seed)
python manage.py createsuperuser

# Iniciar servidor
python manage.py runserver

# Acessar admin
http://localhost:8000/admin
```

**Verificar:**
- Usuários em `/admin/accounts/user/`
- Workspaces em `/admin/workspaces/workspace/`
- Membros em `/admin/workspaces/userworkspace/`

---

## TROUBLESHOOTING

### Erro: "relation does not exist"

**Causa:** Migrations não foram aplicadas

**Solução:**
```bash
python manage.py migrate
```

---

### Erro: "FATAL: database does not exist"

**Causa:** Banco de dados não foi criado

**Solução:**
```bash
psql -U postgres
CREATE DATABASE nef_cadencia;
\q
```

---

### Erro: "FATAL: password authentication failed"

**Causa:** Senha incorreta no .env

**Solução:**
1. Verificar senha do PostgreSQL
2. Atualizar `DB_PASSWORD` no .env
3. Reiniciar servidor

---

### Erro: "AUTH_USER_MODEL refers to model 'accounts.User' that has not been installed"

**Causa:** App accounts não está em INSTALLED_APPS ou model não existe

**Solução:**
1. Verificar `INSTALLED_APPS` em settings.py
2. Verificar se `apps.accounts.models.User` existe
3. Rodar `python manage.py makemigrations`

---

### Erro: "Cannot alter table 'auth_user' because it is being referenced"

**Causa:** Tentando alterar User model após já ter criado dados

**Solução:**
1. **Desenvolvimento:** Deletar banco e recriar
```bash
python manage.py flush
python manage.py migrate
```

2. **Produção:** Criar migration customizada para migrar dados

---

## VERIFICAÇÃO

### Verificar Tabelas Criadas

```bash
# Conectar ao banco
psql -U postgres -d nef_cadencia

# Listar tabelas
\dt

# Ver estrutura da tabela users
\d users

# Ver estrutura da tabela workspaces
\d workspaces

# Ver estrutura da tabela user_workspaces
\d user_workspaces
```

**Tabelas esperadas:**
- users
- workspaces
- user_workspaces
- django_migrations
- django_session
- ...

---

### Verificar Dados

```sql
-- Contar usuários
SELECT COUNT(*) FROM users;

-- Contar workspaces
SELECT COUNT(*) FROM workspaces;

-- Contar membros
SELECT COUNT(*) FROM user_workspaces;

-- Ver workspaces do admin
SELECT w.name, uw.role 
FROM workspaces w
INNER JOIN user_workspaces uw ON w.id = uw.workspace_id
INNER JOIN users u ON uw.user_id = u.id
WHERE u.username = 'admin';
```

---

## BACKUP INICIAL

### Criar Backup

```bash
# Backup completo
pg_dump -U postgres -d nef_cadencia > backup_inicial.sql

# Backup apenas schema
pg_dump -U postgres -d nef_cadencia --schema-only > schema.sql

# Backup apenas dados
pg_dump -U postgres -d nef_cadencia --data-only > data.sql
```

---

## PERFORMANCE

### Configurações Recomendadas

**PostgreSQL (postgresql.conf):**
```ini
# Memória
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB

# Conexões
max_connections = 100

# Logging
log_min_duration_statement = 1000  # Log queries > 1s
```

**Django (settings.py):**
```python
# Connection pooling
DATABASES['default']['CONN_MAX_AGE'] = 600

# Query logging (desenvolvimento)
LOGGING = {
    'loggers': {
        'django.db.backends': {
            'level': 'DEBUG',
            'handlers': ['console'],
        }
    }
}
```

---

## MONITORAMENTO

### Queries Lentas

```sql
-- Ver queries ativas
SELECT pid, now() - pg_stat_activity.query_start AS duration, query
FROM pg_stat_activity
WHERE state = 'active'
ORDER BY duration DESC;

-- Ver queries lentas (pg_stat_statements)
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
```

### Tamanho das Tabelas

```sql
-- Tamanho das tabelas
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

---

## PRÓXIMOS PASSOS

### Imediato

1. ✅ Rodar migrations
2. ✅ Criar seed inicial
3. ✅ Verificar no admin
4. ✅ Testar login

### Curto Prazo

5. Criar API REST para workspaces
6. Implementar middleware de workspace
7. Filtrar dados por workspace
8. Adicionar testes

### Médio Prazo

9. Adicionar auditoria
10. Implementar permissões granulares
11. Otimizar queries
12. Adicionar cache

---

## COMANDOS ÚTEIS

```bash
# Criar migrations
python manage.py makemigrations

# Aplicar migrations
python manage.py migrate

# Reverter migration
python manage.py migrate workspaces 0001

# Ver SQL da migration
python manage.py sqlmigrate workspaces 0001

# Verificar migrations pendentes
python manage.py showmigrations

# Criar seed
python manage.py seed_workspaces

# Limpar banco (CUIDADO!)
python manage.py flush

# Shell do Django
python manage.py shell

# Shell do PostgreSQL
python manage.py dbshell
```

---

## CHECKLIST

### ✅ Pré-requisitos

- [ ] PostgreSQL instalado e rodando
- [ ] Banco `nef_cadencia` criado
- [ ] Arquivo `.env` configurado
- [ ] Dependências Python instaladas (`pip install -r requirements.txt`)

### ✅ Setup

- [ ] Migrations criadas (`makemigrations`)
- [ ] Migrations aplicadas (`migrate`)
- [ ] Seed executado (`seed_workspaces`)
- [ ] Admin acessível (`/admin`)
- [ ] Login funcionando (`/login`)

### ✅ Validação

- [ ] Tabelas criadas no PostgreSQL
- [ ] Dados de seed presentes
- [ ] Login com admin funciona
- [ ] Workspaces aparecem no admin
- [ ] Relacionamentos funcionando

---

## RESUMO

### Estrutura Criada

```
PostgreSQL Database: nef_cadencia
├── users (tabela de usuários)
├── workspaces (tabela de workspaces)
└── user_workspaces (relacionamento many-to-many)
```

### Comandos Principais

```bash
# 1. Criar banco
psql -U postgres -c "CREATE DATABASE nef_cadencia;"

# 2. Aplicar migrations
python manage.py migrate

# 3. Criar dados iniciais
python manage.py seed_workspaces

# 4. Iniciar servidor
python manage.py runserver
```

---

**Status:** ✅ **PRONTO PARA EXECUTAR**

Siga os passos acima para configurar o banco de dados multi-tenant!

---

**Documento criado em:** 18 de Março de 2026  
**Setup completo do PostgreSQL multi-tenant.**
