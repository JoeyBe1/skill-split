# Changelog

All notable changes to skill-split will be documented in this file.

## [1.0.0] - 2026-02-10

### Added
- **Complete parsing system** for YAML frontmatter, Markdown headings, and XML tags
- **Progressive disclosure API** for token-efficient section loading
- **Three search modes**: BM25 keyword, Vector semantic, and Hybrid combined
- **Component handlers** for plugins, hooks, configs, and scripts (Python, JS, TS, Shell)
- **Skill composition** - create new skills from existing sections
- **Supabase integration** with pgvector for cloud storage
- **Checkout/Checkin system** with transaction safety for file deployment
- **Backup/Restore** with gzip compression for disaster recovery
- **SecretManager** for secure API key management
- **Batch embedding generation** with 10-100x performance improvement
- **20 CLI commands** covering all operations

### Performance
- 623 tests passing with comprehensive coverage
- 1,368 production files indexed
- 19,271 sections stored and searchable
- 99% token savings from progressive disclosure

### CLI Commands
- parse, validate, store, get, tree, verify
- get-section, next, list, search, compose
- search-semantic, ingest, checkout, checkin
- list-library, status, search-library
- backup, restore

[1.0.0]: https://github.com/yourusername/skill-split/releases/tag/v1.0.0
