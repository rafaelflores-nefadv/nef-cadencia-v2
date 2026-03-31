# Deploy em VPS Linux - NEF Cadência

**Versão:** 1.0  
**Data:** 18 de Março de 2026  
**Sistema:** Ubuntu 24.04 / Debian 12+

---

## ÍNDICE

1. [Visão Geral](#visão-geral)
2. [Pré-requisitos](#pré-requisitos)
3. [Instalação Inicial](#instalação-inicial)
4. [Configuração do Ambiente](#configuração-do-ambiente)
5. [Deploy da Aplicação](#deploy-da-aplicação)
6. [Configuração SSL](#configuração-ssl)
7. [Operação e Manutenção](#operação-e-manutenção)
8. [Troubleshooting](#troubleshooting)

---

## VISÃO GERAL

### Arquitetura

```
Internet
    ↓
Nginx (Port 80/443)
    ↓
Gunicorn (Unix Socket)
    ↓
Django Application
    ↓
PostgreSQL + Redis
```

### Componentes

- **Nginx:** Reverse proxy, SSL termination, static files
- **Gunicorn:** WSGI server
- **Django:** Application framework
- **PostgreSQL:** Database
- **Redis:** Cache and session storage
- **Systemd:** Process management

---

## PRÉ-REQUISITOS

### Servidor

- **OS:** Ubuntu 24.04 LTS ou Debian 12+
- **RAM:** Mínimo 2GB (recomendado 4GB+)
- **CPU:** Mínimo 2 cores
- **Disco:** Mínimo 20GB SSD
- **Acesso:** SSH com sudo/root

### Domínio

- Domínio registrado
- DNS configurado apontando para o IP do servidor
- Registros A/AAAA configurados

### Localmente

- Git configurado
- Acesso SSH ao servidor
- Código-fonte do projeto

---

## INSTALAÇÃO INICIAL

### 1. Conectar ao Servidor

```bash
ssh root@seu-servidor.com
# ou
ssh usuario@seu-servidor.com
```

### 2. Atualizar Sistema

```bash
sudo apt update
sudo apt upgrade -y
```

### 3. Executar Script de Instalação

```bash
# Transferir script para o servidor
scp deployment/install.sh root@seu-servidor.com:/tmp/

# No servidor, executar
cd /tmp
chmod +x install.sh
sudo ./install.sh
```

O script irá instalar:
- Python 3.11
- PostgreSQL 15
- Redis
- Nginx
- Certbot (Let's Encrypt)
- Dependências do sistema

**Tempo estimado:** 10-15 minutos

### 4. Verificar Instalação

```bash
# Verificar serviços
systemctl status postgresql
systemctl status redis-server
systemctl status nginx

# Verificar Python
python3.11 --version

# Verificar PostgreSQL
sudo -u postgres psql -c "SELECT version();"
```

---

## CONFIGURAÇÃO DO AMBIENTE

### 1. Criar Usuário da Aplicação

```bash
# Já criado pelo script install.sh
# Verificar
id nef-cadencia
```

### 2. Configurar PostgreSQL

```bash
# Conectar ao PostgreSQL
sudo -u postgres psql

# Criar usuário e banco
CREATE USER nef_cadencia WITH PASSWORD 'SUA_SENHA_FORTE_AQUI';
CREATE DATABASE nef_cadencia_prod OWNER nef_cadencia;
GRANT ALL PRIVILEGES ON DATABASE nef_cadencia_prod TO nef_cadencia;

# Configurar extensões
\c nef_cadencia_prod
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS unaccent;

# Sair
\q
```

**Gerar senha forte:**
```bash
openssl rand -base64 32
```

### 3. Configurar Redis

```bash
# Editar configuração
sudo nano /etc/redis/redis.conf

# Configurar senha (opcional mas recomendado)
requirepass SUA_SENHA_REDIS_AQUI

# Reiniciar Redis
sudo systemctl restart redis-server
```

### 4. Clonar Repositório

```bash
# Mudar para usuário da aplicação
sudo su - nef-cadencia

# Clonar repositório
cd /opt
git clone https://github.com/seu-usuario/nef-cadencia.git nef-cadencia

# Ou transferir via SCP
# scp -r /caminho/local/nef-cadencia usuario@servidor:/opt/
```

### 5. Criar Arquivo .env

```bash
cd /opt/nef-cadencia

# Copiar template
cp .env.example .env

# Editar com valores de produção
nano .env
```

**Configuração mínima do .env:**

```env
# Ambiente
DJANGO_ENV=production

# Django Core
SECRET_KEY=<gerar-com-comando-seguro>
DEBUG=False
ALLOWED_HOSTS=seu-dominio.com,www.seu-dominio.com

# Database
DB_NAME=nef_cadencia_prod
DB_USER=nef_cadencia
DB_PASSWORD=<senha-do-postgres>
DB_HOST=localhost
DB_PORT=5432
DB_CONN_MAX_AGE=600

# Redis
REDIS_URL=redis://:senha-redis@localhost:6379/1

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=seu-email@gmail.com
EMAIL_HOST_PASSWORD=<app-password>
DEFAULT_FROM_EMAIL=noreply@seu-dominio.com

# Security
CSRF_TRUSTED_ORIGINS=https://seu-dominio.com,https://www.seu-dominio.com

# OpenAI
OPENAI_API_KEY=sk-sua-chave-aqui
```

**Gerar SECRET_KEY:**
```bash
python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

**Proteger .env:**
```bash
chmod 600 .env
chown nef-cadencia:www-data .env
```

---

## DEPLOY DA APLICAÇÃO

### 1. Executar Script de Deploy

```bash
# Como usuário nef-cadencia
cd /opt/nef-cadencia
chmod +x deployment/deploy.sh
./deployment/deploy.sh
```

O script irá:
1. ✅ Criar backup
2. ✅ Criar virtual environment
3. ✅ Instalar dependências
4. ✅ Validar .env
5. ✅ Executar migrações
6. ✅ Coletar static files
7. ✅ Configurar permissões
8. ✅ Reiniciar serviços

**Tempo estimado:** 5-10 minutos

### 2. Configurar Systemd Service

```bash
# Copiar service file
sudo cp /opt/nef-cadencia/deployment/nef-cadencia.service /etc/systemd/system/

# Recarregar systemd
sudo systemctl daemon-reload

# Habilitar serviço
sudo systemctl enable nef-cadencia

# Iniciar serviço
sudo systemctl start nef-cadencia

# Verificar status
sudo systemctl status nef-cadencia
```

### 3. Configurar Nginx

```bash
# Copiar configuração
sudo cp /opt/nef-cadencia/deployment/nginx-site.conf /etc/nginx/sites-available/nef-cadencia

# Editar e ajustar domínio
sudo nano /etc/nginx/sites-available/nef-cadencia
# Alterar: server_name example.com www.example.com;
# Para: server_name seu-dominio.com www.seu-dominio.com;

# Criar link simbólico
sudo ln -s /etc/nginx/sites-available/nef-cadencia /etc/nginx/sites-enabled/

# Remover site padrão
sudo rm -f /etc/nginx/sites-enabled/default

# Testar configuração
sudo nginx -t

# Recarregar Nginx
sudo systemctl reload nginx
```

### 4. Criar Superusuário Django

```bash
cd /opt/nef-cadencia
source venv/bin/activate
python manage.py createsuperuser
```

### 5. Verificar Aplicação

```bash
# Verificar serviços
sudo systemctl status nef-cadencia
sudo systemctl status nginx

# Testar endpoint
curl http://localhost/health/

# Ver logs
sudo journalctl -u nef-cadencia -f
```

---

## CONFIGURAÇÃO SSL

### Opção 1: Let's Encrypt (Recomendado - Gratuito)

```bash
# Instalar Certbot (já instalado pelo install.sh)
sudo apt install certbot python3-certbot-nginx -y

# Obter certificado
sudo certbot --nginx -d seu-dominio.com -d www.seu-dominio.com

# Seguir instruções interativas
# Escolher: Redirect HTTP to HTTPS (opção 2)

# Verificar renovação automática
sudo certbot renew --dry-run

# Certificados serão renovados automaticamente via cron
```

**Localização dos certificados:**
```
/etc/letsencrypt/live/seu-dominio.com/fullchain.pem
/etc/letsencrypt/live/seu-dominio.com/privkey.pem
```

### Opção 2: Certificado Próprio

```bash
# Criar diretório
sudo mkdir -p /etc/nginx/ssl

# Copiar certificados
sudo cp seu-certificado.crt /etc/nginx/ssl/
sudo cp sua-chave.key /etc/nginx/ssl/

# Ajustar permissões
sudo chmod 600 /etc/nginx/ssl/sua-chave.key
sudo chown root:root /etc/nginx/ssl/*

# Editar nginx-site.conf
sudo nano /etc/nginx/sites-available/nef-cadencia

# Descomentar seção HTTPS e ajustar caminhos
```

### Verificar SSL

```bash
# Testar HTTPS
curl https://seu-dominio.com/health/

# Verificar certificado
openssl s_client -connect seu-dominio.com:443 -servername seu-dominio.com

# Testar com SSL Labs
# https://www.ssllabs.com/ssltest/
```

---

## OPERAÇÃO E MANUTENÇÃO

### Comandos Úteis

#### Gerenciar Serviços

```bash
# Status
sudo systemctl status nef-cadencia
sudo systemctl status nginx

# Iniciar
sudo systemctl start nef-cadencia

# Parar
sudo systemctl stop nef-cadencia

# Reiniciar
sudo systemctl restart nef-cadencia

# Recarregar (sem downtime)
sudo systemctl reload nef-cadencia

# Ver logs em tempo real
sudo journalctl -u nef-cadencia -f

# Ver últimas 100 linhas
sudo journalctl -u nef-cadencia -n 100
```

#### Restart Rápido

```bash
# Usar script de restart
sudo /opt/nef-cadencia/deployment/restart.sh
```

#### Deploy de Atualizações

```bash
# Como usuário nef-cadencia
cd /opt/nef-cadencia

# Pull do código
git pull origin main

# Executar deploy
./deployment/deploy.sh
```

#### Backup do Banco

```bash
# Manual
sudo /opt/nef-cadencia/deployment/backup.sh

# Configurar cron para backup automático
sudo crontab -e

# Adicionar (backup diário às 2h da manhã)
0 2 * * * /opt/nef-cadencia/deployment/backup.sh >> /var/log/nef-cadencia/backup.log 2>&1
```

#### Health Check

```bash
# Executar health check
sudo python3 /opt/nef-cadencia/deployment/healthcheck.py

# Ou via HTTP
curl http://localhost/health/
```

### Monitoramento

#### Logs

```bash
# Application logs
sudo journalctl -u nef-cadencia -f

# Nginx access log
sudo tail -f /var/log/nginx/nef-cadencia-access.log

# Nginx error log
sudo tail -f /var/log/nginx/nef-cadencia-error.log

# PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql-15-main.log
```

#### Recursos do Sistema

```bash
# CPU e memória
htop

# Disco
df -h

# Processos Gunicorn
ps aux | grep gunicorn

# Conexões de rede
sudo netstat -tulpn | grep -E '(80|443|8000|5432|6379)'
```

### Manutenção Regular

#### Semanal

- [ ] Verificar logs de erro
- [ ] Verificar espaço em disco
- [ ] Verificar backups

#### Mensal

- [ ] Atualizar pacotes do sistema
- [ ] Revisar logs de segurança
- [ ] Testar restore de backup
- [ ] Verificar certificados SSL

#### Trimestral

- [ ] Atualizar dependências Python
- [ ] Revisar configurações de segurança
- [ ] Análise de performance
- [ ] Limpeza de logs antigos

---

## TROUBLESHOOTING

### Aplicação Não Inicia

**Sintomas:** `systemctl status nef-cadencia` mostra failed

**Diagnóstico:**
```bash
# Ver logs detalhados
sudo journalctl -u nef-cadencia -n 50 --no-pager

# Verificar .env
cat /opt/nef-cadencia/.env

# Testar manualmente
cd /opt/nef-cadencia
source venv/bin/activate
python manage.py check --deploy
```

**Soluções Comuns:**
- Verificar SECRET_KEY no .env
- Verificar ALLOWED_HOSTS
- Verificar conexão com banco de dados
- Verificar permissões de arquivos

### Erro 502 Bad Gateway

**Sintomas:** Nginx retorna 502

**Diagnóstico:**
```bash
# Verificar se Gunicorn está rodando
sudo systemctl status nef-cadencia

# Verificar socket
ls -la /opt/nef-cadencia/run/gunicorn.sock

# Verificar logs do Nginx
sudo tail -f /var/log/nginx/nef-cadencia-error.log
```

**Soluções:**
- Reiniciar Gunicorn: `sudo systemctl restart nef-cadencia`
- Verificar permissões do socket
- Verificar configuração do upstream no Nginx

### Erro 500 Internal Server Error

**Sintomas:** Aplicação retorna 500

**Diagnóstico:**
```bash
# Ver logs da aplicação
sudo journalctl -u nef-cadencia -n 100

# Ver logs do Django
sudo tail -f /var/log/nef-cadencia/gunicorn-error.log
```

**Soluções:**
- Verificar migrações: `python manage.py showmigrations`
- Verificar static files: `python manage.py collectstatic`
- Verificar DEBUG=False no .env
- Verificar ALLOWED_HOSTS

### Static Files Não Carregam

**Sintomas:** CSS/JS não aparecem

**Diagnóstico:**
```bash
# Verificar static files
ls -la /opt/nef-cadencia/staticfiles/

# Verificar permissões
ls -ld /opt/nef-cadencia/staticfiles/

# Testar Nginx
curl -I http://localhost/static/admin/css/base.css
```

**Soluções:**
```bash
# Coletar static files
cd /opt/nef-cadencia
source venv/bin/activate
python manage.py collectstatic --noinput

# Ajustar permissões
sudo chown -R nef-cadencia:www-data /opt/nef-cadencia/staticfiles
sudo chmod -R 755 /opt/nef-cadencia/staticfiles
```

### Banco de Dados Não Conecta

**Sintomas:** Erro de conexão com PostgreSQL

**Diagnóstico:**
```bash
# Verificar se PostgreSQL está rodando
sudo systemctl status postgresql

# Testar conexão
sudo -u postgres psql -c "SELECT 1;"

# Testar com credenciais da aplicação
psql -h localhost -U nef_cadencia -d nef_cadencia_prod -c "SELECT 1;"
```

**Soluções:**
- Verificar credenciais no .env
- Verificar pg_hba.conf: `sudo nano /etc/postgresql/15/main/pg_hba.conf`
- Reiniciar PostgreSQL: `sudo systemctl restart postgresql`

### Performance Lenta

**Diagnóstico:**
```bash
# Verificar recursos
htop

# Verificar workers Gunicorn
ps aux | grep gunicorn | wc -l

# Verificar conexões ao banco
sudo -u postgres psql -c "SELECT count(*) FROM pg_stat_activity;"
```

**Soluções:**
- Aumentar workers Gunicorn (editar service file)
- Configurar connection pooling (DB_CONN_MAX_AGE)
- Habilitar cache Redis
- Otimizar queries do banco

---

## CHECKLIST PÓS-DEPLOY

### Segurança

- [ ] SECRET_KEY gerada e segura (50+ caracteres)
- [ ] DEBUG=False
- [ ] ALLOWED_HOSTS configurado corretamente
- [ ] Firewall (UFW) configurado
- [ ] SSL/HTTPS configurado
- [ ] Certificado SSL válido
- [ ] HSTS habilitado
- [ ] Senha forte no PostgreSQL
- [ ] Redis com senha (se exposto)
- [ ] Arquivo .env com permissões 600
- [ ] Superusuário Django criado
- [ ] Admin acessível apenas via HTTPS

### Funcionalidade

- [ ] Aplicação responde em HTTP/HTTPS
- [ ] Health check funcionando
- [ ] Admin panel acessível
- [ ] Static files carregando
- [ ] Media files funcionando
- [ ] Login/logout funcionando
- [ ] Emails sendo enviados
- [ ] Cache Redis funcionando

### Infraestrutura

- [ ] Gunicorn rodando como serviço
- [ ] Nginx rodando
- [ ] PostgreSQL rodando
- [ ] Redis rodando
- [ ] Logs sendo gerados
- [ ] Log rotation configurado
- [ ] Backup automático configurado
- [ ] Monitoramento configurado

### Performance

- [ ] Workers Gunicorn adequados (2*CPU+1)
- [ ] Connection pooling habilitado
- [ ] Gzip habilitado no Nginx
- [ ] Static files com cache headers
- [ ] Database indexes criados

### Operacional

- [ ] Documentação atualizada
- [ ] Credenciais documentadas (seguramente)
- [ ] Runbook de operação criado
- [ ] Contatos de emergência definidos
- [ ] Plano de rollback documentado
- [ ] Backup testado (restore)

---

## COMANDOS RÁPIDOS

### Restart Completo

```bash
sudo systemctl restart nef-cadencia nginx postgresql redis-server
```

### Ver Todos os Logs

```bash
sudo journalctl -u nef-cadencia -u nginx -f
```

### Backup Completo

```bash
sudo /opt/nef-cadencia/deployment/backup.sh
```

### Health Check Completo

```bash
sudo python3 /opt/nef-cadencia/deployment/healthcheck.py
```

### Deploy de Atualização

```bash
cd /opt/nef-cadencia && git pull && ./deployment/deploy.sh
```

---

## RECURSOS ADICIONAIS

### Documentação

- Django Deployment: https://docs.djangoproject.com/en/stable/howto/deployment/
- Gunicorn: https://docs.gunicorn.org/
- Nginx: https://nginx.org/en/docs/
- PostgreSQL: https://www.postgresql.org/docs/
- Let's Encrypt: https://letsencrypt.org/docs/

### Ferramentas Úteis

- SSL Test: https://www.ssllabs.com/ssltest/
- Security Headers: https://securityheaders.com/
- GTmetrix: https://gtmetrix.com/

---

**Última Atualização:** 18 de Março de 2026  
**Versão:** 1.0  
**Suporte:** devops@seu-dominio.com
