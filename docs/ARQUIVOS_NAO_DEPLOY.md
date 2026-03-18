# Arquivos que NÃO Devem Ir para Deploy - NEF Cadência

**Versão:** 1.0  
**Data:** 18 de Março de 2026  
**Objetivo:** Identificar arquivos e diretórios que devem ser excluídos do deploy em produção

---

## CATEGORIAS DE EXCLUSÃO

### 🔴 CRÍTICO - Segredos e Credenciais

**Risco:** Exposição de credenciais e comprometimento total do sistema

| Arquivo/Diretório | Motivo | Ação |
|-------------------|--------|------|
| `.env` | Contém segredos de produção | ❌ NUNCA deployar |
| `.env.*` | Variações de .env | ❌ NUNCA deployar |
| `*.env` | Qualquer arquivo .env | ❌ NUNCA deployar |
| `.env.backup` | Backup de .env | ❌ NUNCA deployar |
| `.env.old` | .env antigo | ❌ NUNCA deployar |
| `.env.local` | .env local | ❌ NUNCA deployar |
| `.env.production` | .env de produção | ❌ NUNCA deployar |
| `secrets/` | Diretório de segredos | ❌ NUNCA deployar |
| `*.key` | Chaves privadas | ❌ NUNCA deployar |
| `*.pem` | Certificados privados | ❌ NUNCA deployar |
| `*.p12` | Certificados PKCS12 | ❌ NUNCA deployar |
| `*.pfx` | Certificados PFX | ❌ NUNCA deployar |
| `credentials.json` | Credenciais de serviços | ❌ NUNCA deployar |
| `service-account.json` | Conta de serviço | ❌ NUNCA deployar |
| `config.ini` | Configurações com segredos | ❌ NUNCA deployar |

**Status no .gitignore:** ✅ Protegido

---

### 🟠 ALTO - Arquivos Temporários

**Risco:** Poluição do ambiente de produção, possível exposição de dados

| Arquivo/Diretório | Motivo | Ação |
|-------------------|--------|------|
| `tmp/` | Arquivos temporários | ❌ Não deployar |
| `temp/` | Arquivos temporários | ❌ Não deployar |
| `tmp_*` | Arquivos temporários com prefixo | ❌ Não deployar |
| `temp_*` | Arquivos temporários com prefixo | ❌ Não deployar |
| `*.tmp` | Extensão temporária | ❌ Não deployar |
| `*.temp` | Extensão temporária | ❌ Não deployar |
| `tmp_dashboard_*.html` | **Arquivos presentes no projeto** | ❌ **DELETAR antes do deploy** |
| `temp_dashboard_*.html` | Arquivos temporários de dashboard | ❌ Não deployar |

**Arquivos Identificados no Projeto:**
```
✗ tmp_dashboard_rendered_after_fix.html (70KB)
✗ tmp_dashboard_risk_rendered_after_fix.html (69KB)
```

**Ação Recomendada:**
```bash
# Deletar arquivos temporários
rm tmp_dashboard_rendered_after_fix.html
rm tmp_dashboard_risk_rendered_after_fix.html

# Verificar que não há outros
find . -name "tmp_*" -o -name "temp_*"
```

**Status no .gitignore:** ✅ Protegido

---

### 🟠 ALTO - Banco de Dados Local

**Risco:** Exposição de dados de desenvolvimento, conflito com banco de produção

| Arquivo/Diretório | Motivo | Ação |
|-------------------|--------|------|
| `db.sqlite3` | Banco SQLite de desenvolvimento | ❌ Não deployar |
| `db.sqlite3-journal` | Journal do SQLite | ❌ Não deployar |
| `*.sqlite` | Qualquer banco SQLite | ❌ Não deployar |
| `*.sqlite3` | Qualquer banco SQLite3 | ❌ Não deployar |
| `*.db` | Arquivos de banco | ❌ Não deployar |
| `*.sql` | Dumps SQL | ❌ Não deployar |
| `*.dump` | Dumps de banco | ❌ Não deployar |
| `backups/` | Backups de banco | ❌ Não deployar |

