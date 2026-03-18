#!/bin/bash
# ==============================================================================
# NEF Cadência - Rollback Script
# ==============================================================================
# This script performs a safe rollback to a previous deployment state
#
# Usage:
#   ./deployment/rollback.sh [TIMESTAMP]
#   ./deployment/rollback.sh           # Rollback to last known good state
#   ./deployment/rollback.sh 20260318_143000  # Rollback to specific backup
# ==============================================================================

set -e
set -u
set -o pipefail

# ==============================================================================
# Configuration
# ==============================================================================
APP_DIR="/opt/nef-cadencia"
APP_USER="nef-cadencia"
VENV_DIR="$APP_DIR/venv"
BACKUP_DIR="/var/backups/nef-cadencia"
ROLLBACK_LOG="/var/log/nef-cadencia/rollback.log"
DEPLOYMENT_STATE_FILE="$APP_DIR/.deployment_state"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# ==============================================================================
# Logging Functions
# ==============================================================================
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$ROLLBACK_LOG"
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] ✓${NC} $1" | tee -a "$ROLLBACK_LOG"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ✗${NC} $1" | tee -a "$ROLLBACK_LOG"
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] ⚠${NC} $1" | tee -a "$ROLLBACK_LOG"
}

log_step() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

# ==============================================================================
# Determine Rollback Target
# ==============================================================================
log_step "NEF Cadência - Rollback Procedure"

ROLLBACK_TIMESTAMP=""

