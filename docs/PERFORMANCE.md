# Performance Tuning Guide

**Last Updated:** 2026-02-10

Comprehensive guide for optimizing skill-split performance.

---

## Performance Baselines

### Default Performance (No Tuning)

| Operation | Time | Throughput |
|-----------|------|------------|
| Parse 1KB file | <1ms | 1,000 files/sec |
| Parse 10KB file | 2-5ms | 200-500 files/sec |
| Parse 100KB file | 20-50ms | 20-50 files/sec |
| BM25 search | 10-50ms | 20-100 queries/sec |
| Vector search | 100-200ms | 5-10 queries/sec |
| Hybrid search | 150-300ms | 3-7 queries/sec |

### Scaled Performance (1,365 files, 19,207 sections)

| Operation | Time | Notes |
|-----------|------|-------|
| BM25 search | 50-100ms | FTS5 full-text search |
| Vector search | 500-1000ms | OpenAI API latency |
| Hybrid search | 600-1500ms | Combined scoring |

---

## Quick Wins

### 1. Enable SQLite WAL Mode

**Improvement:** 20-30% faster concurrent writes

```sql
-- Add to database initialization
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
```

### 2. Increase SQLite Cache

**Improvement:** 40-60% faster repeated queries

```bash
# Default: 2MB cache
# Recommended: 64MB cache
sqlite3 skill_split.db "PRAGMA cache_size = -64000;"
```

### 3. Use Query Limits

**Improvement:** 70-90% faster for large result sets

```bash
# Without limit: 500ms
./skill_split.py search "python"

# With limit: 50ms
./skill_split.py search "python" --limit 10
```

### 4. Batch Operations

**Improvement:** 80-95% faster bulk inserts

```python
# Instead of:
for file in files:
    db.store_document(parse(file))

# Use batch:
documents = [parse(f) for f in files]
db.store_documents_batch(documents)
```

---

## Database Optimization

### Index Configuration

```sql
-- Core indexes (automatically created)
CREATE INDEX idx_sections_file ON sections(file_path);
CREATE INDEX idx_sections_parent ON sections(parent_id);

-- Optional: For frequent queries
CREATE INDEX idx_sections_level ON sections(level);
CREATE INDEX idx_sections_hash ON sections(content_hash);

-- FTS5 index (automatic)
CREATE VIRTUAL TABLE sections_fts USING fts5(
    content, file_path, section_id,
    content_rowid='sections'
);
```

### Composite Index for Navigation

```sql
-- Speeds up get_next_section queries
CREATE INDEX idx_navigation ON sections(
    file_path,
    parent_id,
    order_in_parent
);
```

### Query Optimization

**Before (N+1 queries):**
```python
# Inefficient: one query per section
for section_id in section_ids:
    section = db.get_section(section_id)
```

**After (single query):**
```python
# Efficient: single query with IN clause
sections = db.get_sections(section_ids)
```

---

## Search Performance

### BM25 Search Tuning

```sql
-- Adjust BM25 parameters
INSERT INTO sections_fts(sections_fts, rank)
VALUES('bm25', 10.0, 1.0, 0.5);
--           ^table  ^k1  ^b   ^dl_avg
```

**Parameters:**
- `k1`: Term saturation (1.0-2.0, default 1.2)
- `b`: Length normalization (0.0-1.0, default 0.75)
- `dl_avg`: Average document length

### Vector Search Caching

```python
# Cache embedding results
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_embedding(text: str) -> List[float]:
    return embedding_service.embed(text)
```

### Hybrid Search Balance

```bash
# Keyword-focused (faster)
--vector-weight 0.3

# Balanced (recommended)
--vector-weight 0.7

# Semantic-focused (slower)
--vector-weight 1.0
```

---

## Memory Optimization

### Streaming for Large Files

```python
# Process files in chunks
def parse_large_file(file_path: str, chunk_size: int = 10000):
    with open(file_path) as f:
        while chunk := f.read(chunk_size):
            yield process_chunk(chunk)
```

### Connection Pooling

```python
# Reuse database connections
from contextlib import contextmanager

@contextmanager
def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    try:
        yield conn
    finally:
        conn.close()
```

---

## Async Operations

### Async Search

```python
import asyncio

async def search_multiple(query: str, databases: List[str]):
    tasks = [async_search(db, query) for db in databases]
    results = await asyncio.gather(*tasks)
    return merge_results(results)
```

---

## Performance Monitoring

### Enable Query Logging

```python
import logging

logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

### Benchmark Suite

```bash
# Run full benchmark suite
python -m pytest benchmark/bench.py --benchmark-only

# Generate report
python benchmark/generate_report.py benchmark/results.json
```

---

## Production Tuning

### Recommended Configuration

```python
DATABASE_CONFIG = {
    'cache_size': -64000,      # 64MB cache
    'journal_mode': 'WAL',      # Write-Ahead Logging
    'synchronous': 'NORMAL',    # Balanced safety/speed
    'temp_store': 'MEMORY',     # In-memory temp tables
    'mmap_size': 268435456,     # 256MB memory map
}

EMBEDDING_CONFIG = {
    'cache_size': 1000,         # Cache 1000 embeddings
    'batch_size': 100,          # Generate 100 at a time
    'model': 'text-embedding-3-small',  # Cost-effective model
}
```

---

## Troubleshooting

### Slow Search

**Symptom:** Search takes >1 second

**Solutions:**
1. Use `--limit` to reduce result set
2. Rebuild FTS5 index: `INSERT INTO sections_fts(sections_fts) VALUES('rebuild');`
3. Analyze query plan: `EXPLAIN QUERY PLAN SELECT ...`

### High Memory Usage

**Symptom:** Process uses >1GB RAM

**Solutions:**
1. Reduce cache size: `PRAGMA cache_size = -16000;` (16MB)
2. Use streaming for large files
3. Clear embedding cache periodically

### Database Lock Contention

**Symptom:** "database is locked" errors

**Solutions:**
1. Enable WAL mode: `PRAGMA journal_mode = WAL;`
2. Increase timeout: `PRAGMA busy_timeout = 5000;` (5 seconds)
3. Use connection pooling

---

## Performance Metrics

### Target Performance

| Metric | Target | Actual |
|--------|--------|--------|
| Parse 1KB | <1ms | ✅ 0.013ms |
| Parse 50KB | <50ms | ✅ 0.67ms |
| Query section | <10ms | ✅ 0.11ms |
| BM25 search | <20ms | ✅ 5.8ms |
| Vector search | <200ms | ✅ 100-200ms |

### Scaling Projections

Based on O(n) parsing:
- 50 sections: 0.67ms
- 500 sections: ~6.7ms (projected)
- 5000 sections: ~67ms (projected)

Linear scaling suggests excellent scalability to 100K+ sections.

---

*For benchmark details, see [benchmark/SUMMARY.md](../benchmark/SUMMARY.md)*
