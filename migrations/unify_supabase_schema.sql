-- Supabase Schema Migration: Unification Task
-- Adds missing columns to sections table for feature parity with SQLite
--
-- This migration ensures SupabaseStore has the same capabilities as DatabaseStore:
-- - line_start, line_end: For script round-trip reconstruction
-- - closing_tag_prefix: For XML tag support
-- - Indexes for performance
-- - Full-text search support
--
-- Run this against your Supabase project before using the new features.

-- Phase 1: Add missing columns to sections table
-- These columns are required for byte-perfect round-trip and script handler support

ALTER TABLE sections
ADD COLUMN IF NOT EXISTS line_start INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS line_end INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS closing_tag_prefix TEXT DEFAULT '';

-- Phase 2: Add indexes for progressive disclosure queries
-- These indexes improve performance for get_next_section() and order-based queries

CREATE INDEX IF NOT EXISTS idx_sections_file_order
ON sections(file_id, parent_id, order_index);

CREATE INDEX IF NOT EXISTS idx_sections_file_parent
ON sections(file_id, parent_id);

-- Phase 3: Add GIN index for full-text search
-- Enables fast content search across titles and content

CREATE INDEX IF NOT EXISTS idx_sections_search
ON sections USING gin(to_tsvector('english', title || ' ' || content));

-- Phase 4: Add timestamps to files table for tracking
-- These are useful for auditing and incremental updates

ALTER TABLE files
ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

-- Phase 5: Update existing rows to set defaults
-- Ensure all existing sections have proper default values

UPDATE sections
SET closing_tag_prefix = ''
WHERE closing_tag_prefix IS NULL;

UPDATE sections
SET line_start = 0
WHERE line_start IS NULL;

UPDATE sections
SET line_end = 0
WHERE line_end IS NULL;

-- Phase 6: Add function to update updated_at timestamp
-- Automatically updates the updated_at column when a row is modified

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply the trigger to the files table
DROP TRIGGER IF EXISTS update_files_updated_at ON files;
CREATE TRIGGER update_files_updated_at
BEFORE UPDATE ON files
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- Verification queries
-- Run these after the migration to verify everything is set up correctly:

-- Check sections table has new columns:
-- SELECT column_name, data_type, column_default
-- FROM information_schema.columns
-- WHERE table_name = 'sections'
--   AND column_name IN ('line_start', 'line_end', 'closing_tag_prefix');

-- Check indexes were created:
-- SELECT indexname, tablename
-- FROM pg_indexes
-- WHERE tablename = 'sections'
--   AND indexname LIKE 'idx_sections_%';

-- Check timestamps on files table:
-- SELECT column_name, data_type, column_default
-- FROM information_schema.columns
-- WHERE table_name = 'files'
--   AND column_name IN ('created_at', 'updated_at');
