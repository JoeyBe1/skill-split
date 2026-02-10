# Troubleshooting Guide

**Last Updated:** 2026-02-10

This guide helps you diagnose and resolve common issues with skill-split.

---

## Quick Diagnosis Checklist

- [ ] Python version >= 3.11
- [ ] All dependencies installed (`pip install -r requirements.txt`)
- [ ] Database file exists and is writable
- [ ] File paths are correct
- [ ] Sufficient disk space
- [ ] No database locks

---

## Common Issues

### 1. Database Locked Error

**Symptom:**
```
sqlite3.OperationalError: database is locked
```

**Causes:**
- Another process is using the database
- Previous crash left a lock file
- Multiple concurrent writes

**Solutions:**
```bash
# Check for other processes
lsof | grep skill_split.db

# Remove stale lock files
rm -f skill_split.db-wal skill_split.db-shm

# Use a different database
./skill_split.py store file.md --db /tmp/test.db
```

**Prevention:**
- Use one database connection per process
- Close connections properly
- Use `--db` flag for concurrent operations

---

### 2. Parser Not Finding Sections

**Symptom:**
```
No sections found in file
```

**Causes:**
- Incorrect file format
- Missing heading markers
- Empty file

**Solutions:**
```bash
# Validate file structure
./skill_split.py validate file.md

# Check what parser detects
./skill_split.py parse file.md

# Try explicit format
./skill_split.py store file.md --format markdown
```

**Expected Format:**
```markdown
---
frontmatter: optional
---

# Heading 1
Content here

## Heading 2
More content

### Heading 3
Nested content
```

---

### 3. Search Returns No Results

**Symptom:**
```
No results found for "query"
```

**Causes:**
- Content not indexed
- Search term too specific
- FTS5 index missing

**Solutions:**
```bash
# Verify content was stored
./skill_split.py list file.md --db skill_split.db

# Check FTS5 index
sqlite3 skill_split.db "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%fts%';"

# Re-index database
./skill_split.py verify skill_split.db

# Try broader search
./skill_split.py search "partial:word" --db skill_split.db
```

---

### 4. Embedding Generation Fails

**Symptom:**
```
Error: OPENAI_API_KEY not set
```

**Causes:**
- Missing API key
- Invalid API key
- Network issues

**Solutions:**
```bash
# Set API key
export OPENAI_API_KEY="sk-..."

# Verify key works
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# Check quota
# Visit: https://platform.openai.com/usage

# Test embedding service
python3 -c "
from core.embedding_service import EmbeddingService
service = EmbeddingService()
print(service.generate_embedding('test'))
"
```

---

### 5. Round-Trip Verification Fails

**Symptom:**
```
SHA256 mismatch: abc123 != def456
```

**Causes:**
- Encoding issues
- Trailing whitespace changes
- Line ending differences (CRLF vs LF)

**Solutions:**
```bash
# Check encoding
file -I input.md

# Normalize line endings
dos2unix input.md
# or
sed -i 's/\r$//' input.md

# Strip trailing whitespace
sed -i 's/[[:space:]]*$//' input.md

# Re-verify
./skill_split.py verify input.md
```

---

### 6. Memory Issues with Large Files

**Symptom:**
```
MemoryError: Unable to allocate array
```

**Causes:**
- File too large for memory
- Too many sections loaded at once

**Solutions:**
```bash
# Process in chunks
split -l 1000 large_file.md chunk_

# Process each chunk
for chunk in chunk_*; do
    ./skill_split.py store "$chunk" --db skill_split.db
done

# Increase memory limit (not recommended)
export PYTHONHASHSEED=0
python3 -X maxsize=100M skill_split.py store large_file.md
```

---

### 7. Supabase Connection Failed

**Symptom:**
```
Error: Could not connect to Supabase
```

**Causes:**
- Invalid credentials
- Network issues
- Supabase service down

**Solutions:**
```bash
# Check credentials
echo $SUPABASE_URL
echo $SUPABASE_KEY

# Test connection
curl "$SUPABASE_URL/rest/v1/" \
  -H "apikey: $SUPABASE_KEY"

# Verify table exists
curl "$SUPABASE_URL/rest/v1/sections?limit=1" \
  -H "apikey: $SUPABASE_KEY" \
  -H "Authorization: Bearer $SUPABASE_KEY"

# Check Supabase status
# Visit: https://status.supabase.com
```

---

### 8. Performance: Slow Search

**Symptom:**
Search takes >5 seconds

**Causes:**
- Missing FTS5 index
- Large database
- No query optimization

**Solutions:**
```bash
# Check index exists
sqlite3 skill_split.db "PRAGMA index_list('sections_fts');"

# Rebuild index
sqlite3 skill_split.db "INSERT INTO sections_fts(sections_fts) VALUES('rebuild');"

# Analyze query plan
sqlite3 skill_split.db "EXPLAIN QUERY PLAN SELECT * FROM sections_fts WHERE sections_fts MATCH 'query';"

# Use limits
./skill_split.py search "query" --limit 10
```

