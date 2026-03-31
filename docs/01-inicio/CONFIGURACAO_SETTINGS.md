# Configuração de Settings - NEF Cadência

## Visão Geral

O projeto agora utiliza uma estrutura modular de settings separando configurações de **desenvolvimento**, **produção** e **testes**.

### Estrutura de Arquivos

```
alive_platform/
└── settings/
    ├── __init__.py      # Auto-seleção baseada em DJANGO_ENV
    ├── base.py          # Configurações comuns a todos ambientes
    ├── development.py   # Configurações de desenvolvimento
    ├── production.py    # Configurações de produção (hardened)
    └── test.py          # Configurações para testes
```

---

## Como Usar

### 1. Desenvolvimento Local (Padrão)

**Método 1: Automático (Recomendado)**
```bash
# O manage.py já usa development por padrão
python manage.py runserver
```

**Método 2: Via variável de ambiente**
```bash
# Windows PowerShell
$env:DJANGO_ENV="development"
python manage.py runserver

# Linux/Mac
export DJANGO_ENV=development
python manage.py runserver
```

**Método 3: Via DJANGO_SETTINGS_MODULE**
```bash
# Windows PowerShell
$env:DJANGO_SETTINGS_MODULE="alive_platform.settings.development"
python manage.py runserver

# Linux/Mac
export DJANGO_SETTINGS_MODULE=alive_platform.settings.development
python manage.py runserver
```

### 2. Produção

**Configurar variável de ambiente:**
```bash
# Linux/Mac (adicionar ao .bashrc ou .profile)
export DJANGO_ENV=production

# Ou usar DJANGO_SETTINGS_MODULE diretamente
export DJANGO_SETTINGS_MODULE=alive_platform.settings.production
```

**Executar com Gunicorn:**
```bash
gunicorn alive_platform.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --env DJANGO_ENV=production
```

**Systemd Service:**
```ini
[Service]
Environment="DJANGO_ENV=production"
Environment="DJANGO_SETTINGS_MODULE=alive_platform.settings.production"
```

### 3. Testes

```bash
# Automático via pytest
pytest

# Manual
python manage.py test --settings=alive_platform.settings.test
```

---

## Configuração do .env

### Passo 1: Criar arquivo .env

```bash
# Copiar template
cp .env.example .env
```

### Passo 2: Configurar variáveis

#### Desenvolvimento Local

```env
DJANGO_ENV=development
SECRET_KEY=qualquer-chave-para-desenvolvimento
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

DB_NAME=alive_platform
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=127.0.0.1
DB_PORT=5432

OPENAI_API_KEY=sk-your-key-here
```

#### Produção

```env
DJANGO_ENV=production

# CRÍTICO: Gerar chave segura
SECRET_KEY=<gerar-chave-segura>

DEBUG=False
ALLOWED_HOSTS=seu-dominio.com,www.seu-dominio.com

# Database
DB_NAME=alive_platform_prod
DB_USER=nef_user
DB_PASSWORD=<senha-forte-aqui>
DB_HOST=db.production.local
DB_PORT=5432
DB_CONN_MAX_AGE=600

# Redis
REDIS_URL=redis://redis.production.local:6379/1

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=noreply@seu-dominio.com
EMAIL_HOST_PASSWORD=<senha-email>
DEFAULT_FROM_EMAIL=noreply@seu-dominio.com
SERVER_EMAIL=server@seu-dominio.com

# Security
CSRF_TRUSTED_ORIGINS=https://seu-dominio.com,https://www.seu-dominio.com
SECURE_HSTS_SECONDS=31536000
SECURE_SSL_REDIRECT=True

# OpenAI
OPENAI_API_KEY=sk-prod-key-here
OPENAI_MODEL=gpt-4-turbo

# Logging
LOG_FILE=/var/log/nef-cadencia/django.log
ERROR_LOG_FILE=/var/log/nef-cadencia/error.log

# Admins
ADMINS=Nome Admin:admin@seu-dominio.com
```

