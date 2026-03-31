# Checklist Operacional de Deploy - NEF Cadência

**Data:** ___/___/______  
**Responsável:** _________________  
**Tipo de Deploy:** [ ] Normal [ ] Hotfix [ ] Rollback  
**Ambiente:** [ ] Staging [ ] Production

---

## PRÉ-DEPLOY

### Preparação (30 min antes)

- [ ] **Código revisado e aprovado**
  - [ ] Pull request aprovado
  - [ ] Code review completo
  - [ ] Sem conflitos de merge

- [ ] **Testes locais**
  - [ ] Testes unitários passando
  - [ ] Testes de integração passando
  - [ ] Aplicação roda localmente sem erros

- [ ] **Migrations**
  - [ ] Migrations criadas
  - [ ] Migrations testadas localmente
  - [ ] Migrations reversíveis (se possível)
  - [ ] Sem migrations destrutivas sem backup

- [ ] **Dependências**
  - [ ] `requirements.txt` atualizado
  - [ ] Novas dependências documentadas
  - [ ] Compatibilidade verificada

- [ ] **Documentação**
  - [ ] README atualizado (se necessário)
  - [ ] CHANGELOG atualizado
  - [ ] Documentação de API atualizada (se aplicável)

- [ ] **Comunicação**
  - [ ] Stakeholders notificados
  - [ ] Janela de manutenção agendada (se necessário)
  - [ ] Equipe de suporte informada

### Validação Técnica (15 min antes)

- [ ] **Executar pre-deploy-check.sh**
  ```bash
  cd /opt/nef-cadencia
  ./deployment/pre-deploy-check.sh
  ```
  - [ ] Todos os checks passaram
  - [ ] Warnings revisados e aceitos
  - [ ] Nenhum check crítico falhou

- [ ] **Verificar ambiente**
  - [ ] SSH funcionando
  - [ ] Acesso sudo disponível
  - [ ] Conexão estável

- [ ] **Verificar backups**
  - [ ] Backup recente existe (< 24h)
  - [ ] Backup testado (restore funciona)
  - [ ] Espaço suficiente para novo backup

- [ ] **Verificar recursos**
  - [ ] Disco: < 80% usado
  - [ ] RAM: Suficiente disponível
  - [ ] CPU: Não sobrecarregada

- [ ] **Verificar serviços**
  - [ ] PostgreSQL: Running
  - [ ] Redis: Running
  - [ ] Nginx: Running
  - [ ] Gunicorn: Running

---

## DEPLOY

### Início do Deploy

**Hora de início:** ___:___

- [ ] **Conectar ao servidor**
  ```bash
  ssh nef-cadencia@servidor
  cd /opt/nef-cadencia
  ```

- [ ] **Verificar branch/commit**
  ```bash
  git status
  git log -1
  ```
  - Commit atual: _________________________________

- [ ] **Iniciar monitoramento de logs**
  ```bash
  # Em terminal separado
  sudo journalctl -u nef-cadencia -f
  ```

### Execução

- [ ] **Executar deploy-safe.sh**
  ```bash
  ./deployment/deploy-safe.sh
  ```
  
  **Opções usadas:**
  - [ ] Nenhuma (deploy normal)
  - [ ] `--skip-tests`
  - [ ] `--force`

- [ ] **Monitorar progresso**
  - [ ] STEP 1: Pre-flight Checks ✓
  - [ ] STEP 2: Code Validation ✓
  - [ ] STEP 3: Backup Current State ✓
  - [ ] STEP 4: Install Dependencies ✓
  - [ ] STEP 5: Run Tests ✓
  - [ ] STEP 6: Database Migrations ✓
  - [ ] STEP 7: Collect Static Files ✓
  - [ ] STEP 8: Set Permissions ✓
  - [ ] STEP 9: Pre-restart Validation ✓
  - [ ] STEP 10: Restart Application ✓
  - [ ] STEP 11: Post-deployment Health Checks ✓
  - [ ] STEP 12: Cleanup ✓

**Hora de conclusão:** ___:___  
**Duração total:** _____ minutos

### Resultado do Deploy

- [ ] **Deploy bem-sucedido**
  - Backup criado: _________________________________
  - Commit deployado: _________________________________

- [ ] **Deploy falhou (rollback automático)**
  - Etapa que falhou: _________________________________
  - Erro: _________________________________
  - Rollback executado: [ ] Sim [ ] Não

---

## PÓS-DEPLOY

### Validação Imediata (5 min)

- [ ] **Verificar serviço**
  ```bash
  sudo systemctl status nef-cadencia
  ```
  - Status: [ ] Active (running) [ ] Failed [ ] Outro: _______

- [ ] **Testar endpoints**
  ```bash
  curl http://localhost/health/
  curl https://seu-dominio.com/
  ```
  - [ ] Health endpoint: 200 OK
  - [ ] Homepage: 200 OK
  - [ ] Admin: Acessível

- [ ] **Verificar static files**
  ```bash
  curl -I https://seu-dominio.com/static/admin/css/base.css
  ```
  - [ ] Static files carregando: 200 OK

- [ ] **Verificar logs (primeiros 5 min)**
  ```bash
  sudo journalctl -u nef-cadencia -n 50
  ```
  - [ ] Sem erros críticos
  - [ ] Sem warnings inesperados
  - [ ] Aplicação iniciou corretamente

### Testes Funcionais (10 min)

- [ ] **Login/Logout**
  - [ ] Login funcionando
  - [ ] Logout funcionando
  - [ ] Sessões persistindo

