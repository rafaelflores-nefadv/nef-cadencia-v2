#!/bin/bash
# ==============================================================================
# NEF Cadência - Production Cleanup Script
# ==============================================================================
# This script removes temporary files, cache, and development artifacts
# Run before creating production deployment artifact
# ==============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}NEF Cadência - Production Cleanup${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Counters
REMOVED_FILES=0
REMOVED_DIRS=0

# ==============================================================================
# 1. Remove Temporary Files
# ==============================================================================
echo -e "${BLUE}1. Removing temporary files...${NC}"

# tmp_* files
TMP_COUNT=$(find . -name "tmp_*" -type f 2>/dev/null | wc -l)
if [ "$TMP_COUNT" -gt 0 ]; then
    find . -name "tmp_*" -type f -delete 2>/dev/null
    echo -e "${GREEN}  ✓ Removed $TMP_COUNT tmp_* files${NC}"
    REMOVED_FILES=$((REMOVED_FILES + TMP_COUNT))
else
    echo -e "${YELLOW}  ⊘ No tmp_* files found${NC}"
fi

# temp_* files
TEMP_COUNT=$(find . -name "temp_*" -type f 2>/dev/null | wc -l)
if [ "$TEMP_COUNT" -gt 0 ]; then
    find . -name "temp_*" -type f -delete 2>/dev/null
    echo -e "${GREEN}  ✓ Removed $TEMP_COUNT temp_* files${NC}"
    REMOVED_FILES=$((REMOVED_FILES + TEMP_COUNT))
else
    echo -e "${YELLOW}  ⊘ No temp_* files found${NC}"
fi

# *.tmp files
TMP_EXT_COUNT=$(find . -name "*.tmp" -type f 2>/dev/null | wc -l)
if [ "$TMP_EXT_COUNT" -gt 0 ]; then
    find . -name "*.tmp" -type f -delete 2>/dev/null
    echo -e "${GREEN}  ✓ Removed $TMP_EXT_COUNT *.tmp files${NC}"
    REMOVED_FILES=$((REMOVED_FILES + TMP_EXT_COUNT))
else
    echo -e "${YELLOW}  ⊘ No *.tmp files found${NC}"
fi

# ==============================================================================
# 2. Remove Python Cache
# ==============================================================================
echo ""
echo -e "${BLUE}2. Removing Python cache...${NC}"

# *.pyc files
PYC_COUNT=$(find . -name "*.pyc" -type f 2>/dev/null | wc -l)
if [ "$PYC_COUNT" -gt 0 ]; then
    find . -name "*.pyc" -type f -delete 2>/dev/null
    echo -e "${GREEN}  ✓ Removed $PYC_COUNT *.pyc files${NC}"
    REMOVED_FILES=$((REMOVED_FILES + PYC_COUNT))
else
    echo -e "${YELLOW}  ⊘ No *.pyc files found${NC}"
fi

# *.pyo files
PYO_COUNT=$(find . -name "*.pyo" -type f 2>/dev/null | wc -l)
if [ "$PYO_COUNT" -gt 0 ]; then
    find . -name "*.pyo" -type f -delete 2>/dev/null
    echo -e "${GREEN}  ✓ Removed $PYO_COUNT *.pyo files${NC}"
    REMOVED_FILES=$((REMOVED_FILES + PYO_COUNT))
else
    echo -e "${YELLOW}  ⊘ No *.pyo files found${NC}"
fi

# __pycache__ directories
PYCACHE_COUNT=$(find . -type d -name "__pycache__" 2>/dev/null | wc -l)
if [ "$PYCACHE_COUNT" -gt 0 ]; then
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    echo -e "${GREEN}  ✓ Removed $PYCACHE_COUNT __pycache__ directories${NC}"
    REMOVED_DIRS=$((REMOVED_DIRS + PYCACHE_COUNT))
else
    echo -e "${YELLOW}  ⊘ No __pycache__ directories found${NC}"
fi

# .pytest_cache directories
PYTEST_COUNT=$(find . -type d -name ".pytest_cache" 2>/dev/null | wc -l)
if [ "$PYTEST_COUNT" -gt 0 ]; then
    find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
    echo -e "${GREEN}  ✓ Removed $PYTEST_COUNT .pytest_cache directories${NC}"
    REMOVED_DIRS=$((REMOVED_DIRS + PYTEST_COUNT))
else
    echo -e "${YELLOW}  ⊘ No .pytest_cache directories found${NC}"
fi

# ==============================================================================
# 3. Remove Log Files
# ==============================================================================
echo ""
echo -e "${BLUE}3. Removing log files...${NC}"

