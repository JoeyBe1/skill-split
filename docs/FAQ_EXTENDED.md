# Extended FAQ - Advanced Topics

**For basic FAQ, see [FAQ.md](FAQ.md)**

## Performance & Scalability

### Q: How large can files be before performance degrades?

**A:** Benchmarks show excellent performance up to 100KB:
- Parse 1KB: 0.013ms
- Parse 50KB: 0.67ms
- Parse 100KB: ~1.3ms

For files larger than 100KB, consider:
1. Splitting into smaller files
2. Using streaming mode (planned v1.1.0)
3. Batch processing with `migrate_database.py`

### Q: How many sections can the database handle?

**A:** Tested with 19,207 sections from 1,365 files. SQLite FTS5 handles millions efficiently. Key considerations:
- Use indexes on frequently queried columns
- Consider WAL mode for concurrent access
- Archive old sections with `backup_database.sh`

### Q: What's the memory footprint?

**A:** Typical usage:
- CLI startup: ~30MB
- Parse 50KB file: ~35MB peak
- BM25 search: ~40MB peak
- Vector search: ~60MB peak (with embeddings)

Memory scales linearly with database size. A database with 10K sections uses ~50MB.

## Advanced Usage

### Q: Can I use skill-split with non-markdown files?

**A:** Yes! The parser supports:
- **YAML frontmatter** - Any file with `---` delimited metadata
- **XML tags** - Custom tags with level attributes
- **Markdown headings** - Standard `#`, `##`, etc.

For custom formats, create a component handler in `handlers/`.

### Q: How do I create custom component handlers?

**A:** Extend the `BaseHandler` class:

```python
from handlers.base import BaseHandler

class CustomHandler(BaseHandler):
    def parse(self, content: str) -> list[Section]:
        # Your parsing logic
        pass

    def validate(self, sections: list[Section]) -> bool:
        # Your validation logic
        pass
```

Register in `handlers/factory.py`.

### Q: Can I integrate with my own database?

**A:** Yes. The `Database` class in `core/database.py` uses standard SQLite. You can:
1. Use a custom database path via `--db` flag
2. Access the database directly via SQLAlchemy
3. Use `SupabaseStore` for cloud storage

## Semantic Search

### Q: What embedding model does skill-split use?

**A:** Default is `text-embedding-3-small` (OpenAI). Benefits:
- Cost-effective: $0.02 per 1M tokens
- Fast: ~10ms per section
- Accurate: 96.8% of relevant content in top 5

To change models, set `OPENAI_EMBEDDING_MODEL` in `.env`.

### Q: How do I tune hybrid search?

**A:** The `--vector-weight` parameter controls semantic vs keyword balance:
- `1.0` = Pure semantic (concepts)
- `0.7` = Default (70% semantic, 30% keyword)
- `0.5` = Balanced
- `0.3` = Keyword-focused
- `0.0` = Pure BM25 (exact matches)

Example:
```bash
# Concept-focused (semantic search)
./skill_split.py search-semantic "authentication" --vector-weight 1.0

# Exact match focused (keyword search)
./skill_split.py search-semantic "authentication" --vector-weight 0.3
```

### Q: How do I reduce embedding costs?

**A:** Strategies:
1. **Use BM25 only** - No API costs, 95% accuracy for exact matches
2. **Selective embedding** - Only embed important sections
3. **Cache embeddings** - Stored locally after generation
4. **Batch processing** - Reduce API calls with `--batch-size`

## Troubleshooting

### Q: Why does round-trip fail with special characters?

**A:** Check:
1. File encoding (must be UTF-8)
2. Line endings (LF, not CRLF)
3. No BOM (byte order mark)

Fix:
```bash
file --mime-encoding yourfile.md
dos2unix yourfile.md  # If CRLF
```

### Q: Why are sections missing after parsing?

**A:** Common causes:
1. Empty sections (filtered out)
2. Invalid heading levels
3. Malformed YAML frontmatter

Debug with:
```bash
./skill_split.py parse yourfile.md --verbose
./skill_split.py validate yourfile.md
```

### Q: Database locked errors?

**A:** SQLite locks during writes. Solutions:
1. Enable WAL mode: `PRAGMA journal_mode=WAL`
2. Use connection pooling
3. Reduce concurrent write operations

## Integration

### Q: Can I use skill-split programmatically?

**A:** Yes! Import as a Python library:

```python
from skill_split import SkillSplit
from core.database import Database

# Initialize
ss = SkillSplit()

# Parse file
doc = ss.parse_file("README.md")

# Store in database
db = Database()
db.store_document(doc)

# Search
results = db.search_sections("query")
```

### Q: How do I integrate with CI/CD?

**A:** See `integrations/CI_CD.md` for complete examples. Basic workflow:
```yaml
- name: Validate documentation
  run: |
    pip install skill-split
    skill-split validate docs/**/*.md
```

### Q: Can I deploy to production?

**A:** Yes. Production checklist:
1. ✅ Use WAL mode for concurrency
2. ✅ Enable error logging
3. ✅ Set up database backups
4. ✅ Monitor with health checks
5. ✅ Use environment variables for secrets

See `docs/DEPLOYMENT.md` for complete guide.

## Migration

### Q: How do I migrate from v0.x to v1.0.0?

**A:** See `MIGRATION.md` for complete guide. Quick steps:
1. Backup database: `make backup`
2. Run migrations: `make migrate-apply`
3. Verify: `make test`
4. Deploy

### Q: Are database schemas backwards compatible?

**A:** v1.0.0 uses `ALTER TABLE` for migrations, so old data is preserved. However:
- Always backup before migrating
- Test in staging first
- Use `migrate_database.py --dry-run` to preview

## Contributing

### Q: How do I run tests locally?

**A:**
```bash
# All tests
make test

# Specific file
pytest test/test_parser.py -v

# With coverage
make coverage

# Benchmark
make benchmark
```

### Q: Code style requirements?

**A:** See `CONTRIBUTING.md` for details. Summary:
- Line length: 100
- Type hints required
- Docstrings for public APIs
- Pre-commit hooks enforce style

## Licensing

### Q: Can I use skill-split commercially?

**A:** Yes! MIT License permits:
- ✅ Commercial use
- ✅ Modification
- ✅ Distribution
- ✅ Private use

See [LICENSE](LICENSE) for full terms.

### Q: Attribution required?

**A:** No, but appreciated. Include in your notices:
```
 Portions copyright (c) 2026 skill-split contributors
```

---

**Still have questions?**
- Open an issue on GitHub
- See [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- Check [docs/](./) for detailed guides

*skill-split - Progressive disclosure for AI workflows*
