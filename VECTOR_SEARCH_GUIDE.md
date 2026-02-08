# Vector Search Guide

**Version**: 1.0
**Status**: Production Ready
**Last Updated**: 2026-02-05

---

## Overview

This guide covers the vector search capabilities in skill-split, including semantic similarity search, hybrid ranking, and cost management.

Vector search enables you to find relevant sections based on semantic meaning rather than exact keyword matching. Combined with traditional text search through hybrid ranking, it provides superior relevance.

## Quick Start

### Enable Vector Search

Set environment variables:

```bash
export ENABLE_EMBEDDINGS=true
export OPENAI_API_KEY=sk-...  # Your OpenAI API key
export SUPABASE_URL=https://...  # Your Supabase URL
export SUPABASE_KEY=...  # Your Supabase anon key
```

### Generate Embeddings for Existing Sections

Run the batch migration script to generate embeddings for all existing sections:

```bash
python3 scripts/generate_embeddings.py
```

This will:
1. Count total sections requiring embeddings
2. Generate embeddings in batches of 100
3. Track progress and estimated cost
4. Update embedding metadata in the database
5. Resume gracefully if interrupted

Output example:
```
============================================================
EMBEDDING MIGRATION - Generating embeddings for all sections
============================================================

📊 Total sections to process: 19207
📊 Starting from offset: 0

📦 Processing batch: 0-100 / 19207
✓ Embedded section 1 (156 tokens)
✓ Embedded section 2 (234 tokens)
...
💾 Stored 100 embeddings in this batch

============================================================
MIGRATION SUMMARY
============================================================
✓ Total sections processed: 19207
✓ Newly embedded: 19207
✓ Already embedded: 0
✗ Failed: 0
📊 Total tokens used: 2,040,821
💰 Estimated cost: $0.0408
⏱ Duration: 0:45:32
============================================================
```

### Search Semantically

Use the CLI to perform semantic searches:

```bash
# Basic semantic search
./skill_split.py search-semantic "authentication patterns"

# Adjust vector vs. text weight (0.0 = pure text, 1.0 = pure vector)
./skill_split.py search-semantic "browser automation" --vector-weight 0.8 --limit 15

# Pure vector search (ignores text matching)
./skill_split.py search-semantic "react hooks" --vector-weight 1.0
```

## How Vector Search Works

### Architecture

1. **Embedding Generation**: Text content → 1536-dimensional vector via OpenAI API
2. **Storage**: Vectors stored in Supabase with pgvector extension
3. **Query Processing**: Query text → embedding → similarity search
4. **Ranking**: Vector similarity + text relevance → hybrid score

### Embedding Model

- **Model**: OpenAI text-embedding-3-small
- **Dimensions**: 1536
- **Training Data**: Natural text from Claude Code skills and tools
- **Cost**: $0.02 per 1M tokens

### Similarity Scoring

Vector similarity uses **cosine distance**, which measures the angle between embedding vectors:

```
Similarity = 1 - (cosine_distance)
Range: [0, 1] where 1 = identical, 0 = completely different
```

### Hybrid Ranking

Hybrid search combines vector similarity with keyword-based text relevance:

```
Hybrid Score = (vector_weight × vector_similarity) +
               ((1 - vector_weight) × text_relevance)
```

**Default**: vector_weight = 0.7 (70% semantic, 30% keyword)

## CLI Commands

### search-semantic

Search sections using semantic similarity and hybrid ranking.

```bash
./skill_split.py search-semantic [OPTIONS] QUERY
```

**Options**:
- `--limit INT`: Maximum results to return (default: 10)
- `--vector-weight FLOAT`: Weight for vector similarity (0.0-1.0, default: 0.7)
- `--db STR`: Database path or "supabase" (default: supabase)

**Examples**:

```bash
# Find authentication-related sections
./skill_split.py search-semantic "how to implement JWT tokens" --limit 20

# Pure semantic search (ignores keywords)
./skill_split.py search-semantic "callbacks and promises" --vector-weight 1.0

# Favor text matching for specific terms
./skill_split.py search-semantic "Docker container configuration" --vector-weight 0.2
```

**Output**:
```
[0.95] Authentication with JWT - OAuth patterns (ID: 1234)
[0.91] Token-based auth middleware (ID: 1235)
[0.87] Session management strategies (ID: 1236)
```

## Tuning Vector Weight

