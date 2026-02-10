# CLI Backup/Restore Documentation Research

**Phase**: 07-documentation_gaps
**Research Date**: 2026-02-10
**Purpose**: Inform documentation structure for backup/restore commands in skill-split

---

## Executive Summary

Research on CLI backup/restore documentation best practices reveals clear patterns for disaster recovery documentation. The backup/restore feature (Phase 05) is fully implemented but lacks user-facing documentation. This research identifies optimal documentation structure, examples, and best practices for making these capabilities accessible to users.

---

## 1. Current Documentation Patterns in skill-split

### 1.1 Established Documentation Structure

Based on analysis of existing documentation:

**README.md** - Main project documentation
- Installation and quick start
- Feature overview with use cases
- Basic command examples
- Architecture overview

**EXAMPLES.md** - Practical scenarios
- Search workflows (finding, exact phrase, narrowing)
- Progressive disclosure workflows (loading, navigation)
- Component handler workflows (plugins, hooks, configs)
- Real-world scenarios with before/after comparisons

**docs/CLI_REFERENCE.md** - Complete command reference
- Command name and syntax
- Description
- Arguments and options
- Exit codes
- Examples with realistic output

**COMPONENT_HANDLERS.md** - Feature-specific guide
- Overview of component types
- Usage examples
- Validation procedures
- Troubleshooting section
- API documentation
- Best practices

### 1.2 Documentation Style Patterns

From `.planning/phases/07-documentation_gaps/07-STYLE.md`:

**Section Flow Pattern**:
1. Problem Statement
2. Solution Overview
3. Step-by-Step Implementation
4. Examples
5. Benefits
6. Related Commands/Features

**Command Reference Format**:
- Command syntax with bash code block
- Clear one-line description
- Arguments with types
- Options with descriptions
- Exit codes
- Multiple examples with realistic output

**Cross-Referencing**:
- Internal links to related documentation
- "Related Commands" sections
- "See Also" sections with specific links

---

## 2. Industry Best Practices for CLI Backup/Restore Documentation

### 2.1 Sources Referenced

Based on web research of industry-standard CLI tools:

