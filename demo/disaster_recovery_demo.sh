#!/usr/bin/env bash

#############################################################################
# Disaster Recovery Demo - Backup/Restore Workflow
#
# This demo demonstrates the backup and restore capabilities of skill-split,
# showing how to recover from database corruption or data loss.
#
# Value Proposition:
# - Automated timestamped backups with gzip compression
# - Integrity validation during restoration
# - Safe recovery from data corruption
# - Rollback safety with compensating actions
#############################################################################

set -e

DEMO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$DEMO_DIR")"
WORK_DIR="$DEMO_DIR/work"
TEST_DB="$WORK_DIR/test_recovery.db"
BACKUP_DIR="$WORK_DIR/backups"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

echo -e "${BLUE}═════════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Disaster Recovery Demo - Backup/Restore Workflow                ${NC}"
echo -e "${BLUE}═════════════════════════════════════════════════════════════════════${NC}"
echo ""

# Setup work directory
echo -e "${YELLOW}📁 Setting up test environment...${NC}"
rm -rf "$WORK_DIR"
mkdir -p "$BACKUP_DIR"
echo -e "${GREEN}✓ Test directory ready${NC}"
echo ""

# Create test database with sample data
echo -e "${YELLOW}🔧 Creating test database with sample data...${NC}"
cd "$PROJECT_ROOT"

# Store sample file to create database
SAMPLE_FILE="$DEMO_DIR/sample_skill.md"
python3 skill_split.py store "$SAMPLE_FILE" --db "$TEST_DB" > /dev/null 2>&1

# Verify database creation
if [ ! -f "$TEST_DB" ]; then
    echo -e "${RED}Error: Failed to create test database${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Test database created: $TEST_DB${NC}"
echo ""

# Show database statistics
echo -e "${CYAN}Database Statistics:${NC}"
python3 -c "
import sqlite3
conn = sqlite3.connect('$TEST_DB')
cursor = conn.execute('SELECT COUNT(*) FROM files')
files = cursor.fetchone()[0]
cursor = conn.execute('SELECT COUNT(*) FROM sections')
sections = cursor.fetchone()[0]
print(f'  Files: {files}')
print(f'  Sections: {sections}')
conn.close()
"
echo ""

# Step 1: Create backup
echo -e "${MAGENTA}═════════════════════════════════════════════════════════════════════${NC}"
echo -e "${MAGENTA}  Step 1: Creating Backup${NC}"
echo -e "${MAGENTA}═════════════════════════════════════════════════════════════════════${NC}"
echo ""

echo -e "${YELLOW}📦 Creating backup from database...${NC}"
echo ""

# Use backup manager to create backup
python3 -c "
import sys
sys.path.insert(0, '$PROJECT_ROOT')
from core.backup_manager import BackupManager
manager = BackupManager('$BACKUP_DIR')
backup_path = manager.create_backup('$TEST_DB', 'before-disaster')
print(f'✓ Backup created: {backup_path}')
"

echo ""

# List backups
echo -e "${CYAN}Available Backups:${NC}"
python3 -c "
import sys
sys.path.insert(0, '$PROJECT_ROOT')
from core.backup_manager import BackupManager
manager = BackupManager('$BACKUP_DIR')
backups = manager.list_backups()
for backup in backups:
    print(f'  • {backup[\"filename\"]}')
    print(f'    Size: {backup[\"size\"]:,} bytes (uncompressed)')
    print(f'    Compressed: {backup[\"compressed_size\"]:,} bytes')
    if backup['created_at']:
        print(f'    Created: {backup[\"created_at\"]}')
"
echo ""

# Step 2: Simulate disaster
echo -e "${MAGENTA}═════════════════════════════════════════════════════════════════════${NC}"
echo -e "${MAGENTA}  Step 2: Simulating Disaster${NC}"
echo -e "${MAGENTA}═════════════════════════════════════════════════════════════════════${NC}"
echo ""

echo -e "${RED}⚠ Simulating database corruption...${NC}"
echo ""

# Corrupt the database by writing garbage data
dd if=/dev/urandom of="$TEST_DB" bs=1024 count=10 2>/dev/null

echo -e "${RED}✗ Database corrupted!${NC}"
echo ""

# Verify corruption
echo -e "${CYAN}Attempting to access corrupted database...${NC}"
if python3 -c "
import sqlite3
try:
    conn = sqlite3.connect('$TEST_DB')
    conn.execute('SELECT COUNT(*) FROM files')
    print('Database appears OK')
except Exception as e:
    print(f'✗ Error: {e}')
" 2>&1 | grep -q "Error"; then
    echo -e "${GREEN}✓ Corruption detected${NC}"
else
    echo -e "${YELLOW}⚠ Database still accessible (partial corruption)${NC}"
fi
echo ""

# Step 3: Restore from backup
echo -e "${MAGENTA}═════════════════════════════════════════════════════════════════════${NC}"
echo -e "${MAGENTA}  Step 3: Restoring from Backup${NC}"
echo -e "${MAGENTA}═════════════════════════════════════════════════════════════════════${NC}"
echo ""

echo -e "${YELLOW}🔄 Restoring database from backup...${NC}"
echo ""

# Find the backup file
BACKUP_FILE=$(find "$BACKUP_DIR" -name "before-disaster*.sql.gz" | head -1)

if [ -z "$BACKUP_FILE" ]; then
    echo -e "${RED}Error: Backup file not found${NC}"
    exit 1
fi

echo -e "${CYAN}Backup file: $BACKUP_FILE${NC}"
echo ""

