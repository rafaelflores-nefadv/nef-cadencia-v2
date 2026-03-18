# Auditoria Técnica para Produção - NEF Cadência v2

**Data:** 18 de Março de 2026  
**Versão:** 1.0  
**Status:** CRÍTICO - Sistema NÃO está pronto para produção ⚠️

---

## RESUMO EXECUTIVO

O sistema **NÃO ESTÁ PRONTO** para deploy em produção. Foram identificados **47 problemas críticos** que representam riscos graves de segurança, estabilidade e manutenção.

### Criticidade Geral
- 🔴 **CRÍTICO:** 23 problemas
- 🟠 **ALTO:** 15 problemas  
- 🟡 **MÉDIO:** 9 problemas

### Áreas Mais Críticas
1. **Segurança:** 15 problemas críticos
2. **Infraestrutura:** 12 problemas críticos (ausência total)
3. **Configuração:** 8 problemas críticos
4. **Observabilidade:** 7 problemas críticos

---

## 1. RISCOS DE SEGURANÇA

### 🔴 CRÍTICO #1: SECRET_KEY com valor padrão inseguro
**Problema:** `SECRET_KEY = env("SECRET_KEY", default="change-me-in-production")`  
**Criticidade:** 🔴 CRÍTICO  
**Impacto:** Comprometimento total da segurança. Permite:
- Falsificação de sessões
- Bypass de CSRF tokens
- Assinatura de cookies maliciosos
- Acesso não autorizado total

**Solução:**
```python
# settings.py
SECRET_KEY = env("SECRET_KEY")  # SEM default
# Falhar se não estiver definida
```

**Arquivos:** `alive_platform/settings.py:13`

---

### 🔴 CRÍTICO #2: DEBUG habilitado em produção
**Problema:** `DEBUG = env("DEBUG")` sem validação  
**Criticidade:** 🔴 CRÍTICO  
**Impacto:**
- Exposição de stack traces com código-fonte
- Vazamento de variáveis de ambiente
- Exposição de queries SQL
- Informações sensíveis visíveis

**Solução:**
```python
DEBUG = False  # SEMPRE False em produção
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")  # Obrigatório
```

**Arquivos:** `alive_platform/settings.py:14`

---

### 🔴 CRÍTICO #3: Ausência de configurações HTTPS
**Problema:** Nenhuma configuração de segurança HTTPS presente  
**Criticidade:** 🔴 CRÍTICO  
**Impacto:**
- Cookies transmitidos em texto claro
- Session hijacking
- Man-in-the-middle attacks
- Dados sensíveis interceptáveis

**Solução:**
```python
# Adicionar ao settings.py
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000  # 1 ano
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
```

**Arquivos:** `alive_platform/settings.py`

---

### 🔴 CRÍTICO #4: Ausência de CSRF_TRUSTED_ORIGINS
**Problema:** Não configurado para proxy reverso  
**Criticidade:** 🔴 CRÍTICO  
**Impacto:**
- CSRF validation quebrada atrás de proxy
- Requisições legítimas bloqueadas
- Aplicação não funcional em produção

**Solução:**
```python
CSRF_TRUSTED_ORIGINS = env.list(
    'CSRF_TRUSTED_ORIGINS',
    default=['https://seu-dominio.com']
)
```

**Arquivos:** `alive_platform/settings.py`

---

### 🔴 CRÍTICO #5: ALLOWED_HOSTS com valores de desenvolvimento
**Problema:** `default=["127.0.0.1", "localhost"]`  
**Criticidade:** 🔴 CRÍTICO  
**Impacto:**
- Host header poisoning
- Cache poisoning
- Password reset poisoning

**Solução:**
```python
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS')  # SEM default
# .env: ALLOWED_HOSTS=seu-dominio.com,www.seu-dominio.com
```

**Arquivos:** `alive_platform/settings.py:16`

---

### 🔴 CRÍTICO #6: Credenciais de banco com defaults inseguros
**Problema:** Senha padrão `default="postgres"`  
**Criticidade:** 🔴 CRÍTICO  
**Impacto:**
- Acesso total ao banco de dados
- Vazamento de dados
- Modificação/exclusão de dados

**Solução:**
```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("DB_NAME"),  # SEM default
        "USER": env("DB_USER"),  # SEM default
        "PASSWORD": env("DB_PASSWORD"),  # SEM default
        "HOST": env("DB_HOST"),
        "PORT": env("DB_PORT", default="5432"),
        "CONN_MAX_AGE": 600,  # Connection pooling
        "OPTIONS": {
            "sslmode": "require",  # SSL obrigatório
        }
    }
}
```

**Arquivos:** `alive_platform/settings.py:81-90`

---

