# Frequently Asked Questions

**Last Updated:** 2026-02-10

---

## General

### What is skill-split?

skill-split is a Python tool that splits YAML and Markdown files into searchable sections stored in SQLite. It enables progressive disclosure for efficient Claude Code interactions.

### What is progressive disclosure?

Loading only the specific section you need instead of entire files. This provides 94-99% token savings.

### Why use skill-split?

- **Token Efficiency**: Load 50 tokens instead of 5,000 (99% savings)
- **Fast Search**: BM25, Vector, and Hybrid search modes
- **Round-Trip Integrity**: Byte-perfect file reconstruction
- **Developer Friendly**: CLI, Python API, and CI/CD integration

---

## Installation

### How do I install skill-split?

```bash
# From source
git clone https://github.com/joeymafella/skill-split.git
cd skill-split
pip install -e .

# Using pip (when published)
pip install skill-split
```

### What are the requirements?

- Python 3.11 or higher
- SQLite 3.35+ (for FTS5)
- Optional: OpenAI API key for semantic search

### Does it work with Windows?

Yes. skill-split is cross-platform (Linux, macOS, Windows).

---

## Usage

### How do I parse a file?

```bash
./skill_split.py parse file.md
```

### How do I search for content?

```bash
# BM25 keyword search (fast)
./skill_split.py search "error handling"

# Semantic search (requires API key)
ENABLE_EMBEDDINGS=true ./skill_split.py search-semantic "code patterns"

# Hybrid search (combined)
ENABLE_EMBEDDINGS=true ./skill_split.py search-semantic "authentication" --vector-weight 0.7
```

### How do I get a specific section?

```bash
# List sections with IDs
./skill_split.py list file.md

# Get section by ID
./skill_split.py get-section 42

# Navigate to next section
./skill_split.py next 42 file.md
```

---

## Databases

### Where is the database stored?

Default locations:
- Demo: `./skill_split.db`
- Production: `~/.claude/databases/skill-split.db`
- Custom: Use `--db /path/to/database.db`

### Can I use multiple databases?

Yes. Use the `--db` flag:

```bash
./skill_split.py store file.md --db project1.db
./skill_split.py store other.md --db project2.db
```

### How do I share databases?

Copy the `.db` file. It's a single portable SQLite file:

```bash
# Export
cp skill_split.db /shared/location/

# Import (just copy and use)
cp /shared/location/skill-split.db ~/my-copy.db
./skill_split.py search "query" --db ~/my-copy.db
```

### What about Supabase?

skill-split supports Supabase for cloud storage:

```bash
export SUPABASE_URL="https://xxx.supabase.co"
export SUPABASE_KEY="your-key"

./skill_split.py ingest file.md
./skill_split.py search-library "query"
```

---

## Search

### What's the difference between search modes?

| Mode | Command | Speed | Best For |
|------|---------|-------|----------|
| BM25 | `search` | Fast (10-50ms) | Exact keyword matches |
| Vector | `search-semantic --vector-weight 1.0` | Slow (100-200ms) | Concept-based discovery |
| Hybrid | `search-semantic --vector-weight 0.7` | Medium (150-300ms) | Balanced results |

### When should I use each mode?

- **BM25**: Quick lookups, exact phrases, code snippets
- **Vector**: "Find me content like X", concept searches
- **Hybrid**: Best of both, default recommendation

### How do I use boolean operators?

```bash
# AND (both terms)
./skill_split.py search "python AND handler"

# OR (either term - default for multi-word)
./skill_split.py search "python handler"

# NOT (exclude term)
./skill_split.py search "authentication NOT token"

# NEAR (proximity search)
./skill_split.py search "error NEAR/5 handling"
```

---

## Performance

### How many files can skill-split handle?

Tested with 1,365 files (19,207 sections). Scales to 10,000+ files with proper indexing.

### Why is search slow?

Check for:
- Missing FTS5 index (`sqlite3 db.db "PRAGMA index_list('sections_fts');"`)
- Large database without query limits
- Network latency (Supabase)

### How do I improve performance?

```bash
# Use query limits
./skill_split.py search "query" --limit 10

# Rebuild FTS5 index
sqlite3 skill_split.db "INSERT INTO sections_fts(sections_fts) VALUES('rebuild');"

# Optimize database
sqlite3 skill_split.db "VACUUM; ANALYZE;"
```

---

## Integration

### Can I use skill-split in Python?

Yes:

```python
from core.parser import Parser
from core.database import DatabaseStore

parser = Parser()
db = DatabaseStore("my_database.db")

document = parser.parse(content, "file.md")
db.store_document(document)

results = db.search_sections("query")
```

### Does it work with CI/CD?

Yes. See [integrations/CI_CD.md](../integrations/CI_CD.md) for GitHub Actions and GitLab CI examples.

### Can I integrate with Claude Code?

Yes. See [integrations/CLAUDE_CODE.md](../integrations/CLAUDE_CODE.md) for progressive disclosure workflows.

---

## Troubleshooting

### "Database is locked" error?

Another process is using the database:

```bash
# Find and close other processes
lsof | grep skill_split.db

# Remove stale locks
rm -f skill_split.db-wal skill_split.db-shm
```

### "No sections found"?

Check file format:

```bash
# Validate structure
./skill_split.py validate file.md

# Check what parser sees
./skill_split.py parse file.md
```

### Search returns no results?

```bash
# Verify content exists
./skill_split.py list file.md

# Check index
sqlite3 skill_split.db "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%fts%';"

# Try broader search
./skill_split.py search "part:word"
```

### Embedding errors?

```bash
# Check API key
echo $OPENAI_API_KEY

# Test connection
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

---

## Advanced

### Can I compose new skills from sections?

Yes:

```bash
./skill_split.py compose \
  --sections 42,57,103 \
  --output new_skill.md
```

### How do I verify round-trip integrity?

```bash
./skill_split.py verify file.md
# Checks SHA256 before parse/recompose
```

### Can I use custom handlers?

Yes. Create custom handlers in `handlers/` extending `base.py`.

### What about migration from v0.x to v1.0?

See [docs/MIGRATION.md](./MIGRATION.md) for complete migration guide.

---

## Contributing

### How do I contribute?

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Submit a pull request

See [CONTRIBUTING.md](../CONTRIBUTING.md) for details.

### What's the test coverage?

623 tests covering all core functionality. Run with:

```bash
python -m pytest test/ -v
```

### How do I add a new feature?

1. Discuss in an issue first
2. Follow existing patterns
3. Add tests for new code
4. Update documentation

---

## License

### What license does skill-split use?

MIT License. See [LICENSE](../LICENSE) for details.

### Can I use it commercially?

Yes. MIT license permits commercial use.

---

## Support

### Where do I get help?

- [GitHub Issues](https://github.com/joeymafella/skill-split/issues)
- [Documentation](../README.md)
- [Examples](../EXAMPLES.md)

### How do I report a bug?

Include:
- skill-split version (`git log -1`)
- Python version
- Error message
- Steps to reproduce
- System information

---

## Roadmap

### What's coming next?

- v1.1: Enhanced caching layer
- v1.2: Distributed search
- v1.3: Real-time collaboration
- v2.0: Multi-database sharding

Follow the project for updates!

---

*More questions? Open an issue on GitHub!*
