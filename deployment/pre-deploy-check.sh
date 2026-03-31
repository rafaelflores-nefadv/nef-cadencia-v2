#!/bin/bash
# ==============================================================================
# NEF Cadência - Pre-deployment Validation Script
# ==============================================================================
# This script performs comprehensive pre-deployment checks
# Run this before deploying to catch issues early
#
# Usage:
#   ./deployment/pre-deploy-check.sh
# ==============================================================================

set -e
set -u

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Counters
CHECKS_PASSED=0
CHECKS_FAILED=0
CHECKS_WARNING=0

# ==============================================================================
# Helper Functions
# ==============================================================================
print_header() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

check_pass() {
    echo -e "${GREEN}✓${NC} $1"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
}

check_fail() {
    echo -e "${RED}✗${NC} $1"
    CHECKS_FAILED=$((CHECKS_FAILED + 1))
}

check_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
    CHECKS_WARNING=$((CHECKS_WARNING + 1))
}

# ==============================================================================
# Start Checks
# ==============================================================================
print_header "Pre-deployment Validation"

APP_DIR="/opt/nef-cadencia"

# ==============================================================================
# 1. Environment Checks
# ==============================================================================
print_header "1. Environment Checks"

# Check if .env exists
if [ -f "$APP_DIR/.env" ]; then
    check_pass ".env file exists"
    
    # Source .env
    set -a
    source "$APP_DIR/.env"
    set +a
    
    # Check critical variables
    if [ -n "${SECRET_KEY:-}" ] && [ "$SECRET_KEY" != "change-me-in-production" ]; then
        check_pass "SECRET_KEY is set and not default"
    else
        check_fail "SECRET_KEY is not set or is default value"
    fi
    
    if [ "${DEBUG:-}" = "False" ] || [ "${DEBUG:-}" = "false" ]; then
        check_pass "DEBUG is False"
    else
        check_fail "DEBUG is not False (current: ${DEBUG:-not set})"
    fi
    
    if [ -n "${ALLOWED_HOSTS:-}" ]; then
        check_pass "ALLOWED_HOSTS is set"
    else
        check_fail "ALLOWED_HOSTS is not set"
    fi
    
    if [ -n "${DB_NAME:-}" ] && [ -n "${DB_USER:-}" ] && [ -n "${DB_PASSWORD:-}" ]; then
        check_pass "Database credentials are set"
    else
        check_fail "Database credentials are incomplete"
    fi
    
else
    check_fail ".env file not found"
fi

# ==============================================================================
# 2. Code Quality Checks
# ==============================================================================
print_header "2. Code Quality Checks"

cd "$APP_DIR"

# Check for Python syntax errors
if find . -name "*.py" -not -path "./venv/*" -not -path "./.venv/*" | xargs python3 -m py_compile 2>/dev/null; then
    check_pass "No Python syntax errors"
else
    check_fail "Python syntax errors detected"
fi

# Check for uncommitted changes (if git repo)
if [ -d ".git" ]; then
    if git diff-index --quiet HEAD --; then
        check_pass "No uncommitted changes"
    else
        check_warn "Uncommitted changes detected"
    fi
    
    # Check if behind remote
    git fetch origin --quiet
    LOCAL=$(git rev-parse @)
    REMOTE=$(git rev-parse @{u} 2>/dev/null || echo "")
    
    if [ -n "$REMOTE" ]; then
        if [ "$LOCAL" = "$REMOTE" ]; then
            check_pass "Up to date with remote"
        else
            check_warn "Local is behind remote"
        fi
    fi
fi

# ==============================================================================
# 3. Dependencies Check
# ==============================================================================
print_header "3. Dependencies Check"