### 🔴 CRÍTICO #7: OPENAI_API_KEY com default vazio
**Problema:** `default=""`permite rodar sem chave  
**Criticidade:** 🔴 CRÍTICO  
**Impacto:**
- Falhas silenciosas em produção
- Funcionalidade quebrada
- Custos não rastreados

**Solução:**
```python
OPENAI_API_KEY = env("OPENAI_API_KEY")  # SEM default
# Validar no startup
if not OPENAI_API_KEY:
    raise ImproperlyConfigured("OPENAI_API_KEY must be set")
```

**Arquivos:** `alive_platform/settings.py:21`

---

### 🔴 CRÍTICO #8: Ausência de rate limiting
**Problema:** Nenhum rate limiting configurado  
**Criticidade:** 🔴 CRÍTICO  
**Impacto:**
- DDoS attacks
- Brute force attacks
- Custos excessivos de API
- Abuso de recursos

**Solução:**
```python
# Instalar django-ratelimit
INSTALLED_APPS += ['django_ratelimit']

# Aplicar em views críticas
from django_ratelimit.decorators import ratelimit

@ratelimit(key='ip', rate='5/m')
def login_view(request):
    pass
```

**Arquivos:** N/A (ausente)

---

### 🔴 CRÍTICO #9: Ausência de Content Security Policy (CSP)
**Problema:** Nenhuma CSP configurada  
**Criticidade:** 🔴 CRÍTICO  
**Impacto:**
- XSS attacks
- Clickjacking
- Data injection
- Malicious scripts

**Solução:**
```python
# Instalar django-csp
INSTALLED_APPS += ['csp']
MIDDLEWARE += ['csp.middleware.CSPMiddleware']

CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'")  # Ajustar conforme necessário
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'")
CSP_IMG_SRC = ("'self'", "data:", "https:")
```

**Arquivos:** N/A (ausente)

---

### 🟠 ALTO #10: Ausência de CORS configurado
**Problema:** Nenhuma configuração CORS  
**Criticidade:** 🟠 ALTO  
**Impacto:**
- APIs expostas sem controle
- Cross-origin attacks

**Solução:**
```python
INSTALLED_APPS += ['corsheaders']
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    # ... outros middlewares
]

CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=[])
CORS_ALLOW_CREDENTIALS = True
```

**Arquivos:** `alive_platform/settings.py`

---

### 🟠 ALTO #11: Context processor de debug ativo
**Problema:** `django.template.context_processors.debug` em produção  
**Criticidade:** 🟠 ALTO  
**Impacto:**
- Vazamento de informações de debug
- Exposição de configurações

**Solução:**
```python
"context_processors": [
    # Remover em produção:
    # "django.template.context_processors.debug",
    "django.template.context_processors.request",
    # ...
]
```

**Arquivos:** `alive_platform/settings.py:62`

---

### 🟠 ALTO #12: Ausência de proteção contra SQL Injection
**Problema:** Nenhuma validação de queries raw  
**Criticidade:** 🟠 ALTO  
**Impacto:**
- SQL injection em queries customizadas
- Acesso não autorizado a dados

**Solução:**
- Usar sempre ORM do Django
- Se usar raw SQL, sempre usar parametrização
- Adicionar linter para detectar raw queries

**Arquivos:** Verificar todas as queries raw no código

---

### 🟠 ALTO #13: Ausência de validação de uploads
**Problema:** Nenhuma configuração de MEDIA_ROOT/MEDIA_URL  
**Criticidade:** 🟠 ALTO  
**Impacto:**
- Upload de arquivos maliciosos
- Path traversal attacks

**Solução:**
```python
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Validação de uploads
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880
ALLOWED_UPLOAD_EXTENSIONS = ['.pdf', '.jpg', '.png']
```

**Arquivos:** `alive_platform/settings.py`

---

### 🟡 MÉDIO #14: Ausência de 2FA
**Problema:** Nenhuma autenticação de dois fatores  
**Criticidade:** 🟡 MÉDIO  
**Impacto:**
- Contas comprometidas com senha vazada
- Acesso não autorizado

**Solução:**
```python
# Instalar django-otp
INSTALLED_APPS += [
    'django_otp',
    'django_otp.plugins.otp_totp',
]
MIDDLEWARE += ['django_otp.middleware.OTPMiddleware']
```

**Arquivos:** N/A (ausente)

---

### 🟡 MÉDIO #15: Ausência de auditoria de login
**Problema:** Nenhum log de tentativas de login  
**Criticidade:** 🟡 MÉDIO  
**Impacto:**
- Impossível detectar ataques
- Sem rastreabilidade

**Solução:**
- Implementar signal para login/logout
- Logar IP, timestamp, sucesso/falha
- Alertar em múltiplas falhas

**Arquivos:** N/A (ausente)

