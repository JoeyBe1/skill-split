-- Create section_embeddings table for storing vector embeddings
-- Task 8.2: Create Embeddings Table
-- Purpose: Store section embeddings with fast vector similarity search
-- Time: 20 min
-- Dependencies: Task 8.1 (pgvector extension)

CREATE TABLE section_embeddings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    section_id INTEGER NOT NULL REFERENCES sections(id) ON DELETE CASCADE,
    embedding VECTOR(1536),  -- text-embedding-3-small dimensions
    model_name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(section_id, model_name)
);

-- Index for fast vector similarity search
CREATE INDEX section_embeddings_vector_idx
ON section_embeddings
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Additional indexes for efficient queries
CREATE INDEX section_embeddings_section_id_idx ON section_embeddings(section_id);
CREATE INDEX section_embeddings_model_name_idx ON section_embeddings(model_name);
CREATE INDEX section_embeddings_created_at_idx ON section_embeddings(created_at);
