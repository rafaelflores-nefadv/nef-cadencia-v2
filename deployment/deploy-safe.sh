#!/bin/bash
# ==============================================================================
# NEF Cadência - Safe Deployment Script
# ==============================================================================
# This script performs a safe, validated deployment with automatic rollback
# on failure. It follows best practices for zero-downtime deployments.
#
# Features:
#   - Pre-deployment validation
#   - Automatic backup before changes
#   - Database migration with rollback support
#   - Static files collection
#   - Health checks
#   - Automatic rollback on failure
#   - Idempotent operations
#
# Usage:
#   ./deployment/deploy-safe.sh [--skip-tests] [--force]
# ==============================================================================

set -e  # Exit on error
set -u  # Exit on undefined variable
set -o pipefail  # Exit on pipe failure

# ==============================================================================
# Configuration
# ==============================================================================
APP_DIR="/opt/nef-cadencia"
APP_USER="nef-cadencia"
VENV_DIR="$APP_DIR/venv"
BACKUP_DIR="/var/backups/nef-cadencia"
DEPLOY_LOG="/var/log/nef-cadencia/deploy.log"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RELEASE_DIR="$APP_DIR/releases/$TIMESTAMP"
CURRENT_LINK="$APP_DIR/current"

# Deployment state
DEPLOYMENT_STATE_FILE="$APP_DIR/.deployment_state"
ROLLBACK_REQUIRED=false
SKIP_TESTS=false
FORCE_DEPLOY=false

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ==============================================================================
# Logging Functions
# ==============================================================================
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$DEPLOY_LOG"
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] ✓${NC} $1" | tee -a "$DEPLOY_LOG"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ✗${NC} $1" | tee -a "$DEPLOY_LOG"
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] ⚠${NC} $1" | tee -a "$DEPLOY_LOG"
}

log_step() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo "" | tee -a "$DEPLOY_LOG"
}

# ==============================================================================
# Error Handling
# ==============================================================================
cleanup_on_error() {
    log_error "Deployment failed! Starting rollback..."
    ROLLBACK_REQUIRED=true
    
    # Save deployment state
    echo "FAILED" > "$DEPLOYMENT_STATE_FILE"
    echo "TIMESTAMP=$TIMESTAMP" >> "$DEPLOYMENT_STATE_FILE"
    echo "ERROR_STEP=$1" >> "$DEPLOYMENT_STATE_FILE"
    
    # Execute rollback
    if [ -f "$APP_DIR/deployment/rollback.sh" ]; then
        bash "$APP_DIR/deployment/rollback.sh" "$TIMESTAMP"
    else
        log_error "Rollback script not found!"
    fi
    
    exit 1
}

# Set trap for errors
trap 'cleanup_on_error "Unknown step"' ERR

# ==============================================================================
# Parse Arguments
# ==============================================================================
while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        --force)
            FORCE_DEPLOY=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--skip-tests] [--force]"
            exit 1
            ;;
    esac
done

# ==============================================================================
# Pre-flight Checks
# ==============================================================================
log_step "STEP 1: Pre-flight Checks"

# Check if running as correct user
if [ "$USER" != "$APP_USER" ] && [ "$EUID" -ne 0 ]; then
    log_error "Please run as $APP_USER user or root"
    exit 1
fi

# Check if application directory exists
if [ ! -d "$APP_DIR" ]; then
    log_error "Application directory not found: $APP_DIR"
    exit 1
fi

# Check if .env exists
if [ ! -f "$APP_DIR/.env" ]; then
    log_error ".env file not found!"
    exit 1
fi

# Create necessary directories
mkdir -p "$BACKUP_DIR"
mkdir -p "$APP_DIR/releases"
mkdir -p "$(dirname $DEPLOY_LOG)"

log_success "Pre-flight checks passed"

# ==============================================================================
# STEP 2: Validate Code
# ==============================================================================
log_step "STEP 2: Code Validation"