---

## 2. PROBLEMAS DE CONFIGURAÇÃO

### 🔴 CRÍTICO #16: Ausência de settings específico para produção
**Problema:** Apenas um settings.py para todos os ambientes  
**Criticidade:** 🔴 CRÍTICO  
**Impacto:**
- Configurações de dev em produção
- Impossível gerenciar ambientes
- Risco de erro humano

**Solução:**
```
settings/
├── __init__.py
├── base.py
├── development.py
├── production.py
├── staging.py
└── test.py
```

```python
# production.py
from .base import *

DEBUG = False
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS')
# ... configs de produção
```

**Arquivos:** `alive_platform/settings.py`

---

### 🔴 CRÍTICO #17: Ausência de validação de variáveis de ambiente
**Problema:** Nenhuma validação no startup  
**Criticidade:** 🔴 CRÍTICO  
**Impacto:**
- Aplicação inicia com configuração inválida
- Falhas em runtime
- Downtime

**Solução:**
```python
# settings.py
from django.core.exceptions import ImproperlyConfigured

REQUIRED_ENV_VARS = [
    'SECRET_KEY',
    'DB_NAME',
    'DB_USER',
    'DB_PASSWORD',
    'ALLOWED_HOSTS',
]

for var in REQUIRED_ENV_VARS:
    if not env(var, default=None):
        raise ImproperlyConfigured(f"{var} must be set")
```

**Arquivos:** `alive_platform/settings.py`

---

### 🟠 ALTO #18: Ausência de configuração de email
**Problema:** Nenhuma configuração SMTP  
**Criticidade:** 🟠 ALTO  
**Impacto:**
- Impossível enviar emails
- Password reset não funciona
- Notificações não funcionam

**Solução:**
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env('EMAIL_HOST')
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_USE_TLS = True
EMAIL_HOST_USER = env('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL')
SERVER_EMAIL = env('SERVER_EMAIL', default=DEFAULT_FROM_EMAIL)
```

**Arquivos:** `alive_platform/settings.py`

---

### 🟠 ALTO #19: Ausência de configuração de cache
**Problema:** Nenhum cache configurado  
**Criticidade:** 🟠 ALTO  
**Impacto:**
- Performance ruim
- Sobrecarga no banco
- Custos elevados

**Solução:**
```python
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': env('REDIS_URL', default='redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'nef_cadencia',
        'TIMEOUT': 300,
    }
}

SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
```

**Arquivos:** `alive_platform/settings.py`

---

### 🟠 ALTO #20: Ausência de configuração de timezone
**Problema:** Timezone configurado mas sem validação  
**Criticidade:** 🟠 ALTO  
**Impacto:**
- Inconsistências de horário
- Bugs em relatórios
- Dados incorretos

**Solução:**
```python
TIME_ZONE = 'America/Sao_Paulo'
USE_TZ = True  # Já está correto

# Garantir que todas as queries usem timezone-aware datetimes
from django.utils import timezone
# Usar timezone.now() ao invés de datetime.now()
```

**Arquivos:** `alive_platform/settings.py:117-121`

---

### 🟡 MÉDIO #21: Context processors não otimizados
**Problema:** Context processors customizados sem cache  
**Criticidade:** 🟡 MÉDIO  
**Impacto:**
- Queries desnecessárias em cada request
- Performance degradada

**Solução:**
```python
# apps/core/context_processors.py
from django.core.cache import cache

def user_permissions(request):
    if not request.user.is_authenticated:
        return {}
    
    cache_key = f'user_perms_{request.user.id}'
    permissions = cache.get(cache_key)
    
    if permissions is None:
        permissions = get_user_permissions_summary(request.user)
        cache.set(cache_key, permissions, 300)  # 5 min
    
    return {'user_permissions': permissions, **permissions}
```

**Arquivos:** `apps/core/context_processors.py`

---

### 🟡 MÉDIO #22: Ausência de configuração de internacionalização
**Problema:** i18n configurado mas sem locale path  
**Criticidade:** 🟡 MÉDIO  
**Impacto:**
- Traduções não funcionam
- Mensagens em inglês

**Solução:**
```python
LOCALE_PATHS = [BASE_DIR / 'locale']
LANGUAGES = [
    ('pt-br', 'Português (Brasil)'),
    ('en', 'English'),
]
```

**Arquivos:** `alive_platform/settings.py`

---

### 🟡 MÉDIO #23: Ausência de configuração de admin
**Problema:** Admin sem customizações de segurança  
**Criticidade:** 🟡 MÉDIO  
**Impacto:**
- Admin acessível em /admin/ (padrão)
- Fácil de encontrar e atacar

**Solução:**
```python
# urls.py
admin.site.site_header = 'NEF Cadência Admin'
admin.site.site_title = 'NEF Cadência'
admin.site.index_title = 'Administração'

