# Checklist Final de Produção - NEF Cadência

**Versão:** 1.0  
**Data:** 18 de Março de 2026  
**Ambiente:** Production  
**Responsável:** _________________  
**Data de Execução:** ___/___/______

---

## ÍNDICE

1. [Segurança](#1-segurança)
2. [Ambiente](#2-ambiente)
3. [Banco de Dados](#3-banco-de-dados)
4. [Migrações](#4-migrações)
5. [Assets](#5-assets)
6. [Web Server](#6-web-server)
7. [App Server](#7-app-server)
8. [Health Check](#8-health-check)
9. [Logging](#9-logging)
10. [Backup](#10-backup)
11. [Restore](#11-restore)
12. [Monitoramento](#12-monitoramento)
13. [Testes de Fumaça](#13-testes-de-fumaça-pós-deploy)

---

## 1. SEGURANÇA

### 1.1. Secrets e Variáveis de Ambiente

- [ ] **SECRET_KEY gerada e segura**
  ```bash
  # Gerar nova SECRET_KEY
  python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
  
  # Verificar tamanho (deve ter 50+ caracteres)
  echo $SECRET_KEY | wc -c
  ```
  - Arquivo: `.env`
  - Valor não deve ser padrão
  - Mínimo 50 caracteres

- [ ] **DEBUG=False**
  ```bash
  # Verificar no .env
  grep "^DEBUG=" /opt/nef-cadencia/.env
  # Deve retornar: DEBUG=False
  ```
  - Arquivo: `.env`
  - Validação: `alive_platform/settings/production.py`

- [ ] **ALLOWED_HOSTS configurado**
  ```bash
  # Verificar no .env
  grep "^ALLOWED_HOSTS=" /opt/nef-cadencia/.env
  # Deve conter domínios reais, sem localhost
  ```
  - Arquivo: `.env`
  - Não pode conter: localhost, 127.0.0.1, 0.0.0.0

- [ ] **Senhas de banco fortes**
  ```bash
  # Gerar senha forte
  openssl rand -base64 32
  ```
  - Arquivo: `.env`
  - Variáveis: `DB_PASSWORD`, `LEGACY_PASSWORD`
  - Mínimo 16 caracteres

- [ ] **OPENAI_API_KEY configurada**
  ```bash
  # Verificar formato
  grep "^OPENAI_API_KEY=" /opt/nef-cadencia/.env
  # Deve começar com sk-
  ```
  - Arquivo: `.env`
  - Formato: `sk-...`

- [ ] **Arquivo .env com permissões corretas**
  ```bash
  # Verificar permissões
  ls -la /opt/nef-cadencia/.env
  # Deve ser: -rw------- (600)
  
  # Corrigir se necessário
  chmod 600 /opt/nef-cadencia/.env
  chown nef-cadencia:www-data /opt/nef-cadencia/.env
  ```
  - Permissões: 600
  - Owner: nef-cadencia:www-data

- [ ] **.env não está no git**
  ```bash
  # Verificar
  cd /opt/nef-cadencia
  git ls-files | grep "^\.env$"
  # Não deve retornar nada
  ```

### 1.2. Configurações de Segurança Django

- [ ] **CSRF_TRUSTED_ORIGINS configurado**
  ```bash
  grep "^CSRF_TRUSTED_ORIGINS=" /opt/nef-cadencia/.env
  # Deve conter: https://seu-dominio.com
  ```
  - Arquivo: `.env`
  - Formato: `https://dominio.com` (com protocolo)

- [ ] **SECURE_SSL_REDIRECT=True**
  - Arquivo: `alive_platform/settings/production.py`
  - Força redirecionamento HTTP → HTTPS

- [ ] **SESSION_COOKIE_SECURE=True**
  - Arquivo: `alive_platform/settings/production.py`
  - Cookies apenas via HTTPS

- [ ] **CSRF_COOKIE_SECURE=True**
  - Arquivo: `alive_platform/settings/production.py`
  - CSRF cookies apenas via HTTPS

- [ ] **SECURE_HSTS_SECONDS configurado**
  - Arquivo: `.env` ou `production.py`
  - Valor: 31536000 (1 ano)

### 1.3. Firewall

- [ ] **UFW habilitado e configurado**
  ```bash
  # Verificar status
  sudo ufw status
  
  # Configurar se necessário
  sudo ufw enable
  sudo ufw allow ssh
  sudo ufw allow 'Nginx Full'
  ```
  - Portas abertas: 22 (SSH), 80 (HTTP), 443 (HTTPS)
  - Outras portas: fechadas

### 1.4. SSL/TLS

- [ ] **Certificado SSL instalado**
  ```bash
  # Verificar certificado
  sudo certbot certificates
  
  # Testar SSL
  openssl s_client -connect seu-dominio.com:443 -servername seu-dominio.com
  ```
  - Certificado válido
  - Não expirado
  - Renovação automática configurada

- [ ] **Teste SSL Labs**
  - Acessar: https://www.ssllabs.com/ssltest/
  - Resultado esperado: A ou A+

---

## 2. AMBIENTE

### 2.1. Sistema Operacional

- [ ] **Sistema atualizado**
  ```bash
  sudo apt update
  sudo apt upgrade -y
  ```

- [ ] **Pacotes necessários instalados**
  ```bash
  # Verificar
  dpkg -l | grep -E "python3.11|postgresql|nginx|redis"
  ```
  - Python 3.11
  - PostgreSQL 15
  - Nginx
  - Redis

### 2.2. Usuário da Aplicação

- [ ] **Usuário nef-cadencia criado**
  ```bash
  # Verificar
  id nef-cadencia
  ```
  - Usuário: nef-cadencia
  - Grupo: www-data

### 2.3. Estrutura de Diretórios

- [ ] **Diretórios criados**
  ```bash
  # Verificar
  ls -la /opt/nef-cadencia/
  ls -la /var/log/nef-cadencia/
  ls -la /var/backups/nef-cadencia/
  ```
  - `/opt/nef-cadencia/` - Aplicação
  - `/opt/nef-cadencia/run/` - Sockets
  - `/opt/nef-cadencia/staticfiles/` - Static files
  - `/opt/nef-cadencia/media/` - Media files
  - `/var/log/nef-cadencia/` - Logs
  - `/var/backups/nef-cadencia/` - Backups

- [ ] **Permissões corretas**
  ```bash
  # Verificar
  ls -ld /opt/nef-cadencia/
  # Deve ser: drwxr-xr-x nef-cadencia www-data
  
  # Corrigir se necessário
  sudo chown -R nef-cadencia:www-data /opt/nef-cadencia
  sudo chmod 755 /opt/nef-cadencia
  ```

### 2.4. Virtual Environment

- [ ] **Virtual environment criado**
  ```bash
  # Verificar
  ls -la /opt/nef-cadencia/venv/
  
  # Criar se necessário
  cd /opt/nef-cadencia
  python3.11 -m venv venv
  ```

- [ ] **Dependências instaladas**
  ```bash
  # Ativar venv
  source /opt/nef-cadencia/venv/bin/activate
  
  # Instalar
  pip install -r requirements.txt
  
  # Verificar pacotes críticos
  pip show django gunicorn psycopg2-binary openai
  ```
  - Arquivo: `requirements.txt`

### 2.5. Variáveis de Ambiente

- [ ] **Arquivo .env criado**
  ```bash
  # Criar a partir do template
  cd /opt/nef-cadencia
  cp .env.example .env
  nano .env
  ```
  - Arquivo: `.env`
  - Baseado em: `.env.example`

- [ ] **Todas as variáveis obrigatórias configuradas**
  ```bash
  # Verificar variáveis críticas
  grep -E "^(SECRET_KEY|DEBUG|ALLOWED_HOSTS|DB_NAME|DB_USER|DB_PASSWORD|DB_HOST)=" .env
  ```
  - SECRET_KEY
  - DEBUG
  - ALLOWED_HOSTS
  - DB_NAME, DB_USER, DB_PASSWORD, DB_HOST
  - OPENAI_API_KEY

---

## 3. BANCO DE DADOS

### 3.1. PostgreSQL

- [ ] **PostgreSQL instalado e rodando**
  ```bash
  # Verificar status
  sudo systemctl status postgresql
  
  # Iniciar se necessário
  sudo systemctl start postgresql
  sudo systemctl enable postgresql
  ```

- [ ] **Banco de dados criado**
  ```bash
  # Conectar ao PostgreSQL
  sudo -u postgres psql
  
  # Criar banco
  CREATE DATABASE nef_cadencia_prod OWNER nef_cadencia;
  
  # Verificar
  \l nef_cadencia_prod
  ```
  - Nome: nef_cadencia_prod
  - Owner: nef_cadencia

- [ ] **Usuário criado com senha forte**
  ```bash
  # No psql
  CREATE USER nef_cadencia WITH PASSWORD 'senha-forte-aqui';
  GRANT ALL PRIVILEGES ON DATABASE nef_cadencia_prod TO nef_cadencia;
  ```

- [ ] **Extensões instaladas**
  ```bash
  # No psql, conectado ao banco
  \c nef_cadencia_prod
  CREATE EXTENSION IF NOT EXISTS pg_trgm;
  CREATE EXTENSION IF NOT EXISTS unaccent;
  
  # Verificar
  \dx
  ```
  - pg_trgm
  - unaccent

- [ ] **Conexão testada**
  ```bash
  # Testar conexão
  psql -h localhost -U nef_cadencia -d nef_cadencia_prod -c "SELECT 1;"
  ```

### 3.2. Redis

- [ ] **Redis instalado e rodando**
  ```bash
  # Verificar status
  sudo systemctl status redis-server
  
  # Iniciar se necessário
  sudo systemctl start redis-server
  sudo systemctl enable redis-server
  ```

- [ ] **Redis configurado**
  ```bash
  # Testar conexão
  redis-cli ping
  # Deve retornar: PONG
  ```

- [ ] **REDIS_URL configurado no .env**
  ```bash
  grep "^REDIS_URL=" /opt/nef-cadencia/.env
  ```
  - Formato: `redis://localhost:6379/1`

---

## 4. MIGRAÇÕES

### 4.1. Pré-Migração

- [ ] **Backup do banco antes das migrations**
  ```bash
  # Criar backup
  sudo -u postgres pg_dump nef_cadencia_prod > /var/backups/nef-cadencia/pre_migration_$(date +%Y%m%d_%H%M%S).sql
  
  # Comprimir
  gzip /var/backups/nef-cadencia/pre_migration_*.sql
  ```

- [ ] **Verificar migrations pendentes**
  ```bash
  cd /opt/nef-cadencia
  source venv/bin/activate
  export DJANGO_SETTINGS_MODULE=alive_platform.settings.production
  
  python manage.py showmigrations | grep '\[ \]'
  ```

### 4.2. Execução

- [ ] **Aplicar migrations**
  ```bash
  cd /opt/nef-cadencia
  source venv/bin/activate
  
  # Aplicar
  python manage.py migrate --noinput
  ```
  - Arquivo: `apps/*/migrations/*.py`

- [ ] **Verificar que todas foram aplicadas**
  ```bash
  # Não deve retornar nada
  python manage.py showmigrations | grep '\[ \]'
  ```

### 4.3. Pós-Migração

- [ ] **Testar conexão ao banco**
  ```bash
  python manage.py dbshell --command="SELECT COUNT(*) FROM django_migrations;"
  ```

- [ ] **Verificar integridade**
  ```bash
  python manage.py check --database default
  ```

---

## 5. ASSETS

### 5.1. Static Files

- [ ] **Coletar static files**
  ```bash
  cd /opt/nef-cadencia
  source venv/bin/activate
  
  python manage.py collectstatic --noinput --clear
  ```
  - Origem: `static/`
  - Destino: `staticfiles/`

- [ ] **Verificar arquivos coletados**
  ```bash
  # Verificar diretório
  ls -la /opt/nef-cadencia/staticfiles/
  
  # Contar arquivos
  find /opt/nef-cadencia/staticfiles/ -type f | wc -l
  ```
  - Deve conter arquivos CSS, JS, imagens

- [ ] **Permissões corretas**
  ```bash
  sudo chown -R nef-cadencia:www-data /opt/nef-cadencia/staticfiles
  sudo chmod -R 755 /opt/nef-cadencia/staticfiles
  ```

### 5.2. Media Files

- [ ] **Diretório media criado**
  ```bash
  mkdir -p /opt/nef-cadencia/media
  sudo chown -R nef-cadencia:www-data /opt/nef-cadencia/media
  sudo chmod 775 /opt/nef-cadencia/media
  ```

---

## 6. WEB SERVER (NGINX)

### 6.1. Instalação e Configuração

- [ ] **Nginx instalado**
  ```bash
  sudo systemctl status nginx
  ```

- [ ] **Configuração do site copiada**
  ```bash
  # Copiar configuração
  sudo cp /opt/nef-cadencia/deployment/nginx-site.conf /etc/nginx/sites-available/nef-cadencia
  
  # Editar domínio
  sudo nano /etc/nginx/sites-available/nef-cadencia
  # Alterar: server_name seu-dominio.com www.seu-dominio.com;
  ```
  - Arquivo: `deployment/nginx-site.conf`
  - Destino: `/etc/nginx/sites-available/nef-cadencia`

- [ ] **Site habilitado**
  ```bash
  # Criar link simbólico
  sudo ln -s /etc/nginx/sites-available/nef-cadencia /etc/nginx/sites-enabled/
  
  # Remover site padrão
  sudo rm -f /etc/nginx/sites-enabled/default
  ```

- [ ] **Configuração testada**
  ```bash
  sudo nginx -t
  # Deve retornar: syntax is ok, test is successful
  ```

- [ ] **Nginx recarregado**
  ```bash
  sudo systemctl reload nginx
  ```

### 6.2. Verificação

- [ ] **Nginx rodando**
  ```bash
  sudo systemctl status nginx
  # Deve estar: active (running)
  ```

- [ ] **Portas abertas**
  ```bash
  sudo netstat -tulpn | grep nginx
  # Deve mostrar: 80, 443
  ```

---

## 7. APP SERVER (GUNICORN)

### 7.1. Configuração Systemd

- [ ] **Service file copiado**
  ```bash
  sudo cp /opt/nef-cadencia/deployment/nef-cadencia.service /etc/systemd/system/
  ```
  - Arquivo: `deployment/nef-cadencia.service`
  - Destino: `/etc/systemd/system/nef-cadencia.service`

- [ ] **Systemd recarregado**
  ```bash
  sudo systemctl daemon-reload
  ```

- [ ] **Serviço habilitado**
  ```bash
  sudo systemctl enable nef-cadencia
  ```

- [ ] **Serviço iniciado**
  ```bash
  sudo systemctl start nef-cadencia
  ```

### 7.2. Verificação

- [ ] **Gunicorn rodando**
  ```bash
  sudo systemctl status nef-cadencia
  # Deve estar: active (running)
  ```

- [ ] **Socket criado**
  ```bash
  ls -la /opt/nef-cadencia/run/gunicorn.sock
  # Deve existir
  ```

- [ ] **Workers rodando**
  ```bash
  ps aux | grep gunicorn
  # Deve mostrar master + workers
  ```

- [ ] **Logs sem erros**
  ```bash
  sudo journalctl -u nef-cadencia -n 50 --no-pager
  # Verificar se não há erros críticos
  ```

---

## 8. HEALTH CHECK

### 8.1. Endpoint de Health

- [ ] **Health endpoint respondendo**
  ```bash
  # Teste local
  curl -f http://localhost/health/
  
  # Teste externo
  curl -f https://seu-dominio.com/health/
  ```
  - Deve retornar: 200 OK

### 8.2. Health Check Completo

- [ ] **Executar script de health check**
  ```bash
  sudo python3 /opt/nef-cadencia/deployment/healthcheck.py
  ```
  - Arquivo: `deployment/healthcheck.py`
  - Deve passar todos os checks

### 8.3. Verificações Manuais

- [ ] **Serviços ativos**
  ```bash
  systemctl is-active nef-cadencia nginx postgresql redis-server
  # Todos devem retornar: active
  ```

- [ ] **Portas abertas**
  ```bash
  sudo netstat -tulpn | grep -E '(80|443|5432|6379)'
  ```
  - 80: Nginx HTTP
  - 443: Nginx HTTPS
  - 5432: PostgreSQL
  - 6379: Redis

- [ ] **Disco com espaço**
  ```bash
  df -h
  # Partição / deve ter < 80% de uso
  ```

---

## 9. LOGGING

### 9.1. Configuração de Logs

- [ ] **Diretório de logs criado**
  ```bash
  sudo mkdir -p /var/log/nef-cadencia
  sudo chown -R nef-cadencia:www-data /var/log/nef-cadencia
  sudo chmod 755 /var/log/nef-cadencia
  ```

- [ ] **Log rotation configurado**
  ```bash
  # Verificar configuração
  cat /etc/logrotate.d/nef-cadencia
  ```
  - Arquivo: `/etc/logrotate.d/nef-cadencia`
  - Rotação: diária
  - Retenção: 14 dias

### 9.2. Verificação de Logs

- [ ] **Logs da aplicação**
  ```bash
  # Ver logs em tempo real
  sudo journalctl -u nef-cadencia -f
  
  # Ver últimas 100 linhas
  sudo journalctl -u nef-cadencia -n 100
  ```

- [ ] **Logs do Gunicorn**
  ```bash
  tail -f /var/log/nef-cadencia/gunicorn-access.log
  tail -f /var/log/nef-cadencia/gunicorn-error.log
  ```

- [ ] **Logs do Nginx**
  ```bash
  tail -f /var/log/nginx/nef-cadencia-access.log
  tail -f /var/log/nginx/nef-cadencia-error.log
  ```

- [ ] **Sem erros críticos**
  ```bash
  # Verificar erros recentes
  sudo journalctl -u nef-cadencia -p err -n 20
  # Não deve ter erros críticos
  ```

---

## 10. BACKUP

### 10.1. Configuração de Backup

- [ ] **Script de backup testado**
  ```bash
  # Executar backup manual
  sudo /opt/nef-cadencia/deployment/backup.sh
  ```
  - Arquivo: `deployment/backup.sh`

- [ ] **Backup criado com sucesso**
  ```bash
  # Verificar backups
  ls -lth /var/backups/nef-cadencia/
  ```
  - Backup do banco (*.sql.gz)
  - Backup de media (*.tar.gz)

- [ ] **Cron job configurado**
  ```bash
  # Editar crontab
  sudo crontab -e
  
  # Adicionar (backup diário às 2h)
  0 2 * * * /opt/nef-cadencia/deployment/backup.sh >> /var/log/nef-cadencia/backup.log 2>&1
  
  # Verificar
  sudo crontab -l
  ```

### 10.2. Verificação de Backup

- [ ] **Backup íntegro**
  ```bash
  # Testar descompressão
  gunzip -t /var/backups/nef-cadencia/db_daily_*.sql.gz
  # Deve retornar sem erros
  ```

- [ ] **Espaço suficiente para backups**
  ```bash
  df -h /var/backups/
  # Deve ter espaço livre
  ```

---

## 11. RESTORE

### 11.1. Teste de Restore (Opcional)

- [ ] **Documentação de restore revisada**
  - Arquivo: `deployment/rollback.sh`
  - Procedimento documentado

- [ ] **Backup de teste restaurado (ambiente de staging)**
  ```bash
  # Em ambiente de teste/staging
  gunzip -c backup.sql.gz | psql -d test_db
  ```

### 11.2. Plano de Rollback

- [ ] **Script de rollback testado**
  ```bash
  # Testar sintaxe (não executar)
  bash -n /opt/nef-cadencia/deployment/rollback.sh
  ```
  - Arquivo: `deployment/rollback.sh`

- [ ] **Backups disponíveis para rollback**
  ```bash
  ls -lth /var/backups/nef-cadencia/ | head -n 5
  # Deve ter backups recentes
  ```

---

## 12. MONITORAMENTO

### 12.1. Monitoramento Básico

- [ ] **Logs sendo gerados**
  ```bash
  # Verificar se logs estão sendo escritos
  ls -lth /var/log/nef-cadencia/
  stat /var/log/nef-cadencia/gunicorn-access.log
  ```

- [ ] **Métricas de sistema**
  ```bash
  # CPU e memória
  htop
  
  # Disco
  df -h
  
  # Processos
  ps aux | grep -E '(gunicorn|nginx|postgres|redis)'
  ```

### 12.2. Alertas (Opcional)

- [ ] **Alertas de disco configurados**
  ```bash
  # Verificar uso de disco
  df -h | awk '$5 > 80 {print $0}'
  ```

- [ ] **Alertas de serviços configurados**
  ```bash
  # Script de verificação
  systemctl is-active nef-cadencia nginx postgresql redis-server
  ```

---

## 13. TESTES DE FUMAÇA PÓS-DEPLOY

### 13.1. Testes de Conectividade

- [ ] **Homepage carrega**
  ```bash
  curl -I https://seu-dominio.com/
  # Deve retornar: 200 OK
  ```

- [ ] **Admin acessível**
  ```bash
  curl -I https://seu-dominio.com/admin/
  # Deve retornar: 200 OK ou 302 (redirect para login)
  ```

- [ ] **Health endpoint**
  ```bash
  curl -f https://seu-dominio.com/health/
  # Deve retornar: 200 OK
  ```

### 13.2. Testes de Funcionalidade

- [ ] **Login funciona**
  - Acessar: https://seu-dominio.com/admin/
  - Fazer login com superusuário
  - Verificar acesso ao admin

- [ ] **Static files carregando**
  ```bash
  curl -I https://seu-dominio.com/static/admin/css/base.css
  # Deve retornar: 200 OK
  ```
  - CSS carregando
  - JS carregando
  - Imagens carregando

- [ ] **Dashboard carrega**
  - Acessar dashboard principal
  - Verificar que dados aparecem
  - Sem erros 500

- [ ] **Formulários funcionam**
  - Testar criação de registro
  - Testar edição de registro
  - Testar exclusão de registro

### 13.3. Testes de Integração

- [ ] **Banco de dados respondendo**
  ```bash
  # Testar query
  cd /opt/nef-cadencia
  source venv/bin/activate
  python manage.py dbshell --command="SELECT COUNT(*) FROM django_session;"
  ```

- [ ] **Cache funcionando**
  ```bash
  # Testar Redis
  redis-cli ping
  # Deve retornar: PONG
  ```

- [ ] **Email configurado (se aplicável)**
  ```bash
  # Testar envio de email
  python manage.py shell
  >>> from django.core.mail import send_mail
  >>> send_mail('Test', 'Test message', 'from@example.com', ['to@example.com'])
  ```

- [ ] **OpenAI funcionando (se aplicável)**
  - Testar funcionalidade do assistente
  - Verificar que API responde

### 13.4. Testes de Performance

- [ ] **Tempo de resposta aceitável**
  ```bash
  # Testar tempo de resposta
  time curl -s https://seu-dominio.com/ > /dev/null
  # Deve ser < 2 segundos
  ```

- [ ] **Workers Gunicorn adequados**
  ```bash
  ps aux | grep gunicorn | wc -l
  # Deve ter: (2 x CPU cores) + 1
  ```

- [ ] **Sem memory leaks**
  ```bash
  # Monitorar memória por 5 minutos
  watch -n 10 'ps aux | grep gunicorn | awk "{sum+=\$6} END {print sum/1024 \" MB\"}"'
  ```

### 13.5. Testes de Segurança

- [ ] **HTTPS funcionando**
  ```bash
  curl -I https://seu-dominio.com/
  # Deve usar HTTPS
  ```

- [ ] **Redirect HTTP → HTTPS**
  ```bash
  curl -I http://seu-dominio.com/
  # Deve retornar: 301 ou 302 para HTTPS
  ```

- [ ] **Headers de segurança**
  ```bash
  curl -I https://seu-dominio.com/ | grep -E '(X-Frame-Options|X-Content-Type-Options|Strict-Transport-Security)'
  ```
  - X-Frame-Options: DENY
  - X-Content-Type-Options: nosniff
  - Strict-Transport-Security: presente

- [ ] **Admin não acessível sem autenticação**
  ```bash
  curl -I https://seu-dominio.com/admin/
  # Deve retornar: 302 (redirect para login)
  ```

### 13.6. Monitoramento Pós-Deploy

- [ ] **Monitorar logs por 30 minutos**
  ```bash
  sudo journalctl -u nef-cadencia -f
  ```
  - Sem erros críticos
  - Sem warnings inesperados

- [ ] **Monitorar recursos**
  ```bash
  htop
  ```
  - CPU: Normal
  - RAM: Normal
  - Disco: Normal

- [ ] **Verificar métricas (se disponível)**
  - Requests/segundo
  - Response time
  - Error rate

---

## ASSINATURAS

### Execução

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

### Aprovação

**Aprovado por:**

Nome: _________________  
Cargo: _________________  
Data: ___/___/______  
Assinatura: _________________

---

## OBSERVAÇÕES

_________________________________________________________________

_________________________________________________________________

_________________________________________________________________

_________________________________________________________________

---

## PRÓXIMOS PASSOS

- [ ] Monitorar aplicação por 24 horas
- [ ] Revisar logs diariamente
- [ ] Agendar próxima manutenção
- [ ] Documentar lições aprendidas

---

## COMANDOS RÁPIDOS DE REFERÊNCIA

### Restart Completo
```bash
sudo systemctl restart nef-cadencia nginx postgresql redis-server
```

### Ver Todos os Logs
```bash
sudo journalctl -u nef-cadencia -u nginx -f
```

### Backup Manual
```bash
sudo /opt/nef-cadencia/deployment/backup.sh
```

### Health Check
```bash
sudo python3 /opt/nef-cadencia/deployment/healthcheck.py
```

### Status de Todos os Serviços
```bash
systemctl status nef-cadencia nginx postgresql redis-server
```

---

**Checklist Versão:** 1.0  
**Última Atualização:** 18 de Março de 2026  
**Mantido por:** DevOps Team