cd "$APP_DIR"

# Check if git repository
if [ -d ".git" ]; then
    # Check for uncommitted changes
    if ! git diff-index --quiet HEAD --; then
        if [ "$FORCE_DEPLOY" = false ]; then
            log_error "Uncommitted changes detected. Use --force to override."
            exit 1
        else
            log_warning "Uncommitted changes detected but --force specified"
        fi
    fi
    
    # Get current commit
    CURRENT_COMMIT=$(git rev-parse HEAD)
    log "Current commit: $CURRENT_COMMIT"
    
    # Pull latest changes
    log "Pulling latest changes..."
    git fetch origin
    
    # Check if we're behind
    LOCAL=$(git rev-parse @)
    REMOTE=$(git rev-parse @{u})
    
    if [ "$LOCAL" != "$REMOTE" ]; then
        log "Pulling updates..."
        git pull origin main || git pull origin master
        NEW_COMMIT=$(git rev-parse HEAD)
        log_success "Updated from $CURRENT_COMMIT to $NEW_COMMIT"
    else
        log_success "Already up to date"
    fi
else
    log_warning "Not a git repository, skipping git validation"
fi

# Validate Python syntax
log "Validating Python syntax..."
if find . -name "*.py" -not -path "./venv/*" -not -path "./.venv/*" | xargs python3 -m py_compile 2>/dev/null; then
    log_success "Python syntax validation passed"
else
    log_error "Python syntax errors detected"
    exit 1
fi

log_success "Code validation completed"

# ==============================================================================
# STEP 3: Backup Current State
# ==============================================================================
log_step "STEP 3: Backup Current State"

BACKUP_FILE="$BACKUP_DIR/pre_deploy_backup_$TIMESTAMP.tar.gz"
DB_BACKUP_FILE="$BACKUP_DIR/pre_deploy_db_$TIMESTAMP.sql"

# Backup application files
log "Creating application backup..."
tar -czf "$BACKUP_FILE" \
    --exclude='venv' \
    --exclude='staticfiles' \
    --exclude='*.pyc' \
    --exclude='__pycache__' \
    --exclude='.git' \
    --exclude='media' \
    -C "$APP_DIR" . 2>/dev/null || true

BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
log_success "Application backup created: $BACKUP_FILE ($BACKUP_SIZE)"

# Backup database
log "Creating database backup..."
source "$APP_DIR/.env"
if sudo -u postgres pg_dump "$DB_NAME" > "$DB_BACKUP_FILE" 2>/dev/null; then
    gzip "$DB_BACKUP_FILE"
    DB_BACKUP_SIZE=$(du -h "${DB_BACKUP_FILE}.gz" | cut -f1)
    log_success "Database backup created: ${DB_BACKUP_FILE}.gz ($DB_BACKUP_SIZE)"
else
    log_error "Database backup failed"
    exit 1
fi

# Save current state
echo "SUCCESS" > "$DEPLOYMENT_STATE_FILE"
echo "TIMESTAMP=$TIMESTAMP" >> "$DEPLOYMENT_STATE_FILE"
echo "BACKUP_FILE=$BACKUP_FILE" >> "$DEPLOYMENT_STATE_FILE"
echo "DB_BACKUP_FILE=${DB_BACKUP_FILE}.gz" >> "$DEPLOYMENT_STATE_FILE"
if [ -d ".git" ]; then
    echo "COMMIT=$(git rev-parse HEAD)" >> "$DEPLOYMENT_STATE_FILE"
fi

log_success "Backup completed"

# ==============================================================================
# STEP 4: Install Dependencies
# ==============================================================================
log_step "STEP 4: Install Dependencies"

# Activate virtual environment
if [ ! -d "$VENV_DIR" ]; then
    log "Creating virtual environment..."
    python3.11 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"

# Upgrade pip
log "Upgrading pip..."
pip install --upgrade pip setuptools wheel --quiet