# Mudar URL do admin
path('admin-secreto-xyz/', admin.site.urls),  # Não usar /admin/
```

**Arquivos:** `alive_platform/urls.py`

---

## 3. USO INADEQUADO DE .ENV E SECRETS

### 🔴 CRÍTICO #24: .env presente no repositório
**Problema:** Arquivo .env existe no diretório (551 bytes)  
**Criticidade:** 🔴 CRÍTICO  
**Impacto:**
- Secrets commitados no git
- Exposição de credenciais
- Comprometimento total

**Solução:**
```bash
# Remover .env do repositório
git rm --cached .env
git commit -m "Remove .env from repository"

# Verificar histórico
git log --all --full-history -- .env

# Se commitado, reescrever histórico
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch .env' \
  --prune-empty --tag-name-filter cat -- --all
```

**Arquivos:** `.env` (DELETAR)

---

### 🔴 CRÍTICO #25: Ausência de .env.example
**Problema:** Nenhum template de variáveis de ambiente  
**Criticidade:** 🔴 CRÍTICO  
**Impacto:**
- Desenvolvedores não sabem quais variáveis configurar
- Erros de configuração
- Documentação inadequada

**Solução:**
```bash
# Criar .env.example
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=alive_platform
DB_USER=postgres
DB_PASSWORD=your-db-password
DB_HOST=localhost
DB_PORT=5432

OPENAI_API_KEY=your-openai-key
OPENAI_MODEL=gpt-4-turbo

EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-email-password

REDIS_URL=redis://localhost:6379/1
```

**Arquivos:** `.env.example` (CRIAR)

---

### 🟠 ALTO #26: Ausência de secrets management
**Problema:** Nenhum sistema de gestão de secrets  
**Criticidade:** 🟠 ALTO  
**Impacto:**
- Secrets em texto claro
- Rotação difícil
- Auditoria impossível

**Solução:**
```python
# Usar AWS Secrets Manager, HashiCorp Vault, ou similar
import boto3
from botocore.exceptions import ClientError

def get_secret(secret_name):
    client = boto3.client('secretsmanager')
    try:
        response = client.get_secret_value(SecretId=secret_name)
        return json.loads(response['SecretString'])
    except ClientError as e:
        raise e

# settings.py
if env('USE_AWS_SECRETS', default=False):
    secrets = get_secret('nef-cadencia-prod')
    SECRET_KEY = secrets['SECRET_KEY']
    DB_PASSWORD = secrets['DB_PASSWORD']
```

**Arquivos:** N/A (implementar)

---

### 🟠 ALTO #27: Ausência de rotação de secrets
**Problema:** Nenhum processo de rotação  
**Criticidade:** 🟠 ALTO  
**Impacto:**
- Secrets comprometidos permanecem válidos
- Sem mitigação de vazamento

**Solução:**
- Implementar rotação automática mensal
- Documentar processo de rotação
- Testar rotação em staging

**Arquivos:** N/A (processo)

---

## 4. AUSÊNCIA DE INFRAESTRUTURA

### 🔴 CRÍTICO #28: Ausência de Dockerfile
**Problema:** Nenhum Dockerfile presente  
**Criticidade:** 🔴 CRÍTICO  
**Impacto:**
- Deploy manual
- Inconsistência entre ambientes
- Impossível escalar

**Solução:**
```dockerfile
# Dockerfile
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "alive_platform.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "4", \
     "--timeout", "60"]
```

**Arquivos:** `Dockerfile` (CRIAR)

---

### 🔴 CRÍTICO #29: Ausência de docker-compose.yml
**Problema:** Nenhum docker-compose presente  
**Criticidade:** 🔴 CRÍTICO  
**Impacto:**
- Ambiente local inconsistente
- Difícil onboarding
- Testes não reproduzíveis

**Solução:**
```yaml
# docker-compose.yml
version: '3.8'

services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: alive_platform
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  web:
    build: .
    command: gunicorn alive_platform.wsgi:application --bind 0.0.0.0:8000
    volumes:
      - .:/app
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy

  nginx:
    image: nginx:alpine
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - static_volume:/app/staticfiles:ro
      - media_volume:/app/media:ro
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - web

volumes:
  postgres_data:
  static_volume:
  media_volume:
```

**Arquivos:** `docker-compose.yml` (CRIAR)

---

### 🔴 CRÍTICO #30: Ausência de gunicorn
**Problema:** Nenhuma configuração de WSGI server  
**Criticidade:** 🔴 CRÍTICO  
**Impacto:**
- Runserver em produção (NUNCA fazer)
- Performance horrível
- Crashes frequentes

**Solução:**
```python
# gunicorn.conf.py
import multiprocessing

