# Guia de Migração - User Model Customizado

**⚠️ IMPORTANTE: LEIA ANTES DE EXECUTAR**

---

## SITUAÇÃO ATUAL

O projeto **já possui dados no banco de dados** usando o User model padrão do Django (`django.contrib.auth.models.User`).

Agora estamos **customizando o User model** para adicionar campos adicionais e suporte multi-tenant.

---

## ⚠️ PROBLEMA

**Não é possível alterar `AUTH_USER_MODEL` depois que o banco já foi criado!**

Django não permite trocar o User model após as migrations iniciais terem sido aplicadas.

---

## OPÇÕES DISPONÍVEIS

### Opção 1: Ambiente de Desenvolvimento (RECOMENDADO) ✅

**Se você está em desenvolvimento e pode perder os dados:**

1. **Deletar banco de dados**
```bash
# Conectar ao PostgreSQL
psql -U postgres

# Deletar banco
DROP DATABASE alive_platform;

# Criar novo banco
CREATE DATABASE nef_cadencia;

# Sair
\q
```

2. **Deletar migrations antigas**
```bash
# Windows PowerShell
Remove-Item -Recurse -Force apps\*/migrations\0*.py
Remove-Item -Recurse -Force apps\*/migrations\__pycache__
```

3. **Criar novas migrations**
```bash
python manage.py makemigrations
python manage.py migrate
```

4. **Criar seed**
```bash
python manage.py seed_workspaces
```

---

### Opção 2: Produção (COMPLEXO) ⚠️

**Se você tem dados em produção que não pode perder:**

1. **Criar Profile model** ao invés de customizar User
```python
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20)
    avatar = models.ImageField(...)
    bio = models.TextField()
    default_workspace = models.ForeignKey(Workspace, ...)
```

2. **Migrar dados** do User antigo para o novo
3. **Manter compatibilidade** com código existente

---

### Opção 3: Híbrido (INTERMEDIÁRIO) 🔄

**Se você quer testar sem perder tudo:**

1. **Fazer backup do banco atual**
```bash
pg_dump -U postgres -d alive_platform > backup_antes_migracao.sql
```

2. **Tentar migração com Profile model**
3. **Se der problema, restaurar backup**
```bash
psql -U postgres -d alive_platform < backup_antes_migracao.sql
```

---

## MINHA RECOMENDAÇÃO

### Para Desenvolvimento: Opção 1 ✅

**Vantagens:**
- ✅ Limpo e simples
- ✅ User model customizado correto
- ✅ Sem gambiarras
- ✅ Arquitetura correta

**Desvantagens:**
- ❌ Perde dados existentes
- ❌ Precisa recriar tudo

**Quando usar:**
- Ambiente de desenvolvimento
- Dados não são importantes
- Quer arquitetura correta

---

### Para Produção: Opção 2 ⚠️

**Vantagens:**
- ✅ Não perde dados
- ✅ Migração segura

**Desvantagens:**
- ❌ Mais complexo
- ❌ Profile model separado
- ❌ Menos elegante

**Quando usar:**
- Produção com dados reais
- Não pode perder dados
- Precisa manter compatibilidade

---

## PASSO A PASSO (OPÇÃO 1 - DESENVOLVIMENTO)

### 1. Fazer Backup (Segurança)

```bash
# Backup do banco atual
pg_dump -U postgres -d alive_platform > backup_antes_reset.sql
```

### 2. Deletar Banco Antigo

```bash
# Conectar
psql -U postgres

# Deletar
DROP DATABASE alive_platform;

# Criar novo
CREATE DATABASE nef_cadencia;

# Sair
\q
```

### 3. Limpar Migrations

```bash
# Windows PowerShell
# Deletar migrations antigas (exceto __init__.py)
Get-ChildItem -Path apps\*\migrations\0*.py | Remove-Item
Get-ChildItem -Path apps\*\migrations\__pycache__ -Recurse | Remove-Item -Recurse -Force
```

### 4. Atualizar .env

```bash
# Mudar nome do banco
DB_NAME=nef_cadencia  # Era: alive_platform
```

### 5. Criar Migrations

```bash
# Criar migrations
python manage.py makemigrations

# Verificar
python manage.py showmigrations
```

### 6. Aplicar Migrations

```bash
# Aplicar
python manage.py migrate

# Verificar
python manage.py showmigrations
```

### 7. Criar Dados Iniciais

```bash
# Seed
python manage.py seed_workspaces

# Verificar
python manage.py shell
>>> from django.contrib.auth import get_user_model
>>> User = get_user_model()
>>> User.objects.count()
3
>>> from apps.workspaces.models import Workspace
>>> Workspace.objects.count()
3
```

### 8. Testar

```bash
# Iniciar servidor
python manage.py runserver

# Testar login
http://localhost:8000/login
# Usuário: admin
# Senha: admin123
```

---

## ROLLBACK (SE DER PROBLEMA)

### Restaurar Banco Antigo

```bash
# Deletar banco novo
psql -U postgres -c "DROP DATABASE nef_cadencia;"

# Criar banco antigo
psql -U postgres -c "CREATE DATABASE alive_platform;"

# Restaurar backup
psql -U postgres -d alive_platform < backup_antes_reset.sql

# Atualizar .env
DB_NAME=alive_platform
```

---

## CHECKLIST

### Antes de Começar

- [ ] Fazer backup do banco atual
- [ ] Confirmar que está em desenvolvimento
- [ ] Confirmar que pode perder dados
- [ ] Ter PostgreSQL rodando

### Durante Migração

- [ ] Deletar banco antigo
- [ ] Criar banco novo
- [ ] Limpar migrations
- [ ] Atualizar .env
- [ ] Criar migrations
- [ ] Aplicar migrations
- [ ] Criar seed
- [ ] Testar login

### Após Migração

- [ ] Login funciona
- [ ] Admin acessível
- [ ] Workspaces aparecem
- [ ] Relacionamentos funcionam
- [ ] Frontend funciona

---

## PERGUNTAS FREQUENTES

### Posso manter os dois bancos?

Sim! Você pode:
- `alive_platform` - Banco antigo (backup)
- `nef_cadencia` - Banco novo (multi-tenant)

### Vou perder meus dados?

**Opção 1:** Sim, mas você tem backup.  
**Opção 2:** Não, mas é mais complexo.

### Quanto tempo leva?

- Backup: 1 minuto
- Deletar/criar banco: 1 minuto
- Migrations: 2 minutos
- Seed: 1 minuto
- **Total: ~5 minutos**

### E se der erro?

Restaure o backup:
```bash
psql -U postgres -d alive_platform < backup_antes_reset.sql
```

---

## RESUMO

### Para Desenvolvimento (Recomendado)

1. Backup
2. Deletar banco antigo
3. Criar banco novo
4. Limpar migrations
5. Criar migrations
6. Aplicar migrations
7. Seed
8. Testar

**Tempo:** ~5 minutos  
**Risco:** Baixo (tem backup)  
**Resultado:** Arquitetura limpa e correta

---

**Pronto para executar?**

Siga o **Passo a Passo (Opção 1)** acima!

---

**Documento criado em:** 18 de Março de 2026  
**Guia de migração para User model customizado.**