- [ ] **Funcionalidades Críticas**
  - [ ] Dashboard carrega
  - [ ] Listagens funcionam
  - [ ] Formulários funcionam
  - [ ] Buscas funcionam

- [ ] **Integrações**
  - [ ] OpenAI funcionando (se aplicável)
  - [ ] Email funcionando (teste)
  - [ ] Cache funcionando

- [ ] **Performance**
  - [ ] Tempo de resposta aceitável
  - [ ] Sem lentidão perceptível
  - [ ] Workers Gunicorn adequados

### Monitoramento Contínuo (30 min)

- [ ] **Monitorar logs**
  ```bash
  sudo journalctl -u nef-cadencia -f
  ```
  - [ ] 10 min: Sem erros
  - [ ] 20 min: Sem erros
  - [ ] 30 min: Sem erros

- [ ] **Monitorar recursos**
  ```bash
  htop
  ```
  - [ ] CPU: Normal
  - [ ] RAM: Normal
  - [ ] Disco: Normal

- [ ] **Verificar métricas** (se disponível)
  - [ ] Requests/segundo: Normal
  - [ ] Response time: Normal
  - [ ] Error rate: Normal

### Health Check Completo

- [ ] **Executar healthcheck.py**
  ```bash
  sudo python3 deployment/healthcheck.py
  ```
  - [ ] Todos os checks passaram
  - [ ] Warnings aceitáveis

---

## COMUNICAÇÃO

### Durante o Deploy

- [ ] **Início comunicado**
  - [ ] Equipe técnica
  - [ ] Stakeholders (se necessário)

- [ ] **Problemas comunicados** (se houver)
  - [ ] Descrição do problema
  - [ ] Ação tomada
  - [ ] ETA de resolução

### Pós-Deploy

- [ ] **Sucesso comunicado**
  - [ ] Equipe técnica
  - [ ] Stakeholders
  - [ ] Usuários (se necessário)

- [ ] **Changelog compartilhado**
  - [ ] Novas funcionalidades
  - [ ] Correções de bugs
  - [ ] Melhorias

---

## ROLLBACK (Se necessário)

### Decisão de Rollback

**Motivo:** _________________________________

**Aprovado por:** _________________________________

### Execução do Rollback

- [ ] **Executar rollback.sh**
  ```bash
  sudo ./deployment/rollback.sh
  ```

- [ ] **Confirmar rollback**
  - Timestamp do backup: _________________________________

- [ ] **Monitorar rollback**
  - [ ] Database restaurado
  - [ ] Código restaurado
  - [ ] Serviços reiniciados
  - [ ] Validação passou

- [ ] **Verificar aplicação**
  - [ ] Health check passou
  - [ ] Funcionalidades funcionando
  - [ ] Sem erros nos logs

**Hora do rollback:** ___:___  
**Duração:** _____ minutos

### Pós-Rollback

- [ ] **Comunicar rollback**
  - [ ] Equipe técnica
  - [ ] Stakeholders

- [ ] **Investigar causa raiz**
  - Causa identificada: _________________________________
  - Ação corretiva: _________________________________

- [ ] **Planejar re-deploy**
  - Data/hora: ___/___/______ ___:___
  - Correções aplicadas: _________________________________

---

## DOCUMENTAÇÃO

### Informações do Deploy

**Versão deployada:** _________________________________  
**Commit hash:** _________________________________  
**Branch:** _________________________________  
**Tag:** _________________________________ (se aplicável)

### Mudanças Principais

1. _________________________________
2. _________________________________
3. _________________________________

### Migrations Aplicadas

- [ ] Nenhuma migration
- [ ] Migrations aplicadas:
  1. _________________________________
  2. _________________________________
  3. _________________________________

### Dependências Atualizadas

- [ ] Nenhuma dependência atualizada
- [ ] Dependências atualizadas:
  1. _________________________________
  2. _________________________________

### Problemas Encontrados

- [ ] Nenhum problema
- [ ] Problemas:
  1. _________________________________
     - Solução: _________________________________
  2. _________________________________
     - Solução: _________________________________

### Lições Aprendidas

1. _________________________________
2. _________________________________
3. _________________________________

---

## MÉTRICAS

### Tempo de Deploy

- **Preparação:** _____ min
- **Execução:** _____ min
- **Validação:** _____ min
- **Total:** _____ min

### Downtime

- **Planejado:** _____ min
- **Real:** _____ min
- **Não planejado:** _____ min

### Impacto

- **Usuários afetados:** _____
- **Requests perdidos:** _____
- **Incidentes gerados:** _____

---

## APROVAÇÕES

### Deploy

**Executado por:**

Nome: _________________  
Data: ___/___/______  
Hora: ___:___  
Assinatura: _________________

### Validação

**Validado por:**

Nome: _________________  
Data: ___/___/______  
Hora: ___:___  
Assinatura: _________________

### Aprovação Final

**Aprovado por:**

Nome: _________________  
Cargo: _________________  
Data: ___/___/______  
Hora: ___:___  
Assinatura: _________________

---

## OBSERVAÇÕES ADICIONAIS

_________________________________________________________________

_________________________________________________________________

_________________________________________________________________

_________________________________________________________________

_________________________________________________________________

---

## PRÓXIMOS PASSOS

- [ ] Monitorar por 24h
- [ ] Revisar métricas de performance
- [ ] Atualizar documentação
- [ ] Agendar próximo deploy
- [ ] Implementar melhorias identificadas

---

**Checklist Versão:** 1.0  
**Última Atualização:** 18 de Março de 2026  
**Mantido por:** DevOps Team
