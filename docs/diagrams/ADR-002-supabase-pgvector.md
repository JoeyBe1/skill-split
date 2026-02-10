# ADR-002: Supabase + pgvector for Cloud Storage

**Status**: Accepted
**Date**: 2025-02-10
**Context**: Phase 07 - Supabase Integration

## Context

As the skill-split library grows (1,365 files, 19,207 sections), there's a need for:
1. Cloud backup and synchronization
2. Semantic search capabilities beyond keyword matching
3. Multi-user access and collaboration
4. Automatic backups and disaster recovery

## Decision

Use Supabase (PostgreSQL) with pgvector extension for cloud storage and vector similarity search.

### Technical Details

- **PostgreSQL**: Reliable relational database with ACID guarantees
- **pgvector Extension**: Vector similarity search with ivfflat indexing
- **OpenAI Embeddings**: text-embedding-3-small model (1536 dimensions)
- **RPC Functions**: Custom SQL functions for efficient vector matching
- **Real-time**: PostgreSQL subscriptions for live updates

### Implementation

```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Add embedding column to sections
ALTER TABLE sections ADD COLUMN embedding vector(1536);

-- Create ivfflat index for fast similarity search
CREATE INDEX ON sections USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- RPC function for vector search
CREATE OR REPLACE FUNCTION match_sections(
  query_embedding vector(1536),
  match_threshold float,
  match_count int
) RETURNS TABLE (
  section_id uuid,
  similarity float
) LANGUAGE plpgsql AS $$
BEGIN
  RETURN QUERY
  SELECT
    id,
    1 - (embedding <=> query_embedding) as similarity
  FROM sections
  WHERE 1 - (embedding <=> query_embedding) > match_threshold
  ORDER BY embedding <=> query_embedding
  LIMIT match_count;
END;
$$;
```

```python
# Generate embeddings
embedding_service = EmbeddingService(openai_api_key)
embedding = embedding_service.generate_embedding(section_content)

# Vector search
results = supabase_store.client.rpc('match_sections', {
    'query_embedding': query_embedding,
    'match_threshold': 0.7,
    'match_count': 10
}).execute()
```

## Rationale

### Advantages

1. **Vector Similarity**: Semantic search beyond keyword matching
2. **Managed Service**: Automatic backups, replication, and scaling
3. **Real-time**: PostgreSQL subscriptions for live updates
4. **Multi-user**: Built-in authentication and row-level security
5. **Free Tier**: Generous limits for development and small projects

### Alternatives Considered

1. **Cloud-only SQLite (Dropbox, Google Drive)**
   - Rejected: No native search capabilities
   - Synchronization complexity
   - No multi-user support

2. **Elasticsearch**
   - Rejected: Higher infrastructure cost
   - Steeper learning curve
   - Overkill for document storage focus

3. **Pinecone (Vector-only DB)**
   - Rejected: Doesn't support relational data
   - Additional cost for vector storage
   - Would need separate storage for files/sections

## Consequences

### Positive

- Semantic search finds conceptually similar content
- Automatic backups and point-in-time recovery
- Real-time collaboration possibilities
- CDN integration for fast file downloads
- Row-level security for multi-user access

### Negative

- Requires network connectivity
- OpenAI API costs for embeddings ($0.02/1M tokens)
- Vendor lock-in (though PostgreSQL is portable)
- Latency for remote operations (~50-100ms)

### Mitigation

- Local SQLite as primary cache for fast operations
- Batch embedding generation to reduce API calls
- Periodic exports to SQLite for offline access
- Embedding caching to avoid regeneration

## Related Decisions

- [ADR-001](./ADR-001-sqlite-fts5.md): SQLite FTS5 for local search
- [ADR-003](./ADR-003-hybrid-search.md): Hybrid search combining both approaches

## References

- [Supabase Documentation](https://supabase.com/docs)
- [pgvector GitHub](https://github.com/pgvector/pgvector)
- [OpenAI Embeddings](https://platform.openai.com/docs/guides/embeddings)
