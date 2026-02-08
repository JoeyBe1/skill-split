-- Create embedding_metadata table for tracking embedding generation stats
-- Task 8.3: Add Embedding Metadata
-- Purpose: Track embedding generation statistics and costs
-- Time: 20 min
-- Dependencies: Task 8.2 (section_embeddings table must exist)

CREATE TABLE embedding_metadata (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    total_sections INTEGER NOT NULL DEFAULT 0,
    embedded_sections INTEGER NOT NULL DEFAULT 0,
    last_batch_at TIMESTAMP,
    total_tokens_used INTEGER NOT NULL DEFAULT 0,
    estimated_cost_usd DECIMAL(10, 4) NOT NULL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Index for efficient metadata queries
CREATE INDEX embedding_metadata_updated_at_idx ON embedding_metadata(updated_at);

-- Trigger to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_embedding_metadata_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER embedding_metadata_updated_at_trigger
BEFORE UPDATE ON embedding_metadata
FOR EACH ROW
EXECUTE FUNCTION update_embedding_metadata_timestamp();