---

## Gerar SECRET_KEY Segura

### Método 1: Django
```bash
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

### Método 2: Python
```python
import secrets
print(secrets.token_urlsafe(50))
```

### Método 3: OpenSSL
```bash
openssl rand -base64 50
```

---

## Diferenças entre Ambientes

### Development (`development.py`)

✅ **Habilitado:**
- DEBUG=True
- Console email backend
- SQL queries no console (opcional)
- Logs verbosos
- ALLOWED_HOSTS permissivo

❌ **Desabilitado:**
- HTTPS redirect
- Secure cookies
- HSTS
- Template caching

### Production (`production.py`)

✅ **Habilitado:**
- HTTPS redirect obrigatório
- Secure cookies (HTTPS only)
- HSTS com 1 ano
- Content Security headers
- Template caching
- Redis cache
- SMTP email
- Structured logging (JSON)
- Connection pooling
- Error notifications

❌ **Desabilitado:**
- DEBUG (sempre False)
- Debug context processor
- Defaults inseguros

🔒 **Validações:**
- SECRET_KEY obrigatória (sem default)
- ALLOWED_HOSTS obrigatório
- Falha se configurações críticas ausentes

### Test (`test.py`)

✅ **Otimizado para:**
- Velocidade (SQLite in-memory)
- Isolamento (dummy cache)
- Hashing rápido (MD5)
- Logs mínimos

---

## Configurações de Segurança (Produção)

### HTTPS e SSL

```python
SECURE_SSL_REDIRECT = True                    # Força HTTPS
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True                  # Cookie apenas HTTPS
CSRF_COOKIE_SECURE = True                     # CSRF apenas HTTPS
```

### HSTS (HTTP Strict Transport Security)

```python
SECURE_HSTS_SECONDS = 31536000                # 1 ano
SECURE_HSTS_INCLUDE_SUBDOMAINS = True         # Incluir subdomínios
SECURE_HSTS_PRELOAD = True                    # Preload list
```

### Content Security

```python
SECURE_CONTENT_TYPE_NOSNIFF = True            # Previne MIME sniffing
SECURE_BROWSER_XSS_FILTER = True              # XSS protection
X_FRAME_OPTIONS = 'DENY'                      # Previne clickjacking
```

### CSRF Protection

```python
CSRF_TRUSTED_ORIGINS = [
    'https://seu-dominio.com',
    'https://www.seu-dominio.com',
]
```

---

## Logging

### Development
- **Handler:** Console
- **Format:** Verbose text
- **Level:** DEBUG para apps, INFO para Django

### Production
- **Handlers:** Console + File (rotating) + Error file + Email admins
- **Format:** JSON estruturado
- **Level:** INFO geral, ERROR para notificações
- **Rotation:** 10 arquivos de 10MB cada

### Localização dos Logs (Produção)

```
/var/log/nef-cadencia/
├── django.log       # Logs gerais
└── error.log        # Apenas erros
```

---

## Cache

### Development
```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}
```

### Production
```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}
```

---

## Arquivos Estáticos

### Development
```bash
# Django serve automaticamente
python manage.py runserver
```

### Production

**Opção 1: Nginx (Recomendado)**
```bash
# Coletar arquivos estáticos
python manage.py collectstatic --noinput

# Nginx serve de /staticfiles/
```

**Opção 2: WhiteNoise**
```python
# Adicionar ao requirements.txt
whitenoise==6.6.0

# Adicionar ao MIDDLEWARE (production.py)
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

# Configurar storage
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

---

## Migrations

### Development
```bash
python manage.py makemigrations
python manage.py migrate
```

### Production
```bash
# Sempre rodar antes de deploy
python manage.py migrate --noinput

# Verificar status
python manage.py showmigrations
```

---

## Checklist de Deploy

### Antes do Deploy