### When to Use Pure Vector Search (weight = 1.0)

Best for:
- Semantic/conceptual searches ("coding best practices")
- Vague or natural language queries ("how to debug errors")
- Cross-domain searches ("apply auth patterns to form validation")

Example:
```bash
./skill_split.py search-semantic "what's a better way to handle state?" --vector-weight 1.0
```

### When to Use Balanced Search (weight = 0.5)

Best for:
- Mixed intent searches
- When you want both semantics AND keywords

Example:
```bash
./skill_split.py search-semantic "React hooks and custom implementations" --vector-weight 0.5
```

### When to Use Pure Text Search (weight = 0.0)

Best for:
- Precise terminology ("useCallback hook")
- Acronyms ("JWT", "CORS", "REST")
- Product/tool names ("Next.js", "TypeScript")

Example:
```bash
./skill_split.py search-semantic "next.js middleware" --vector-weight 0.0
```

## Cost Analysis

### One-Time Costs (Initial Setup)

**Scenario**: 19,207 sections at ~100 tokens average

```
Tokens: 19,207 × 100 = 1,920,700 tokens
Cost: (1,920,700 / 1,000,000) × $0.02 = $0.0384
```

**Estimate**: ~$0.04 for initial embedding

### Monthly Costs

**Scenario**: 50 new sections per month at ~100 tokens average

```
Tokens: 50 × 100 = 5,000 tokens
Cost: (5,000 / 1,000,000) × $0.02 = $0.0001
```

**Estimate**: ~$0.0001 per month for new content

### Per-Query Costs

**Cost per search**: ~$0.0001 per query (embedding the search query)

With 100 searches per month:
```
100 × $0.0001 = $0.01 per month
```

### Total Monthly Estimate

After initial setup:
```
New sections: $0.0001
Queries: $0.01
Total: ~$0.011 per month ($0.13 per year)
```

## Performance Characteristics

### Query Latency

Typical latencies on production database (19,207 sections):

```
Vector search only:     25-50ms
Text search only:       10-30ms
Hybrid search:          40-80ms
Cache hit (embedding):  20-40ms faster
```

### Throughput

Expected queries per second (single connection):

```
Pure vector:            20-40 qps
Pure text:              33-100 qps
Hybrid:                 12-25 qps
```

### Memory Usage

Vector storage requirements:

```
Per section: 1536 floats × 4 bytes = 6,144 bytes (~6 KB)
Total (19,207 sections): ~118 MB
Supabase overhead: ~50% = ~177 MB
```

## Caching

Vector embeddings are cached after generation to avoid redundant API calls:

```python
# First query - generates embedding (costs money)
results = hybrid_search.hybrid_search("authentication")  # ~$0.0001

# Second query with same text - uses cache (free)
results = hybrid_search.hybrid_search("authentication")  # $0.0000
```

**Cache Stats** (from metrics):
```python
metrics = hybrid_search.get_metrics()
print(f"Cache hit rate: {metrics['cache_hit_rate']:.1%}")
print(f"Cache hits: {metrics['embedding_cache_hits']}")
print(f"Cache misses: {metrics['embedding_cache_misses']}")
```

## Database Setup

### Prerequisites

1. Supabase project with PostgreSQL
2. pgvector extension enabled
3. Embeddings table created

### Schema

```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Embeddings table
CREATE TABLE section_embeddings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    section_id INTEGER NOT NULL REFERENCES sections(id) ON DELETE CASCADE,
    embedding VECTOR(1536),
    model_name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(section_id, model_name)
);

-- Index for fast search
CREATE INDEX section_embeddings_vector_idx
ON section_embeddings
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

### Apply Migrations

Run PostgreSQL migrations to enable vector search:

```bash
# Enable pgvector extension
psql -d your_database -f migrations/enable_pgvector.sql

# Create embeddings table
psql -d your_database -f migrations/create_embeddings_table.sql

# Add embedding metadata tracking
psql -d your_database -f migrations/add_embedding_metadata.sql

# Optimize vector search performance
psql -d your_database -f migrations/optimize_vector_search.sql
```

Or apply via Supabase SQL Editor:
1. Navigate to SQL Editor in Supabase dashboard
2. Create a new query
3. Copy content from `migrations/optimize_vector_search.sql`
4. Run the query

## Programmatic Usage

### Basic Vector Search

```python
from core.embedding_service import EmbeddingService
from core.hybrid_search import HybridSearch
from core.supabase_store import SupabaseStore
from core.query import QueryAPI

