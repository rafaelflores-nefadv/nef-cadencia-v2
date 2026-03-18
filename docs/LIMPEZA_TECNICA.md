# Limpeza Técnica para Produção - NEF Cadência

**Data:** 18 de Março de 2026  
**Objetivo:** Identificar e remover arquivos desnecessários para deploy em produção

---

## RESUMO EXECUTIVO

### Arquivos Identificados

| Categoria | Quantidade | Ação |
|-----------|-----------|------|
| Arquivos Temporários | 2 | ❌ REMOVER |
| Cache Python | 34+ arquivos | ❌ REMOVER |
| Diretórios __pycache__ | 27 | ❌ REMOVER |
| Arquivos de Teste | 19 | ✅ MANTER (mas não deployar) |
| Dependências Dev-Only | 3 | 📦 Separar |
| Debug Traces | 4 locais | ⚠️ REVISAR |

---

## 1. ARQUIVOS TEMPORÁRIOS

### ❌ REMOVER IMEDIATAMENTE

#### Arquivos HTML Temporários

```
tmp_dashboard_rendered_after_fix.html (70 KB)
tmp_dashboard_risk_rendered_after_fix.html (69 KB)
```

**Motivo:** Arquivos de debug/desenvolvimento que não devem ir para produção

**Ação:**
```bash
rm tmp_dashboard_rendered_after_fix.html
rm tmp_dashboard_risk_rendered_after_fix.html
```

**Impacto:** Nenhum - arquivos não utilizados pelo sistema

---

## 2. CACHE PYTHON

### ❌ REMOVER ANTES DO DEPLOY

#### Arquivos .pyc (34+ arquivos)

```
alive_platform/__pycache__/*.pyc
apps/**/__pycache__/*.pyc
```

**Motivo:** Bytecode compilado específico da versão Python local

**Ação:**
```bash
# Remover todos os .pyc
find . -type f -name "*.pyc" -delete

# Remover todos os __pycache__
find . -type d -name "__pycache__" -exec rm -rf {} +
```

**Impacto:** Nenhum - Python recompila automaticamente

#### Diretórios __pycache__ (27 diretórios)

```
alive_platform/__pycache__/
alive_platform/settings/__pycache__/
apps/__pycache__/
apps/accounts/__pycache__/
apps/accounts/migrations/__pycache__/
apps/accounts/templatetags/__pycache__/
apps/assistant/__pycache__/
apps/assistant/migrations/__pycache__/
apps/assistant/services/__pycache__/
apps/assistant/templatetags/__pycache__/
apps/core/__pycache__/
apps/core/services/__pycache__/
apps/integrations/__pycache__/
apps/integrations/migrations/__pycache__/
apps/integrations/services/__pycache__/
apps/messaging/__pycache__/
apps/messaging/migrations/__pycache__/
apps/messaging/services/__pycache__/
apps/monitoring/__pycache__/
apps/monitoring/management/__pycache__/
apps/monitoring/migrations/__pycache__/
apps/monitoring/services/__pycache__/
apps/reports/__pycache__/
apps/reports/migrations/__pycache__/
apps/rules/__pycache__/
apps/rules/migrations/__pycache__/
apps/rules/services/__pycache__/
```

**Status no .gitignore:** ✅ Já protegido

---

## 3. ARQUIVOS DE TESTE

### ✅ MANTER (mas não deployar)

#### Arquivos test_*.py (19 arquivos)

```
apps/assistant/tests/test_assistant_endpoints.py
apps/assistant/tests/test_assistant_page.py
apps/assistant/tests/test_assistant_tool_calling.py
apps/assistant/tests/test_capabilities.py
apps/assistant/tests/test_guardrails.py
apps/assistant/tests/test_observability.py
apps/assistant/tests/test_openai_settings.py
apps/assistant/tests/test_persistence.py
apps/assistant/tests/test_semantic_intent.py
apps/assistant/tests/test_semantic_resolution.py
apps/assistant/tests/test_tools_actions.py
apps/assistant/tests/test_tools_read.py
apps/assistant/tests/test_widget_session_endpoints.py
apps/core/tests/test_navigation.py
apps/core/tests/test_permissions.py
apps/core/tests/test_settings_selectors.py
apps/core/tests/test_settings_services.py
apps/core/tests/test_settings_views.py
apps/rules/tests/test_system_config_service.py
```

**Motivo:** Testes são essenciais para CI/CD e desenvolvimento