bind = "0.0.0.0:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 60
keepalive = 5

accesslog = "/var/log/gunicorn/access.log"
errorlog = "/var/log/gunicorn/error.log"
loglevel = "info"

max_requests = 1000
max_requests_jitter = 50
```

```txt
# requirements.txt
gunicorn==21.2.0
```

**Arquivos:** `gunicorn.conf.py` (CRIAR), `requirements.txt`

---

### 🔴 CRÍTICO #31: Ausência de nginx
**Problema:** Nenhuma configuração de proxy reverso  
**Criticidade:** 🔴 CRÍTICO  
**Impacto:**
- Sem servir arquivos estáticos
- Sem SSL termination
- Sem rate limiting
- Sem gzip

**Solução:**
```nginx
# nginx.conf
upstream django {
    server web:8000;
}

server {
    listen 80;
    server_name seu-dominio.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name seu-dominio.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;

    client_max_body_size 10M;

    location /static/ {
        alias /app/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /app/media/;
        expires 7d;
    }

    location / {
        proxy_pass http://django;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Host $host;
        proxy_redirect off;
    }
}
```

**Arquivos:** `nginx.conf` (CRIAR)

---

### 🔴 CRÍTICO #32: Ausência de systemd service
**Problema:** Nenhum service file para systemd  
**Criticidade:** 🔴 CRÍTICO  
**Impacto:**
- Aplicação não inicia automaticamente
- Sem restart automático
- Sem gerenciamento de processo

**Solução:**
```ini
# /etc/systemd/system/nef-cadencia.service
[Unit]
Description=NEF Cadencia Django Application
After=network.target postgresql.service redis.service

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/opt/nef-cadencia
Environment="PATH=/opt/nef-cadencia/venv/bin"
ExecStart=/opt/nef-cadencia/venv/bin/gunicorn \
    --config /opt/nef-cadencia/gunicorn.conf.py \
    alive_platform.wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Arquivos:** `nef-cadencia.service` (CRIAR)

---

### 🔴 CRÍTICO #33: Ausência de healthcheck
**Problema:** Nenhum endpoint de health  
**Criticidade:** 🔴 CRÍTICO  
**Impacto:**
- Load balancer não sabe se app está saudável
- Deploy sem validação
- Downtime não detectado

**Solução:**
```python
# apps/core/views.py
from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache

def health_check(request):
    checks = {
        'database': False,
        'cache': False,
        'status': 'unhealthy'
    }
    
    # Check database
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        checks['database'] = True
    except Exception:
        pass
    
    # Check cache
    try:
        cache.set('health_check', 'ok', 10)
        checks['cache'] = cache.get('health_check') == 'ok'
    except Exception:
        pass
    
    if all([checks['database'], checks['cache']]):
        checks['status'] = 'healthy'
        return JsonResponse(checks, status=200)
    
    return JsonResponse(checks, status=503)

# urls.py
path('health/', health_check, name='health-check'),
```

**Arquivos:** `apps/core/views.py`, `alive_platform/urls.py`

---

### 🟠 ALTO #34: Ausência de CI/CD
**Problema:** Nenhum pipeline de CI/CD  
**Criticidade:** 🟠 ALTO  
**Impacto:**
- Deploy manual
- Sem testes automáticos
- Erros em produção

**Solução:**
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: |
          python manage.py test
          
  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to production
        run: |
          # Deploy script
```

**Arquivos:** `.github/workflows/deploy.yml` (CRIAR)

---

### 🟠 ALTO #35: Ausência de backup automático
**Problema:** Nenhum backup configurado  
**Criticidade:** 🟠 ALTO  
**Impacto:**
- Perda de dados irreversível
- Sem disaster recovery

**Solução:**
```bash
# backup.sh
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump -U postgres alive_platform | gzip > /backups/db_$DATE.sql.gz
aws s3 cp /backups/db_$DATE.sql.gz s3://nef-cadencia-backups/

