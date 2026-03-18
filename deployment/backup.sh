#!/bin/bash
# ==============================================================================
# NEF Cadência - Database Backup Script
# ==============================================================================
# Creates backups of the PostgreSQL database
# Can be run manually or via cron
# ==============================================================================

set -e

# ------------------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------------------
DB_NAME="nef_cadencia_prod"
DB_USER="nef_cadencia"
BACKUP_DIR="/var/backups/nef-cadencia"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DATE=$(date +%Y-%m-%d)

# Retention settings
DAILY_RETENTION=7    # Keep 7 daily backups
WEEKLY_RETENTION=4   # Keep 4 weekly backups
MONTHLY_RETENTION=6  # Keep 6 monthly backups

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# ------------------------------------------------------------------------------
# Create backup directories
# ------------------------------------------------------------------------------
mkdir -p "$BACKUP_DIR/daily"
mkdir -p "$BACKUP_DIR/weekly"
mkdir -p "$BACKUP_DIR/monthly"

# ------------------------------------------------------------------------------
# Determine backup type
# ------------------------------------------------------------------------------
DAY_OF_WEEK=$(date +%u)  # 1-7 (Monday-Sunday)
DAY_OF_MONTH=$(date +%d)

if [ "$DAY_OF_MONTH" = "01" ]; then
    BACKUP_TYPE="monthly"
    BACKUP_SUBDIR="$BACKUP_DIR/monthly"
    RETENTION=$MONTHLY_RETENTION
elif [ "$DAY_OF_WEEK" = "7" ]; then
    BACKUP_TYPE="weekly"
    BACKUP_SUBDIR="$BACKUP_DIR/weekly"
    RETENTION=$WEEKLY_RETENTION
else
    BACKUP_TYPE="daily"
    BACKUP_SUBDIR="$BACKUP_DIR/daily"
    RETENTION=$DAILY_RETENTION
fi

# ------------------------------------------------------------------------------
# Create database backup
# ------------------------------------------------------------------------------
echo "========================================"
echo "NEF Cadência - Database Backup"
echo "========================================"
echo "Type: $BACKUP_TYPE"
echo "Date: $DATE"
echo ""

BACKUP_FILE="$BACKUP_SUBDIR/db_${BACKUP_TYPE}_${TIMESTAMP}.sql"
BACKUP_FILE_GZ="${BACKUP_FILE}.gz"

echo "Creating database backup..."

# Dump database
if sudo -u postgres pg_dump "$DB_NAME" > "$BACKUP_FILE"; then
    echo -e "${GREEN}✓ Database dumped${NC}"
else
    echo -e "${RED}✗ Database dump failed${NC}"
    exit 1
fi

# Compress backup
echo "Compressing backup..."
gzip "$BACKUP_FILE"

# Get backup size
BACKUP_SIZE=$(du -h "$BACKUP_FILE_GZ" | cut -f1)

echo -e "${GREEN}✓ Backup created: $BACKUP_FILE_GZ${NC}"
echo "Size: $BACKUP_SIZE"

# ------------------------------------------------------------------------------
# Verify backup
# ------------------------------------------------------------------------------
echo "Verifying backup..."

if gunzip -t "$BACKUP_FILE_GZ"; then
    echo -e "${GREEN}✓ Backup verified${NC}"
else
    echo -e "${RED}✗ Backup verification failed${NC}"
    exit 1
fi

# ------------------------------------------------------------------------------
# Backup media files (optional)
# ------------------------------------------------------------------------------
MEDIA_DIR="/opt/nef-cadencia/media"

if [ -d "$MEDIA_DIR" ] && [ "$(ls -A $MEDIA_DIR)" ]; then
    echo "Backing up media files..."
    
    MEDIA_BACKUP="$BACKUP_SUBDIR/media_${BACKUP_TYPE}_${TIMESTAMP}.tar.gz"
    
    tar -czf "$MEDIA_BACKUP" -C "/opt/nef-cadencia" media/
    
    MEDIA_SIZE=$(du -h "$MEDIA_BACKUP" | cut -f1)
    echo -e "${GREEN}✓ Media backup created: $MEDIA_BACKUP${NC}"
    echo "Size: $MEDIA_SIZE"
fi

# ------------------------------------------------------------------------------
# Cleanup old backups
# ------------------------------------------------------------------------------
echo "Cleaning up old backups..."

# Remove old daily backups
if [ -d "$BACKUP_DIR/daily" ]; then
    find "$BACKUP_DIR/daily" -name "db_daily_*.sql.gz" -mtime +$DAILY_RETENTION -delete
    find "$BACKUP_DIR/daily" -name "media_daily_*.tar.gz" -mtime +$DAILY_RETENTION -delete
fi

# Remove old weekly backups
if [ -d "$BACKUP_DIR/weekly" ]; then
    find "$BACKUP_DIR/weekly" -name "db_weekly_*.sql.gz" -mtime +$((WEEKLY_RETENTION * 7)) -delete
    find "$BACKUP_DIR/weekly" -name "media_weekly_*.tar.gz" -mtime +$((WEEKLY_RETENTION * 7)) -delete
fi

# Remove old monthly backups
if [ -d "$BACKUP_DIR/monthly" ]; then
    find "$BACKUP_DIR/monthly" -name "db_monthly_*.sql.gz" -mtime +$((MONTHLY_RETENTION * 30)) -delete
    find "$BACKUP_DIR/monthly" -name "media_monthly_*.tar.gz" -mtime +$((MONTHLY_RETENTION * 30)) -delete
fi

echo -e "${GREEN}✓ Old backups cleaned${NC}"

# ------------------------------------------------------------------------------
# Summary
# ------------------------------------------------------------------------------
echo ""
echo "========================================"
echo -e "${GREEN}Backup Complete${NC}"
echo "========================================"
echo ""
echo "Backup Details:"
echo "  Type: $BACKUP_TYPE"
echo "  Database: $BACKUP_FILE_GZ ($BACKUP_SIZE)"
if [ -f "$MEDIA_BACKUP" ]; then
    echo "  Media: $MEDIA_BACKUP ($MEDIA_SIZE)"
fi
echo ""
echo "Retention Policy:"
echo "  Daily: $DAILY_RETENTION days"
echo "  Weekly: $WEEKLY_RETENTION weeks"
echo "  Monthly: $MONTHLY_RETENTION months"
echo ""
echo "Backup Location: $BACKUP_DIR"
echo ""

# ------------------------------------------------------------------------------
# Optional: Upload to remote storage
# ------------------------------------------------------------------------------
# Uncomment and configure for remote backup (S3, rsync, etc.)
#
# echo "Uploading to remote storage..."
# aws s3 cp "$BACKUP_FILE_GZ" s3://your-bucket/backups/nef-cadencia/
# echo -e "${GREEN}✓ Uploaded to S3${NC}"