**Ação:** 
- ✅ MANTER no repositório
- ❌ NÃO incluir em artefato de deploy (Docker/tar.gz)
- ✅ Executar em CI/CD antes do deploy

**Configuração Docker:**
```dockerfile
# Dockerfile já exclui testes
COPY --chown=appuser:appuser alive_platform ./alive_platform
COPY --chown=appuser:appuser apps ./apps
# Não copia diretórios tests/
```

**Configuração deploy.sh:**
```bash
# deploy.sh já exclui testes no backup
tar -czf "$BACKUP_FILE" \
    --exclude='venv' \
    --exclude='*/tests/*' \
    --exclude='*.pyc' \
    ...
```

---

## 4. DEBUG TRACES E VAZAMENTOS

### ⚠️ REVISAR E PROTEGER

#### 4.1. ASSISTANT_DEBUG - USO CORRETO ✅

**Localização:** `apps/assistant/services/assistant_service.py`

```python
# Linha 190 - Logging condicional (CORRETO)
def _log_pipeline_trace(trace: dict):
    if not getattr(settings, "ASSISTANT_DEBUG", False):
        return
    logger.warning("assistant.pipeline_trace %s", ...)

# Linhas 1179, 1202, 1226 - Debug trace condicional (CORRETO)
"debug_trace": deepcopy(pipeline_trace) if getattr(settings, "ASSISTANT_DEBUG", False) else {},
```

**Status:** ✅ **SEGURO**
- Debug trace só é incluído se `ASSISTANT_DEBUG=True`
- Em produção, `ASSISTANT_DEBUG=False` (default)
- Não vaza informações sensíveis

**Recomendação:** Manter como está

#### 4.2. Print Statements - deployment/healthcheck.py

**Localização:** `deployment/healthcheck.py` (7 ocorrências)

```python
def print_header(text):
    print(f"\n{Colors.BLUE}{'='*60}{Colors.NC}")
    ...

def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.NC}")
    ...
```

**Status:** ✅ **SEGURO**
- Script de healthcheck usa print para output intencional
- Não é código da aplicação
- Executado manualmente, não em runtime

**Recomendação:** Manter como está

#### 4.3. Settings DEBUG - production.py

**Localização:** `alive_platform/settings/production.py`

```python
# Linha com referência a DEBUG (CORRETO)
DEBUG = False  # Forçado em produção
```

**Status:** ✅ **SEGURO**
- DEBUG sempre False em produção
- Configuração correta

**Recomendação:** Manter como está

#### 4.4. Teste com DEBUG - test_assistant_endpoints.py

**Localização:** `apps/assistant/tests/test_assistant_endpoints.py`

```python
@override_settings(ASSISTANT_DEBUG=True)
def test_chat_returns_debug_trace_when_assistant_debug_is_enabled(self):
    ...
```

**Status:** ✅ **SEGURO**
- Apenas em arquivo de teste
- Não afeta produção

**Recomendação:** Manter como está

---

## 5. DEPENDÊNCIAS

### 📦 SEPARAR DEV-ONLY

#### Análise do requirements.txt

**Dependências de Produção (MANTER):**
```
Django==4.2.16
django-environ==0.13.0
psycopg==3.3.3
psycopg-binary==3.3.3
openai==2.26.0
requests==2.32.5
pandas==3.0.1
numpy==2.4.3
openpyxl==3.1.5
python-dateutil==2.9.0.post0
python-dotenv==1.2.2
gunicorn (FALTANDO - ADICIONAR)
redis (FALTANDO - ADICIONAR)
```

**Dependências de Desenvolvimento (SEPARAR):**
```
selenium==4.41.0
webdriver-manager==4.0.2
pytest (FALTANDO - ADICIONAR)
pytest-django (FALTANDO - ADICIONAR)
```

**Dependências Questionáveis:**
```
pyodbc==5.3.0  # Apenas se usar banco legado SQL Server
```

**Recomendação:** Criar `requirements-dev.txt`

```txt
# requirements-dev.txt
-r requirements.txt

# Testing
pytest==8.0.0
pytest-django==4.8.0
pytest-cov==4.1.0
coverage==7.4.0

# Browser automation (se necessário)
selenium==4.41.0
webdriver-manager==4.0.2

# Code quality
black==24.2.0
flake8==7.0.0
isort==5.13.2
mypy==1.8.0

# Development tools
django-debug-toolbar==4.3.0
ipython==8.21.0
```

---

## 6. ARQUIVOS DE CONFIGURAÇÃO

