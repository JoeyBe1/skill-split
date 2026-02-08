-- Enable pgvector extension for vector similarity search
-- Task 8.1: Enable pgvector Extension
-- Purpose: Enable PostgreSQL pgvector extension for embedding storage and search
-- Time: 5 min
-- Dependencies: None

CREATE EXTENSION IF NOT EXISTS vector;
