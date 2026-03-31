#!/bin/bash
# ==============================================================================
# NEF Cadência - Deployment Script
# ==============================================================================
# This script deploys the application to the server
# Run from the application directory: /opt/nef-cadencia
# ==============================================================================

set -e  # Exit on error

echo "========================================"
echo "NEF Cadência - Deployment"
echo "========================================"

# ------------------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------------------
APP_DIR="/opt/nef-cadencia"
APP_USER="nef-cadencia"
VENV_DIR="$APP_DIR/venv"
BACKUP_DIR="/var/backups/nef-cadencia"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ------------------------------------------------------------------------------
# Check if running as correct user
# ------------------------------------------------------------------------------
if [ "$USER" != "$APP_USER" ] && [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Please run as $APP_USER user or root${NC}"
    exit 1
fi

# ------------------------------------------------------------------------------
# Backup current version
# ------------------------------------------------------------------------------
echo "Creating backup..."
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup_$TIMESTAMP.tar.gz"

if [ -d "$APP_DIR/alive_platform" ]; then
    tar -czf "$BACKUP_FILE" \
        -C "$APP_DIR" \
        --exclude='venv' \
        --exclude='staticfiles' \
        --exclude='media' \
        --exclude='*.pyc' \
        --exclude='__pycache__' \
        --exclude='.git' \
        .
    echo -e "${GREEN}✓ Backup created: $BACKUP_FILE${NC}"
else
    echo -e "${YELLOW}⊘ No existing installation to backup${NC}"
fi

# ------------------------------------------------------------------------------
# Pull latest code (if using git)
# ------------------------------------------------------------------------------
if [ -d "$APP_DIR/.git" ]; then
    echo "Pulling latest code from git..."
    cd "$APP_DIR"
    git fetch origin
    git pull origin main  # or master, adjust as needed
    echo -e "${GREEN}✓ Code updated${NC}"
else
    echo -e "${YELLOW}⊘ Not a git repository, skipping pull${NC}"
    echo "Make sure code is updated manually"
fi

# ------------------------------------------------------------------------------
# Create/Activate Virtual Environment
# ------------------------------------------------------------------------------
echo "Setting up Python virtual environment..."

if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3.11 -m venv "$VENV_DIR"
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${YELLOW}⊘ Virtual environment already exists${NC}"
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Upgrade pip
pip install --upgrade pip setuptools wheel

echo -e "${GREEN}✓ Virtual environment ready${NC}"

# ------------------------------------------------------------------------------
# Install/Update Dependencies
# ------------------------------------------------------------------------------
echo "Installing Python dependencies..."

if [ -f "$APP_DIR/requirements.txt" ]; then
    pip install -r "$APP_DIR/requirements.txt"
    echo -e "${GREEN}✓ Dependencies installed${NC}"
else
    echo -e "${RED}✗ requirements.txt not found!${NC}"
    exit 1
fi

# ------------------------------------------------------------------------------
# Check Environment Variables
# ------------------------------------------------------------------------------
echo "Checking environment configuration..."

if [ ! -f "$APP_DIR/.env" ]; then
    echo -e "${RED}✗ .env file not found!${NC}"
    echo "Please create .env file with production settings"
    exit 1
fi

# Source environment variables
set -a
source "$APP_DIR/.env"
set +a

# Validate critical variables
REQUIRED_VARS=("SECRET_KEY" "DB_NAME" "DB_USER" "DB_PASSWORD" "ALLOWED_HOSTS")
MISSING_VARS=()

for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        MISSING_VARS+=("$var")
    fi
done

if [ ${#MISSING_VARS[@]} -gt 0 ]; then
    echo -e "${RED}✗ Missing required environment variables:${NC}"
    printf '%s\n' "${MISSING_VARS[@]}"
    exit 1
fi

echo -e "${GREEN}✓ Environment configuration valid${NC}"

# ------------------------------------------------------------------------------
# Run Database Migrations
# ------------------------------------------------------------------------------
echo "Running database migrations..."

# Check for pending migrations
PENDING=$(python manage.py showmigrations --plan | grep '\[ \]' | wc -l)

if [ "$PENDING" -gt 0 ]; then
    echo "Found $PENDING pending migrations"
    
    # Backup database before migrations
    echo "Backing up database..."
    sudo -u postgres pg_dump nef_cadencia_prod > "$BACKUP_DIR/db_backup_$TIMESTAMP.sql"
    echo -e "${GREEN}✓ Database backed up${NC}"
    
    # Run migrations
    python manage.py migrate --noinput
    echo -e "${GREEN}✓ Migrations completed${NC}"
else
    echo -e "${YELLOW}⊘ No pending migrations${NC}"
fi

# ------------------------------------------------------------------------------
# Collect Static Files
# ------------------------------------------------------------------------------
echo "Collecting static files..."

python manage.py collectstatic --noinput --clear
echo -e "${GREEN}✓ Static files collected${NC}"

# ------------------------------------------------------------------------------
# Run Django Checks
# ------------------------------------------------------------------------------
echo "Running Django system checks..."

if python manage.py check --deploy; then
    echo -e "${GREEN}✓ Django checks passed${NC}"
else
    echo -e "${RED}✗ Django checks failed!${NC}"
    echo "Please fix the issues before continuing"
    exit 1
fi

# ------------------------------------------------------------------------------
# Set Permissions
# ------------------------------------------------------------------------------
echo "Setting file permissions..."

# Set ownership
chown -R $APP_USER:www-data "$APP_DIR"

# Set directory permissions
find "$APP_DIR" -type d -exec chmod 755 {} \;

# Set file permissions
find "$APP_DIR" -type f -exec chmod 644 {} \;

# Make manage.py executable
chmod +x "$APP_DIR/manage.py"

# Secure .env file
chmod 600 "$APP_DIR/.env"

# Set permissions for runtime directories
chmod 775 "$APP_DIR/run"
chmod 775 "$APP_DIR/staticfiles"
chmod 775 "$APP_DIR/media"

echo -e "${GREEN}✓ Permissions set${NC}"

# ------------------------------------------------------------------------------
# Restart Services
# ------------------------------------------------------------------------------
echo "Restarting services..."

# Reload systemd
systemctl daemon-reload

# Restart Gunicorn
systemctl restart nef-cadencia

# Wait for service to start
sleep 3

# Check service status
if systemctl is-active --quiet nef-cadencia; then
    echo -e "${GREEN}✓ Gunicorn service started${NC}"
else
    echo -e "${RED}✗ Gunicorn service failed to start${NC}"
    systemctl status nef-cadencia
    exit 1
fi

# Reload Nginx
systemctl reload nginx

if systemctl is-active --quiet nginx; then
    echo -e "${GREEN}✓ Nginx reloaded${NC}"
else
    echo -e "${RED}✗ Nginx failed to reload${NC}"
    systemctl status nginx
    exit 1
fi

# ------------------------------------------------------------------------------
# Health Check
# ------------------------------------------------------------------------------
echo "Running health check..."

sleep 5  # Wait for application to fully start

# Check if application responds
if curl -f http://localhost/health/ > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Application is healthy${NC}"
else
    echo -e "${YELLOW}⚠ Health check failed (this may be normal if health endpoint doesn't exist)${NC}"
fi

# ------------------------------------------------------------------------------
# Cleanup Old Backups
# ------------------------------------------------------------------------------
echo "Cleaning up old backups..."

# Keep only last 10 backups
cd "$BACKUP_DIR"
ls -t backup_*.tar.gz 2>/dev/null | tail -n +11 | xargs -r rm
ls -t db_backup_*.sql 2>/dev/null | tail -n +11 | xargs -r rm

echo -e "${GREEN}✓ Old backups cleaned${NC}"

# ------------------------------------------------------------------------------
# Summary
# ------------------------------------------------------------------------------
echo ""
echo "========================================"
echo -e "${GREEN}Deployment Complete!${NC}"
echo "========================================"
echo ""
echo "Service Status:"
systemctl status nef-cadencia --no-pager -l | head -n 10
echo ""
echo "Recent Logs:"
journalctl -u nef-cadencia -n 20 --no-pager
echo ""
echo "Next steps:"
echo "  - Monitor logs: journalctl -u nef-cadencia -f"
echo "  - Check application: curl http://localhost/health/"
echo "  - View Nginx logs: tail -f /var/log/nginx/nef-cadencia-error.log"
echo ""