LOG_COUNT=$(find . -name "*.log" -type f 2>/dev/null | wc -l)
if [ "$LOG_COUNT" -gt 0 ]; then
    find . -name "*.log" -type f -delete 2>/dev/null
    echo -e "${GREEN}  ✓ Removed $LOG_COUNT *.log files${NC}"
    REMOVED_FILES=$((REMOVED_FILES + LOG_COUNT))
else
    echo -e "${YELLOW}  ⊘ No *.log files found${NC}"
fi

# ==============================================================================
# 4. Remove SQLite Databases
# ==============================================================================
echo ""
echo -e "${BLUE}4. Removing SQLite databases...${NC}"

SQLITE_COUNT=$(find . -name "*.sqlite3" -type f 2>/dev/null | wc -l)
if [ "$SQLITE_COUNT" -gt 0 ]; then
    find . -name "*.sqlite3" -type f -delete 2>/dev/null
    echo -e "${GREEN}  ✓ Removed $SQLITE_COUNT *.sqlite3 files${NC}"
    REMOVED_FILES=$((REMOVED_FILES + SQLITE_COUNT))
else
    echo -e "${YELLOW}  ⊘ No *.sqlite3 files found${NC}"
fi

DB_COUNT=$(find . -name "*.db" -type f 2>/dev/null | wc -l)
if [ "$DB_COUNT" -gt 0 ]; then
    find . -name "*.db" -type f -delete 2>/dev/null
    echo -e "${GREEN}  ✓ Removed $DB_COUNT *.db files${NC}"
    REMOVED_FILES=$((REMOVED_FILES + DB_COUNT))
else
    echo -e "${YELLOW}  ⊘ No *.db files found${NC}"
fi

# ==============================================================================
# 5. Remove Coverage Files
# ==============================================================================
echo ""
echo -e "${BLUE}5. Removing coverage files...${NC}"

if [ -f ".coverage" ]; then
    rm -f .coverage
    echo -e "${GREEN}  ✓ Removed .coverage${NC}"
    REMOVED_FILES=$((REMOVED_FILES + 1))
else
    echo -e "${YELLOW}  ⊘ No .coverage file found${NC}"
fi

if [ -d "htmlcov" ]; then
    rm -rf htmlcov
    echo -e "${GREEN}  ✓ Removed htmlcov/ directory${NC}"
    REMOVED_DIRS=$((REMOVED_DIRS + 1))
else
    echo -e "${YELLOW}  ⊘ No htmlcov/ directory found${NC}"
fi

# ==============================================================================
# 6. Remove Node Modules (optional)
# ==============================================================================
echo ""
echo -e "${BLUE}6. Checking node_modules...${NC}"

if [ -d "node_modules" ]; then
    echo -e "${YELLOW}  ⚠ node_modules/ found (not removing - needed for build)${NC}"
    echo -e "${YELLOW}    If you want to remove it, run: rm -rf node_modules${NC}"
else
    echo -e "${YELLOW}  ⊘ No node_modules/ directory found${NC}"
fi

# ==============================================================================
# 7. Remove Virtual Environment (optional)
# ==============================================================================
echo ""
echo -e "${BLUE}7. Checking virtual environment...${NC}"

if [ -d ".venv" ] || [ -d "venv" ]; then
    echo -e "${YELLOW}  ⚠ Virtual environment found (not removing - needed for development)${NC}"
    echo -e "${YELLOW}    If you want to remove it, run: rm -rf .venv venv${NC}"
else
    echo -e "${YELLOW}  ⊘ No virtual environment found${NC}"
fi

# ==============================================================================
# 8. Verify .env is not in git
# ==============================================================================
echo ""
echo -e "${BLUE}8. Verifying .env security...${NC}"

if git ls-files | grep -q "^\.env$"; then
    echo -e "${RED}  ✗ WARNING: .env is tracked by git!${NC}"
    echo -e "${RED}    Run: git rm --cached .env${NC}"
else
    echo -e "${GREEN}  ✓ .env is not tracked by git${NC}"
fi

# ==============================================================================
# Summary
# ==============================================================================
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Cleanup Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${GREEN}Files removed: $REMOVED_FILES${NC}"
echo -e "${GREEN}Directories removed: $REMOVED_DIRS${NC}"
echo ""
echo "Cleaned categories:"
echo "  ✓ Temporary files (tmp_*, temp_*, *.tmp)"
echo "  ✓ Python cache (*.pyc, *.pyo, __pycache__)"
echo "  ✓ Log files (*.log)"
echo "  ✓ SQLite databases (*.sqlite3, *.db)"
echo "  ✓ Coverage files (.coverage, htmlcov/)"
echo ""
echo -e "${GREEN}Cleanup completed successfully!${NC}"
echo ""
echo "Next steps:"
echo "  1. Review changes: git status"
echo "  2. Run tests: pytest"
echo "  3. Create deployment artifact"
echo ""
