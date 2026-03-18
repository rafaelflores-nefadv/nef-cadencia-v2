#!/bin/bash
# ==============================================================================
# NEF Cadência - Restart Script
# ==============================================================================
# Quick restart of the application services
# ==============================================================================

set -e

echo "========================================"
echo "NEF Cadência - Restarting Services"
echo "========================================"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Please run as root or with sudo${NC}"
    exit 1
fi

# ------------------------------------------------------------------------------
# Restart Gunicorn
# ------------------------------------------------------------------------------
echo "Restarting Gunicorn..."

systemctl restart nef-cadencia

# Wait for service to start
sleep 2

if systemctl is-active --quiet nef-cadencia; then
    echo -e "${GREEN}✓ Gunicorn restarted successfully${NC}"
else
    echo -e "${RED}✗ Gunicorn failed to restart${NC}"
    systemctl status nef-cadencia --no-pager
    exit 1
fi

# ------------------------------------------------------------------------------
# Reload Nginx
# ------------------------------------------------------------------------------
echo "Reloading Nginx..."

nginx -t && systemctl reload nginx

if systemctl is-active --quiet nginx; then
    echo -e "${GREEN}✓ Nginx reloaded successfully${NC}"
else
    echo -e "${RED}✗ Nginx failed to reload${NC}"
    systemctl status nginx --no-pager
    exit 1
fi

# ------------------------------------------------------------------------------
# Health Check
# ------------------------------------------------------------------------------
echo "Running health check..."

sleep 3

if curl -f http://localhost/health/ > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Application is healthy${NC}"
else
    echo -e "${YELLOW}⚠ Health check failed${NC}"
fi

# ------------------------------------------------------------------------------
# Summary
# ------------------------------------------------------------------------------
echo ""
echo "========================================"
echo -e "${GREEN}Services Restarted${NC}"
echo "========================================"
echo ""
echo "Status:"
systemctl status nef-cadencia --no-pager -l | head -n 5
echo ""
echo "Recent logs:"
journalctl -u nef-cadencia -n 10 --no-pager
echo ""