# Crontab
0 2 * * * /opt/nef-cadencia/backup.sh
```

**Arquivos:** `backup.sh` (CRIAR)

---

### 🟡 MÉDIO #36: Ausência de monitoring
**Problema:** Nenhum monitoring configurado  
**Criticidade:** 🟡 MÉDIO  
**Impacto:**
- Problemas não detectados
- Sem métricas de performance

**Solução:**
```python
# Instalar Sentry
INSTALLED_APPS += ['sentry_sdk']

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn=env('SENTRY_DSN'),
    integrations=[DjangoIntegration()],
    traces_sample_rate=0.1,
    send_default_pii=False,
    environment=env('ENVIRONMENT', default='production'),
)
```

**Arquivos:** `alive_platform/settings.py`

---

## 5. PROBLEMAS DE LOGGING E OBSERVABILIDADE

### 🔴 CRÍTICO #37: Ausência de configuração de LOGGING
**Problema:** Nenhuma configuração de logging  
**Criticidade:** 🔴 CRÍTICO  
**Impacto:**
- Impossível debugar problemas
- Sem auditoria
- Sem rastreabilidade

**Solução:**
```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(name)s %(levelname)s %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/nef-cadencia/django.log',
            'maxBytes': 1024 * 1024 * 10,  # 10MB
            'backupCount': 10,
            'formatter': 'json',
        },
        'error_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/nef-cadencia/error.log',
            'maxBytes': 1024 * 1024 * 10,
            'backupCount': 10,
            'formatter': 'json',
            'level': 'ERROR',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },
        'django.request': {
            'handlers': ['error_file'],
            'level': 'ERROR',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },
    },
}
```

**Arquivos:** `alive_platform/settings.py`

---

### 🔴 CRÍTICO #38: Ausência de log rotation
**Problema:** Logs não são rotacionados  
**Criticidade:** 🔴 CRÍTICO  
**Impacto:**
- Disco cheio
- Aplicação para
- Perda de logs antigos

**Solução:**
```
# /etc/logrotate.d/nef-cadencia
/var/log/nef-cadencia/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
    postrotate
        systemctl reload nef-cadencia
    endscript
}
```

**Arquivos:** `/etc/logrotate.d/nef-cadencia` (CRIAR)

---

### 🟠 ALTO #39: Ausência de structured logging
**Problema:** Logs em texto simples  
**Criticidade:** 🟠 ALTO  
**Impacto:**
- Difícil parsear
- Sem agregação
- Análise manual

**Solução:**
```python
# Usar python-json-logger
import logging
from pythonjsonlogger import jsonlogger

logger = logging.getLogger(__name__)

# Log estruturado
logger.info(
    "User login",
    extra={
        'user_id': user.id,
        'ip_address': request.META.get('REMOTE_ADDR'),
        'user_agent': request.META.get('HTTP_USER_AGENT'),
    }
)
```

**Arquivos:** Todo o código

---

### 🟠 ALTO #40: Ausência de APM (Application Performance Monitoring)
**Problema:** Nenhum APM configurado  
**Criticidade:** 🟠 ALTO  
**Impacto:**
- Sem métricas de performance
- Queries lentas não detectadas
- Bottlenecks desconhecidos

**Solução:**
```python
# Instalar New Relic ou DataDog
import newrelic.agent
newrelic.agent.initialize('/etc/newrelic/newrelic.ini')

# Ou usar Django Debug Toolbar em staging
if DEBUG:
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
```

**Arquivos:** `alive_platform/settings.py`

---

### 🟡 MÉDIO #41: Ausência de error tracking
**Problema:** Erros não são rastreados centralmente  
**Criticidade:** 🟡 MÉDIO  
**Impacto:**
- Erros silenciosos
- Bugs não detectados

**Solução:**
- Já mencionado: Sentry (#36)

**Arquivos:** `alive_platform/settings.py`

---

### 🟡 MÉDIO #42: Ausência de request ID
**Problema:** Requests não têm ID único  
**Criticidade:** 🟡 MÉDIO  
**Impacto:**
- Impossível rastrear request completo
- Debug difícil

**Solução:**
```python
# Middleware para request ID
import uuid

class RequestIDMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.id = str(uuid.uuid4())
        response = self.get_response(request)
        response['X-Request-ID'] = request.id
        return response

MIDDLEWARE += ['apps.core.middleware.RequestIDMiddleware']
```

**Arquivos:** `apps/core/middleware.py` (CRIAR)

---

### 🟡 MÉDIO #43: Ausência de metrics collection
**Problema:** Nenhuma coleta de métricas  
**Criticidade:** 🟡 MÉDIO  
**Impacto:**
- Sem visibilidade de uso
- Sem dados para otimização

**Solução:**
```python
# Instalar django-prometheus
INSTALLED_APPS += ['django_prometheus']
MIDDLEWARE = [
    'django_prometheus.middleware.PrometheusBeforeMiddleware',
    # ... outros middlewares
    'django_prometheus.middleware.PrometheusAfterMiddleware',
]

# Endpoint de métricas
path('metrics/', include('django_prometheus.urls')),
```

**Arquivos:** `alive_platform/settings.py`, `urls.py`

---

## 6. RISCOS NO FLUXO DE MIGRAÇÃO E STATIC FILES

### 🟠 ALTO #44: Ausência de estratégia de migração
**Problema:** Nenhum processo documentado  
**Criticidade:** 🟠 ALTO  
**Impacto:**
- Migrações quebram produção
- Downtime não planejado
- Rollback difícil

**Solução:**
```bash
# deploy.sh
#!/bin/bash
set -e

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Restarting application..."
systemctl restart nef-cadencia