# Restore from backup
python3 -c "
import sys
sys.path.insert(0, '$PROJECT_ROOT')
from core.backup_manager import BackupManager, BackupError
manager = BackupManager('$BACKUP_DIR')
try:
    result = manager.restore_backup('$BACKUP_FILE', '$TEST_DB', overwrite=True)
    print(f'✓ Database restored successfully')
    print(f'  Files: {result[\"files_count\"]}')
    print(f'  Sections: {result[\"sections_count\"]}')
    print(f'  FTS5 index: {\"OK\" if result.get(\"fts5_exists\") else \"MISSING\"}')
    print(f'  Integrity check: {\"PASSED\" if result[\"integrity_check_passed\"] else \"FAILED\"}')
except BackupError as e:
    print(f'✗ Restore failed: {e}')
"

echo ""

# Verify restoration
echo -e "${CYAN}Verifying restored database...${NC}"
python3 -c "
import sqlite3
try:
    conn = sqlite3.connect('$TEST_DB')
    cursor = conn.execute('SELECT COUNT(*) FROM files')
    files = cursor.fetchone()[0]
    cursor = conn.execute('SELECT COUNT(*) FROM sections')
    sections = cursor.fetchone()[0]
    print(f'  Files: {files}')
    print(f'  Sections: {sections}')
    print(f'✓ Database is accessible and contains data')
except Exception as e:
    print(f'✗ Error: {e}')
"
echo ""

# Step 4: Validate data integrity
echo -e "${MAGENTA}═════════════════════════════════════════════════════════════════════${NC}"
echo -e "${MAGENTA}  Step 4: Validating Data Integrity${NC}"
echo -e "${MAGENTA}═════════════════════════════════════════════════════════════════════${NC}"
echo ""

echo -e "${YELLOW}🔍 Running integrity checks...${NC}"
echo ""

python3 -c "
import sys
sys.path.insert(0, '$PROJECT_ROOT')
from core.backup_manager import BackupManager
manager = BackupManager('$BACKUP_DIR')
result = manager.validate_integrity('$TEST_DB')
print(f'Integrity check: {\"PASSED\" if result[\"integrity_ok\"] else \"FAILED\"}')
print(f'  Files: {result[\"files_count\"]}')
print(f'  Sections: {result[\"sections_count\"]}')
print(f'  FTS5 exists: {result[\"fts5_exists\"]}')
print(f'  Foreign keys OK: {result[\"foreign_keys_ok\"]}')
"

echo ""

# Test query on restored database
echo -e "${CYAN}Testing queries on restored database...${NC}"
echo ""

SEARCH_RESULT=$(cd "$PROJECT_ROOT" && python3 skill_split.py search "sentiment" --db "$TEST_DB" 2>&1 | head -5)
echo "$SEARCH_RESULT"
echo ""

# Step 5: Test incremental backups
echo -e "${MAGENTA}═════════════════════════════════════════════════════════════════════${NC}"
echo -e "${MAGENTA}  Step 5: Testing Incremental Backups${NC}"
echo -e "${MAGENTA}═════════════════════════════════════════════════════════════════════${NC}"
echo ""

echo -e "${YELLOW}📦 Adding more data and creating second backup...${NC}"
echo ""

# Add another file to the database
TEST_FILE_2="$WORK_DIR/test_skill_2.md"
cat > "$TEST_FILE_2" << 'EOF'
---
name: test-skill-2
description: Second test skill
version: 1.0.0
---

# Test Skill 2

Additional content for backup testing.

## Features

- Feature 1
- Feature 2

## Usage

Usage instructions here.
EOF

python3 skill_split.py store "$TEST_FILE_2" --db "$TEST_DB" > /dev/null 2>&1

# Create second backup
python3 -c "
import sys
sys.path.insert(0, '$PROJECT_ROOT')
from core.backup_manager import BackupManager
manager = BackupManager('$BACKUP_DIR')
backup_path = manager.create_backup('$TEST_DB', 'after-additions')
print(f'✓ Second backup created: {backup_path}')
"

echo ""

# Show all backups
echo -e "${CYAN}All Backups:${NC}"
python3 -c "
import sys
sys.path.insert(0, '$PROJECT_ROOT')
from core.backup_manager import BackupManager
manager = BackupManager('$BACKUP_DIR')
backups = manager.list_backups()
for i, backup in enumerate(backups, 1):
    print(f'{i}. {backup[\"filename\"]}')
    print(f'   Files: {backup[\"size\"]:,} bytes (uncompressed)')
    print(f'   Created: {backup[\"created_at\"]}')
"

echo ""

# Summary
echo -e "${BLUE}═════════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  DISASTER RECOVERY SUMMARY${NC}"
echo -e "${BLUE}═════════════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${CYAN}Backup Features:${NC}"
echo "  ✓ Automated timestamped backups"
echo "  ✓ Gzip compression for space efficiency"
echo "  ✓ SQL dump format for portability"
echo "  ✓ Multiple backup versions supported"
echo ""
echo -e "${CYAN}Restore Features:${NC}"
echo "  ✓ Integrity validation during restoration"
echo "  ✓ FTS5 index recreation"
echo "  ✓ Foreign key verification"
echo "  ✓ Safe overwrite with confirmation"
echo ""
echo -e "${CYAN}Workflow:${NC}"
echo "  1. Create regular backups (cron job recommended)"
echo "  2. Store backups in secure location"
echo "  3. When disaster occurs, identify latest good backup"
echo "  4. Restore with integrity validation"
echo "  5. Verify data access and queries"
echo ""
echo -e "${CYAN}Best Practices:${NC}"
echo "  • Schedule automated daily backups"
echo "  • Store backups off-site or in cloud storage"
echo "  • Test restore procedures regularly"
echo "  • Keep multiple backup generations"
echo "  • Monitor backup file sizes for anomalies"
echo ""
echo -e "${BLUE}═════════════════════════════════════════════════════════════════════${NC}"