- **[TiDB BR Command-line Tool](https://docs.pingcap.com/tidb/v5.4/use-br-command-line-tool/)** - Enterprise database backup/restore
- **[Couchbase CLI Backup/Restore](https://docs.couchbase.com/cloud/clusters/cli-backup-restore.html)** - NoSQL database backup management
- **[IBM Cloud Pak for Data - cpd-cli backup-restore](https://www.ibm.com/docs/en/software-hub/5.1.x?topic=reference-backup-restore)** - Enterprise data backup utility
- **[Clibato - CLI Backup Tool](https://jigarius.com/blog/clibato-cli-backup-tool)** - Python CLI backup implementation example
- **[Rafay KOP CLI - Backup and Restore](https://docs.rafay.co/cli/backup_cli/)** - Cloud platform backup operations

### 2.2 Key Best Practices Identified

#### 2.2.1 Command Structure
- **Clear, intuitive naming**: `backup`, `restore`, `list-backups`
- **Consistent argument patterns**: Positional arguments for required values, flags for options
- **Help text**: Comprehensive `--help` output with examples

#### 2.2.2 Safety Features (Critical for disaster recovery)
- **Pre-flight validation**: Verify database exists before backup
- **Overwrite protection**: Require explicit `--overwrite` flag for restore
- **Confirmation prompts**: Warn before destructive operations
- **Backup validation**: Verify backup integrity after creation
- **Restore validation**: Verify database integrity after restore

#### 2.2.3 Documentation Elements
- **When to use**: Clear guidance on backup frequency and timing
- **What gets backed up**: List of all tables, indexes, and data
- **Restore scenarios**: Different recovery situations (full, partial, testing)
- **Troubleshooting**: Common errors and solutions
- **Automated backups**: Cron job examples for scheduled backups

#### 2.2.4 Output Information
- **Progress indicators**: Show operation progress
- **Completion confirmation**: Clear success/failure messages
- **Statistics**: File sizes, record counts, compression ratios
- **Integrity status**: Verification results

---

## 3. skill-split Backup/Restore Implementation Analysis

### 3.1 Current Implementation (Phase 05 Complete)

**File**: `core/backup_manager.py`

**Key Features**:
- Timestamped gzip-compressed SQL dumps
- Complete database backup (files, sections, FTS5 indexes)
- Integrity validation using PRAGMA integrity_check
- Foreign key constraint verification
- List available backups with metadata
- Overwrite protection with explicit flag

**CLI Commands**:
```bash
./skill_split.py backup [--db <path>] [--filename <name>]
./skill_split.py restore <backup_file> [--db <path>] [--overwrite]
```

**Backup Location**: `~/.claude/backups/` (default)

**Backup Format**: `skill-split-YYYYMMDD-HHMMSS.sql.gz`

### 3.2 Implementation Highlights

**Safety Features**:
- Validates database before backup
- Requires `--overwrite` flag to restore over existing database
- Runs PRAGMA integrity_check after restore
- Tests foreign key enforcement
- Validates FTS5 virtual table recreation

**Statistics Provided**:
- Records restored (files + sections count)
- Tables restored
- Integrity check status
- FTS5 index status
- Foreign key status

---

## 4. Recommended Documentation Structure

### 4.1 Primary Documentation Location

**Add to README.md** - New section before "Supabase Integration"

```markdown
## Backup and Restore

Protect your skill database with automated backups and restore functionality.

### Why Back Up Matter

Your skill-split database contains parsed sections from your skills, commands, and references. Regular backups protect against:
- Database corruption
- Accidental data loss
- Migration between machines
- Testing and development

### Quick Backup

```bash
# Create timestamped backup
./skill_split.py backup

# Output
Backup created: ~/.claude/backups/skill-split-20260210-143052.sql.gz
Size: 2.1 MB (compressed: 156 KB)
Files: 1,365
Sections: 19,207
```

### Quick Restore

```bash
# Restore from backup (requires --overwrite to replace existing)
./skill_split.py restore ~/.claude/backups/skill-split-20260210-143052.sql.gz --overwrite

# Output
Database restored: ~/.claude/databases/skill-split.db
Files: 1,365
Sections: 19,207
FTS5 index: OK
Integrity check: PASSED
```

### See Also

- [CLI Reference - backup](docs/CLI_REFERENCE.md#backup) - Complete command options
- [CLI Reference - restore](docs/CLI_REFERENCE.md#restore) - Complete restore options
- [EXAMPLES.md - Backup Workflows](EXAMPLES.md#backup-workflows) - Real-world scenarios
```

### 4.2 CLI_REFERENCE.md Addition

Add new commands to `docs/CLI_REFERENCE.md` after `verify` and before `tree`:

```markdown
### backup

Create a timestamped backup of the skill-split database.

```bash
./skill_split.py backup [--db <path>] [--filename <name>]
```

**Description**: Create a gzip-compressed SQL dump of the database with integrity validation.

**Options**:
- `--db <path>`: Database path to backup (default: `~/.claude/databases/skill-split.db`)
- `--filename <name>`: Custom backup filename (default: auto-generated timestamp)

**Exit Codes**:
- `0`: Backup created successfully
- `1`: Backup failed (database not found, not readable, or write error)

**Examples**:
```bash
# Create timestamped backup
./skill_split.py backup

# Backup specific database
./skill_split.py backup --db /custom/path/database.db

# Custom filename
./skill_split.py backup --filename my-backup
```

**What Gets Backed Up**:
- All files (skills, commands, references, components)
- All sections with metadata
- FTS5 full-text search indexes
- Foreign key constraints
- SHA256 hashes for integrity verification

**Output**:
```
Backup created: ~/.claude/backups/skill-split-20260210-143052.sql.gz
Size: 2.1 MB (compressed: 156 KB)
Compression ratio: 13.5x
```

---

### restore

Restore a database from a backup file with integrity validation.

```bash
./skill_split.py restore <backup_file> [--db <path>] [--overwrite]
```

**Description**: Restore database from gzip-compressed SQL dump. Validates integrity after restoration.

**Arguments**:
- `backup_file`: Path to backup file (.sql.gz)

**Options**:
- `--db <path>`: Target database path (default: `~/.claude/databases/skill-split.db`)
- `--overwrite`: Overwrite existing database (required if target exists)

**Exit Codes**:
- `0`: Restore successful
- `1`: Restore failed (invalid backup, integrity check failed, or target exists without --overwrite)

**Examples**:
```bash
# Restore to default location
./skill_split.py restore ~/.claude/backups/skill-split-20260210-143052.sql.gz

# Restore to custom location
./skill_split.py restore backup.sql.gz --db /tmp/test.db

# Overwrite existing database
./skill_split.py restore backup.sql.gz --overwrite
```

**Safety Features**:
- Requires `--overwrite` flag to replace existing database
- Validates backup file format before restore
- Runs PRAGMA integrity_check after restore
- Verifies FTS5 indexes recreated
- Tests foreign key constraints

**Output**:
```
Database restored: ~/.claude/databases/skill-split.db
Files: 1,365
Sections: 19,207
FTS5 index: OK
Integrity check: PASSED
Foreign keys: OK
```

**Warning**: Restoring over an existing database requires explicit `--overwrite` flag.
```

### 4.3 EXAMPLES.md New Section

Add new section after "Combined Search + Navigation Workflow":

```markdown
## Backup and Restore Workflows

### Scenario 1: Regular Backup Routine

**Use Case**: Protect your skill database with regular automated backups.

**Problem**: You've invested time building a comprehensive skill library. Database corruption or accidental deletion would lose all that work.

**Solution**: Set up automated backups with cron.

**Commands**:

```bash
# Manual backup (create after major changes)
./skill_split.py backup

# Output
Backup created: ~/.claude/backups/skill-split-20260210-143052.sql.gz
Size: 2.1 MB (compressed: 156 KB)
Files: 1,365
Sections: 19,207

# Automated daily backup (add to crontab)
crontab -e

# Add this line for daily backup at 2 AM
0 2 * * * /path/to/skill_split.py backup

# Weekly backup with retention script
0 2 * * 0 /path/to/skill_split.py backup && find ~/.claude/backups/ -name "skill-split-*.sql.gz" -mtime +30 -delete
```

**Benefits**:
- **Disaster recovery**: Restore from backup if database corrupted
- **Version history**: Keep multiple backups for rollback options
- **Migration**: Transfer database between machines
- **Testing**: Restore to test database for experiments

---

### Scenario 2: Disaster Recovery

**Use Case**: Restore database after corruption or data loss.

**Problem**: Database becomes corrupted or accidentally deleted. All skills and sections are inaccessible.

**Solution**: Restore from recent backup with integrity validation.

**Commands**:

```bash
# Identify corruption
./skill_split.py search "test query"
Error: database disk image is malformed

# List available backups (manual: ls ~/.claude/backups/)
ls -lt ~/.claude/backups/

# Output
-rw-r--r-- 1 user group 156K Feb 10 14:30 skill-split-20260210-143052.sql.gz
-rw-r--r-- 1 user group 155K Feb  9 02:00 skill-split-20260209-020000.sql.gz

# Restore from most recent backup
./skill_split.py restore ~/.claude/backups/skill-split-20260210-143052.sql.gz --overwrite

# Output
Database restored: ~/.claude/databases/skill-split.db
Files: 1,365
Sections: 19,207
FTS5 index: OK
Integrity check: PASSED
Foreign keys: OK

# Verify restored database
./skill_split.py search "test query"

# Output
Found 5 section(s) matching 'test query':
...
```

**Benefits**:
- **Quick recovery**: Restore entire database in seconds
- **Integrity verified**: PRAGMA integrity_check confirms restore success
- **Data preserved**: All sections, FTS5 indexes, and hashes intact
- **Validation**: Foreign key constraints verified after restore

---

### Scenario 3: Database Migration

**Use Case**: Transfer skill database to new machine or user account.

**Problem**: Setting up a new development machine and need to transfer existing skill library.

**Solution**: Backup on source machine, restore on destination.

**Commands**:

```bash
# On source machine: create backup
./skill_split.py backup

# Output
Backup created: /Users/olduser/.claude/backups/skill-split-20260210-143052.sql.gz
Size: 2.1 MB (compressed: 156 KB)

# Transfer backup to new machine (via scp, cloud storage, etc.)
scp ~/.claude/backups/skill-split-20260210-143052.sql.gz newmachine:/tmp/

# On destination machine: restore from backup
./skill_split.py restore /tmp/skill-split-20260210-143052.sql.gz

# Output
Database restored: /Users/newuser/.claude/databases/skill-split.db
Files: 1,365
Sections: 19,207
FTS5 index: OK
Integrity check: PASSED

# Verify migration
./skill_split.py search "python"
./skill_split.py list ~/.claude/skills/my-skill.md
```

**Benefits**:
- **Complete transfer**: All skills, commands, and references preserved
- **Portable format**: Single compressed SQL file transfers easily
- **Cross-platform**: Works on any platform with Python and SQLite
- **Verified integrity**: Hash validation ensures no data loss

---

### Scenario 4: Testing with Restored Database

**Use Case**: Test destructive operations on a copy of the database.

**Problem**: Want to test database operations without risking production data.

**Solution**: Restore backup to test database for experiments.

**Commands**:

```bash
# Create test database from backup
./skill_split.py restore ~/.claude/backups/skill-split-20260210-143052.sql.gz --db /tmp/test.db

# Output
Database restored: /tmp/test.db
Files: 1,365
Sections: 19,207
FTS5 index: OK
Integrity check: PASSED

# Run tests on test database
./skill_split.py search "query" --db /tmp/test.db
./skill_split.py list ~/.claude/skills/test.md --db /tmp/test.db

# Test destructive operations
./skill_split.py store test-file.md --db /tmp/test.db

# Clean up test database when done
rm /tmp/test.db

# Production database untouched
./skill_split.py search "query"
```

**Benefits**:
- **Safe experimentation**: Test without affecting production data
- **Isolated environment**: Separate database for testing
- **Quick setup**: Restore test database in seconds
- **Easy cleanup**: Delete test database when done

---

### Scenario 5: Backup Before Major Changes

**Use Case**: Create backup checkpoint before making significant changes.

**Problem**: Planning to bulk ingest many skills or run database maintenance. Want rollback option if something goes wrong.

**Solution**: Create pre-change backup with descriptive filename.

**Commands**:

```bash
# Create backup before bulk operations
./skill_split.py backup --filename before-bulk-ingest

# Output
Backup created: ~/.claude/backups/before-bulk-ingest.sql.gz
Size: 2.1 MB (compressed: 156 KB)

# Perform bulk operations
./skill_split.py ingest ~/.claude/new-skills/

# If problems occur, restore pre-change backup
./skill_split.py restore ~/.claude/backups/before-bulk-ingest.sql.gz --overwrite

# Output
Database restored: ~/.claude/databases/skill-split.db
Files: 1,365 (pre-ingest count)
Sections: 19,207 (pre-ingest count)
Integrity check: PASSED
```

**Benefits**:
- **Rollback capability**: Restore to pre-change state if needed
- **Descriptive names**: Custom filenames identify backup purpose
- **Peace of mind**: Know you can undo changes
- **Quick recovery**: Rollback in seconds if operations fail
```

### 4.4 Optional: Dedicated BACKUP_RESTORE.md

For comprehensive coverage, consider a dedicated guide:

```markdown
# skill-split Backup and Restore Guide

Complete guide for database backup and recovery operations.

## Overview

skill-split provides automated backup and restore functionality to protect your skill database against data loss and enable disaster recovery.

## Why Backup Matters

Your skill-split database contains:
- Parsed sections from all your skills
- Search indexes for fast queries
- File metadata and integrity hashes
- Component handler data (plugins, hooks, configs)

**Regular backups protect against**:
- Database corruption
- Accidental deletion
- Migration between machines
- Testing and development

## Backup Operations

### When to Backup

**Recommended Schedule**:
- **Before bulk ingest**: Backup before adding many new files
- **After major changes**: Backup after reorganizing skills
- **Regular automated**: Daily or weekly automated backups
- **Before maintenance**: Backup before database operations

### Manual Backup

```bash
./skill_split.py backup
```

### Automated Backups

Add to crontab for scheduled backups:

```bash
# Edit crontab
crontab -e

# Daily backup at 2 AM
0 2 * * * /path/to/skill_split.py backup

# Weekly backup with retention (keep last 30 days)
0 2 * * 0 /path/to/skill_split.py backup && find ~/.claude/backups/ -name "skill-split-*.sql.gz" -mtime +30 -delete
```

### Backup Management

```bash
# List backup files
ls -lh ~/.claude/backups/

# View backup contents (decompress to temp)
gunzip -c ~/.claude/backups/skill-split-20260210.sql.gz | less

# Check backup integrity
gunzip -t ~/.claude/backups/skill-split-20260210.sql.gz
```

## Restore Operations

### When to Restore

**Common Scenarios**:
- **Database corruption**: Restore when database is malformed
- **Data loss**: Restore after accidental deletion
- **Migration**: Transfer database to new machine
- **Testing**: Create test database from backup
- **Rollback**: Undo problematic changes

### Restore Procedure

```bash
# 1. Identify corruption or need for restore
./skill_split.py search "test"
Error: database disk image is malformed

# 2. List available backups
ls -lt ~/.claude/backups/

# 3. Choose backup to restore
./skill_split.py restore ~/.claude/backups/skill-split-20260210.sql.gz --overwrite

# 4. Verify restore success
./skill_split.py search "test"
```

### Restore Validation

The restore command automatically validates:
- **Integrity check**: PRAGMA integrity_check
- **Record counts**: Files and sections match backup
- **FTS5 indexes**: Full-text search indexes functional
- **Foreign keys**: Constraints enforced

## Troubleshooting

### Backup Fails

**Error**: "Database not found or not readable"
- Check database path exists
- Verify database file is readable
- Check file permissions

**Error**: "Failed to write backup file"
- Check backup directory exists
- Verify write permissions
- Check disk space

### Restore Fails

**Error**: "Target database already exists"
- Use `--overwrite` flag to replace existing database
- Or specify different target with `--db`

**Error**: "Invalid or corrupted backup file"
- Verify backup file is not corrupted
- Check gzip integrity: `gunzip -t backup.sql.gz`
- Try a different backup file

**Error**: "Integrity check failed"
- Backup may be corrupted
- Database restore may have failed
- Check SQLite version compatibility

## Best Practices

1. **Regular backups**: Automate with cron
2. **Retention policy**: Keep multiple backups for rollback options
3. **Off-site storage**: Copy backups to cloud storage for disaster recovery
4. **Test restores**: Periodically test restore procedure
5. **Before changes**: Always backup before bulk operations
6. **Monitor size**: Watch backup sizes for unexpected growth

## Advanced Topics

### Backup Rotation

Implement automatic backup rotation:

```bash
#!/bin/bash
# backup-rotate.sh - Daily backup with 30-day retention

BACKUP_DIR="$HOME/.claude/backups"
KEEP_DAYS=30

# Create backup
/path/to/skill_split.py backup

# Delete old backups
find "$BACKUP_DIR" -name "skill-split-*.sql.gz" -mtime +$KEEP_DAYS -delete

# Log result
echo "Backup completed: $(date)" >> "$BACKUP_DIR/backup.log"
ls -lh "$BACKUP_DIR" >> "$BACKUP_DIR/backup.log"
```

### Off-Site Backup Storage

Copy backups to cloud storage:

```bash
# After backup creation
aws s3 sync ~/.claude/backups/ s3://my-bucket/skill-split-backups/
# or
rclone copy ~/.claude/backups/ remote:skill-split-backups/
```

### Backup Verification

Periodically verify backup integrity:

```bash
#!/bin/bash
# verify-backups.sh - Check all backup files

for backup in ~/.claude/backups/skill-split-*.sql.gz; do
    echo "Checking: $backup"
    gunzip -t "$backup" && echo "OK" || echo "FAILED"
done
```

## See Also

- [CLI Reference - backup](docs/CLI_REFERENCE.md#backup)
- [CLI Reference - restore](docs/CLI_REFERENCE.md#restore)
- [EXAMPLES.md - Backup Workflows](EXAMPLES.md#backup-workflows)
```

---

## 5. Example Scenarios to Document

### 5.1 Essential Scenarios

Based on industry best practices and skill-split implementation:

1. **Regular Backup Routine**
   - Manual backup after major changes
   - Automated daily/weekly backups with cron
   - Backup retention policy

2. **Disaster Recovery**
   - Identify database corruption
   - Restore from most recent backup
   - Verify restored database

3. **Database Migration**
   - Backup on source machine
   - Transfer backup file
   - Restore on destination machine

4. **Testing with Restored Database**
   - Create test database from backup
   - Test operations safely
   - Clean up test database

5. **Pre-Change Backup**
   - Backup before bulk operations
   - Rollback if needed
   - Verify changes

### 5.2 Additional Useful Scenarios

6. **Backup Rotation**
   - Implement retention policy
   - Automatically delete old backups
   - Monitor backup sizes

7. **Off-Site Backup Storage**
   - Copy backups to cloud storage
   - Implement 3-2-1 backup strategy
   - Verify off-site copies

8. **Backup Verification**
   - Periodic integrity checks
   - Test restore procedure
   - Validate backup contents

---

## 6. Key Documentation Elements

### 6.1 Critical Information to Include

**For backup command**:
- What gets backed up (all tables, indexes, hashes)
- Where backups are stored (~/.claude/backups/)
- Backup format (gzip-compressed SQL)
- Filename pattern (skill-split-YYYYMMDD-HHMMSS.sql.gz)
- Size information (uncompressed, compressed, ratio)

**For restore command**:
- Safety features (overwrite protection)
- Validation performed (integrity, FTS5, foreign keys)
- Statistics provided (files, sections, tables)
- Error conditions (invalid backup, corruption)

**For both commands**:
- Exit codes and their meanings
- Common errors and solutions
- Performance expectations (time, size)

### 6.2 Safety Messaging

**Emphasize safety features**:
- Restore requires explicit `--overwrite` flag
- Integrity validation after restore
- Foreign key constraint verification
- FTS5 index recreation and validation

**Clear warnings**:
- "Restoring over an existing database requires explicit --overwrite flag"
- "Always test restore procedure before relying on it"
- "Keep multiple backups for rollback options"

### 6.3 Practical Guidance

**When to backup**:
- Before bulk operations
- After major changes
- On regular schedule (automated)
- Before maintenance

**How often to backup**:
- Development: Weekly or before major changes
- Production: Daily automated backups
- Critical data: Multiple times per day

**Backup retention**:
- Keep at least 5-10 recent backups
- Implement retention policy (30-90 days)
- Monitor backup storage usage

---

## 7. Cross-References and Navigation

### 7.1 Internal Links

**From README.md**:
- Link to CLI_REFERENCE.md for complete command options
- Link to EXAMPLES.md for real-world scenarios
- Link to BACKUP_RESTORE.md (if created) for comprehensive guide

**From CLI_REFERENCE.md**:
- backup command reference
- restore command reference
- Links to EXAMPLES.md scenarios

**From EXAMPLES.md**:
- Backup workflows section
- Links to CLI_REFERENCE.md
- Links to related features (search, list)

### 7.2 Related Features

**Connect to**:
- Progressive disclosure (why backups matter for large databases)
- Search functionality (verify after restore)
- Component handlers (backups include component data)
- Supabase integration (backup vs remote storage)

---

## 8. Implementation Checklist

### 8.1 Documentation Files to Update

- [ ] **README.md**: Add "Backup and Restore" section
- [ ] **docs/CLI_REFERENCE.md**: Add backup and restore command documentation
- [ ] **EXAMPLES.md**: Add "Backup and Restore Workflows" section
- [ ] **BACKUP_RESTORE.md** (optional): Create comprehensive guide

### 8.2 Content to Include

- [ ] Command syntax and options
- [ ] Realistic output examples
- [ ] Safety features and warnings
- [ ] When to use guidance
- [ ] Common scenarios (5+ examples)
- [ ] Troubleshooting section
- [ ] Automated backup examples (cron)
- [ ] Best practices
- [ ] Cross-references to related documentation

### 8.3 Style Consistency

- [ ] Follow 07-STYLE.md guidelines
- [ ] Use active voice
- [ ] Include realistic command output
- [ ] Use absolute paths
- [ ] Test all command examples
- [ ] Verify all internal links

---

## 9. Next Steps

1. **Review and approve** this research document
2. **Create documentation plan** based on recommended structure
3. **Draft documentation** following style guide
4. **Test all examples** against actual implementation
5. **Review and refine** based on feedback
6. **Update cross-references** in existing documentation
7. **Final review** against 07-STYLE.md checklist

---

## 10. Industry Sources Referenced

- [TiDB BR Command-line Tool - PingCAP Docs](https://docs.pingcap.com/tidb/v5.4/use-br-command-line-tool/)
- [Back Up and Restore with Command Line Tools - Couchbase Docs](https://docs.couchbase.com/cloud/clusters/cli-backup-restore.html)
- [cpd-cli backup-restore - IBM Docs](https://www.ibm.com/docs/en/software-hub/5.1.x?topic=reference-backup-restore)
- [Clibato - CLI Backup Tool: Building a Command-line Python App](https://jigarius.com/blog/clibato-cli-backup-tool)
- [KOP CLI - Backup and Restore - Rafay Product Documentation](https://docs.rafay.co/cli/backup_cli/)

---

**Document Version**: 1.0
**Last Updated**: 2026-02-10
**Status**: Research Complete
**Next**: Create documentation plan based on findings