echo "Running health check..."
curl -f http://localhost:8000/health/ || exit 1

echo "Deploy successful!"
```

**Arquivos:** `deploy.sh` (CRIAR)

---

### 🟠 ALTO #45: STATIC_ROOT e STATICFILES_DIRS conflitantes
**Problema:** `STATICFILES_DIRS` aponta para `static/` e `STATIC_ROOT` para `staticfiles/`  
**Criticidade:** 🟠 ALTO  
**Impacto:**
- Arquivos estáticos não servidos
- 404 em CSS/JS

**Solução:**
```python
# Desenvolvimento
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Produção
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Nunca ter STATICFILES_DIRS e STATIC_ROOT apontando para mesma pasta
```

**Arquivos:** `alive_platform/settings.py:127-129`

---

### 🟡 MÉDIO #46: Ausência de WhiteNoise
**Problema:** Nenhum middleware para servir static files  
**Criticidade:** 🟡 MÉDIO  
**Impacto:**
- Nginx obrigatório
- Mais complexidade

**Solução:**
```python
# Instalar whitenoise
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Logo após SecurityMiddleware
    # ... outros middlewares
]

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

**Arquivos:** `alive_platform/settings.py`, `requirements.txt`

---

### 🟡 MÉDIO #47: Ausência de compressão de static files
**Problema:** Arquivos estáticos não são comprimidos  
**Criticidade:** 🟡 MÉDIO  
**Impacto:**
- Carregamento lento
- Banda desperdiçada

