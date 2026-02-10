#!/usr/bin/env bash
#
# skill-split Database Backup Script
#
# Usage:
#   ./scripts/backup_database.sh [output_directory]
#

set -euo pipefail

# Configuration
DB_PATH="${SKILL_SPLIT_DB:-./skill_split.db}"
BACKUP_DIR="${1:-./backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/skill_split_${TIMESTAMP}.db"
RETENTION_DAYS=30

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if database exists
check_database() {
    if [ ! -f "$DB_PATH" ]; then
        log_error "Database not found: $DB_PATH"
        exit 1
    fi
}

# Create backup directory
create_backup_dir() {
    if [ ! -d "$BACKUP_DIR" ]; then
        log_info "Creating backup directory: $BACKUP_DIR"
        mkdir -p "$BACKUP_DIR"
    fi
}

# Get database size
get_db_size() {
    local size=$(du -h "$DB_PATH" | cut -f1)
    echo "$size"
}

# Create backup
create_backup() {
    log_info "Creating backup: $BACKUP_FILE"

    # Use sqlite3 backup for online backup
    sqlite3 "$DB_PATH" ".backup '$BACKUP_FILE'"

    if [ $? -eq 0 ]; then
        log_info "✅ Backup created successfully ($(get_db_size))"
    else
        log_error "Backup failed"
        exit 1
    fi
}

# Verify backup
verify_backup() {
    log_info "Verifying backup..."

    if sqlite3 "$BACKUP_FILE" "PRAGMA integrity_check;" > /dev/null 2>&1; then
        log_info "✅ Backup verified"
    else
        log_error "Backup verification failed"
        exit 1
    fi
}

# Compress backup
compress_backup() {
    log_info "Compressing backup..."
    gzip "$BACKUP_FILE"
    BACKUP_FILE="${BACKUP_FILE}.gz"
    log_info "✅ Compressed: $(du -h "$BACKUP_FILE" | cut -f1)"
}

# Clean old backups
cleanup_old_backups() {
    log_info "Cleaning backups older than $RETENTION_DAYS days..."

    local count=$(find "$BACKUP_DIR" -name "skill_split_*.db.gz" -mtime +"$RETENTION_DAYS" | wc -l)

    if [ "$count" -gt 0 ]; then
        find "$BACKUP_DIR" -name "skill_split_*.db.gz" -mtime +"$RETENTION_DAYS" -delete
        log_info "✅ Removed $count old backup(s)"
    else
        log_info "No old backups to remove"
    fi
}

# List backups
list_backups() {
    log_info "Current backups:"
    echo ""
    find "$BACKUP_DIR" -name "skill_split_*.db.gz" -type f -printf "%T+ %s\n" | \
        sort -r | \
        while read -r timestamp size; do
            local human_size=$(numfmt --to=si --suffix=B "$size")
            local filename=$(find "$BACKUP_DIR" -name "skill_split_*.db.gz" -newermt "$timestamp" -ls | awk '{print $11}')
            local basename=$(basename "$filename")
            echo "  $basename ($human_size)"
        done
}

# Main function
main() {
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  skill-split Database Backup"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    log_info "Database: $DB_PATH"
    log_info "Output: $BACKUP_DIR"
    log_info "Retention: $RETENTION_DAYS days"
    echo ""

    check_database
    create_backup_dir
    create_backup
    verify_backup
    compress_backup
    cleanup_old_backups
    list_backups

    echo ""
    log_info "✅ Backup complete!"
    echo "   File: $BACKUP_FILE"
}

# Run main
main "$@"
