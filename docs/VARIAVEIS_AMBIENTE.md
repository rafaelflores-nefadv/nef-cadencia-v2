# Referência Completa de Variáveis de Ambiente - NEF Cadência

**Versão:** 1.0  
**Data:** 18 de Março de 2026

---

## ÍNDICE

1. [Visão Geral](#visão-geral)
2. [Variáveis Obrigatórias](#variáveis-obrigatórias)
3. [Variáveis Opcionais](#variáveis-opcionais)
4. [Variáveis por Categoria](#variáveis-por-categoria)
5. [Validações Automáticas](#validações-automáticas)
6. [Exemplos de Configuração](#exemplos-de-configuração)

---

## VISÃO GERAL

### Níveis de Criticidade

| Símbolo | Nível | Descrição |
|---------|-------|-----------|
| 🔴 | CRÍTICO | Obrigatório em produção. Sistema falha se ausente. |
| 🟠 | REQUERIDO | Obrigatório em produção. Funcionalidade limitada se ausente. |
| 🟡 | OPCIONAL | Recomendado. Usa defaults seguros se ausente. |
| 🟢 | DEV-ONLY | Apenas para desenvolvimento. Ignorado em produção. |

### Ambientes

- **Development:** Desenvolvimento local
- **Production:** Produção
- **Test:** Testes automatizados

---

## VARIÁVEIS OBRIGATÓRIAS

### 🔴 SECRET_KEY

**Descrição:** Chave secreta do Django para criptografia de sessões, cookies e tokens CSRF.

**Obrigatório em:** Production  
**Tipo:** String  
**Tamanho mínimo:** 50 caracteres  
**Formato:** Caracteres aleatórios

**Geração:**
```bash
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

**Exemplo:**
```env
SECRET_KEY=django-insecure-8k#2p9$x@m5n&q7w!e3r4t5y6u7i8o9p0a1s2d3f4g5h6j7k8l9
```

**Validações:**
- ✅ Não pode estar vazio
- ✅ Não pode ser valor padrão ("change-me-in-production", "django-insecure", etc.)
- ✅ Deve ter mínimo 50 caracteres
- ✅ Deve ser único por ambiente

**Segurança:**
- 🔴 Nível Crítico
- Rotação: 90 dias
- Armazenamento: Secrets Manager

---

### 🔴 ALLOWED_HOSTS

**Descrição:** Lista de domínios permitidos para acessar a aplicação (proteção contra Host Header attacks).

**Obrigatório em:** Production  
**Tipo:** Lista (comma-separated)  
**Formato:** Domínios sem protocolo

**Exemplo:**
```env
# Production
ALLOWED_HOSTS=example.com,www.example.com,api.example.com

# Development
ALLOWED_HOSTS=127.0.0.1,localhost
```

**Validações:**
- ✅ Não pode estar vazio em produção
- ✅ Não pode conter localhost/127.0.0.1 em produção
- ✅ Deve listar todos os domínios que acessarão a aplicação

**Segurança:**
- 🟡 Nível Configuração
- Pode estar em código (valores de produção no .env)

---

### 🔴 DB_NAME

**Descrição:** Nome do banco de dados PostgreSQL.

**Obrigatório em:** Production  
**Tipo:** String  
**Default (dev):** alive_platform

**Exemplo:**
```env
# Production
DB_NAME=alive_platform_prod

# Development
DB_NAME=alive_platform
```

**Validações:**
- ✅ Não pode estar vazio em produção

**Segurança:**
- 🟡 Nível Configuração

---

### 🔴 DB_USER

**Descrição:** Usuário do banco de dados PostgreSQL.

**Obrigatório em:** Production  
**Tipo:** String  
**Default (dev):** postgres

**Exemplo:**
```env
# Production
DB_USER=nef_cadencia_user

# Development
DB_USER=postgres
```

**Validações:**
- ✅ Não pode estar vazio em produção

**Segurança:**
- 🟡 Nível Configuração

---

### 🔴 DB_PASSWORD

**Descrição:** Senha do banco de dados PostgreSQL.

**Obrigatório em:** Production  
**Tipo:** String  
**Tamanho mínimo:** 16 caracteres (recomendado)

**Geração:**
```bash
openssl rand -base64 32
```

**Exemplo:**
```env
DB_PASSWORD=Kj8#mP2$nQ9@xR5!wE7&tY3
```

**Validações:**
- ✅ Não pode estar vazio em produção

**Segurança:**
- 🔴 Nível Crítico
- Rotação: 90 dias
- Armazenamento: Secrets Manager
- NUNCA commitar no git

---

### 🔴 DB_HOST

**Descrição:** Hostname ou IP do servidor PostgreSQL.

**Obrigatório em:** Production  
**Tipo:** String  
**Default (dev):** 127.0.0.1

**Exemplo:**
```env
# Production
DB_HOST=db.internal.example.com

# Development
DB_HOST=127.0.0.1
```

**Validações:**
- ✅ Não pode estar vazio em produção

**Segurança:**
- 🟡 Nível Configuração

---

## VARIÁVEIS OPCIONAIS

### 🟡 DJANGO_ENV

**Descrição:** Ambiente de execução. Determina qual settings usar.

**Obrigatório em:** Nenhum (auto-detectado)  
**Tipo:** String  
**Valores:** development, production, test  
**Default:** development

**Exemplo:**
```env
DJANGO_ENV=production
```

**Uso:**
- Development: Usa `settings/development.py`
- Production: Usa `settings/production.py`
- Test: Usa `settings/test.py`

---

### 🟢 DEBUG

**Descrição:** Habilita modo debug do Django.

**Obrigatório em:** Nenhum  
**Tipo:** Boolean  
**Default (dev):** True  
**Default (prod):** False (forçado)

**Exemplo:**
```env
# Development
DEBUG=True

# Production (ignorado, sempre False)
DEBUG=False
```

**Nota:** Em produção, DEBUG é sempre False independente desta variável.

---

### 🟡 DB_PORT

**Descrição:** Porta do servidor PostgreSQL.

**Obrigatório em:** Nenhum  
**Tipo:** Integer  
**Default:** 5432

**Exemplo:**
```env
DB_PORT=5432
```

---

### 🟡 DB_CONN_MAX_AGE

**Descrição:** Tempo máximo de vida de uma conexão ao banco (connection pooling).

**Obrigatório em:** Nenhum  
**Tipo:** Integer (segundos)  
**Default (dev):** 0 (sem pooling)  
**Default (prod):** 600 (10 minutos)

**Exemplo:**
```env
# Production
DB_CONN_MAX_AGE=600

# Development
DB_CONN_MAX_AGE=0
```

**Recomendação:** 600 segundos (10 minutos) em produção.

---

### 🟠 REDIS_URL

**Descrição:** URL de conexão ao Redis (cache e sessões).

**Obrigatório em:** Production  
**Tipo:** String (URL)  
**Formato:** redis://[username:password@]host:port/database

**Exemplo:**
```env
# Production
REDIS_URL=redis://:password@redis.internal.example.com:6379/1

# Development
REDIS_URL=redis://127.0.0.1:6379/1
```

**Nota:** Em desenvolvimento, usa cache em memória se não definido.

**Segurança:**
- 🟠 Nível Sensível (se contém senha)

---

### 🟠 EMAIL_HOST

**Descrição:** Servidor SMTP para envio de emails.

**Obrigatório em:** Production (para funcionalidade completa)  
**Tipo:** String

**Exemplo:**
```env
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST=smtp.sendgrid.net
EMAIL_HOST=smtp.mailgun.org
```

---

### 🟠 EMAIL_PORT

**Descrição:** Porta do servidor SMTP.

**Obrigatório em:** Nenhum  
**Tipo:** Integer  
**Default:** 587

**Valores comuns:**
- 587: TLS (recomendado)
- 465: SSL
- 25: Plain (não recomendado)

**Exemplo:**
```env
EMAIL_PORT=587
```

---

### 🟡 EMAIL_USE_TLS

**Descrição:** Usar TLS para conexão SMTP.

**Obrigatório em:** Nenhum  
**Tipo:** Boolean  
**Default:** True

**Exemplo:**
```env
EMAIL_USE_TLS=True
```

---

### 🟠 EMAIL_HOST_USER

**Descrição:** Usuário para autenticação SMTP.

**Obrigatório em:** Production (se EMAIL_HOST definido)  
**Tipo:** String

**Exemplo:**
```env
EMAIL_HOST_USER=noreply@example.com
```

---

### 🟠 EMAIL_HOST_PASSWORD

**Descrição:** Senha para autenticação SMTP.

**Obrigatório em:** Production (se EMAIL_HOST definido)  
**Tipo:** String

**Exemplo:**
```env
EMAIL_HOST_PASSWORD=app-specific-password-here
```

**Segurança:**
- 🟠 Nível Sensível
- Rotação: 180 dias
- Para Gmail: Usar App Password

---

### 🟠 DEFAULT_FROM_EMAIL

**Descrição:** Email padrão do remetente.

**Obrigatório em:** Production (se EMAIL_HOST definido)  
**Tipo:** String (email)

**Exemplo:**
```env
DEFAULT_FROM_EMAIL=noreply@example.com
```

---

### 🟡 SERVER_EMAIL

**Descrição:** Email para notificações de erro do servidor.

**Obrigatório em:** Nenhum  
**Tipo:** String (email)  
**Default:** Valor de DEFAULT_FROM_EMAIL

**Exemplo:**
```env
SERVER_EMAIL=server@example.com
```

---

### 🟠 CSRF_TRUSTED_ORIGINS

**Descrição:** Domínios confiáveis para requisições CSRF (necessário para AJAX atrás de proxy).

**Obrigatório em:** Production (se usar AJAX)  
**Tipo:** Lista (comma-separated)  
**Formato:** URLs completas com protocolo

**Exemplo:**
```env
CSRF_TRUSTED_ORIGINS=https://example.com,https://www.example.com,https://api.example.com
```

**Nota:** DEVE incluir o protocolo (https://).

---

### 🟡 SECURE_HSTS_SECONDS

**Descrição:** Tempo (em segundos) para HSTS (HTTP Strict Transport Security).

**Obrigatório em:** Nenhum  
**Tipo:** Integer  
**Default (prod):** 31536000 (1 ano)

**Exemplo:**
```env
SECURE_HSTS_SECONDS=31536000
```

**Valores recomendados:**
- Staging: 3600 (1 hora) para testes
- Production: 31536000 (1 ano)

---

### 🟡 SECURE_SSL_REDIRECT

**Descrição:** Forçar redirecionamento HTTP → HTTPS.

**Obrigatório em:** Nenhum  
**Tipo:** Boolean  
**Default (prod):** True

**Exemplo:**
```env
SECURE_SSL_REDIRECT=True
```

---

### 🟠 OPENAI_API_KEY

**Descrição:** Chave de API da OpenAI para funcionalidades de assistente.

**Obrigatório em:** Production (para funcionalidade de assistente)  
**Tipo:** String  
**Formato:** sk-...

**Obter em:** https://platform.openai.com/api-keys

**Exemplo:**
```env
OPENAI_API_KEY=sk-proj-abc123def456ghi789jkl012mno345pqr678stu901vwx234
```

**Validações:**
- ✅ Deve começar com "sk-"
- ✅ Deve ter mínimo 20 caracteres

**Segurança:**
- 🔴 Nível Crítico
- Rotação: 180 dias
- Configurar limites de uso na plataforma OpenAI

---

### 🟡 OPENAI_MODEL

**Descrição:** Modelo da OpenAI a ser usado.

**Obrigatório em:** Nenhum  
**Tipo:** String  
**Default:** gpt-4-turbo-mini

**Valores comuns:**
- gpt-4-turbo
- gpt-4
- gpt-3.5-turbo

**Exemplo:**
```env
OPENAI_MODEL=gpt-4-turbo
```

---

### 🟢 ASSISTANT_DEBUG

**Descrição:** Habilita logs verbosos do assistente.

**Obrigatório em:** Nenhum  
**Tipo:** Boolean  
**Default:** False

**Exemplo:**
```env
# Development
ASSISTANT_DEBUG=True

# Production
ASSISTANT_DEBUG=False
```

---

### 🟡 LOG_FILE

**Descrição:** Caminho do arquivo de log principal.

**Obrigatório em:** Nenhum  
**Tipo:** String (path)  
**Default (prod):** /var/log/nef-cadencia/django.log

**Exemplo:**
```env
LOG_FILE=/var/log/nef-cadencia/django.log
```

**Nota:** Diretório deve existir e ter permissões de escrita.

---

### 🟡 ERROR_LOG_FILE

**Descrição:** Caminho do arquivo de log de erros.

**Obrigatório em:** Nenhum  
**Tipo:** String (path)  
**Default (prod):** /var/log/nef-cadencia/error.log

**Exemplo:**
```env
ERROR_LOG_FILE=/var/log/nef-cadencia/error.log
```

---

### 🟡 DJANGO_LOG_LEVEL

**Descrição:** Nível de log do Django.

**Obrigatório em:** Nenhum  
**Tipo:** String  
**Valores:** DEBUG, INFO, WARNING, ERROR, CRITICAL  
**Default (dev):** DEBUG  
**Default (prod):** INFO

**Exemplo:**
```env
# Production
DJANGO_LOG_LEVEL=INFO

# Development
DJANGO_LOG_LEVEL=DEBUG
```

---

### 🟡 ADMINS

**Descrição:** Lista de administradores para receber notificações de erro.

**Obrigatório em:** Nenhum  
**Tipo:** Lista (comma-separated)  
**Formato:** Nome:email@example.com

**Exemplo:**
```env
ADMINS=John Doe:john@example.com,Jane Smith:jane@example.com
```

---

### 🟡 SESSION_COOKIE_AGE

**Descrição:** Tempo de vida da sessão (em segundos).

**Obrigatório em:** Nenhum  
**Tipo:** Integer  
**Default (prod):** 3600 (1 hora)

**Valores comuns:**
- 3600: 1 hora (recomendado para produção)
- 7200: 2 horas
- 28800: 8 horas
- 86400: 24 horas

**Exemplo:**
```env
SESSION_COOKIE_AGE=3600
```

---

### 🟢 SHOW_SQL

**Descrição:** Mostrar queries SQL no console (apenas desenvolvimento).

**Obrigatório em:** Nenhum  
**Tipo:** Boolean  
**Default:** False

**Exemplo:**
```env
# Development only
SHOW_SQL=True
```

**Nota:** Ignorado em produção.

---

## VARIÁVEIS LEGADAS (OPCIONAL)

### 🟡 LEGACY_DRIVER

**Descrição:** Driver ODBC para conexão com banco legado SQL Server.

**Obrigatório em:** Apenas se usar sincronização com sistema legado  
**Tipo:** String

**Exemplo:**
```env
LEGACY_DRIVER=ODBC Driver 17 for SQL Server
```

---

### 🟡 LEGACY_SERVER

**Descrição:** Servidor do banco legado.

**Obrigatório em:** Apenas se usar sincronização com sistema legado  
**Tipo:** String

**Exemplo:**
```env
LEGACY_SERVER=legacy-db.internal.example.com
```

---

### 🟡 LEGACY_PORT

**Descrição:** Porta do banco legado.

**Obrigatório em:** Nenhum  
**Tipo:** Integer  
**Default:** 1433 (SQL Server)

**Exemplo:**
```env
LEGACY_PORT=1433
```

---

### 🟡 LEGACY_USER

**Descrição:** Usuário do banco legado.

**Obrigatório em:** Apenas se usar sincronização com sistema legado  
**Tipo:** String

**Exemplo:**
```env
LEGACY_USER=legacy_user
```

---

### 🟡 LEGACY_PASSWORD

**Descrição:** Senha do banco legado.

**Obrigatório em:** Apenas se usar sincronização com sistema legado  
**Tipo:** String

**Exemplo:**
```env
LEGACY_PASSWORD=legacy-password-here
```

**Segurança:**
- 🟠 Nível Sensível
- Rotação: 180 dias

---

### 🟡 LEGACY_DATABASE

**Descrição:** Nome do banco legado.

**Obrigatório em:** Apenas se usar sincronização com sistema legado  
**Tipo:** String

**Exemplo:**
```env
LEGACY_DATABASE=LH_ALIVE
```

---

### 🟡 LEGACY_SCHEMA

**Descrição:** Schema do banco legado.

**Obrigatório em:** Nenhum  
**Tipo:** String  
**Default:** dbo

**Exemplo:**
```env
LEGACY_SCHEMA=dbo
```

---

### 🟡 LEGACY_EVENTS_TABLE

**Descrição:** Nome da tabela de eventos no banco legado.

**Obrigatório em:** Nenhum  
**Tipo:** String  
**Default:** agent_events

**Exemplo:**
```env
LEGACY_EVENTS_TABLE=agent_events
```

---

## VALIDAÇÕES AUTOMÁTICAS

### Production Settings

O arquivo `settings/production.py` valida automaticamente:

#### Validações Críticas (Falha Fatal)

✅ **SECRET_KEY:**
- Não pode estar vazio
- Não pode ser valor padrão
- Deve ter mínimo 50 caracteres

✅ **ALLOWED_HOSTS:**
- Não pode estar vazio
- Não pode conter localhost/127.0.0.1

✅ **Database:**
- DB_NAME não pode estar vazio
- DB_USER não pode estar vazio
- DB_PASSWORD não pode estar vazio
- DB_HOST não pode estar vazio

✅ **OPENAI_API_KEY (se definido):**
- Deve começar com "sk-"
- Deve ter mínimo 20 caracteres

#### Validações de Aviso (Warning)

⚠️ **Email (se incompleto):**
- EMAIL_HOST
- EMAIL_HOST_USER
- EMAIL_HOST_PASSWORD
- DEFAULT_FROM_EMAIL

---

## EXEMPLOS DE CONFIGURAÇÃO

### Desenvolvimento Local

```env
# Ambiente
DJANGO_ENV=development

# Django
SECRET_KEY=qualquer-chave-para-desenvolvimento
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

# Database
DB_NAME=alive_platform
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=127.0.0.1
DB_PORT=5432
DB_CONN_MAX_AGE=0

# OpenAI
OPENAI_API_KEY=sk-dev-key-here
OPENAI_MODEL=gpt-4-turbo-mini
ASSISTANT_DEBUG=True

# Development Tools
SHOW_SQL=False
```

### Produção

```env
# Ambiente
DJANGO_ENV=production

# Django (CRÍTICO)
SECRET_KEY=<gerar-com-comando-seguro>
DEBUG=False
ALLOWED_HOSTS=example.com,www.example.com

# Database (CRÍTICO)
DB_NAME=alive_platform_prod
DB_USER=nef_cadencia_user
DB_PASSWORD=<senha-forte-gerada>
DB_HOST=db.internal.example.com
DB_PORT=5432
DB_CONN_MAX_AGE=600

# Redis
REDIS_URL=redis://:password@redis.internal.example.com:6379/1

# Email
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=<sendgrid-api-key>
DEFAULT_FROM_EMAIL=noreply@example.com
SERVER_EMAIL=server@example.com

# Security
CSRF_TRUSTED_ORIGINS=https://example.com,https://www.example.com
SECURE_HSTS_SECONDS=31536000
SECURE_SSL_REDIRECT=True

# OpenAI
OPENAI_API_KEY=<chave-producao>
OPENAI_MODEL=gpt-4-turbo

# Logging
LOG_FILE=/var/log/nef-cadencia/django.log
ERROR_LOG_FILE=/var/log/nef-cadencia/error.log
DJANGO_LOG_LEVEL=INFO

# Admins
ADMINS=DevOps:devops@example.com

# Session
SESSION_COOKIE_AGE=3600
```

---

## RESUMO POR CRITICIDADE

### 🔴 CRÍTICO (6 variáveis)

1. SECRET_KEY
2. ALLOWED_HOSTS
3. DB_NAME
4. DB_USER
5. DB_PASSWORD
6. DB_HOST

### 🟠 REQUERIDO (8 variáveis)

1. REDIS_URL
2. EMAIL_HOST
3. EMAIL_HOST_USER
4. EMAIL_HOST_PASSWORD
5. DEFAULT_FROM_EMAIL
6. CSRF_TRUSTED_ORIGINS
7. OPENAI_API_KEY

### 🟡 OPCIONAL (15 variáveis)

1. DJANGO_ENV
2. DB_PORT
3. DB_CONN_MAX_AGE
4. EMAIL_PORT
5. EMAIL_USE_TLS
6. SERVER_EMAIL
7. SECURE_HSTS_SECONDS
8. SECURE_SSL_REDIRECT
9. OPENAI_MODEL
10. LOG_FILE
11. ERROR_LOG_FILE
12. DJANGO_LOG_LEVEL
13. ADMINS
14. SESSION_COOKIE_AGE
15. LEGACY_* (7 variáveis)

### 🟢 DEV-ONLY (3 variáveis)

1. DEBUG
2. ASSISTANT_DEBUG
3. SHOW_SQL

---

**Total de Variáveis:** 32 (principais) + 7 (legado) = 39 variáveis

---

**Última Atualização:** 18 de Março de 2026  
**Versão:** 1.0
