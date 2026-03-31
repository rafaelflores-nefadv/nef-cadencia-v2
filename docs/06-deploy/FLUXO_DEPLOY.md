# Fluxo Seguro de Deploy - NEF Cadência

**Versão:** 1.0  
**Data:** 18 de Março de 2026  
**Objetivo:** Deploy seguro, idempotente e previsível com rollback automático

---

## ÍNDICE

1. [Visão Geral](#visão-geral)
2. [Pré-requisitos](#pré-requisitos)
3. [Fluxo de Deploy](#fluxo-de-deploy)
4. [Validação Pré-Deploy](#validação-pré-deploy)
5. [Execução do Deploy](#execução-do-deploy)
6. [Rollback](#rollback)
7. [Troubleshooting](#troubleshooting)

---

## VISÃO GERAL

### Princípios

- **Seguro:** Backup automático antes de qualquer mudança
- **Idempotente:** Pode ser executado múltiplas vezes com o mesmo resultado
- **Previsível:** Cada etapa é validada antes de prosseguir
- **Reversível:** Rollback automático em caso de falha

### Arquitetura do Deploy

```
┌─────────────────────────────────────────────────────────────┐
│                    FLUXO DE DEPLOY                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Validação Pré-Deploy                                   │
│     ├── Código (sintaxe, git)                              │
│     ├── Ambiente (.env, variáveis)                         │
│     ├── Dependências (packages)                            │
│     ├── Serviços (PostgreSQL, Redis, Nginx)                │
│     └── Espaço em disco                                    │
│                                                             │
│  2. Backup                                                  │
│     ├── Aplicação (código)                                 │
│     ├── Banco de dados (PostgreSQL dump)                   │
│     └── Estado do deployment                               │
│                                                             │
│  3. Instalação de Dependências                             │
│     ├── Virtual environment                                │
│     ├── pip install -r requirements.txt                    │
│     └── Verificação de pacotes críticos                    │
│                                                             │
│  4. Testes                                                  │
│     ├── Django system checks                               │
│     ├── pytest (se disponível)                             │
│     └── Validação de configurações                         │
│                                                             │
│  5. Migrações de Banco                                      │
│     ├── Backup pré-migration                               │
│     ├── python manage.py migrate                           │
│     └── Verificação de migrations                          │
│                                                             │
│  6. Collect Static Files                                    │
│     ├── python manage.py collectstatic                     │
│     └── Verificação de arquivos                            │
│                                                             │
│  7. Permissões                                              │
│     ├── Ownership (nef-cadencia:www-data)                  │
│     ├── Diretórios (755)                                   │
│     └── Arquivos (644)                                     │
│                                                             │
│  8. Restart da Aplicação                                    │
│     ├── systemctl restart nef-cadencia                     │
│     ├── systemctl reload nginx                             │
│     └── Health check                                       │
│                                                             │
│  9. Validação Pós-Deploy                                    │
│     ├── HTTP endpoint                                      │
│     ├── Logs de erro                                       │
│     └── Health check completo                              │
│                                                             │
│ 10. Cleanup                                                 │
│     ├── Remover backups antigos                            │
│     └── Limpar cache Python                                │
│                                                             │
│                    ✓ SUCESSO                                │
│                                                             │
│  ┌──────────────────────────────────────┐                  │
│  │  Em caso de FALHA em qualquer etapa │                  │
│  │  ↓                                   │                  │
│  │  ROLLBACK AUTOMÁTICO                │                  │
│  │  ├── Restaurar código                │                  │
│  │  ├── Restaurar banco de dados        │                  │
│  │  ├── Restart serviços                │                  │
│  │  └── Validação                       │                  │
│  └──────────────────────────────────────┘                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## PRÉ-REQUISITOS

### Ambiente

- [ ] VPS configurado e acessível
- [ ] SSH configurado
- [ ] Usuário `nef-cadencia` criado
- [ ] Serviços instalados (PostgreSQL, Redis, Nginx)
- [ ] Aplicação já deployada uma vez

### Código

- [ ] Código commitado no git
- [ ] Testes passando localmente
- [ ] Migrations criadas
- [ ] `requirements.txt` atualizado

### Configuração

- [ ] `.env` configurado em produção
- [ ] Secrets configurados corretamente
- [ ] Backup recente disponível

---

## FLUXO DE DEPLOY

### Etapa 1: Validação Pré-Deploy

**Objetivo:** Detectar problemas antes de iniciar o deploy

**Script:** `deployment/pre-deploy-check.sh`

```bash
cd /opt/nef-cadencia
./deployment/pre-deploy-check.sh
```

**Validações Realizadas:**

1. **Ambiente**
   - `.env` existe
   - `SECRET_KEY` configurada e segura
   - `DEBUG=False`
   - `ALLOWED_HOSTS` configurado
   - Credenciais de banco completas

2. **Código**
   - Sem erros de sintaxe Python
   - Sem mudanças não commitadas (git)
   - Atualizado com remote

3. **Dependências**
   - `requirements.txt` existe
   - Virtual environment existe
   - Pacotes críticos instalados
   - Pacotes atualizados

4. **Banco de Dados**
   - PostgreSQL rodando
   - Conexão funcionando
   - Migrations pendentes identificadas

5. **Serviços**
   - Gunicorn rodando
   - Nginx rodando
   - Redis rodando

6. **Recursos**
   - Espaço em disco suficiente
   - Backups recentes existem

7. **SSL**
   - Certificados válidos
   - Não expirados

8. **Segurança**
   - `.env` com permissões corretas (600)
   - Firewall ativo

9. **Saúde da Aplicação**
   - Health endpoint respondendo
   - Sem erros recentes nos logs

**Resultado:**
- ✅ **Passed:** Pronto para deploy
- ⚠️ **Warnings:** Revisar antes de deploy
- ❌ **Failed:** Corrigir antes de deploy

---

### Etapa 2: Execução do Deploy

**Script:** `deployment/deploy-safe.sh`

```bash
cd /opt/nef-cadencia
./deployment/deploy-safe.sh
```

**Opções:**
```bash
# Deploy normal (com testes)
./deployment/deploy-safe.sh

# Pular testes
./deployment/deploy-safe.sh --skip-tests

# Forçar deploy mesmo com warnings
./deployment/deploy-safe.sh --force

# Combinado
./deployment/deploy-safe.sh --skip-tests --force
```

**Processo Detalhado:**

#### STEP 1: Pre-flight Checks
- Verifica usuário
- Verifica diretório da aplicação
- Verifica `.env`
- Cria diretórios necessários

#### STEP 2: Code Validation
- Valida sintaxe Python
- Pull do git (se repositório)
- Registra commit atual

#### STEP 3: Backup Current State
- Backup da aplicação (tar.gz)
- Backup do banco de dados (PostgreSQL dump)
- Salva estado do deployment
- Registra timestamp

#### STEP 4: Install Dependencies
- Ativa virtual environment
- Upgrade pip
- Instala requirements.txt
- Verifica pacotes críticos

#### STEP 5: Run Tests
- Django system checks
- pytest (se disponível)
- Validação de configurações

**Rollback automático se falhar**

#### STEP 6: Database Migrations
- Backup pré-migration
- Aplica migrations
- Verifica que todas foram aplicadas

**Rollback automático se falhar**

#### STEP 7: Collect Static Files
- Coleta static files
- Limpa arquivos antigos
- Verifica diretório

**Rollback automático se falhar**

#### STEP 8: Set Permissions
- Ownership correto
- Permissões de diretórios (755)
- Permissões de arquivos (644)
- `.env` seguro (600)

#### STEP 9: Pre-restart Validation
- Valida settings Django
- Testa conexão ao banco
- Verifica configurações

**Rollback automático se falhar**

#### STEP 10: Restart Application
- Reload systemd
- Restart Gunicorn
- Reload Nginx
- Aguarda inicialização

**Rollback automático se falhar**

#### STEP 11: Post-deployment Health Checks
- Testa HTTP endpoint (com retries)
- Verifica logs de erro
- Health check completo

**Rollback automático se falhar**

#### STEP 12: Cleanup
- Remove backups antigos (mantém últimos 10)
- Limpa cache Python

**Resultado:**
- ✅ **SUCCESS:** Deploy concluído
- ❌ **FAILED:** Rollback executado automaticamente

---

### Etapa 3: Validação Pós-Deploy

**Checklist Manual:**

```bash
# 1. Verificar serviço
sudo systemctl status nef-cadencia

# 2. Verificar logs
sudo journalctl -u nef-cadencia -n 50

# 3. Testar endpoint
curl http://localhost/health/
curl https://seu-dominio.com/

# 4. Testar admin
# Acessar https://seu-dominio.com/admin/

# 5. Verificar static files
curl -I https://seu-dominio.com/static/admin/css/base.css

# 6. Monitorar por 10 minutos
sudo journalctl -u nef-cadencia -f
```

---

## VALIDAÇÃO PRÉ-DEPLOY

### Checklist Rápido

```bash
# Executar validação completa
cd /opt/nef-cadencia
./deployment/pre-deploy-check.sh
```

### Validação Manual

```bash
# 1. Verificar .env
cat /opt/nef-cadencia/.env | grep -E "SECRET_KEY|DEBUG|ALLOWED_HOSTS"

# 2. Verificar git status
cd /opt/nef-cadencia
git status
git log -1

# 3. Verificar serviços
systemctl status postgresql nginx redis-server nef-cadencia

# 4. Verificar espaço em disco
df -h

# 5. Verificar backups recentes
ls -lth /var/backups/nef-cadencia/ | head -n 5

# 6. Testar conexão ao banco
psql -h localhost -U nef_cadencia -d nef_cadencia_prod -c "SELECT 1;"

# 7. Verificar migrations pendentes
cd /opt/nef-cadencia
source venv/bin/activate
python manage.py showmigrations | grep '\[ \]'
```

---

## ROLLBACK

### Rollback Automático

O script `deploy-safe.sh` executa rollback **automaticamente** se qualquer etapa falhar.

**Processo:**
1. Detecta falha
2. Salva estado de erro
3. Executa `rollback.sh`
4. Restaura código e banco
5. Reinicia serviços
6. Valida rollback

### Rollback Manual

```bash
# Rollback para último backup
cd /opt/nef-cadencia
sudo ./deployment/rollback.sh

# Rollback para backup específico
sudo ./deployment/rollback.sh 20260318_143000
```

**Processo do Rollback:**

1. **Confirmação**
   - Solicita confirmação do usuário
   - Mostra detalhes do backup

2. **Safety Backup**
   - Cria backup do estado atual
   - Permite re-rollback se necessário

3. **Stop Application**
   - Para Gunicorn

4. **Restore Database**
   - Descomprime backup
   - Restaura PostgreSQL dump
   - Verifica integridade

5. **Restore Application Files**
   - Extrai backup
   - Preserva `.env` e `media/`
   - Restaura código

6. **Restore Dependencies**
   - Reinstala requirements.txt do backup

7. **Collect Static Files**
   - Recoleta static files

8. **Set Permissions**
   - Restaura permissões corretas

9. **Start Application**
   - Inicia Gunicorn
   - Recarrega Nginx

10. **Verify Rollback**
    - Testa HTTP endpoint
    - Verifica logs

**Resultado:**
- ✅ **SUCCESS:** Rollback concluído
- ❌ **FAILED:** Intervenção manual necessária

---

## TROUBLESHOOTING

### Deploy Falhou na Etapa de Migrations

**Sintoma:** Rollback automático após migrations

**Diagnóstico:**
```bash
# Ver logs do deploy
tail -f /var/log/nef-cadencia/deploy.log

# Ver erro específico da migration
sudo journalctl -u nef-cadencia -n 100 | grep -i migration
```

**Soluções:**
1. Corrigir migration localmente
2. Testar migration em staging
3. Fazer deploy novamente

### Deploy Falhou na Etapa de Testes

**Sintoma:** Testes falharam, deploy abortado

**Diagnóstico:**
```bash
# Ver output dos testes
tail -f /var/log/nef-cadencia/deploy.log
```

**Soluções:**
1. Corrigir testes localmente
2. Usar `--skip-tests` se testes não são críticos
3. Usar `--force` para ignorar falhas de teste (não recomendado)

### Rollback Falhou

**Sintoma:** Rollback não completou

**Diagnóstico:**
```bash
# Ver logs do rollback
tail -f /var/log/nef-cadencia/rollback.log

# Verificar estado dos serviços
systemctl status nef-cadencia postgresql nginx
```

**Soluções:**

**Opção 1: Tentar rollback novamente**
```bash
sudo ./deployment/rollback.sh
```

**Opção 2: Rollback manual do banco**
```bash
# Listar backups disponíveis
ls -lth /var/backups/nef-cadencia/

# Restaurar banco manualmente
gunzip -c /var/backups/nef-cadencia/pre_deploy_db_TIMESTAMP.sql.gz | \
    sudo -u postgres psql -d nef_cadencia_prod
```

**Opção 3: Restaurar código manualmente**
```bash
cd /opt/nef-cadencia
tar -xzf /var/backups/nef-cadencia/pre_deploy_backup_TIMESTAMP.tar.gz
sudo systemctl restart nef-cadencia
```

### Aplicação Não Responde Após Deploy

**Sintoma:** Deploy bem-sucedido mas aplicação não responde

**Diagnóstico:**
```bash
# Verificar serviço
sudo systemctl status nef-cadencia

# Ver logs
sudo journalctl -u nef-cadencia -n 100

# Testar socket
ls -la /opt/nef-cadencia/run/gunicorn.sock

# Testar Nginx
sudo nginx -t
curl http://localhost/health/
```

**Soluções:**
1. Restart manual: `sudo systemctl restart nef-cadencia`
2. Verificar `.env` está correto
3. Verificar permissões do socket
4. Executar rollback se problema persistir

---

## BOAS PRÁTICAS

### Antes do Deploy

1. ✅ Executar `pre-deploy-check.sh`
2. ✅ Testar localmente
3. ✅ Revisar migrations
4. ✅ Verificar backups recentes
5. ✅ Notificar stakeholders (se deploy grande)
6. ✅ Escolher horário de baixo tráfego

### Durante o Deploy

1. ✅ Monitorar logs em tempo real
2. ✅ Ter plano de rollback pronto
3. ✅ Não interromper o script
4. ✅ Documentar qualquer problema

### Após o Deploy

1. ✅ Monitorar por 30 minutos
2. ✅ Verificar métricas de performance
3. ✅ Testar funcionalidades críticas
4. ✅ Verificar logs de erro
5. ✅ Notificar conclusão

### Frequência de Deploy

- **Desenvolvimento:** Múltiplas vezes ao dia
- **Staging:** Diariamente
- **Produção:** Semanalmente ou conforme necessário

### Janelas de Manutenção

**Recomendado:**
- Terça a Quinta-feira
- 02:00 - 04:00 (horário de menor tráfego)
- Evitar Sextas-feiras e vésperas de feriados

---

## SCRIPTS DISPONÍVEIS

### 1. `pre-deploy-check.sh`
**Uso:** Validação antes do deploy  
**Quando:** Sempre antes de deployar  
**Tempo:** ~2 minutos

### 2. `deploy-safe.sh`
**Uso:** Deploy completo com rollback automático  
**Quando:** Para deployar código novo  
**Tempo:** ~5-10 minutos  
**Opções:** `--skip-tests`, `--force`

### 3. `rollback.sh`
**Uso:** Reverter para estado anterior  
**Quando:** Após deploy com problemas  
**Tempo:** ~3-5 minutos

### 4. `deploy.sh` (original)
**Uso:** Deploy simples sem rollback automático  
**Quando:** Para atualizações menores  
**Tempo:** ~5 minutos

### 5. `restart.sh`
**Uso:** Restart rápido dos serviços  
**Quando:** Após mudanças de configuração  
**Tempo:** ~30 segundos

### 6. `backup.sh`
**Uso:** Backup manual  
**Quando:** Antes de mudanças críticas  
**Tempo:** ~2 minutos

### 7. `healthcheck.py`
**Uso:** Verificação completa de saúde  
**Quando:** Após deploy ou para diagnóstico  
**Tempo:** ~1 minuto

---

## LOGS E MONITORAMENTO

### Logs de Deploy

```bash
# Deploy log
tail -f /var/log/nef-cadencia/deploy.log

# Rollback log
tail -f /var/log/nef-cadencia/rollback.log
```

### Logs da Aplicação

```bash
# Application logs (systemd)
sudo journalctl -u nef-cadencia -f

# Gunicorn access log
tail -f /var/log/nef-cadencia/gunicorn-access.log

# Gunicorn error log
tail -f /var/log/nef-cadencia/gunicorn-error.log

# Nginx access log
tail -f /var/log/nginx/nef-cadencia-access.log

# Nginx error log
tail -f /var/log/nginx/nef-cadencia-error.log
```

---

## CHECKLIST DE DEPLOY

### Pré-Deploy
- [ ] Código testado localmente
- [ ] `pre-deploy-check.sh` passou
- [ ] Migrations revisadas
- [ ] Backup recente verificado
- [ ] Stakeholders notificados

### Deploy
- [ ] `deploy-safe.sh` executado
- [ ] Deploy concluído sem erros
- [ ] Logs monitorados

### Pós-Deploy
- [ ] Health check passou
- [ ] Funcionalidades testadas
- [ ] Performance verificada
- [ ] Sem erros nos logs (30 min)
- [ ] Stakeholders notificados

### Em Caso de Problema
- [ ] Rollback executado
- [ ] Causa raiz identificada
- [ ] Correção aplicada
- [ ] Re-deploy planejado

---

## REFERÊNCIAS

- **Scripts:** `/opt/nef-cadencia/deployment/`
- **Logs:** `/var/log/nef-cadencia/`
- **Backups:** `/var/backups/nef-cadencia/`
- **Documentação:** `/opt/nef-cadencia/docs/`

---

**Última Atualização:** 18 de Março de 2026  
**Versão:** 1.0  
**Mantido por:** DevOps Team