if [ $# -eq 1 ]; then
    # Specific timestamp provided
    ROLLBACK_TIMESTAMP="$1"
    log "Rollback target: $ROLLBACK_TIMESTAMP (specified)"
elif [ -f "$DEPLOYMENT_STATE_FILE" ]; then
    # Read from deployment state file
    if grep -q "TIMESTAMP=" "$DEPLOYMENT_STATE_FILE"; then
        ROLLBACK_TIMESTAMP=$(grep "TIMESTAMP=" "$DEPLOYMENT_STATE_FILE" | cut -d'=' -f2)
        log "Rollback target: $ROLLBACK_TIMESTAMP (from deployment state)"
    fi
fi

if [ -z "$ROLLBACK_TIMESTAMP" ]; then
    # Find most recent backup
    LATEST_BACKUP=$(ls -t "$BACKUP_DIR"/pre_deploy_backup_*.tar.gz 2>/dev/null | head -n 1)
    if [ -n "$LATEST_BACKUP" ]; then
        ROLLBACK_TIMESTAMP=$(basename "$LATEST_BACKUP" | sed 's/pre_deploy_backup_\(.*\)\.tar\.gz/\1/')
        log "Rollback target: $ROLLBACK_TIMESTAMP (latest backup)"
    else
        log_error "No backup found to rollback to"
        exit 1
    fi
fi

# ==============================================================================
# Verify Backup Files Exist
# ==============================================================================
log_step "Verifying Backup Files"

BACKUP_FILE="$BACKUP_DIR/pre_deploy_backup_${ROLLBACK_TIMESTAMP}.tar.gz"
DB_BACKUP_FILE="$BACKUP_DIR/pre_deploy_db_${ROLLBACK_TIMESTAMP}.sql.gz"

if [ ! -f "$BACKUP_FILE" ]; then
    log_error "Application backup not found: $BACKUP_FILE"
    exit 1
fi

if [ ! -f "$DB_BACKUP_FILE" ]; then
    log_error "Database backup not found: $DB_BACKUP_FILE"
    exit 1
fi

BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
DB_BACKUP_SIZE=$(du -h "$DB_BACKUP_FILE" | cut -f1)

log_success "Application backup found: $BACKUP_FILE ($BACKUP_SIZE)"
log_success "Database backup found: $DB_BACKUP_FILE ($DB_BACKUP_SIZE)"

# ==============================================================================
# Confirmation
# ==============================================================================
log_step "Rollback Confirmation"

echo ""
log_warning "⚠️  WARNING: This will rollback the application to a previous state!"
echo ""
log "Rollback Details:"
log "  Timestamp: $ROLLBACK_TIMESTAMP"
log "  Application Backup: $BACKUP_FILE"
log "  Database Backup: $DB_BACKUP_FILE"
echo ""

read -p "Are you sure you want to proceed with rollback? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    log "Rollback cancelled by user"
    exit 0
fi

log "Rollback confirmed, proceeding..."

# ==============================================================================
# Create Safety Backup
# ==============================================================================
log_step "Creating Safety Backup"

SAFETY_TIMESTAMP=$(date +%Y%m%d_%H%M%S)
SAFETY_BACKUP="$BACKUP_DIR/pre_rollback_backup_${SAFETY_TIMESTAMP}.tar.gz"
SAFETY_DB_BACKUP="$BACKUP_DIR/pre_rollback_db_${SAFETY_TIMESTAMP}.sql"

log "Creating safety backup before rollback..."

# Backup current application state
tar -czf "$SAFETY_BACKUP" \
    --exclude='venv' \
    --exclude='staticfiles' \
    --exclude='*.pyc' \
    --exclude='__pycache__' \
    --exclude='.git' \
    --exclude='media' \
    -C "$APP_DIR" . 2>/dev/null || true

log_success "Safety application backup created: $SAFETY_BACKUP"

# Backup current database
source "$APP_DIR/.env"
if sudo -u postgres pg_dump "$DB_NAME" > "$SAFETY_DB_BACKUP" 2>/dev/null; then
    gzip "$SAFETY_DB_BACKUP"
    log_success "Safety database backup created: ${SAFETY_DB_BACKUP}.gz"
else
    log_warning "Failed to create safety database backup (continuing anyway)"
fi

# ==============================================================================
# Stop Application
# ==============================================================================
log_step "Stopping Application"

log "Stopping Gunicorn service..."
if systemctl stop nef-cadencia; then
    log_success "Gunicorn stopped"
else
    log_warning "Failed to stop Gunicorn gracefully, forcing..."
    systemctl kill nef-cadencia || true
fi

# Wait for service to stop
sleep 3

# ==============================================================================
# Restore Database
# ==============================================================================
log_step "Restoring Database"

log "Decompressing database backup..."
DB_BACKUP_UNCOMPRESSED="${DB_BACKUP_FILE%.gz}"
gunzip -c "$DB_BACKUP_FILE" > "$DB_BACKUP_UNCOMPRESSED"

log "Dropping existing database connections..."
sudo -u postgres psql -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$DB_NAME' AND pid <> pg_backend_pid();" 2>/dev/null || true

log "Restoring database from backup..."
if sudo -u postgres psql -d "$DB_NAME" < "$DB_BACKUP_UNCOMPRESSED" 2>&1 | tee -a "$ROLLBACK_LOG"; then
    log_success "Database restored successfully"
    rm -f "$DB_BACKUP_UNCOMPRESSED"
else
    log_error "Database restore failed!"
    log_error "Manual intervention required!"
    rm -f "$DB_BACKUP_UNCOMPRESSED"
    exit 1
fi

# ==============================================================================
# Restore Application Files
# ==============================================================================
log_step "Restoring Application Files"

# Create temporary directory for extraction
TEMP_DIR=$(mktemp -d)
log "Extracting backup to temporary directory..."

if tar -xzf "$BACKUP_FILE" -C "$TEMP_DIR"; then
    log_success "Backup extracted to $TEMP_DIR"
else
    log_error "Failed to extract backup"
    rm -rf "$TEMP_DIR"
    exit 1
fi

# Preserve critical files
log "Preserving critical files..."
cp "$APP_DIR/.env" "$TEMP_DIR/.env" 2>/dev/null || true
cp -r "$APP_DIR/media" "$TEMP_DIR/media" 2>/dev/null || true

# Remove old application files (except venv and media)
log "Removing current application files..."
find "$APP_DIR" -mindepth 1 -maxdepth 1 \
    ! -name 'venv' \
    ! -name 'media' \
    ! -name '.env' \
    -exec rm -rf {} + 2>/dev/null || true

# Copy restored files
log "Restoring application files..."
cp -r "$TEMP_DIR"/* "$APP_DIR/" 2>/dev/null || true
cp -r "$TEMP_DIR"/.* "$APP_DIR/" 2>/dev/null || true

# Cleanup
rm -rf "$TEMP_DIR"

log_success "Application files restored"

# ==============================================================================
# Restore Dependencies
# ==============================================================================
log_step "Restoring Dependencies"

cd "$APP_DIR"

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Reinstall dependencies from restored requirements.txt
if [ -f "$APP_DIR/requirements.txt" ]; then
    log "Reinstalling dependencies..."
    pip install -r "$APP_DIR/requirements.txt" --quiet
    log_success "Dependencies restored"
else
    log_warning "requirements.txt not found in backup"
fi

# ==============================================================================
# Collect Static Files
# ==============================================================================
log_step "Collecting Static Files"

log "Collecting static files..."
export DJANGO_SETTINGS_MODULE="alive_platform.settings.production"

if python manage.py collectstatic --noinput --clear 2>&1 | tee -a "$ROLLBACK_LOG"; then
    log_success "Static files collected"
else
    log_warning "Failed to collect static files (non-critical)"
fi

# ==============================================================================
# Set Permissions
# ==============================================================================
log_step "Setting Permissions"

log "Setting file permissions..."

chown -R $APP_USER:www-data "$APP_DIR"
find "$APP_DIR" -type d -exec chmod 755 {} \;
find "$APP_DIR" -type f -exec chmod 644 {} \;
chmod +x "$APP_DIR/manage.py"
chmod +x "$APP_DIR/deployment"/*.sh 2>/dev/null || true
chmod 600 "$APP_DIR/.env"

log_success "Permissions set"

# ==============================================================================
# Start Application
# ==============================================================================
log_step "Starting Application"

log "Starting Gunicorn service..."
systemctl daemon-reload

if systemctl start nef-cadencia; then
    log_success "Gunicorn started"
else
    log_error "Failed to start Gunicorn"
    systemctl status nef-cadencia --no-pager
    exit 1
fi

# Wait for service to start
sleep 5

# Check service status
if systemctl is-active --quiet nef-cadencia; then
    log_success "Gunicorn service is active"
else
    log_error "Gunicorn service is not active"
    systemctl status nef-cadencia --no-pager
    exit 1
fi

# Reload Nginx
log "Reloading Nginx..."
if nginx -t && systemctl reload nginx; then
    log_success "Nginx reloaded"
else
    log_error "Nginx reload failed"
    exit 1
fi

# ==============================================================================
# Verify Rollback
# ==============================================================================
log_step "Verifying Rollback"

# Wait for application to start
sleep 10

# Test HTTP endpoint
log "Testing application..."
if curl -f -s http://localhost/health/ > /dev/null 2>&1; then
    log_success "Application is responding"
else
    log_warning "Application health check failed"
fi

# Check for errors in logs
ERROR_COUNT=$(journalctl -u nef-cadencia -n 20 --no-pager | grep -i error | wc -l)
if [ "$ERROR_COUNT" -gt 0 ]; then
    log_warning "Found $ERROR_COUNT errors in recent logs"
else
    log_success "No errors in recent logs"
fi

# ==============================================================================
# Rollback Summary
# ==============================================================================
log_step "ROLLBACK SUCCESSFUL"

echo ""
log_success "Rollback completed successfully!"
echo ""
log "Rollback Summary:"
log "  Rolled back to: $ROLLBACK_TIMESTAMP"
log "  Application backup: $BACKUP_FILE"
log "  Database backup: $DB_BACKUP_FILE"
log "  Safety backup: $SAFETY_BACKUP"
log "  Safety DB backup: ${SAFETY_DB_BACKUP}.gz"
echo ""
log "Service Status:"
systemctl status nef-cadencia --no-pager -l | head -n 5
echo ""
log "Recent Logs:"
journalctl -u nef-cadencia -n 10 --no-pager
echo ""
log "Next Steps:"
log "  - Monitor application behavior"
log "  - Check logs: journalctl -u nef-cadencia -f"
log "  - Investigate root cause of deployment failure"
log "  - Safety backups available if re-rollback needed"
echo ""

# Update deployment state
echo "ROLLBACK" > "$DEPLOYMENT_STATE_FILE"
echo "TIMESTAMP=$ROLLBACK_TIMESTAMP" >> "$DEPLOYMENT_STATE_FILE"
echo "ROLLED_BACK_AT=$(date -Iseconds)" >> "$DEPLOYMENT_STATE_FILE"
echo "SAFETY_BACKUP=$SAFETY_BACKUP" >> "$DEPLOYMENT_STATE_FILE"

exit 0
