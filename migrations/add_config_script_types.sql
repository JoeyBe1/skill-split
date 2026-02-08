-- Migration: Add config and script file types to Supabase schema
-- Date: 2026-02-05

-- Drop the existing CHECK constraint
ALTER TABLE files DROP CONSTRAINT IF EXISTS files_type_check;

-- Add new CHECK constraint with all file types
ALTER TABLE files ADD CONSTRAINT files_type_check
CHECK (type IN (
    'skill',
    'command',
    'reference',
    'agent',
    'plugin',
    'hook',
    'output_style',
    'config',
    'documentation',
    'script'
));