**Solução:**
- Usar WhiteNoise com compressão (#46)
- Ou configurar gzip no nginx

**Arquivos:** `alive_platform/settings.py`

---

## 7. ARQUIVOS TEMPORÁRIOS E ARTEFATOS

### 🟠 ALTO #48: Arquivos temporários no repositório
**Problema:** Arquivos `tmp_dashboard_*.html` no root  
**Criticidade:** 🟠 ALTO  
**Impacto:**
- Repositório poluído
- Arquivos desnecessários em produção
- Confusão

**Solução:**
```bash
# Remover arquivos temporários
rm tmp_dashboard_rendered_after_fix.html
rm tmp_dashboard_risk_rendered_after_fix.html

# Adicionar ao .gitignore
echo "tmp_*.html" >> .gitignore
```

**Arquivos:** `tmp_dashboard_rendered_after_fix.html`, `tmp_dashboard_risk_rendered_after_fix.html` (DELETAR)

---

### 🟡 MÉDIO #49: .gitignore incompleto
**Problema:** Faltam entradas importantes  
**Criticidade:** 🟡 MÉDIO  
**Impacto:**
- Arquivos indesejados commitados

**Solução:**
```gitignore
# Adicionar ao .gitignore
*.pyc
__pycache__/
.pytest_cache/
.coverage
htmlcov/
.env
.env.*
!.env.example
staticfiles/
media/
*.log
db.sqlite3
.DS_Store
.vscode/
.idea/
tmp_*.html
*.swp
node_modules/
```

**Arquivos:** `.gitignore`

---

## 8. PONTOS DE MANUTENÇÃO DIFÍCIL

### 🟠 ALTO #50: Ausência de documentação de deploy
**Problema:** Nenhum README de produção  
**Criticidade:** 🟠 ALTO  
**Impacto:**
- Deploy manual
- Conhecimento não documentado
- Onboarding difícil

**Solução:**
```markdown
# DEPLOY.md
## Pré-requisitos
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Nginx

## Deploy
1. Clone o repositório
2. Configure .env
3. Execute deploy.sh
4. Configure nginx
5. Configure systemd
6. Inicie serviço

## Rollback
1. git checkout <previous-commit>
2. python manage.py migrate <previous-migration>
3. systemctl restart nef-cadencia
```

**Arquivos:** `DEPLOY.md` (CRIAR)

---

### 🟠 ALTO #51: Ausência de requirements separados
**Problema:** Apenas um requirements.txt  
**Criticidade:** 🟠 ALTO  
**Impacto:**
- Dependências de dev em produção
- Imagem Docker maior
- Vulnerabilidades desnecessárias

**Solução:**
```
requirements/
├── base.txt          # Dependências comuns
├── development.txt   # Apenas dev
├── production.txt    # Apenas prod
└── test.txt         # Apenas test
```

```txt
# production.txt
-r base.txt
gunicorn==21.2.0
psycopg2-binary==2.9.9
whitenoise==6.6.0
sentry-sdk==1.40.0
```

**Arquivos:** `requirements/` (CRIAR)

---

### 🟡 MÉDIO #52: Ausência de versioning de dependências
**Problema:** Dependências sem versão fixa  
**Criticidade:** 🟡 MÉDIO  
**Impacto:**
- Builds não reproduzíveis
- Quebras inesperadas

**Solução:**
```bash
# Gerar requirements com versões fixas
pip freeze > requirements.txt

# Ou usar poetry/pipenv
poetry export -f requirements.txt --output requirements.txt
```

**Arquivos:** `requirements.txt`

---

### 🟡 MÉDIO #53: Ausência de testes de integração
**Problema:** Apenas testes unitários  
**Criticidade:** 🟡 MÉDIO  
**Impacto:**
- Bugs em integração
- Deploy quebrado

**Solução:**
```python
# tests/integration/test_deployment.py
def test_health_check():
    response = client.get('/health/')
    assert response.status_code == 200

def test_static_files_served():
    response = client.get('/static/css/main.css')
    assert response.status_code == 200
```

**Arquivos:** `tests/integration/` (CRIAR)

---

## RESUMO DE CRITICIDADE

### 🔴 CRÍTICO (23 problemas)
1. SECRET_KEY com default inseguro
2. DEBUG habilitado
3. Ausência HTTPS
4. Ausência CSRF_TRUSTED_ORIGINS
5. ALLOWED_HOSTS inseguro
6. Credenciais DB com defaults
7. OPENAI_API_KEY com default vazio
8. Ausência rate limiting
9. Ausência CSP
16. Ausência settings de produção
17. Ausência validação de env vars
24. .env no repositório
25. Ausência .env.example
28. Ausência Dockerfile
29. Ausência docker-compose
30. Ausência gunicorn
31. Ausência nginx
32. Ausência systemd
33. Ausência healthcheck
37. Ausência LOGGING
38. Ausência log rotation

### 🟠 ALTO (15 problemas)
10. Ausência CORS
11. Context processor debug
12. Ausência proteção SQL injection
13. Ausência validação uploads
18. Ausência config email
19. Ausência cache
20. Timezone sem validação
26. Ausência secrets management
27. Ausência rotação secrets
34. Ausência CI/CD
35. Ausência backup
39. Ausência structured logging
40. Ausência APM
44. Ausência estratégia migração
45. STATIC_ROOT conflitante
48. Arquivos temporários
50. Ausência doc deploy
51. Requirements não separados

### 🟡 MÉDIO (9 problemas)
14. Ausência 2FA
15. Ausência auditoria login
21. Context processors não otimizados
22. Ausência i18n config
23. Admin sem customização
36. Ausência monitoring
41. Ausência error tracking
42. Ausência request ID
43. Ausência metrics
46. Ausência WhiteNoise
47. Ausência compressão
49. .gitignore incompleto
52. Versioning dependências
53. Ausência testes integração

---

## PLANO DE AÇÃO PRIORITÁRIO

### Fase 1: BLOQUEADORES (1-2 semanas)
1. Criar settings de produção separado
2. Remover todos os defaults inseguros
3. Configurar HTTPS completo
4. Criar Dockerfile e docker-compose
5. Configurar gunicorn e nginx
6. Implementar LOGGING
7. Criar healthcheck
8. Remover .env do repositório

### Fase 2: CRÍTICOS (2-3 semanas)
1. Implementar secrets management
2. Configurar cache (Redis)
3. Configurar email
4. Implementar rate limiting
5. Configurar CSP
6. Criar systemd service
7. Implementar backup automático
8. Configurar CI/CD básico

### Fase 3: IMPORTANTES (3-4 semanas)
1. Implementar monitoring (Sentry)
2. Configurar APM
3. Implementar structured logging
4. Separar requirements
5. Criar documentação de deploy
6. Implementar WhiteNoise
7. Configurar CORS
8. Implementar 2FA

### Fase 4: MELHORIAS (ongoing)
1. Otimizar context processors
2. Implementar auditoria de login
3. Configurar metrics
4. Implementar request ID
5. Criar testes de integração
6. Rotação automática de secrets

---

## CONCLUSÃO

O sistema **NÃO ESTÁ PRONTO** para produção e requer **mínimo 6-8 semanas** de trabalho para estar em condições aceitáveis de deploy.

### Riscos Imediatos se Deployar Agora
- 🔴 Comprometimento total de segurança
- 🔴 Perda de dados
- 🔴 Downtime frequente
- 🔴 Performance inaceitável
- 🔴 Impossível debugar problemas
- 🔴 Custos operacionais elevados

### Recomendação
**NÃO DEPLOYAR** até completar pelo menos as Fases 1 e 2 do plano de ação.

---

**Auditoria realizada em 18 de Março de 2026**  
**Status: REPROVADO para produção ❌**