### ✅ MANTER (mas revisar)

#### .env (551 bytes)

**Status:** ❌ **NÃO DEPLOYAR**
- Contém secrets locais
- Já protegido no .gitignore
- Cada ambiente deve ter seu próprio .env

**Ação:** Garantir que .env nunca vai para deploy

#### .env.example (12 KB)

**Status:** ✅ **DEPLOYAR**
- Template sem secrets
- Útil para referência no servidor

#### package.json / package-lock.json

**Status:** ✅ **MANTER**
- Necessário para build de assets (Tailwind CSS)
- Usado em desenvolvimento e build

#### node_modules/

**Status:** ❌ **NÃO DEPLOYAR**
- Apenas para build local
- Já protegido no .gitignore

---

## 7. DIRETÓRIOS E ARQUIVOS ESPECIAIS

### ✅ MANTER

```
.git/                    # Controle de versão (não deployar)
.venv/                   # Virtual env local (não deployar)
deployment/              # Scripts de deploy (DEPLOYAR)
docker/                  # Configs Docker (DEPLOYAR)
docs/                    # Documentação (DEPLOYAR - útil no servidor)
static/                  # Static source files (DEPLOYAR)
templates/               # Templates Django (DEPLOYAR)
apps/                    # Código da aplicação (DEPLOYAR)
alive_platform/          # Configurações Django (DEPLOYAR)
```

### ❌ NÃO DEPLOYAR

```
.git/                    # Histórico git (usar git archive)
.venv/                   # Virtual environment local
node_modules/            # Dependências Node.js
__pycache__/             # Cache Python
*.pyc                    # Bytecode Python
.env                     # Secrets locais
tmp_*.html               # Arquivos temporários
tests_js/                # Testes JavaScript (opcional)
```

---

## 8. VAZAMENTOS POTENCIAIS DE DEBUG

### ⚠️ PONTOS DE ATENÇÃO

#### 8.1. Settings DEBUG

**Arquivo:** `alive_platform/settings/production.py`

```python
# ✅ CORRETO - DEBUG forçado False
DEBUG = False

# ✅ CORRETO - Validação adicional
if DEBUG:
    raise ImproperlyConfigured("DEBUG must be False in production")
```

**Status:** ✅ Protegido

#### 8.2. ASSISTANT_DEBUG

**Arquivo:** `alive_platform/settings/base.py`

```python
# ✅ CORRETO - Default False
ASSISTANT_DEBUG = env.bool("ASSISTANT_DEBUG", default=False)
```

**Arquivo:** `alive_platform/settings/production.py`

```python
# ⚠️ ADICIONAR - Forçar False em produção
ASSISTANT_DEBUG = False  # Forçar em produção
```

**Recomendação:** Adicionar validação em production.py

#### 8.3. Logging Levels

**Arquivo:** `alive_platform/settings/production.py`

```python
# ✅ CORRETO - Log level INFO em produção
'level': 'INFO',
```

**Status:** ✅ Adequado para produção

---

## 9. SCRIPT DE LIMPEZA

### Criar script de limpeza automática

```bash
#!/bin/bash
# cleanup-for-production.sh

echo "Limpando projeto para produção..."

# Remover arquivos temporários
echo "Removendo arquivos temporários..."
find . -name "tmp_*" -type f -delete
find . -name "temp_*" -type f -delete
find . -name "*.tmp" -type f -delete

# Remover cache Python
echo "Removendo cache Python..."
find . -type f -name "*.pyc" -delete
find . -type f -name "*.pyo" -delete
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null

# Remover logs
echo "Removendo logs..."
find . -name "*.log" -type f -delete

# Remover banco SQLite (se existir)
echo "Removendo bancos SQLite..."
find . -name "*.sqlite3" -type f -delete
find . -name "*.db" -type f -delete

# Remover node_modules (se existir)
if [ -d "node_modules" ]; then
    echo "Removendo node_modules..."
    rm -rf node_modules
fi

# Remover .venv (se existir)
if [ -d ".venv" ]; then
    echo "Removendo .venv..."
    rm -rf .venv
fi

echo "Limpeza concluída!"
echo ""
echo "Arquivos removidos:"
echo "  - Temporários (tmp_*, temp_*, *.tmp)"
echo "  - Cache Python (*.pyc, __pycache__)"
echo "  - Logs (*.log)"
echo "  - Bancos SQLite (*.sqlite3, *.db)"
echo "  - node_modules/"
echo "  - .venv/"
```

