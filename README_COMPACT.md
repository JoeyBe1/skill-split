# skill-split

**v1.0.0** — Progressive disclosure for AI documentation

---

> Split documentation into searchable sections for 94-99% token savings while maintaining byte-perfect round-trip integrity.

---

## Features

- **Multi-format Parsing**: YAML frontmatter, Markdown, XML
- **SQLite Storage**: FTS5 full-text search with BM25 ranking
- **Vector Search**: OpenAI embeddings for semantic search
- **Hybrid Search**: Tunable BM25 + Vector combination
- **Progressive Disclosure**: Load specific sections (99% token savings)
- **Supabase Integration**: Cloud storage with full-text search
- **Component Handlers**: Plugins, hooks, configs, scripts
- **Round-trip Integrity**: SHA256 verified byte-perfect reconstruction

## Quick Start

```bash
# Install
pip install skill-split

# Parse and store
skill-split store README.md

# Search (BM25)
skill-split search "authentication"

# Progressive disclosure
skill-split get-section 42
skill-split next 42 README.md
```

## Token Savings

| File Size | Full Load | One Section | Savings |
|-----------|-----------|-------------|---------|
| 10KB | 2,500 tokens | 50 tokens | **98%** |
| 50KB | 12,500 tokens | 50 tokens | **99.6%** |
| 100KB | 25,000 tokens | 50 tokens | **99.8%** |

## Documentation

- [Installation Guide](INSTALLATION.md)
- [Quick Reference](docs/QUICK_REFERENCE.md)
- [API Documentation](API.md)
- [Contributing Guide](CONTRIBUTING.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)

## Search Modes

| Mode | Command | Speed | Best For |
|------|---------|-------|----------|
| BM25 | `search` | ⚡⚡⚡ | Exact matches |
| Vector | `search-semantic --vector-weight 1.0` | ⚡ | Concepts |
| Hybrid | `search-semantic --vector-weight 0.7` | ⚡⚡ | Balanced |

## Performance

- Parse 1KB: **0.013ms**
- Parse 50KB: **0.67ms**
- Query section: **0.11ms**
- BM25 search: **5.8ms**

## Status

- **Tests**: 623/623 passing ✅
- **Coverage**: 95%+ ✅
- **Release**: v1.0.0 production ready ✅

## License

MIT License - see [LICENSE](LICENSE) for details.

---

*skill-split — Progressive disclosure for AI workflows*
