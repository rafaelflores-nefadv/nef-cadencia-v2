#!/bin/bash
# ==============================================================================
# NEF Cadência - Initial Installation Script
# ==============================================================================
# This script sets up the complete environment for NEF Cadência on Ubuntu/Debian
# Run as root or with sudo
# ==============================================================================

set -e  # Exit on error

echo "========================================"
echo "NEF Cadência - Installation Script"
echo "========================================"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root or with sudo"
    exit 1
fi

# ------------------------------------------------------------------------------
# Configuration Variables
# ------------------------------------------------------------------------------
APP_NAME="nef-cadencia"
APP_USER="nef-cadencia"
APP_GROUP="nef-cadencia"
APP_DIR="/opt/nef-cadencia"
LOG_DIR="/var/log/nef-cadencia"
PYTHON_VERSION="3.11"

# ------------------------------------------------------------------------------
# Update System
# ------------------------------------------------------------------------------
echo "Updating system packages..."
apt-get update
apt-get upgrade -y

# ------------------------------------------------------------------------------
# Install System Dependencies
# ------------------------------------------------------------------------------
echo "Installing system dependencies..."
apt-get install -y \
    python${PYTHON_VERSION} \
    python${PYTHON_VERSION}-venv \
    python${PYTHON_VERSION}-dev \
    python3-pip \
    postgresql \
    postgresql-contrib \
    nginx \
    redis-server \
    git \
    curl \
    wget \
    build-essential \
    libpq-dev \
    libssl-dev \
    libffi-dev \
    certbot \
    python3-certbot-nginx \
    supervisor \
    htop \
    vim \
    ufw

echo "✓ System dependencies installed"

# ------------------------------------------------------------------------------
# Create Application User
# ------------------------------------------------------------------------------
echo "Creating application user..."
if ! id -u $APP_USER > /dev/null 2>&1; then
    useradd --system --gid www-data --shell /bin/bash --home $APP_DIR $APP_USER
    echo "✓ User $APP_USER created"
else
    echo "⊘ User $APP_USER already exists"
fi

# ------------------------------------------------------------------------------
# Create Directory Structure
# ------------------------------------------------------------------------------
echo "Creating directory structure..."
mkdir -p $APP_DIR
mkdir -p $APP_DIR/run
mkdir -p $APP_DIR/staticfiles
mkdir -p $APP_DIR/media
mkdir -p $LOG_DIR
mkdir -p /var/backups/nef-cadencia

# Set permissions
chown -R $APP_USER:www-data $APP_DIR
chown -R $APP_USER:www-data $LOG_DIR
chmod 755 $APP_DIR
chmod 755 $LOG_DIR

echo "✓ Directory structure created"

# ------------------------------------------------------------------------------
# Configure PostgreSQL
# ------------------------------------------------------------------------------
echo "Configuring PostgreSQL..."

# Start PostgreSQL if not running
systemctl start postgresql
systemctl enable postgresql

# Create database and user (interactive - will prompt for password)
echo "Creating PostgreSQL database and user..."
echo "Please enter a strong password for the database user when prompted."

sudo -u postgres psql << EOF
-- Create database user
CREATE USER nef_cadencia WITH PASSWORD 'CHANGE_THIS_PASSWORD';

-- Create database
CREATE DATABASE nef_cadencia_prod OWNER nef_cadencia;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE nef_cadencia_prod TO nef_cadencia;

-- Configure extensions
\c nef_cadencia_prod
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS unaccent;
EOF

echo "✓ PostgreSQL configured"
echo "⚠ IMPORTANT: Change the database password in the SQL above!"

# ------------------------------------------------------------------------------
# Configure Redis
# ------------------------------------------------------------------------------
echo "Configuring Redis..."

# Backup original config
cp /etc/redis/redis.conf /etc/redis/redis.conf.backup

# Configure Redis
cat > /etc/redis/redis.conf << 'EOF'
bind 127.0.0.1 ::1
protected-mode yes
port 6379
tcp-backlog 511
timeout 0
tcp-keepalive 300
daemonize no
supervised systemd
pidfile /var/run/redis/redis-server.pid
loglevel notice
logfile /var/log/redis/redis-server.log
databases 16
save 900 1
save 300 10
save 60 10000
stop-writes-on-bgsave-error yes
rdbcompression yes
rdbchecksum yes
dbfilename dump.rdb
dir /var/lib/redis
maxmemory 256mb
maxmemory-policy allkeys-lru
appendonly yes
appendfilename "appendonly.aof"
appendfsync everysec
EOF

# Restart Redis
systemctl restart redis-server
systemctl enable redis-server

echo "✓ Redis configured"

# ------------------------------------------------------------------------------
# Configure Firewall (UFW)
# ------------------------------------------------------------------------------
echo "Configuring firewall..."

ufw --force enable
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 'Nginx Full'
ufw status

echo "✓ Firewall configured"

# ------------------------------------------------------------------------------
# Configure Nginx
# ------------------------------------------------------------------------------
echo "Configuring Nginx..."

# Remove default site
rm -f /etc/nginx/sites-enabled/default

# Create nginx user if doesn't exist
if ! id -u nginx > /dev/null 2>&1; then
    useradd --system --no-create-home --shell /bin/false nginx
fi

# Optimize Nginx configuration
cat > /etc/nginx/nginx.conf << 'EOF'
user www-data;
worker_processes auto;
pid /run/nginx.pid;
include /etc/nginx/modules-enabled/*.conf;

events {
    worker_connections 2048;
    use epoll;
    multi_accept on;
}

http {
    # Basic Settings
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    server_tokens off;
    client_max_body_size 20M;

    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # SSL Settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers off;

    # Logging
    access_log /var/log/nginx/access.log;
    error_log /var/log/nginx/error.log;

    # Gzip Settings
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml text/javascript 
               application/json application/javascript application/xml+rss 
               application/rss+xml font/truetype font/opentype 
               application/vnd.ms-fontobject image/svg+xml;
    gzip_disable "msie6";

    # Virtual Host Configs
    include /etc/nginx/conf.d/*.conf;
    include /etc/nginx/sites-enabled/*;
}
EOF

# Test nginx configuration
nginx -t

echo "✓ Nginx configured"

# ------------------------------------------------------------------------------
# Create Log Rotation Configuration
# ------------------------------------------------------------------------------
echo "Configuring log rotation..."

cat > /etc/logrotate.d/nef-cadencia << 'EOF'
/var/log/nef-cadencia/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 nef-cadencia www-data
    sharedscripts
    postrotate
        systemctl reload nef-cadencia > /dev/null 2>&1 || true
    endscript
}
EOF

echo "✓ Log rotation configured"

# ------------------------------------------------------------------------------
# Summary
# ------------------------------------------------------------------------------
echo ""
echo "========================================"
echo "Installation Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. Clone your application to $APP_DIR"
echo "2. Create and configure .env file"
echo "3. Run deployment/deploy.sh"
echo "4. Configure SSL with: certbot --nginx -d your-domain.com"
echo ""
echo "Important files:"
echo "  - Application: $APP_DIR"
echo "  - Logs: $LOG_DIR"
echo "  - Nginx config: /etc/nginx/sites-available/nef-cadencia"
echo "  - Systemd service: /etc/systemd/system/nef-cadencia.service"
echo ""
echo "⚠ SECURITY REMINDERS:"
echo "  - Change PostgreSQL password"
echo "  - Configure .env with secure secrets"
echo "  - Set up SSL certificates"
echo "  - Review firewall rules"
echo ""