- [ ] `.env` configurado com valores de produção
- [ ] `SECRET_KEY` gerada e segura
- [ ] `DEBUG=False`
- [ ] `ALLOWED_HOSTS` configurado corretamente
- [ ] `CSRF_TRUSTED_ORIGINS` configurado
- [ ] Credenciais de banco seguras
- [ ] Redis configurado
- [ ] Email SMTP configurado
- [ ] Logs directory criado (`/var/log/nef-cadencia/`)
- [ ] Arquivos estáticos coletados
- [ ] Migrations aplicadas

### Validar Configuração

```bash
# Verificar configurações
python manage.py check --deploy

# Testar settings
python manage.py shell
>>> from django.conf import settings
>>> print(settings.DEBUG)  # Deve ser False
>>> print(settings.ALLOWED_HOSTS)
>>> print(settings.SECRET_KEY[:10])  # Primeiros 10 chars
```

---

## Troubleshooting

### Erro: "SECRET_KEY must be set"

**Causa:** SECRET_KEY não definida no .env em produção

**Solução:**
```bash
# Gerar chave
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'

# Adicionar ao .env
SECRET_KEY=<chave-gerada>
```

### Erro: "ALLOWED_HOSTS must be set"

**Causa:** ALLOWED_HOSTS vazio em produção

**Solução:**
```bash
# Adicionar ao .env
ALLOWED_HOSTS=seu-dominio.com,www.seu-dominio.com
```

### Erro: "DisallowedHost at /"

**Causa:** Host não está em ALLOWED_HOSTS

**Solução:**
```bash
# Adicionar host ao .env
ALLOWED_HOSTS=seu-dominio.com,ip-do-servidor
```

### Erro: "No module named 'django_redis'"

**Causa:** django-redis não instalado (necessário para cache em produção)

**Solução:**
```bash
pip install django-redis
```

### Erro: Logs não são criados

**Causa:** Diretório de logs não existe ou sem permissão

**Solução:**
```bash
# Criar diretório
sudo mkdir -p /var/log/nef-cadencia

# Dar permissão
sudo chown www-data:www-data /var/log/nef-cadencia
sudo chmod 755 /var/log/nef-cadencia
```

### Arquivos estáticos não carregam (404)

**Causa:** collectstatic não executado ou nginx mal configurado

**Solução:**
```bash
# Coletar arquivos
python manage.py collectstatic --noinput

# Verificar STATIC_ROOT
ls -la staticfiles/
```

---

## Migração do Settings Antigo

O arquivo `alive_platform/settings.py` original foi substituído pela estrutura modular.

### Backup (se necessário)

```bash
# Fazer backup do settings.py antigo
cp alive_platform/settings.py alive_platform/settings.py.backup
```

### Compatibilidade

A nova estrutura é **100% compatível** com o código existente. Nenhuma alteração necessária em:
- Views
- Models
- Templates
- URLs
- Management commands

---

## Próximos Passos Recomendados

1. **Instalar dependências adicionais para produção:**
   ```bash
   pip install django-redis gunicorn whitenoise python-json-logger
   ```

2. **Configurar Sentry (monitoring):**
   ```bash
   pip install sentry-sdk
   ```
   
   Adicionar ao `production.py`:
   ```python
   import sentry_sdk
   sentry_sdk.init(dsn=env('SENTRY_DSN'))
   ```

3. **Configurar CI/CD** para validar settings em cada deploy

4. **Implementar healthcheck endpoint** (já documentado na auditoria)

5. **Configurar backup automático** do banco de dados

---

## Referências

- [Django Settings Best Practices](https://docs.djangoproject.com/en/stable/topics/settings/)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/stable/howto/deployment/checklist/)
- [Django Security](https://docs.djangoproject.com/en/stable/topics/security/)
- [12 Factor App](https://12factor.net/)

---

**Última atualização:** 18 de Março de 2026  
**Versão:** 1.0