# Initialize services
embedding_service = EmbeddingService("sk-...")
supabase_store = SupabaseStore(url, key)
query_api = QueryAPI(database_store)

hybrid_search = HybridSearch(embedding_service, supabase_store, query_api)

# Perform hybrid search
results = hybrid_search.hybrid_search(
    "authentication patterns",
    limit=10,
    vector_weight=0.7
)

# results: List[Tuple[section_id, score]]
for section_id, score in results:
    section = query_api.get_section(section_id)
    print(f"[{score:.2f}] {section.title}")
```

### Pure Vector Search

```python
embedding = embedding_service.generate_embedding("your query")
results = hybrid_search.vector_search(embedding, limit=10)
```

### Access Metrics

```python
metrics = hybrid_search.get_metrics()
print(f"Average latency: {metrics['average_latency_ms']:.1f}ms")
print(f"Total searches: {metrics['total_searches']}")
print(f"Cache hit rate: {metrics['cache_hit_rate']:.1%}")
print(f"Avg embedding time: {metrics['average_embedding_time_ms']:.1f}ms")
```

## Troubleshooting

### "pgvector not installed"

Enable the extension:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### "section_embeddings table not found"

Apply the embeddings table migration:
```bash
python3 scripts/generate_embeddings.py
```

### "API rate limit exceeded"

Reduce batch size or add delays between API calls:
```python
# In scripts/generate_embeddings.py
time.sleep(2)  # 2-second delay between batches
```

### "Embeddings generation very slow"

This is expected - 19K sections at ~0.5s per batch takes ~45 minutes.

Run in background:
```bash
nohup python3 scripts/generate_embeddings.py > embeddings.log 2>&1 &
```

Resume from checkpoint if interrupted:
```python
migration = EmbeddingMigration(supabase_store, embedding_service)
stats = migration.run(resume_from=5000)  # Start from section 5000
```

### "Low relevance scores"

Try adjusting vector weight or query formulation:

```bash
# More semantic
./skill_split.py search-semantic "related concept" --vector-weight 1.0

# More keyword-focused
./skill_split.py search-semantic "specific terms" --vector-weight 0.0
```

## Performance Optimization

### IVFFlat Tuning

Adjust the `ivfflat.probes` parameter for accuracy/speed tradeoff:

```sql
-- Faster but less accurate (fewer candidates examined)
SET ivfflat.probes = 5;

-- Slower but more accurate (more candidates examined)
SET ivfflat.probes = 20;

-- Default (good balance)
SET ivfflat.probes = 10;
```

### Batch Size Tuning

For generating embeddings, tune batch size in `scripts/generate_embeddings.py`:

```python
batch_size = 100  # Smaller = more API calls, faster failures recovery
                  # Larger = fewer API calls, but longer to retry on failure
```

### Index Optimization

Monitor index bloat and rebuild if needed:

```sql
-- Check index size
SELECT pg_size_pretty(pg_relation_size('section_embeddings_vector_idx'));

-- Rebuild index (optional, can be slow)
REINDEX INDEX CONCURRENTLY section_embeddings_vector_idx;
```

## Deployment Checklist

- [ ] OpenAI API key configured
- [ ] Supabase pgvector extension enabled
- [ ] `section_embeddings` table created
- [ ] Vector indexes applied
- [ ] `embedding_metadata` table created
- [ ] Batch embedding script runs successfully
- [ ] Vector search queries working
- [ ] Monitoring/cost tracking in place
- [ ] Team educated on vector weight tuning

## Related Documentation

- [Phase 14: Vector Search Plan](docs/plans/phase-14-vector-search.md)
- [Hybrid Search Implementation](core/hybrid_search.py)
- [Embedding Service](core/embedding_service.py)
- [Migration Scripts](scripts/generate_embeddings.py)

## Support

For issues or questions:
1. Check [Troubleshooting](#troubleshooting) section
2. Review performance benchmarks: `python3 benchmarks/vector_search_benchmark.py`
3. Check metrics: `hybrid_search.get_metrics()`
4. Monitor logs: `tail -f embeddings.log`

---

**Last Updated**: 2026-02-05
**Production Ready**: Yes
**Cost Tracking**: Recommended (see cost analysis section)
