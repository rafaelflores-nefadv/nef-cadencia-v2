#!/bin/bash
# ==============================================================================
# Entrypoint script for NEF Cadência Docker container
# ==============================================================================
# This script runs before the main application starts
# It handles:
#   - Database connection waiting
#   - Database migrations
#   - Static files collection
#   - Superuser creation (optional)
# ==============================================================================

set -e  # Exit on error

echo "========================================"
echo "NEF Cadência - Starting Application"
echo "========================================"

# ------------------------------------------------------------------------------
# Wait for PostgreSQL to be ready
# ------------------------------------------------------------------------------
echo "Waiting for PostgreSQL..."

until PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c '\q' 2>/dev/null; do
    echo "PostgreSQL is unavailable - sleeping"
    sleep 2
done

echo "✓ PostgreSQL is up and ready"

# ------------------------------------------------------------------------------
# Wait for Redis to be ready
# ------------------------------------------------------------------------------
if [ -n "$REDIS_URL" ]; then
    echo "Waiting for Redis..."
    
    # Extract host and port from REDIS_URL
    REDIS_HOST=$(echo $REDIS_URL | sed -n 's/.*@\([^:]*\):.*/\1/p')
    REDIS_PORT=$(echo $REDIS_URL | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
    
    if [ -z "$REDIS_HOST" ]; then
        REDIS_HOST=$(echo $REDIS_URL | sed -n 's/.*:\/\/\([^:]*\):.*/\1/p')
    fi
    
    if [ -z "$REDIS_PORT" ]; then
        REDIS_PORT=6379
    fi
    
    until nc -z "$REDIS_HOST" "$REDIS_PORT" 2>/dev/null; do
        echo "Redis is unavailable - sleeping"
        sleep 2
    done
    
    echo "✓ Redis is up and ready"
fi

# ------------------------------------------------------------------------------
# Run Database Migrations (Safe Strategy)
# ------------------------------------------------------------------------------
echo "========================================"
echo "Running database migrations..."
echo "========================================"

# Check if there are pending migrations
PENDING_MIGRATIONS=$(python manage.py showmigrations --plan | grep '\[ \]' | wc -l)

if [ "$PENDING_MIGRATIONS" -gt 0 ]; then
    echo "Found $PENDING_MIGRATIONS pending migrations"
    
    # Run migrations with error handling
    if python manage.py migrate --noinput; then
        echo "✓ Migrations completed successfully"
    else
        echo "✗ Migration failed!"
        echo "Please check the database and migrations manually."
        exit 1
    fi
else
    echo "✓ No pending migrations"
fi

# ------------------------------------------------------------------------------
# Collect Static Files
# ------------------------------------------------------------------------------
echo "========================================"
echo "Collecting static files..."
echo "========================================"

# Only collect static files if COLLECT_STATIC is not set to "false"
if [ "${COLLECT_STATIC:-true}" != "false" ]; then
    if python manage.py collectstatic --noinput --clear; then
        echo "✓ Static files collected successfully"
    else
        echo "⚠ Warning: Static files collection failed (non-critical)"
    fi
else
    echo "⊘ Skipping static files collection (COLLECT_STATIC=false)"
fi

# ------------------------------------------------------------------------------
# Create Superuser (Optional - Development/First Run)
# ------------------------------------------------------------------------------
if [ "${CREATE_SUPERUSER:-false}" = "true" ]; then
    echo "========================================"
    echo "Creating superuser..."
    echo "========================================"
    
    python manage.py shell << END
from django.contrib.auth import get_user_model
User = get_user_model()

username = "${DJANGO_SUPERUSER_USERNAME:-admin}"
email = "${DJANGO_SUPERUSER_EMAIL:-admin@example.com}"
password = "${DJANGO_SUPERUSER_PASSWORD:-admin}"

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username=username, email=email, password=password)
    print(f"✓ Superuser '{username}' created successfully")
else:
    print(f"⊘ Superuser '{username}' already exists")
END
fi

# ------------------------------------------------------------------------------
# Database Health Check
# ------------------------------------------------------------------------------
echo "========================================"
echo "Running database health check..."
echo "========================================"

if python manage.py check --database default; then
    echo "✓ Database health check passed"
else
    echo "✗ Database health check failed!"
    exit 1
fi

# ------------------------------------------------------------------------------
# Application Startup
# ------------------------------------------------------------------------------
echo "========================================"
echo "Starting application..."
echo "========================================"
echo "Environment: ${DJANGO_ENV:-production}"
echo "Debug: ${DEBUG:-False}"
echo "========================================"

# Execute the main command (passed as arguments to this script)
exec "$@"
