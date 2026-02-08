-- Optimize Vector Search Performance
-- This migration adds indexes and optimizations for fast vector similarity search
-- and hybrid search queries.
--
-- Features:
-- - IVFFlat index for fast approximate nearest neighbor search
-- - Full-text search index for text-based queries
-- - Composite index for hybrid search optimization
-- - Query parameter tuning for accuracy/speed tradeoff

-- Enable IVFFlat index tuning for better performance
-- Higher probes = more accurate but slower
-- Lower probes = faster but less accurate (10 is reasonable default)
SET ivfflat.probes = 10;

-- Create IVFFlat index on section embeddings vector column
-- This is the primary optimization for vector similarity search
-- Uses cosine distance for semantic similarity
-- lists=100 is good for datasets with 10K-100K vectors
CREATE INDEX IF NOT EXISTS section_embeddings_vector_idx
ON section_embeddings
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Create full-text search index for text-based queries
-- Allows fast keyword matching and relevance ranking
CREATE INDEX IF NOT EXISTS sections_content_tsvector_idx
ON sections USING GIN (to_tsvector('english', content));

-- Create composite index for fast title searches
CREATE INDEX IF NOT EXISTS sections_title_idx
ON sections (title);

-- Create index on section_id for efficient joins
CREATE INDEX IF NOT EXISTS section_embeddings_section_id_idx
ON section_embeddings (section_id);

-- Create index on model_name for embedding model filtering
CREATE INDEX IF NOT EXISTS section_embeddings_model_idx
ON section_embeddings (model_name);

-- Create index on file_id for file-level queries
CREATE INDEX IF NOT EXISTS sections_file_id_idx
ON sections (file_id);

-- Create partial index for sections with embeddings
-- Speeds up queries filtering by embedded sections
CREATE INDEX IF NOT EXISTS sections_embedded_idx
ON sections (id)
WHERE id IN (SELECT DISTINCT section_id FROM section_embeddings);

-- Set up query planner statistics for better execution plans
-- Run ANALYZE to gather statistics on the indexed columns
ANALYZE section_embeddings;
ANALYZE sections;

-- Optional: Enable parallel query execution for large result sets
-- This can speed up complex aggregations and joins
ALTER TABLE section_embeddings SET (parallel_workers = 4);
ALTER TABLE sections SET (parallel_workers = 4);

-- Create function for efficient vector search
-- This RPC function is used by the HybridSearch class for vector similarity queries
CREATE OR REPLACE FUNCTION match_sections(
  query_embedding VECTOR(1536),
  match_threshold FLOAT8 = 0.7,
  match_count INT = 10
)
RETURNS TABLE (
  section_id BIGINT,
  similarity FLOAT8
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    se.section_id,
    (1 - (se.embedding <=> query_embedding))::FLOAT8 as similarity
  FROM section_embeddings se
  WHERE (1 - (se.embedding <=> query_embedding)) > match_threshold
  ORDER BY se.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;

-- Create function for full-text search
-- Used by QueryAPI for keyword-based searches
CREATE OR REPLACE FUNCTION search_sections_text(
  query_text TEXT,
  match_count INT = 10
)
RETURNS TABLE (
  section_id BIGINT,
  relevance FLOAT8,
  title TEXT
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    s.id,
    ts_rank(to_tsvector('english', s.content), plainto_tsquery('english', query_text))::FLOAT8 as relevance,
    s.title
  FROM sections s
  WHERE to_tsvector('english', s.content) @@ plainto_tsquery('english', query_text)
  ORDER BY relevance DESC
  LIMIT match_count;
END;
$$;

-- Create function for hybrid search ranking
-- Combines vector and text scores with configurable weighting
CREATE OR REPLACE FUNCTION hybrid_search(
  query_embedding VECTOR(1536),
  query_text TEXT,
  vector_weight FLOAT8 = 0.7,
  match_count INT = 10
)
RETURNS TABLE (
  section_id BIGINT,
  hybrid_score FLOAT8,
  vector_similarity FLOAT8,
  text_relevance FLOAT8,
  title TEXT
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  WITH vector_results AS (
    SELECT
      se.section_id,
      (1 - (se.embedding <=> query_embedding))::FLOAT8 as vector_sim
    FROM section_embeddings se
    ORDER BY se.embedding <=> query_embedding
    LIMIT match_count * 2
  ),
  text_results AS (
    SELECT
      s.id,
      ts_rank(to_tsvector('english', s.content), plainto_tsquery('english', query_text))::FLOAT8 as text_rel
    FROM sections s
    WHERE to_tsvector('english', s.content) @@ plainto_tsquery('english', query_text)
    ORDER BY text_rel DESC
    LIMIT match_count * 2
  ),
  combined AS (
    SELECT
      COALESCE(v.section_id, t.id) as section_id,
      COALESCE(v.vector_sim, 0.0)::FLOAT8 as vector_sim,
      COALESCE(t.text_rel, 0.0)::FLOAT8 as text_rel,
      s.title
    FROM vector_results v
    FULL OUTER JOIN text_results t ON v.section_id = t.id
    JOIN sections s ON COALESCE(v.section_id, t.id) = s.id
  )
  SELECT
    section_id,
    (vector_weight * vector_sim + (1 - vector_weight) * text_rel)::FLOAT8 as hybrid_score,
    vector_sim,
    text_rel,
    title
  FROM combined
  ORDER BY hybrid_score DESC
  LIMIT match_count;
END;
$$;

-- Add comment documenting the optimizations
COMMENT ON INDEX section_embeddings_vector_idx IS 'IVFFlat index for fast vector similarity search using cosine distance';
COMMENT ON INDEX sections_content_tsvector_idx IS 'GIN full-text search index for keyword-based queries';
COMMENT ON FUNCTION match_sections IS 'Efficient vector similarity search using pgvector';
COMMENT ON FUNCTION search_sections_text IS 'Full-text search for keyword matching';
COMMENT ON FUNCTION hybrid_search IS 'Hybrid search combining vector and text rankings';