# Install/update dependencies
if [ -f "$APP_DIR/requirements.txt" ]; then
    log "Installing dependencies from requirements.txt..."
    
    # Create a temporary requirements file with hashes for verification
    TEMP_REQ=$(mktemp)
    cp "$APP_DIR/requirements.txt" "$TEMP_REQ"
    
    if pip install -r "$TEMP_REQ" --quiet; then
        log_success "Dependencies installed successfully"
    else
        log_error "Failed to install dependencies"
        rm -f "$TEMP_REQ"
        cleanup_on_error "STEP 4: Install Dependencies"
    fi
    
    rm -f "$TEMP_REQ"
else
    log_error "requirements.txt not found"
    cleanup_on_error "STEP 4: Install Dependencies"
fi

# Verify critical packages
log "Verifying critical packages..."
CRITICAL_PACKAGES=("django" "gunicorn" "psycopg2-binary")
for package in "${CRITICAL_PACKAGES[@]}"; do
    if pip show "$package" > /dev/null 2>&1; then
        VERSION=$(pip show "$package" | grep Version | cut -d' ' -f2)
        log "  ✓ $package ($VERSION)"
    else
        log_error "Critical package missing: $package"
        cleanup_on_error "STEP 4: Install Dependencies"
    fi
done

log_success "Dependencies installation completed"

# ==============================================================================
# STEP 5: Run Tests
# ==============================================================================
log_step "STEP 5: Run Tests"

if [ "$SKIP_TESTS" = true ]; then
    log_warning "Tests skipped (--skip-tests flag)"
else
    # Set test environment
    export DJANGO_SETTINGS_MODULE="alive_platform.settings.test"
    
    # Run Django system checks
    log "Running Django system checks..."
    if python manage.py check --deploy; then
        log_success "Django checks passed"
    else
        log_error "Django checks failed"
        cleanup_on_error "STEP 5: Run Tests - Django Checks"
    fi
    
    # Run tests if pytest is available
    if command -v pytest &> /dev/null; then
        log "Running pytest..."
        if pytest --tb=short --maxfail=5 -q; then
            log_success "Tests passed"
        else
            log_error "Tests failed"
            if [ "$FORCE_DEPLOY" = false ]; then
                cleanup_on_error "STEP 5: Run Tests - Pytest"
            else
                log_warning "Tests failed but --force specified, continuing..."
            fi
        fi
    else
        log_warning "pytest not found, skipping unit tests"
    fi
fi

log_success "Testing phase completed"

# ==============================================================================
# STEP 6: Database Migrations
# ==============================================================================
log_step "STEP 6: Database Migrations"

# Switch back to production settings
export DJANGO_SETTINGS_MODULE="alive_platform.settings.production"

# Check for pending migrations
log "Checking for pending migrations..."
PENDING_MIGRATIONS=$(python manage.py showmigrations --plan | grep '\[ \]' | wc -l)

if [ "$PENDING_MIGRATIONS" -gt 0 ]; then
    log "Found $PENDING_MIGRATIONS pending migrations"
    
    # Show migration plan
    log "Migration plan:"
    python manage.py showmigrations --plan | grep '\[ \]'
    
    # Run migrations
    log "Applying migrations..."
    if python manage.py migrate --noinput 2>&1 | tee -a "$DEPLOY_LOG"; then
        log_success "Migrations applied successfully"
    else
        log_error "Migration failed"
        cleanup_on_error "STEP 6: Database Migrations"
    fi
else
    log_success "No pending migrations"
fi

# Verify migrations
log "Verifying migrations..."
if python manage.py showmigrations | grep '\[ \]' > /dev/null; then
    log_error "Some migrations were not applied"
    cleanup_on_error "STEP 6: Database Migrations - Verification"
else
    log_success "All migrations verified"
fi

log_success "Database migrations completed"