**Status no .gitignore:** ✅ Protegido

---

### 🟡 MÉDIO - Logs e Monitoramento

**Risco:** Arquivos grandes, possível exposição de informações sensíveis

| Arquivo/Diretório | Motivo | Ação |
|-------------------|--------|------|
| `*.log` | Arquivos de log | ❌ Não deployar |
| `*.log.*` | Logs rotativos | ❌ Não deployar |
| `logs/` | Diretório de logs | ❌ Não deployar |
| `log/` | Diretório de logs | ❌ Não deployar |

**Nota:** Logs devem ser gerados no servidor de produção, não copiados.

**Status no .gitignore:** ✅ Protegido

---

### 🟡 MÉDIO - Ambientes Virtuais

**Risco:** Arquivos desnecessários, tamanho excessivo

| Arquivo/Diretório | Motivo | Ação |
|-------------------|--------|------|
| `.venv/` | Ambiente virtual Python | ❌ Não deployar |
| `venv/` | Ambiente virtual Python | ❌ Não deployar |
| `env/` | Ambiente virtual Python | ❌ Não deployar |
| `ENV/` | Ambiente virtual Python | ❌ Não deployar |
| `virtualenv/` | Ambiente virtual Python | ❌ Não deployar |
| `node_modules/` | Dependências Node.js | ❌ Não deployar |

**Nota:** Dependências devem ser instaladas no servidor via `requirements.txt` ou `package.json`.

**Status no .gitignore:** ✅ Protegido

---

### 🟡 MÉDIO - Cache e Build

**Risco:** Arquivos desnecessários, possível incompatibilidade

| Arquivo/Diretório | Motivo | Ação |
|-------------------|--------|------|
| `__pycache__/` | Cache Python | ❌ Não deployar |
| `*.pyc` | Bytecode Python | ❌ Não deployar |
| `*.pyo` | Bytecode otimizado | ❌ Não deployar |
| `*.pyd` | Extensões Python | ❌ Não deployar |
| `.pytest_cache/` | Cache pytest | ❌ Não deployar |
| `.mypy_cache/` | Cache mypy | ❌ Não deployar |
| `.ruff_cache/` | Cache ruff | ❌ Não deployar |
| `dist/` | Build artifacts | ❌ Não deployar |
| `build/` | Build artifacts | ❌ Não deployar |
| `*.egg-info/` | Python egg info | ❌ Não deployar |

**Status no .gitignore:** ✅ Protegido

---

### 🟡 MÉDIO - Testes e Cobertura

**Risco:** Arquivos desnecessários em produção

| Arquivo/Diretório | Motivo | Ação |
|-------------------|--------|------|
| `.coverage` | Dados de cobertura | ❌ Não deployar |
| `.coverage.*` | Dados de cobertura | ❌ Não deployar |
| `htmlcov/` | Relatório HTML de cobertura | ❌ Não deployar |
| `coverage/` | Relatórios de cobertura | ❌ Não deployar |
| `coverage.xml` | Relatório XML de cobertura | ❌ Não deployar |
| `.tox/` | Ambientes tox | ❌ Não deployar |
| `.nox/` | Ambientes nox | ❌ Não deployar |

**Nota:** Testes devem rodar em CI/CD, não em produção.

**Status no .gitignore:** ✅ Protegido

---

### 🟡 MÉDIO - IDEs e Editores

**Risco:** Configurações pessoais, arquivos desnecessários

| Arquivo/Diretório | Motivo | Ação |
|-------------------|--------|------|
| `.vscode/` | Configurações VS Code | ❌ Não deployar |
| `.idea/` | Configurações PyCharm/IntelliJ | ❌ Não deployar |
| `*.swp` | Arquivos swap do Vim | ❌ Não deployar |
| `*.swo` | Arquivos swap do Vim | ❌ Não deployar |
| `*~` | Arquivos backup de editores | ❌ Não deployar |
| `.sublime-project` | Projeto Sublime Text | ❌ Não deployar |
| `.sublime-workspace` | Workspace Sublime Text | ❌ Não deployar |