if [ -f "requirements.txt" ]; then
    check_pass "requirements.txt exists"
    
    # Check if venv exists
    if [ -d "venv" ]; then
        check_pass "Virtual environment exists"
        
        # Activate venv and check packages
        source venv/bin/activate
        
        # Check critical packages
        CRITICAL_PACKAGES=("django" "gunicorn" "psycopg2-binary" "redis")
        for package in "${CRITICAL_PACKAGES[@]}"; do
            if pip show "$package" > /dev/null 2>&1; then
                check_pass "$package is installed"
            else
                check_fail "$package is NOT installed"
            fi
        done
        
        # Check for outdated packages
        OUTDATED=$(pip list --outdated --format=freeze 2>/dev/null | wc -l)
        if [ "$OUTDATED" -eq 0 ]; then
            check_pass "All packages are up to date"
        else
            check_warn "$OUTDATED packages have updates available"
        fi
    else
        check_fail "Virtual environment not found"
    fi
else
    check_fail "requirements.txt not found"
fi

# ==============================================================================
# 4. Database Checks
# ==============================================================================
print_header "4. Database Checks"

# Check PostgreSQL service
if systemctl is-active --quiet postgresql; then
    check_pass "PostgreSQL service is running"
else
    check_fail "PostgreSQL service is NOT running"
fi

# Test database connection
if [ -n "${DB_NAME:-}" ]; then
    if psql -h "${DB_HOST:-localhost}" -U "${DB_USER:-postgres}" -d "$DB_NAME" -c "SELECT 1;" > /dev/null 2>&1; then
        check_pass "Database connection successful"
    else
        check_fail "Cannot connect to database"
    fi
fi

# Check for pending migrations
if [ -d "venv" ]; then
    source venv/bin/activate
    export DJANGO_SETTINGS_MODULE="alive_platform.settings.production"
    
    PENDING=$(python manage.py showmigrations --plan 2>/dev/null | grep '\[ \]' | wc -l)
    if [ "$PENDING" -eq 0 ]; then
        check_pass "No pending migrations"
    else
        check_warn "$PENDING pending migrations"
    fi
fi

# ==============================================================================
# 5. Services Check
# ==============================================================================
print_header "5. Services Check"

# Check Gunicorn service
if systemctl is-active --quiet nef-cadencia; then
    check_pass "Gunicorn service is running"
else
    check_warn "Gunicorn service is NOT running"
fi

# Check Nginx service
if systemctl is-active --quiet nginx; then
    check_pass "Nginx service is running"
else
    check_fail "Nginx service is NOT running"
fi

# Check Redis service
if systemctl is-active --quiet redis-server; then
    check_pass "Redis service is running"
else
    check_warn "Redis service is NOT running"
fi

# ==============================================================================
# 6. Disk Space Check
# ==============================================================================
print_header "6. Disk Space Check"

# Check root partition
ROOT_USAGE=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$ROOT_USAGE" -lt 80 ]; then
    check_pass "Root partition: ${ROOT_USAGE}% used"
elif [ "$ROOT_USAGE" -lt 90 ]; then
    check_warn "Root partition: ${ROOT_USAGE}% used (getting full)"
else
    check_fail "Root partition: ${ROOT_USAGE}% used (CRITICAL)"
fi

# Check /var partition (if separate)
if mountpoint -q /var; then
    VAR_USAGE=$(df /var | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ "$VAR_USAGE" -lt 80 ]; then
        check_pass "/var partition: ${VAR_USAGE}% used"
    else
        check_warn "/var partition: ${VAR_USAGE}% used"
    fi
fi

# ==============================================================================
# 7. Backup Check
# ==============================================================================
print_header "7. Backup Check"

BACKUP_DIR="/var/backups/nef-cadencia"

if [ -d "$BACKUP_DIR" ]; then
    check_pass "Backup directory exists"
    
    # Check for recent backups
    RECENT_BACKUPS=$(find "$BACKUP_DIR" -name "*.tar.gz" -mtime -7 | wc -l)
    if [ "$RECENT_BACKUPS" -gt 0 ]; then
        check_pass "$RECENT_BACKUPS backup(s) from last 7 days"
    else
        check_warn "No recent backups found"
    fi
else
    check_warn "Backup directory not found"
fi

# ==============================================================================
# 8. SSL Certificate Check
# ==============================================================================
print_header "8. SSL Certificate Check"