---

## LISTA FINAL DE AÇÕES

### ❌ REMOVER IMEDIATAMENTE

1. **Arquivos Temporários:**
   ```bash
   rm tmp_dashboard_rendered_after_fix.html
   rm tmp_dashboard_risk_rendered_after_fix.html
   ```

2. **Cache Python:**
   ```bash
   find . -type f -name "*.pyc" -delete
   find . -type d -name "__pycache__" -exec rm -rf {} +
   ```

### ✅ MANTER (no repositório)

1. **Arquivos de Teste:**
   - `apps/*/tests/test_*.py` (19 arquivos)
   - Essenciais para CI/CD

2. **Documentação:**
   - `docs/*.md`
   - Útil para referência no servidor

3. **Scripts de Deploy:**
   - `deployment/*.sh`
   - Necessários para operação

4. **Configurações:**
   - `.env.example`
   - `requirements.txt`
   - `docker-compose.yml`
   - `Dockerfile`

### 📦 SEPARAR (dev vs prod)

1. **Criar requirements-dev.txt:**
   ```txt
   -r requirements.txt
   pytest==8.0.0
   pytest-django==4.8.0
   selenium==4.41.0
   webdriver-manager==4.0.2
   black==24.2.0
   flake8==7.0.0
   ```

2. **Adicionar ao requirements.txt (produção):**
   ```txt
   gunicorn==21.2.0
   redis==5.0.1
   ```

### ⚠️ REVISAR E PROTEGER

1. **Forçar ASSISTANT_DEBUG=False em produção:**
   ```python
   # alive_platform/settings/production.py
   ASSISTANT_DEBUG = False  # Forçar em produção
   ```

2. **Atualizar .gitignore (já feito):**
   ```gitignore
   tmp_*
   temp_*
   *.tmp
   __pycache__/
   *.pyc
   ```

### ❌ NÃO DEPLOYAR (via Docker/tar.gz)

1. `.git/` - Usar git archive
2. `.venv/` - Criar no servidor
3. `node_modules/` - Não necessário em runtime
4. `__pycache__/` - Regenerado automaticamente
5. `*.pyc` - Regenerado automaticamente
6. `.env` - Cada ambiente tem o seu
7. `tmp_*.html` - Arquivos temporários
8. `apps/*/tests/` - Testes (opcional)

---

## CHECKLIST DE LIMPEZA

### Antes do Deploy

- [ ] Executar `cleanup-for-production.sh`
- [ ] Verificar que não há `tmp_*.html`
- [ ] Verificar que não há `__pycache__/`
- [ ] Verificar que `.env` não está no git
- [ ] Verificar que `DEBUG=False` em produção
- [ ] Verificar que `ASSISTANT_DEBUG=False` em produção

### Configuração Docker

- [ ] Dockerfile exclui testes
- [ ] Dockerfile exclui __pycache__
- [ ] Dockerfile exclui .git
- [ ] .dockerignore configurado

### Configuração Git Archive

- [ ] `.gitattributes` configurado para export-ignore
- [ ] Testes marcados como export-ignore (opcional)

---

## IMPACTO

### Redução de Tamanho

| Item | Tamanho Atual | Após Limpeza | Economia |
|------|---------------|--------------|----------|
| tmp_*.html | 140 KB | 0 KB | 140 KB |
| __pycache__/ | ~500 KB | 0 KB | 500 KB |
| *.pyc | ~200 KB | 0 KB | 200 KB |
| **Total** | **~840 KB** | **0 KB** | **~840 KB** |

### Benefícios

1. ✅ **Deploy mais rápido** - Menos arquivos para transferir
2. ✅ **Artefato mais limpo** - Apenas código necessário
3. ✅ **Segurança** - Sem vazamento de debug info
4. ✅ **Manutenibilidade** - Código organizado

---

## PRÓXIMOS PASSOS

1. **Imediato:**
   - Remover `tmp_*.html`
   - Limpar cache Python

2. **Curto Prazo:**
   - Criar `requirements-dev.txt`
   - Adicionar `gunicorn` e `redis` ao `requirements.txt`
   - Criar script `cleanup-for-production.sh`

3. **Médio Prazo:**
   - Forçar `ASSISTANT_DEBUG=False` em production.py
   - Configurar `.gitattributes` para export-ignore
   - Documentar processo de limpeza

---

**Última Atualização:** 18 de Março de 2026  
**Versão:** 1.0  
**Responsável:** DevOps Team
