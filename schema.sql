-- Supabase Schema for skill-split Library Checkout System

-- 1. Files table (metadata about parsed files)
CREATE TABLE files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    storage_path TEXT UNIQUE NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('skill', 'command', 'plugin', 'reference')),
    frontmatter TEXT,
    hash TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_files_type ON files(type);
CREATE INDEX idx_files_name ON files(name);

-- 2. Sections table (hierarchical content structure)
CREATE TABLE sections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_id UUID NOT NULL REFERENCES files(id) ON DELETE CASCADE,
    parent_id UUID REFERENCES sections(id) ON DELETE CASCADE,
    level INTEGER NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    order_index INTEGER NOT NULL,
    line_start INTEGER NOT NULL,
    line_end INTEGER NOT NULL
);

CREATE INDEX idx_sections_file ON sections(file_id);
CREATE INDEX idx_sections_parent ON sections(parent_id);
CREATE INDEX idx_sections_order ON sections(file_id, order_index);

-- 3. Checkouts table (track active deployments)
CREATE TABLE checkouts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_id UUID REFERENCES files(id) ON DELETE CASCADE,
    section_id UUID REFERENCES sections(id) ON DELETE CASCADE,
    user_name TEXT NOT NULL,
    target_path TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'returned')),
    checked_out_at TIMESTAMPTZ DEFAULT NOW(),
    checked_in_at TIMESTAMPTZ,
    notes TEXT,
    CONSTRAINT file_or_section CHECK (
        (file_id IS NOT NULL AND section_id IS NULL) OR
        (file_id IS NULL AND section_id IS NOT NULL)
    )
);

CREATE INDEX idx_checkouts_status ON checkouts(status);
CREATE INDEX idx_checkouts_user ON checkouts(user_name);
CREATE INDEX idx_checkouts_file ON checkouts(file_id);
CREATE INDEX idx_checkouts_target ON checkouts(target_path);

-- 4. Deployment paths table (canonical paths for each file type)
CREATE TABLE deployment_paths (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_type TEXT NOT NULL CHECK (file_type IN ('skill', 'command', 'plugin', 'reference')),
    base_path TEXT NOT NULL,
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Prepopulate with Claude Code paths
INSERT INTO deployment_paths (file_type, base_path, is_default) VALUES
    ('skill', '~/.claude/skills/', TRUE),
    ('command', '~/.claude/commands/', TRUE),
    ('plugin', '~/.claude/plugins/', TRUE),
    ('reference', '~/.claude/references/', TRUE);

-- Auto-update trigger for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_files_updated_at BEFORE UPDATE ON files
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- View for active checkouts
CREATE VIEW active_checkouts AS
SELECT
    c.id,
    c.user_name,
    c.target_path,
    c.checked_out_at,
    c.notes,
    f.name AS file_name,
    f.type AS file_type,
    f.storage_path
FROM checkouts c
LEFT JOIN files f ON c.file_id = f.id
WHERE c.status = 'active'
ORDER BY c.checked_out_at DESC;
