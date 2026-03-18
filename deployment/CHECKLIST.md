# Checklist de Deploy - NEF Cadência

**Data:** ___/___/______  
**Responsável:** _________________  
**Ambiente:** [ ] Staging [ ] Production

---

## PRÉ-DEPLOY

### Preparação

- [ ] Código revisado e aprovado
- [ ] Testes passando localmente
- [ ] Migrations criadas e testadas
- [ ] Documentação atualizada
- [ ] Changelog atualizado
- [ ] Backup do banco de dados atual criado
- [ ] Plano de rollback definido
- [ ] Janela de manutenção agendada (se necessário)
- [ ] Stakeholders notificados

### Ambiente Local

- [ ] `.env.example` atualizado
- [ ] `requirements.txt` atualizado
- [ ] Dependências testadas
- [ ] `python manage.py check --deploy` passou
- [ ] Static files coletados sem erros
- [ ] Migrations aplicadas sem erros

---

## INSTALAÇÃO INICIAL (Primeira vez)

### Servidor

- [ ] VPS provisionado
- [ ] SSH configurado
- [ ] Firewall configurado
- [ ] Domínio DNS apontando para servidor
- [ ] Script `install.sh` executado
- [ ] Todos os serviços instalados

### PostgreSQL

- [ ] PostgreSQL instalado
- [ ] Banco de dados criado
- [ ] Usuário criado com senha forte
- [ ] Extensões instaladas (pg_trgm, unaccent)
- [ ] Backup inicial configurado

### Redis

- [ ] Redis instalado
- [ ] Senha configurada (se necessário)
- [ ] Persistência configurada

### Nginx

- [ ] Nginx instalado
- [ ] Configuração copiada
- [ ] Domínio configurado
- [ ] Site habilitado
- [ ] `nginx -t` passou

### Aplicação

- [ ] Diretório `/opt/nef-cadencia` criado
- [ ] Código clonado/transferido
- [ ] Usuário `nef-cadencia` criado
- [ ] Permissões configuradas

---

## CONFIGURAÇÃO

### Arquivo .env

- [ ] `.env` criado a partir de `.env.example`
- [ ] `SECRET_KEY` gerada (50+ caracteres)
- [ ] `DEBUG=False`
- [ ] `ALLOWED_HOSTS` configurado com domínio real
- [ ] `DB_NAME` configurado
- [ ] `DB_USER` configurado
- [ ] `DB_PASSWORD` configurado (senha forte)
- [ ] `DB_HOST` configurado
- [ ] `REDIS_URL` configurado
- [ ] `EMAIL_HOST` configurado
- [ ] `EMAIL_HOST_USER` configurado
- [ ] `EMAIL_HOST_PASSWORD` configurado
- [ ] `DEFAULT_FROM_EMAIL` configurado
- [ ] `CSRF_TRUSTED_ORIGINS` configurado
- [ ] `OPENAI_API_KEY` configurado
- [ ] Permissões do .env: `chmod 600`

### Validação de Segredos

- [ ] SECRET_KEY não é valor padrão
- [ ] SECRET_KEY tem 50+ caracteres
- [ ] DB_PASSWORD é senha forte (16+ caracteres)
- [ ] ALLOWED_HOSTS não contém localhost
- [ ] Nenhum segredo commitado no git

---

## DEPLOY

### Virtual Environment

- [ ] Virtual environment criado
- [ ] Dependências instaladas
- [ ] `pip list` verificado

### Database

- [ ] Conexão ao banco testada
- [ ] Backup pré-migration criado
- [ ] Migrations executadas: `python manage.py migrate`
- [ ] Sem erros nas migrations
- [ ] Dados verificados

### Static Files

- [ ] `collectstatic` executado
- [ ] Static files em `/opt/nef-cadencia/staticfiles/`
- [ ] Permissões corretas (755)
- [ ] Nginx servindo static files

### Systemd Service

- [ ] Service file copiado para `/etc/systemd/system/`
- [ ] `systemctl daemon-reload` executado
- [ ] Service habilitado: `systemctl enable nef-cadencia`
- [ ] Service iniciado: `systemctl start nef-cadencia`
- [ ] Status verificado: `systemctl status nef-cadencia`
- [ ] Sem erros nos logs

### Nginx

- [ ] Configuração copiada
- [ ] Domínio ajustado
- [ ] Link simbólico criado
- [ ] `nginx -t` passou
- [ ] Nginx recarregado: `systemctl reload nginx`

---

## SSL/HTTPS

### Let's Encrypt

- [ ] Certbot instalado
- [ ] Certificado obtido: `certbot --nginx -d dominio.com`
- [ ] Redirect HTTP→HTTPS configurado
- [ ] Renovação automática testada: `certbot renew --dry-run`
- [ ] Certificado válido verificado

### Validação SSL

