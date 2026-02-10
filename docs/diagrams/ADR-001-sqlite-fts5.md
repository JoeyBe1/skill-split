# ADR-001: SQLite FTS5 for Local Search

**Status**: Accepted
**Date**: 2025-02-10
**Context**: Phase 02 - Search Fix Implementation

## Context

The skill-split system needs fast, reliable keyword search functionality for local databases without requiring external services or network connectivity. Users need to search across thousands of sections stored in SQLite databases with sub-100ms response times.

## Decision

Use SQLite FTS5 (Full-Text Search) extension with BM25 ranking algorithm for local keyword search.

### Technical Details

- **FTS5 Virtual Table**: External content table mirroring the sections table
- **BM25 Ranking**: Built-in ranking function for relevance scoring
- **Query Preprocessing**: Natural language to FTS5 MATCH syntax conversion
- **Automatic Synchronization**: External content table syncs with main table

### Implementation

```sql
CREATE VIRTUAL TABLE IF NOT EXISTS sections_fts USING fts5(
    title,
    content,
    content=sections,
    content_rowid=id
);
```

```python
def search_sections_with_rank(query: str) -> List[Tuple[int, float]]:
    cursor = conn.execute("""
        SELECT s.id, bm25(sections_fts) as rank
        FROM sections_fts
        JOIN sections s ON sections_fts.rowid = s.id
        WHERE sections_fts MATCH ?
        ORDER BY rank
    """, (processed_query,))
```

## Rationale

### Advantages

1. **Performance**: ~10ms average search latency on 19,000+ sections
2. **No Dependencies**: Built into SQLite 3.38+, no external services
3. **Portability**: Database files are self-contained and portable
4. **Relevance**: BM25 algorithm provides high-quality keyword ranking
5. **Offline**: Works without network connectivity

### Alternatives Considered

1. **LIKE query pattern matching**
   - Rejected: Too slow on large datasets (~500ms+)
   - No relevance ranking
   - No query syntax support

2. **External search engine (Elasticsearch)**
   - Rejected: Heavy deployment overhead
   - Requires additional infrastructure
   - Overkill for local development

3. **Regular expressions**
   - Rejected: Limited expressiveness
   - Poor performance on large corpora
   - No relevance scoring

## Consequences

### Positive

- Fast full-text search without external dependencies
- Automatic index maintenance
- Complex query support (AND, OR, NEAR, phrase search)
- Natural language query preprocessing

### Negative

- Limited to keyword matching (no semantic understanding)
- No cross-database search without manual merging
- FTS5 external content requires periodic optimization

### Mitigation

- Hybrid search with vector embeddings for semantic understanding
- Regular FTS index optimization: `INSERT INTO sections_fts(sections_fts) VALUES('optimize')`
- Query preprocessing to improve discovery (multi-word → OR)

## Related Decisions

- [ADR-002](./ADR-002-supabase-pgvector.md): Supabase + pgvector for cloud storage
- [ADR-003](./ADR-003-hybrid-search.md): Hybrid search with configurable weights

## References

- [SQLite FTS5 Documentation](https://www.sqlite.org/fts5.html)
- [BM25 Algorithm](https://en.wikipedia.org/wiki/Okapi_BM25)