# Check if Let's Encrypt certificates exist
if [ -d "/etc/letsencrypt/live" ]; then
    CERT_DIRS=$(find /etc/letsencrypt/live -mindepth 1 -maxdepth 1 -type d | wc -l)
    if [ "$CERT_DIRS" -gt 0 ]; then
        check_pass "SSL certificates found"
        
        # Check certificate expiry
        for cert_dir in /etc/letsencrypt/live/*/; do
            DOMAIN=$(basename "$cert_dir")
            if [ -f "${cert_dir}cert.pem" ]; then
                EXPIRY=$(openssl x509 -enddate -noout -in "${cert_dir}cert.pem" | cut -d= -f2)
                EXPIRY_EPOCH=$(date -d "$EXPIRY" +%s)
                NOW_EPOCH=$(date +%s)
                DAYS_LEFT=$(( ($EXPIRY_EPOCH - $NOW_EPOCH) / 86400 ))
                
                if [ "$DAYS_LEFT" -gt 30 ]; then
                    check_pass "Certificate for $DOMAIN expires in $DAYS_LEFT days"
                elif [ "$DAYS_LEFT" -gt 7 ]; then
                    check_warn "Certificate for $DOMAIN expires in $DAYS_LEFT days"
                else
                    check_fail "Certificate for $DOMAIN expires in $DAYS_LEFT days (URGENT)"
                fi
            fi
        done
    else
        check_warn "No SSL certificates found"
    fi
else
    check_warn "Let's Encrypt directory not found"
fi

# ==============================================================================
# 9. Security Checks
# ==============================================================================
print_header "9. Security Checks"

# Check .env permissions
if [ -f "$APP_DIR/.env" ]; then
    ENV_PERMS=$(stat -c %a "$APP_DIR/.env")
    if [ "$ENV_PERMS" = "600" ]; then
        check_pass ".env has correct permissions (600)"
    else
        check_fail ".env has incorrect permissions ($ENV_PERMS, should be 600)"
    fi
fi

# Check if firewall is active
if command -v ufw &> /dev/null; then
    if ufw status | grep -q "Status: active"; then
        check_pass "Firewall (UFW) is active"
    else
        check_warn "Firewall (UFW) is NOT active"
    fi
fi

# ==============================================================================
# 10. Application Health Check
# ==============================================================================
print_header "10. Application Health Check"

# Test HTTP endpoint
if curl -f -s http://localhost/health/ > /dev/null 2>&1; then
    check_pass "Application health endpoint responding"
else
    check_warn "Application health endpoint not responding"
fi

# Check recent errors in logs
if command -v journalctl &> /dev/null; then
    ERROR_COUNT=$(journalctl -u nef-cadencia -n 100 --no-pager 2>/dev/null | grep -i error | wc -l)
    if [ "$ERROR_COUNT" -eq 0 ]; then
        check_pass "No errors in recent logs"
    else
        check_warn "$ERROR_COUNT errors found in recent logs"
    fi
fi

# ==============================================================================
# Summary
# ==============================================================================
print_header "Validation Summary"

TOTAL_CHECKS=$((CHECKS_PASSED + CHECKS_FAILED + CHECKS_WARNING))

echo ""
echo "Total Checks: $TOTAL_CHECKS"
echo -e "${GREEN}Passed: $CHECKS_PASSED${NC}"
echo -e "${YELLOW}Warnings: $CHECKS_WARNING${NC}"
echo -e "${RED}Failed: $CHECKS_FAILED${NC}"
echo ""

if [ "$CHECKS_FAILED" -eq 0 ]; then
    if [ "$CHECKS_WARNING" -eq 0 ]; then
        echo -e "${GREEN}✓ All checks passed! Ready for deployment.${NC}"
        exit 0
    else
        echo -e "${YELLOW}⚠ Some warnings detected. Review before deployment.${NC}"
        exit 0
    fi
else
    echo -e "${RED}✗ Some checks failed! Fix issues before deployment.${NC}"
    exit 1
fi