**Status no .gitignore:** ✅ Protegido

---

### 🟡 MÉDIO - Sistema Operacional

**Risco:** Arquivos específicos do SO, desnecessários

| Arquivo/Diretório | Motivo | Ação |
|-------------------|--------|------|
| `.DS_Store` | Metadata macOS | ❌ Não deployar |
| `Thumbs.db` | Cache de thumbnails Windows | ❌ Não deployar |
| `desktop.ini` | Configuração de pasta Windows | ❌ Não deployar |
| `.Spotlight-V100` | Índice Spotlight macOS | ❌ Não deployar |
| `.Trashes` | Lixeira macOS | ❌ Não deployar |

**Status no .gitignore:** ✅ Protegido

---

### 🟢 BAIXO - Documentação de Build

**Risco:** Arquivos desnecessários (mas não prejudiciais)

| Arquivo/Diretório | Motivo | Ação |
|-------------------|--------|------|
| `docs/_build/` | Build da documentação | ⚠️ Opcional |
| `site/` | Site gerado (MkDocs) | ⚠️ Opcional |
| `README.md` | Documentação | ✅ Pode deployar |
| `docs/*.md` | Documentação | ✅ Pode deployar |

**Nota:** Documentação pode ser útil no servidor, mas não é necessária.

**Status no .gitignore:** ✅ Protegido (builds)

---

### 🟢 BAIXO - Git

**Risco:** Histórico desnecessário em produção

| Arquivo/Diretório | Motivo | Ação |
|-------------------|--------|------|
| `.git/` | Repositório Git | ⚠️ Depende da estratégia |
| `.gitignore` | Configuração Git | ⚠️ Não necessário |
| `.gitattributes` | Atributos Git | ⚠️ Não necessário |

**Nota:** 
- Se usar `git clone` no servidor: `.git/` estará presente
- Se usar export/archive: `.git/` não estará presente
- Recomendado: Não incluir `.git/` em produção (usar archive)

---

## ARQUIVOS QUE DEVEM IR PARA DEPLOY

### ✅ Código-fonte

```
alive_platform/
apps/
templates/
static/
manage.py
requirements.txt
```

### ✅ Configurações (sem segredos)

```
.env.example
.gitignore (opcional)
```

### ✅ Documentação (opcional)

```
README.md
docs/*.md
```

### ✅ Assets

```
static/
templates/
```

---

## CHECKLIST DE PRÉ-DEPLOY

### Antes de Fazer Deploy

- [ ] Deletar arquivos temporários
  ```bash
  rm tmp_dashboard_rendered_after_fix.html
  rm tmp_dashboard_risk_rendered_after_fix.html
  find . -name "tmp_*" -delete
  find . -name "temp_*" -delete
  ```

- [ ] Verificar que .env não está no repositório
  ```bash
  git ls-files | grep "\.env$"
  # Não deve retornar nada
  ```

- [ ] Verificar .gitignore está atualizado
  ```bash
  cat .gitignore
  ```

- [ ] Limpar cache Python
  ```bash
  find . -type d -name "__pycache__" -exec rm -rf {} +
  find . -type f -name "*.pyc" -delete
  ```

- [ ] Verificar que não há logs commitados
  ```bash
  git ls-files | grep "\.log$"
  # Não deve retornar nada
  ```

- [ ] Verificar que não há bancos SQLite commitados
  ```bash
  git ls-files | grep "\.sqlite"
  # Não deve retornar nada
  ```

---

## ESTRATÉGIAS DE DEPLOY

### Opção 1: Git Clone (Não Recomendado)

```bash
# No servidor
git clone https://github.com/seu-usuario/nef-cadencia.git
cd nef-cadencia
```

**Problemas:**
- Inclui `.git/` (desnecessário)
- Histórico completo (pesado)
- Possível exposição de histórico

### Opção 2: Git Archive (Recomendado)

