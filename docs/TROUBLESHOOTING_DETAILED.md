# skill-split Troubleshooting Guide

**Solutions to common issues and problems**

---

## Quick Diagnostic

```bash
# Run health check
python scripts/health_check.py

# Verify installation
python -c "import skill_split; print('OK')"

# Test database
python -c "from core.database import Database; db = Database(); print('OK')"
```

---

## Installation Issues

### Issue: "Module not found: skill_split"

**Cause:** Package not installed or not in PATH

**Solutions:**
```bash
# Reinstall
pip install -e .

# Or with dev dependencies
pip install -e ".[dev]"

# Verify installation
python -c "import skill_split; print(skill_split.__file__)"
```

### Issue: "Python version too old"

**Cause:** Python < 3.10

**Solution:**
```bash
# Check version
python --version

# Install Python 3.10+
# macOS
brew install python@3.13

# Ubuntu
sudo apt install python3.13

# Windows
# Download from python.org
```

### Issue: "Dependencies conflict"

**Cause:** Version conflicts between packages

**Solution:**
```bash
# Create fresh virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e ".[dev]"
```

---

## Database Issues

### Issue: "Database is locked"

**Cause:** Multiple writes to SQLite without WAL mode

**Solution:**
```bash
# Enable WAL mode
sqlite3 skill_split.db "PRAGMA journal_mode=WAL;"

# Or in Python
import sqlite3
conn = sqlite3.connect("skill_split.db")
conn.execute("PRAGMA journal_mode=WAL")
```

### Issue: "No such table: sections"

**Cause:** Database not initialized

**Solution:**
```bash
# Initialize database
python -c "from core.database import Database; db = Database()"

# Or run init command
./skill_split.py init
```

### Issue: "Database corrupted"

**Cause:** Incomplete write or disk error

**Solution:**
```bash
# Restore from backup
./scripts/backup_database.sh --restore backups/latest.sql

# Or reinitialize
rm skill_split.db
./skill_split.py init
```

---

## Parsing Issues

### Issue: "Round-trip failed"

**Cause:** File encoding or line ending issues

**Solutions:**
```bash
# Check encoding
file --mime-encoding yourfile.md

# Convert to UTF-8
iconv -f ISO-8859-1 -t UTF-8 yourfile.md > yourfile_utf8.md

# Fix line endings (CRLF -> LF)
dos2unix yourfile.md
```

### Issue: "Empty sections"

**Cause:** Consecutive blank lines or headings without content

**Solution:**
```bash
# Validate file first
./skill_split.py validate yourfile.md

# Check for issues
./skill_split.py parse yourfile.md --verbose
```

### Issue: "Frontmatter parsing failed"

**Cause:** Invalid YAML syntax

**Solution:**
```yaml
# Bad
---
title: Unclosed string
description: This won't work

# Good
---
title: "Properly quoted string"
description: "This works"
---
```

---

## Search Issues

### Issue: "No results found"

**Cause:** Search query too specific or wrong mode

**Solutions:**
```bash
# Try BM25 search (keyword matching)
./skill_split.py search "authentication"

# Try semantic search (concepts)
./skill_split.py search-semantic "login security" --vector-weight 1.0

# Try hybrid (balanced)
./skill_split.py search-semantic "authentication" --vector-weight 0.5

# List all sections to find content
./skill_split.py list README.md
```

### Issue: "Vector search not working"

**Cause:** Missing OpenAI API key or embeddings not generated

**Solution:**
```bash
# Check API key
echo $OPENAI_API_KEY

# Set in .env
cat > .env <<EOF
OPENAI_API_KEY=sk-...
ENABLE_EMBEDDINGS=true
EOF

# Generate embeddings
python -c "
from core.embedding_service import EmbeddingService
from core.database import Database
db = Database()
service = EmbeddingService()
service.generate_all_embeddings(db)
"
```

### Issue: "Search is slow"

**Cause:** Missing FTS5 index or large database

**Solution:**
```bash
# Check if FTS5 is enabled
sqlite3 skill_split.db "PRAGMA index_list('sections_fts');"

# Rebuild FTS5 index
sqlite3 skill_split.db "INSERT INTO sections_fts(sections_fts) VALUES('rebuild');"

# For large DB, use pagination
./skill_split.py search "query" --limit 10
```

---

## Performance Issues

### Issue: "Parsing is slow for large files"

**Cause:** File > 100KB

**Solutions:**
```bash
# Split file into smaller parts
split -l 1000 large_file.md part_

# Or use streaming (future feature)
# ./skill_split.py parse large_file.md --stream
```

### Issue: "Memory usage high"

**Cause:** Large database loaded into memory

**Solution:**
```bash
# Use disk-based database
SKILL_SPLIT_DB=/path/to/db.db ./skill_split.py search "query"

# Or clear cache
rm -rf __pycache__/
```

---

## CLI Issues

### Issue: "Command not found: skill-split"

**Cause:** Not in PATH or not installed

**Solution:**
```bash
# Use directly
./skill_split.py --help

# Or install with scripts
pip install -e .

# Check PATH
echo $PATH | tr ':' '\n' | grep local
```

### Issue: "Permission denied"

**Cause:** Script not executable

**Solution:**
```bash
# Make executable
chmod +x skill_split.py
chmod +x scripts/*.sh
```

---

## CI/CD Issues

### Issue: "Tests fail in CI but pass locally"

**Cause:** Environment differences

**Solution:**
```yaml
# In .github/workflows/test.yml
- name: Set up Python
  uses: actions/setup-python@v5
  with:
    python-version: '3.13'  # Match local version

- name: Install dependencies
  run: |
    pip install -e ".[dev]"

- name: Run tests
  run: |
    python -m pytest test/ -v
```

### Issue: "Linting fails in CI"

**Cause:** Code formatting differences

**Solution:**
```bash
# Run format locally first
make lint-all

# Check CI config
cat .github/workflows/lint.yml
```

---

## Docker Issues

### Issue: "Container won't start"

**Cause:** Port conflict or missing volume

**Solution:**
```bash
# Check port usage
docker ps
lsof -i :8000

# Use different port
docker run -p 8001:8000 skill-split

# Check volume
docker run -v $(PWD)/data:/data skill-split
```

### Issue: "Database not accessible in container"

**Cause:** Volume mount issue

**Solution:**
```yaml
# In docker-compose.yml
volumes:
  - ./data:/data  # Mount local directory

environment:
  - SKILL_SPLIT_DB=/data/skill_split.db
```

---

## Getting Help

### Diagnostic Information

When reporting issues, include:

```bash
# System info
python --version
pip list | grep skill-split

# Database info
sqlite3 skill_split.db ".tables"
sqlite3 skill_split.db "SELECT COUNT(*) FROM sections;"

# Error output
./skill_split.py parse yourfile.md --verbose 2>&1 | tee error.log
```

### Where to Get Help

1. **Documentation:** Read relevant docs first
2. **FAQ:** Check `docs/FAQ.md`
3. **Issues:** Search GitHub issues first
4. **New Issue:** Include diagnostic information

### Template for Issues

```markdown
## Description
[Brief description of the issue]

## Steps to Reproduce
1. Run command: `...`
2. Expected: ...
3. Actual: ...

## Environment
- Python version: ...
- skill-split version: ...
- OS: ...

## Error Message
```
[Paste error output]
```

## Diagnostic Info
[Paste output from diagnostic commands above]
```

---

**Still stuck?** Check `docs/FAQ.md` or open a GitHub issue.

---

*skill-split - Progressive disclosure for AI workflows*