- [ ] HTTPS funcionando
- [ ] Redirect HTTP→HTTPS funcionando
- [ ] Certificado válido
- [ ] SSL Labs teste A+ (https://www.ssllabs.com/ssltest/)
- [ ] HSTS habilitado
- [ ] Security headers configurados

---

## FUNCIONALIDADE

### Aplicação

- [ ] Homepage carrega
- [ ] Admin acessível: `/admin/`
- [ ] Login funcionando
- [ ] Logout funcionando
- [ ] Static files carregando (CSS/JS)
- [ ] Media files funcionando
- [ ] Health check: `/health/`
- [ ] Sem erros 500
- [ ] Sem erros 404 inesperados

### Superusuário

- [ ] Superusuário criado
- [ ] Login no admin funcionando
- [ ] Permissões corretas

### Email

- [ ] Configuração SMTP testada
- [ ] Email de teste enviado
- [ ] Email de recuperação de senha funcionando

### Cache

- [ ] Redis conectado
- [ ] Cache funcionando
- [ ] Sessões em Redis

---

## SEGURANÇA

### Firewall

- [ ] UFW habilitado
- [ ] Porta 22 (SSH) aberta
- [ ] Porta 80 (HTTP) aberta
- [ ] Porta 443 (HTTPS) aberta
- [ ] Outras portas fechadas
- [ ] `ufw status` verificado

### Permissões

- [ ] Aplicação roda como usuário não-root
- [ ] `.env` com permissões 600
- [ ] Logs com permissões corretas
- [ ] Media files com permissões corretas
- [ ] Diretórios com owner correto

### Configurações Django

- [ ] `DEBUG=False` confirmado
- [ ] `ALLOWED_HOSTS` restritivo
- [ ] `SECRET_KEY` segura
- [ ] `SECURE_SSL_REDIRECT=True`
- [ ] `SESSION_COOKIE_SECURE=True`
- [ ] `CSRF_COOKIE_SECURE=True`
- [ ] `SECURE_HSTS_SECONDS` configurado

### Headers de Segurança

- [ ] X-Frame-Options: DENY
- [ ] X-Content-Type-Options: nosniff
- [ ] X-XSS-Protection: 1; mode=block
- [ ] Strict-Transport-Security configurado
- [ ] Referrer-Policy configurado

---

## MONITORAMENTO E LOGS

### Logs

- [ ] Logs da aplicação funcionando
- [ ] Logs do Nginx funcionando
- [ ] Log rotation configurado
- [ ] Logs acessíveis: `journalctl -u nef-cadencia`

### Backup

- [ ] Script de backup testado
- [ ] Backup manual executado
- [ ] Cron job configurado
- [ ] Backup restaurado com sucesso (teste)
- [ ] Retenção de backups configurada

### Health Check

- [ ] Script healthcheck.py funcionando
- [ ] Todos os checks passando
- [ ] Endpoint `/health/` respondendo

---

## PERFORMANCE

### Gunicorn

- [ ] Número de workers adequado (2*CPU+1)
- [ ] Timeout configurado
- [ ] Max requests configurado
- [ ] Logs de performance verificados

### Database

- [ ] Connection pooling habilitado
- [ ] Indexes criados
- [ ] Queries otimizadas
- [ ] Conexões monitoradas

### Nginx

- [ ] Gzip habilitado
- [ ] Cache headers configurados
- [ ] Rate limiting configurado
- [ ] Buffer sizes otimizados

### Cache

- [ ] Redis funcionando
- [ ] Cache hit rate verificado
- [ ] Sessões em cache

---

## OPERACIONAL

### Documentação

- [ ] README atualizado
- [ ] Documentação de deploy atualizada
- [ ] Runbook operacional criado
- [ ] Credenciais documentadas (seguramente)
- [ ] Contatos de emergência definidos

### Scripts

- [ ] `deploy.sh` testado
- [ ] `restart.sh` testado
- [ ] `backup.sh` testado
- [ ] `healthcheck.py` testado
- [ ] Todos os scripts executáveis

### Automação

- [ ] Backup automático configurado (cron)
- [ ] Renovação SSL automática
- [ ] Log rotation automático
- [ ] Monitoramento configurado (se aplicável)

---

## PÓS-DEPLOY

### Validação

- [ ] Aplicação acessível publicamente
- [ ] Todas as funcionalidades testadas
- [ ] Performance aceitável
- [ ] Sem erros nos logs
- [ ] Métricas coletadas

### Comunicação

- [ ] Stakeholders notificados do sucesso
- [ ] Documentação de mudanças compartilhada
- [ ] Equipe treinada (se necessário)

### Monitoramento (Primeiras 24h)

- [ ] Logs monitorados
- [ ] Performance monitorada
- [ ] Erros investigados
- [ ] Usuários reportando problemas?

---

## ROLLBACK (Se necessário)

### Preparação

- [ ] Backup disponível
- [ ] Plano de rollback documentado
- [ ] Janela de manutenção comunicada

### Execução

- [ ] Serviços parados
- [ ] Código revertido
- [ ] Database restaurado (se necessário)
- [ ] Migrations revertidas (se necessário)
- [ ] Serviços reiniciados
- [ ] Validação pós-rollback

---

## ASSINATURAS

**Deploy Executado por:**

Nome: _________________  
Data: ___/___/______  
Hora: ___:___

**Validado por:**

Nome: _________________  
Data: ___/___/______  
Hora: ___:___

**Observações:**

_________________________________________________________________

_________________________________________________________________

_________________________________________________________________

---

## NOTAS

- Este checklist deve ser preenchido para cada deploy
- Manter cópia do checklist preenchido para auditoria
- Reportar qualquer item não completado
- Em caso de problemas, executar rollback imediatamente

---

**Versão do Checklist:** 1.0  
**Última Atualização:** 18 de Março de 2026