---

### 9. Import Errors

**Symptom:**
```
ModuleNotFoundError: No module named 'core'
```

**Causes:**
- Wrong working directory
- Python path issues
- Virtual environment not activated

**Solutions:**
```bash
# Check working directory
pwd
# Should be: /path/to/skill-split

# Add to Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Install in development mode
pip install -e .

# Verify import
python3 -c "from core.parser import Parser; print('OK')"
```

---

### 10. Git Hooks Not Running

**Symptom:**
Pre-commit hooks not executing

**Causes:**
- Hooks not executable
- Hooks not installed
- Wrong hook path

**Solutions:**
```bash
# Make hooks executable
chmod +x .git/hooks/*

# Reinstall hooks
pre-commit install

# Check hook path
ls -la .git/hooks/

# Test manually
.git/hooks/pre-commit
```

---

## Diagnostic Commands

### Full System Check

```bash
#!/bin/bash
echo "=== skill-split Diagnostics ==="
echo ""

echo "Python Version:"
python3 --version
echo ""

echo "Dependencies:"
pip list | grep -E "(sqlite|pytest|openai|supabase)"
echo ""

echo "Database:"
ls -lh skill_split.db 2>/dev/null || echo "No database found"
echo ""

echo "Environment:"
env | grep -E "(OPENAI|SUPABASE|ENABLE)" | sort
echo ""

echo "Disk Space:"
df -h .
echo ""

echo "Database Integrity:"
if [ -f skill_split.db ]; then
    sqlite3 skill_split.db "PRAGMA integrity_check;"
else
    echo "No database to check"
fi
echo ""

echo "Tests:"
python3 -m pytest test/ --collect-only -q | tail -5
```

### Performance Profiling

```bash
# Profile parsing
python3 -m cProfile -o profile.stats skill_split.py parse large_file.md

# Analyze results
python3 -c "
import pstats
p = pstats.Stats('profile.stats')
p.sort_stats('cumulative')
p.print_stats(20)
"
```

---

## Getting Help

### Information to Gather

When reporting issues, include:

1. **System Information:**
   ```bash
   python3 --version
   uname -a
   ```

2. **skill-split Version:**
   ```bash
   git log -1 --format="%H %s"
   ```

3. **Error Message:**
   Full error traceback

4. **Steps to Reproduce:**
   Exact commands that triggered the issue

5. **Database State:**
   ```bash
   sqlite3 skill_split.db ".schema"
   sqlite3 skill_split.db "SELECT COUNT(*) FROM sections;"
   ```

### Debug Mode

Enable debug logging:

```bash
export DEBUG=1
./skill_split.py command args
```

### Verbose Output

```bash
./skill_split.py command args --verbose
```

---

## Recovery Procedures

### Database Recovery

```bash
# Backup corrupted database
cp skill_split.db skill_split.db.corrupted

# Export to SQL
sqlite3 skill_split.db.corrupted ".dump" > backup.sql

# Import to new database
sqlite3 skill_split_new.db < backup.sql

# Verify new database
./skill_split.py verify skill_split_new.db
```

### Partial Recovery

```bash
# Recover specific file
./skill_split.py list original_file.md --db skill_split.db.corrupted > sections.txt

# Store to new database
while read id; do
    ./skill_split.py get-section "$id" --db skill_split.db.corrupted >> recovered.md
done < sections.txt
```

---

## Prevention

### Regular Maintenance

```bash
# Weekly database cleanup
sqlite3 skill_split.db "VACUUM;"

# Rebuild indexes
sqlite3 skill_split.db "REINDEX;"

# Update dependencies
pip install --upgrade -r requirements.txt

# Run tests
python3 -m pytest test/ -v
```

### Backup Strategy

```bash
# Automated backup script
#!/bin/bash
DATE=$(date +%Y%m%d)
BACKUP_DIR="/backup/skill-split"

mkdir -p "$BACKUP_DIR"
cp skill_split.db "$BACKUP_DIR/skill_split_$DATE.db"

# Keep last 7 days
find "$BACKUP_DIR" -name "skill_split_*.db" -mtime +7 -delete
```

---

## Performance Tuning

### SQLite Optimization

```python
# In database.py, add:
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA cache_size = -64000;  # 64MB cache
PRAGMA temp_store = MEMORY;
```

### Query Optimization

```bash
# Use EXPLAIN to analyze queries
sqlite3 skill_split.db "EXPLAIN QUERY PLAN SELECT * FROM sections WHERE..."

# Add indexes if needed
sqlite3 skill_split.db "CREATE INDEX IF NOT EXISTS idx_sections_file ON sections(file_path);"
```

---

*Still having issues? Check the [GitHub Issues](https://github.com/joeymafella/skill-split/issues) or open a new issue with the diagnostic information above.*