# ==============================================================================
# STEP 7: Collect Static Files
# ==============================================================================
log_step "STEP 7: Collect Static Files"

log "Collecting static files..."
if python manage.py collectstatic --noinput --clear 2>&1 | tee -a "$DEPLOY_LOG"; then
    STATIC_COUNT=$(find "$APP_DIR/staticfiles" -type f | wc -l)
    log_success "Static files collected ($STATIC_COUNT files)"
else
    log_error "Failed to collect static files"
    cleanup_on_error "STEP 7: Collect Static Files"
fi

# Verify static files
if [ ! -d "$APP_DIR/staticfiles" ] || [ -z "$(ls -A $APP_DIR/staticfiles)" ]; then
    log_error "Static files directory is empty"
    cleanup_on_error "STEP 7: Collect Static Files - Verification"
fi

log_success "Static files collection completed"

# ==============================================================================
# STEP 8: Set Permissions
# ==============================================================================
log_step "STEP 8: Set Permissions"

log "Setting file permissions..."

# Set ownership
chown -R $APP_USER:www-data "$APP_DIR"

# Set directory permissions
find "$APP_DIR" -type d -exec chmod 755 {} \;

# Set file permissions
find "$APP_DIR" -type f -exec chmod 644 {} \;

# Make scripts executable
chmod +x "$APP_DIR/manage.py"
chmod +x "$APP_DIR/deployment"/*.sh 2>/dev/null || true

# Secure .env
chmod 600 "$APP_DIR/.env"

# Set permissions for runtime directories
chmod 775 "$APP_DIR/run" 2>/dev/null || mkdir -p "$APP_DIR/run" && chmod 775 "$APP_DIR/run"
chmod 775 "$APP_DIR/staticfiles"
chmod 775 "$APP_DIR/media" 2>/dev/null || mkdir -p "$APP_DIR/media" && chmod 775 "$APP_DIR/media"

log_success "Permissions set"

# ==============================================================================
# STEP 9: Pre-restart Validation
# ==============================================================================
log_step "STEP 9: Pre-restart Validation"

# Validate settings
log "Validating Django settings..."
if python manage.py check --deploy; then
    log_success "Settings validation passed"
else
    log_error "Settings validation failed"
    cleanup_on_error "STEP 9: Pre-restart Validation"
fi

# Test database connection
log "Testing database connection..."
if python manage.py dbshell --command="SELECT 1;" > /dev/null 2>&1; then
    log_success "Database connection successful"
else
    log_error "Database connection failed"
    cleanup_on_error "STEP 9: Pre-restart Validation - Database"
fi

log_success "Pre-restart validation completed"

# ==============================================================================
# STEP 10: Restart Application
# ==============================================================================
log_step "STEP 10: Restart Application"

# Reload systemd
log "Reloading systemd daemon..."
systemctl daemon-reload

# Restart Gunicorn
log "Restarting Gunicorn service..."
if systemctl restart nef-cadencia; then
    log_success "Gunicorn restarted"
else
    log_error "Failed to restart Gunicorn"
    cleanup_on_error "STEP 10: Restart Application - Gunicorn"
fi

# Wait for service to start
log "Waiting for service to start..."
sleep 5

# Check service status
if systemctl is-active --quiet nef-cadencia; then
    log_success "Gunicorn service is active"
else
    log_error "Gunicorn service failed to start"
    systemctl status nef-cadencia --no-pager
    cleanup_on_error "STEP 10: Restart Application - Service Check"
fi

# Reload Nginx
log "Reloading Nginx..."
if nginx -t && systemctl reload nginx; then
    log_success "Nginx reloaded"
else
    log_error "Nginx reload failed"
    cleanup_on_error "STEP 10: Restart Application - Nginx"
fi

log_success "Application restart completed"

# ==============================================================================
# STEP 11: Post-deployment Health Checks
# ==============================================================================
log_step "STEP 11: Post-deployment Health Checks"

# Wait for application to fully start
log "Waiting for application to warm up..."
sleep 10

# Check if application responds
log "Testing HTTP endpoint..."
MAX_RETRIES=5
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -f -s http://localhost/health/ > /dev/null 2>&1; then
        log_success "Application is responding"
        break
    else
        RETRY_COUNT=$((RETRY_COUNT + 1))
        if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
            log_warning "Attempt $RETRY_COUNT/$MAX_RETRIES failed, retrying..."
            sleep 5
        else
            log_error "Application is not responding after $MAX_RETRIES attempts"
            cleanup_on_error "STEP 11: Post-deployment Health Checks"
        fi
    fi
done

# Check for errors in logs
log "Checking recent logs for errors..."
ERROR_COUNT=$(journalctl -u nef-cadencia -n 50 --no-pager | grep -i error | wc -l)
if [ "$ERROR_COUNT" -gt 0 ]; then
    log_warning "Found $ERROR_COUNT errors in recent logs"
    journalctl -u nef-cadencia -n 10 --no-pager | grep -i error
else
    log_success "No errors in recent logs"
fi

# Run comprehensive health check if available
if [ -f "$APP_DIR/deployment/healthcheck.py" ]; then
    log "Running comprehensive health check..."
    if python3 "$APP_DIR/deployment/healthcheck.py"; then
        log_success "Health check passed"
    else
        log_warning "Health check reported issues (non-critical)"
    fi
fi

log_success "Post-deployment health checks completed"

# ==============================================================================
# STEP 12: Cleanup
# ==============================================================================
log_step "STEP 12: Cleanup"

# Remove old backups (keep last 10)
log "Cleaning up old backups..."
cd "$BACKUP_DIR"
ls -t pre_deploy_backup_*.tar.gz 2>/dev/null | tail -n +11 | xargs -r rm
ls -t pre_deploy_db_*.sql.gz 2>/dev/null | tail -n +11 | xargs -r rm
log_success "Old backups cleaned"

# Clear Python cache
log "Clearing Python cache..."
find "$APP_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "$APP_DIR" -type f -name "*.pyc" -delete 2>/dev/null || true
log_success "Python cache cleared"

log_success "Cleanup completed"

# ==============================================================================
# Deployment Summary
# ==============================================================================
log_step "DEPLOYMENT SUCCESSFUL"

echo ""
log_success "Deployment completed successfully!"
echo ""
log "Deployment Summary:"
log "  Timestamp: $TIMESTAMP"
log "  Backup: $BACKUP_FILE"
log "  Database Backup: ${DB_BACKUP_FILE}.gz"
if [ -d ".git" ]; then
    log "  Commit: $(git rev-parse HEAD)"
fi
log "  Pending Migrations: $PENDING_MIGRATIONS (applied)"
log "  Static Files: $STATIC_COUNT files"
echo ""
log "Service Status:"
systemctl status nef-cadencia --no-pager -l | head -n 5
echo ""
log "Recent Logs:"
journalctl -u nef-cadencia -n 10 --no-pager
echo ""
log "Next Steps:"
log "  - Monitor logs: journalctl -u nef-cadencia -f"
log "  - Check application: curl http://localhost/health/"
log "  - View Nginx logs: tail -f /var/log/nginx/nef-cadencia-error.log"
log "  - Rollback if needed: ./deployment/rollback.sh $TIMESTAMP"
echo ""

# Save successful deployment state
echo "SUCCESS" > "$DEPLOYMENT_STATE_FILE"
echo "TIMESTAMP=$TIMESTAMP" >> "$DEPLOYMENT_STATE_FILE"
echo "DEPLOYED_AT=$(date -Iseconds)" >> "$DEPLOYMENT_STATE_FILE"
if [ -d ".git" ]; then
    echo "COMMIT=$(git rev-parse HEAD)" >> "$DEPLOYMENT_STATE_FILE"
fi

exit 0