```bash
# Local
git archive --format=tar.gz --output=nef-cadencia-v1.0.tar.gz HEAD

# Transferir para servidor
scp nef-cadencia-v1.0.tar.gz user@server:/opt/

# No servidor
cd /opt/
tar -xzf nef-cadencia-v1.0.tar.gz
```

**Vantagens:**
- Sem `.git/`
- Apenas arquivos rastreados
- Leve e limpo

### Opção 3: Docker (Mais Recomendado)

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copiar apenas o necessário
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY alive_platform/ ./alive_platform/
COPY apps/ ./apps/
COPY templates/ ./templates/
COPY static/ ./static/
COPY manage.py .

# Coletar static files
RUN python manage.py collectstatic --noinput

CMD ["gunicorn", "alive_platform.wsgi:application"]
```

**Vantagens:**
- Controle total sobre o que é incluído
- Reproduzível
- Isolado

### Opção 4: CI/CD (Ideal)

```yaml
# .github/workflows/deploy.yml
- name: Create deployment package
  run: |
    mkdir deploy
    cp -r alive_platform apps templates static manage.py requirements.txt deploy/
    tar -czf deploy.tar.gz -C deploy .
    
- name: Deploy to server
  run: |
    scp deploy.tar.gz user@server:/opt/
    ssh user@server 'cd /opt && tar -xzf deploy.tar.gz'
```

---

## VERIFICAÇÃO PÓS-DEPLOY

### No Servidor de Produção

```bash
# Verificar que não há arquivos temporários
find /opt/nef-cadencia -name "tmp_*"
find /opt/nef-cadencia -name "temp_*"

# Verificar que não há .env
find /opt/nef-cadencia -name ".env"

# Verificar que não há __pycache__
find /opt/nef-cadencia -name "__pycache__"

# Verificar que não há .git
ls -la /opt/nef-cadencia/.git

# Verificar tamanho do deploy
du -sh /opt/nef-cadencia
```

**Tamanho Esperado:** < 50MB (sem dependências)

---

## LIMPEZA AUTOMÁTICA

### Script de Limpeza Pré-Deploy

```bash
#!/bin/bash
# cleanup-pre-deploy.sh

echo "Limpando arquivos temporários..."
find . -name "tmp_*" -delete
find . -name "temp_*" -delete
find . -name "*.tmp" -delete
find . -name "*.temp" -delete

echo "Limpando cache Python..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete
find . -type f -name "*.pyo" -delete

echo "Limpando logs..."
find . -name "*.log" -delete

echo "Limpando bancos SQLite..."
find . -name "*.sqlite3" -delete
find . -name "*.db" -delete

echo "Verificando .env..."
if [ -f .env ]; then
    echo "⚠️  AVISO: .env encontrado! Não deve ser deployado."
fi

echo "Limpeza concluída!"
```

**Uso:**
```bash
chmod +x cleanup-pre-deploy.sh
./cleanup-pre-deploy.sh
```

---

## RESUMO

### 🔴 NUNCA Deployar (Crítico)

- `.env` e variações
- Chaves privadas (`.key`, `.pem`)
- Credenciais (`credentials.json`)
- Segredos em geral

### 🟠 NÃO Deployar (Recomendado)

- Arquivos temporários (`tmp_*`, `temp_*`)
- Bancos de dados locais (`.sqlite3`)
- Logs (`.log`)
- Ambientes virtuais (`venv/`, `node_modules/`)
- Cache (`__pycache__/`, `.pytest_cache/`)

### 🟡 OPCIONAL (Depende da Estratégia)

- `.git/` (recomendado não incluir)
- Documentação (`docs/`)
- `.gitignore`

### ✅ SEMPRE Deployar

- Código-fonte (`alive_platform/`, `apps/`)
- Templates (`templates/`)
- Static files (`static/`)
- `manage.py`
- `requirements.txt`
- `.env.example` (como referência)

---

**Última Atualização:** 18 de Março de 2026  
**Versão:** 1.0  
**Próxima Revisão:** Antes de cada deploy
