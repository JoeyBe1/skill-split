# Installation Guide

This guide covers installing and setting up skill-split on your system.

## Table of Contents

- [System Requirements](#system-requirements)
- [Installation Methods](#installation-methods)
- [Verification](#verification)
- [Configuration](#configuration)
- [Optional Features](#optional-features)
- [Troubleshooting](#troubleshooting)

## System Requirements

### Required

- **Python:** 3.8 or higher
- **Operating System:** Linux, macOS, or Windows
- **Disk Space:** ~50 MB for core installation

### Optional (for advanced features)

- **Supabase Account:** For remote storage and semantic search
- **OpenAI API Key:** For vector embeddings and semantic search
- **Git:** For cloning the repository

## Installation Methods

### Method 1: Install from Source (Recommended)

This method gives you the latest code and allows for easy development.

```bash
# Clone the repository
git clone https://github.com/JoeyBe1/skill-split.git
cd skill-split

# Install in editable mode
pip install -e .

# Or install dependencies manually
pip install click pytest
```

**Advantages:**
- Latest features and bug fixes
- Easy to modify and contribute
- Automatic PATH configuration

### Method 2: Using pip (Future Release)

When published to PyPI:

```bash
pip install skill-split
```

### Method 3: Using Docker

Create a `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Set entrypoint
ENTRYPOINT ["python", "skill_split.py"]
```

Build and run:

```bash
docker build -t skill-split .
docker run -v $(pwd):/data skill-split parse /data/SKILL.md
```

### Method 4: Using pipenv

```bash
# Install pipenv if needed
pip install pipenv

# Clone repository
git clone https://github.com/JoeyBe1/skill-split.git
cd skill-split

# Install with pipenv
pipenv install --dev

# Run commands
pipenv run python skill_split.py --help
```

## Verification

After installation, verify that skill-split is working correctly:

```bash
# Check version/help
python skill_split.py --help

# Run test suite
python -m pytest test/ -v

# Parse a test file
python skill_split.py parse test/fixtures/simple_skill.md
```

Expected output from `--help`:

```
Usage: skill_split.py [OPTIONS] COMMAND [ARGS]...

  Intelligently split YAML and Markdown files into sections for progressive
  disclosure.

Options:
  --version  Show the version and exit.
  --help     Show this message and exit.

Commands:
  backup          Create a backup of the database
  checkin         Check in a deployed file
  checkout        Deploy a file from the library
  get             Get file metadata and frontmatter
  get-section     Get a specific section by ID
  ingest          Ingest files into Supabase
  list            List all sections in a file
  list-library    List all files in the library
  next            Get next section (progressive disclosure)
  parse           Parse a file and display its structure
  restore         Restore database from backup
  search          Search sections by content (BM25)
  search-library  Search the library
  search-semantic Search sections using semantic/hybrid search
  status          Show active checkouts
  store           Store a file in the database
  tree            Display section hierarchy as a tree
  validate        Validate a file structure
  verify          Verify round-trip integrity
```

## Configuration

### Environment Variables

Create a `.env` file in your project directory:

```bash
# Supabase Configuration (optional, for remote storage)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_PUBLISHABLE_KEY=your-anon-key

# OpenAI Configuration (optional, for semantic search)
OPENAI_API_KEY=sk-your-key-here

# Enable Embeddings (required for semantic search)
ENABLE_EMBEDDINGS=true
```

### Database Configuration

skill-split uses SQLite by default. Database locations:

- **Default:** `./skill_split.db` (current directory)
- **Production:** `~/.claude/databases/skill-split.db`
- **Custom:** Specify with `--db` flag

```bash
# Use default database
./skill_split.py store SKILL.md

# Use custom database
./skill_split.py store SKILL.md --db ~/.claude/databases/skill-split.db

# Use production database
./skill_split.py search "python" --db ~/.claude/databases/skill-split.db
```

### Supabase Setup (Optional)

For remote storage and semantic search:

1. **Create a Supabase Project**

   Visit https://supabase.com and create a new project.

2. **Get Your Credentials**

   - Go to Project Settings > API
   - Copy your project URL and anon/public key

3. **Configure Database Tables**

   Run the SQL setup script in your Supabase SQL Editor:

   ```sql
   -- Create files table
   CREATE TABLE files (
       id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
       path TEXT UNIQUE NOT NULL,
       original_hash TEXT,
       type TEXT,
       format TEXT,
       frontmatter TEXT,
       created_at TIMESTAMP DEFAULT NOW()
   );

   -- Create sections table
   CREATE TABLE sections (
       id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
       file_id UUID NOT NULL REFERENCES files(id) ON DELETE CASCADE,
       title TEXT,
       level INTEGER,
       content TEXT,
       start_byte INTEGER,
       end_byte INTEGER,
       line_start INTEGER,
       line_end INTEGER,
       parent_id UUID REFERENCES sections(id) ON DELETE CASCADE,
       order_index INTEGER,
       embedding VECTOR(1536),
       created_at TIMESTAMP DEFAULT NOW()
   );

   -- Create indexes
   CREATE INDEX idx_sections_file_id ON sections(file_id);
   CREATE INDEX idx_sections_parent_id ON sections(parent_id);
   ```

4. **Set Environment Variables**

   ```bash
   export SUPABASE_URL="https://your-project.supabase.co"
   export SUPABASE_PUBLISHABLE_KEY="your-anon-key"
   ```

## Optional Features

### Semantic Search

Requires OpenAI API and Supabase:

```bash
# Set OpenAI API key
export OPENAI_API_KEY="sk-your-key-here"

# Enable embeddings
export ENABLE_EMBEDDINGS=true

# Run semantic search
./skill_split.py search-semantic "code execution" --vector-weight 0.7
```

### Vector Embeddings

When storing files with semantic search enabled:

```bash
ENABLE_EMBEDDINGS=true ./skill_split.py store SKILL.md
```

This generates embeddings for each section using OpenAI's text-embedding-3-small model.

### Backup and Restore

Backups are stored in `~/.claude/backups/` by default:

```bash
# Create backup
./skill_split.py backup --output my-backup

# Restore from backup
./skill_split.py restore my-backup --overwrite
```

## Troubleshooting

### Python Not Found

**Problem:** `python: command not found`

**Solution:** Make sure Python 3.8+ is installed and in your PATH:

```bash
# Check Python version
python --version
# or
python3 --version

# On macOS with Homebrew
brew install python@3.11

# On Ubuntu/Debian
sudo apt-get install python3.11
```

### Permission Denied

**Problem:** Permission denied when running skill-split.py

**Solution:** Make the script executable:

```bash
chmod +x skill_split.py
```

### Module Not Found

**Problem:** `ModuleNotFoundError: No module named 'click'`

**Solution:** Install dependencies:

```bash
pip install -r requirements.txt
# or
pip install click pytest
```

### Database Locked

**Problem:** `sqlite3.OperationalError: database is locked`

**Solution:** Close other processes using the database or use a different database:

```bash
./skill_split.py store SKILL.md --db skill-split-new.db
```

### Supabase Connection Failed

**Problem:** `supabase.ClientError: Invalid API key`

**Solution:** Verify your environment variables:

```bash
echo $SUPABASE_URL
echo $SUPABASE_PUBLISHABLE_KEY

# Test connection
curl -I $SUPABASE_URL
```

### OpenAI API Error

**Problem:** `openai.error.AuthenticationError: No API key provided`

**Solution:** Set your OpenAI API key:

```bash
export OPENAI_API_KEY="sk-your-key-here"

# Verify it's set
echo $OPENAI_API_KEY
```

### Tests Failing

**Problem:** Tests fail with import errors

**Solution:** Install test dependencies:

```bash
pip install pytest pytest-mock pytest-cov
```

## Uninstallation

### From Source Installation

```bash
# Remove the installation
pip uninstall skill-split

# Or if installed in editable mode
rm -rf skill-split
```

### Clean Up Databases

```bash
# Remove default database
rm skill-split.db

# Remove production database
rm ~/.claude/databases/skill-split.db

# Remove backups
rm -rf ~/.claude/backups/
```

## Next Steps

After installation:

1. **Read the Quick Start:** [README.md](README.md)
2. **Try Examples:** [EXAMPLES.md](EXAMPLES.md)
3. **Explore the API:** [API.md](API.md)
4. **Contribute:** [CONTRIBUTING.md](CONTRIBUTING.md)

## Support

For installation issues:

1. Check the [Troubleshooting](#troubleshooting) section
2. Review existing GitHub issues
3. Open a new issue with your error message and environment details

---

**Last Updated:** 2026-02-10
