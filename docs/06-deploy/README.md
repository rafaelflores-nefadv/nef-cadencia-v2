# 🚢 Deploy

Guias de implantação e produção do NEF Cadencia v2.

## 📚 Documentos Disponíveis

### [DEPLOY_VPS.md](./DEPLOY_VPS.md)
Deploy em VPS (Ubuntu/Debian)
- Configuração do servidor
- Nginx + Gunicorn
- PostgreSQL
- Certificado SSL
- Systemd services

### [FLUXO_DEPLOY.md](./FLUXO_DEPLOY.md)
Fluxo completo de deploy
- Preparação
- Build
- Deploy
- Rollback
- Monitoramento

### [CHECKLIST_PRODUCAO.md](./CHECKLIST_PRODUCAO.md)
Checklist pré-produção
- Segurança
- Performance
- Backup
- Monitoramento
- Logs

### [POLITICA_SEGREDOS.md](./POLITICA_SEGREDOS.md)
Gerenciamento de segredos
- Variáveis de ambiente
- Chaves de API
- Senhas de banco
- Certificados

### [ARQUIVOS_NAO_DEPLOY.md](./ARQUIVOS_NAO_DEPLOY.md)
Arquivos que não devem ir para produção
- `.env`
- `*.pyc`
- `node_modules/`
- Logs locais

## 🎯 Quick Deploy

### 1. Preparar Servidor
```bash
# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependências
sudo apt install -y python3 python3-venv python3-pip postgresql nginx
```

### 2. Clonar Projeto
```bash
cd /opt
sudo git clone https://github.com/rafaelflores-nefadv/nef-cadencia-v2.git
cd nef-cadencia-v2
```

### 3. Configurar Ambiente
```bash
# Criar venv
python3 -m venv venv
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
npm install

# Configurar .env
cp .env.example .env
nano .env
```

### 4. Preparar Banco
```bash
# Criar banco PostgreSQL
sudo -u postgres createdb nef_cadencia
sudo -u postgres createuser nef_user

# Migrations
python manage.py migrate

# Criar superuser
python manage.py createsuperuser

# Compilar CSS
npm run build:css

# Coletar estáticos
python manage.py collectstatic --noinput
```

### 5. Configurar Gunicorn
```bash
# Criar arquivo de serviço
sudo nano /etc/systemd/system/nef-cadencia.service
```

```ini
[Unit]
Description=NEF Cadencia Gunicorn
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/nef-cadencia-v2
Environment="PATH=/opt/nef-cadencia-v2/venv/bin"
ExecStart=/opt/nef-cadencia-v2/venv/bin/gunicorn \
    --workers 3 \
    --bind unix:/opt/nef-cadencia-v2/gunicorn.sock \
    alive_platform.wsgi:application

[Install]
WantedBy=multi-user.target
```

### 6. Configurar Nginx
```bash
sudo nano /etc/nginx/sites-available/nef-cadencia
```

```nginx
server {
    listen 80;
    server_name seu-dominio.com;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        root /opt/nef-cadencia-v2;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/opt/nef-cadencia-v2/gunicorn.sock;
    }
}
```

### 7. Ativar e Iniciar
```bash
# Ativar site Nginx
sudo ln -s /etc/nginx/sites-available/nef-cadencia /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx

# Iniciar Gunicorn
sudo systemctl start nef-cadencia
sudo systemctl enable nef-cadencia
```

## 🔒 Segurança

### SSL/HTTPS
```bash
# Instalar Certbot
sudo apt install certbot python3-certbot-nginx

# Obter certificado
sudo certbot --nginx -d seu-dominio.com
```

### Firewall
```bash
sudo ufw allow 'Nginx Full'
sudo ufw allow OpenSSH
sudo ufw enable
```

### Variáveis Sensíveis
```bash
# Nunca commitar .env
echo ".env" >> .gitignore

# Usar variáveis de ambiente
export SECRET_KEY="sua-chave-secreta"
export DB_PASSWORD="senha-forte"
```

## 📊 Monitoramento

### Logs
```bash
# Logs do Gunicorn
sudo journalctl -u nef-cadencia -f

# Logs do Nginx
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Logs do Django
tail -f logs/django.log
```

### Status dos Serviços
```bash
sudo systemctl status nef-cadencia
sudo systemctl status nginx
sudo systemctl status postgresql
```

## 🔄 Atualização

```bash
cd /opt/nef-cadencia-v2

# Backup do banco
sudo -u postgres pg_dump nef_cadencia > backup_$(date +%Y%m%d).sql

# Atualizar código
git pull origin main

# Ativar venv
source venv/bin/activate

# Atualizar dependências
pip install -r requirements.txt
npm install

# Migrations
python manage.py migrate

# Compilar CSS
npm run build:css

# Coletar estáticos
python manage.py collectstatic --noinput

# Reiniciar serviço
sudo systemctl restart nef-cadencia
```

## 🆘 Rollback

```bash
# Voltar para commit anterior
git reset --hard HEAD~1

# Restaurar banco
sudo -u postgres psql nef_cadencia < backup_20260327.sql

# Reiniciar
sudo systemctl restart nef-cadencia
```

## 📋 Checklist Pré-Deploy

- [ ] `.env` configurado corretamente
- [ ] `DEBUG=False` em produção
- [ ] `SECRET_KEY` única e segura
- [ ] Banco de dados criado
- [ ] Migrations aplicadas
- [ ] Estáticos coletados
- [ ] SSL configurado
- [ ] Firewall ativo
- [ ] Backup configurado
- [ ] Logs configurados
- [ ] Monitoramento ativo
