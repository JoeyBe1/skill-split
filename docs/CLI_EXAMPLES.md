# CLI Examples

**Last Updated:** 2026-02-10

Practical examples for skill-split CLI commands.

---

## Getting Started

### Check Installation

```bash
./skill_split.py --version
./skill_split.py --help
```

---

## Parsing and Validation

### Parse a Single File

```bash
./skill_split.py parse README.md
```

Output:
```
File: README.md
Format: markdown
Sections: 12
Heading 1: # skill-split
Heading 2: ## Features
...
```

### Validate File Structure

```bash
./skill_split.py validate README.md
```

Output:
```
✅ File structure is valid
✅ 12 sections found
✅ Hierarchical structure correct
```

### Verify Round-Trip

```bash
./skill_split.py verify README.md
```

Output:
```
✅ Parsing: SUCCESS
✅ Reconstruction: SUCCESS
✅ SHA256 Match: TRUE
```

---

## Storage Operations

### Store a File

```bash
./skill_split.py store README.md
```

### Store Multiple Files

```bash
./skill_split.py store docs/**/*.md
```

### Use Custom Database

```bash
./skill_split.py store README.md --db /path/to/database.db
```

### Store with Progress

```bash
./skill_split.py store large_file.md --verbose
```

---

## Search Operations

### BM25 Keyword Search (Default)

```bash
./skill_split.py search "authentication"
```

### Search with Limit

```bash
./skill_split.py search "python" --limit 5
```

### Boolean Operators

```bash
# AND - both terms must match
./skill_split.py search "authentication AND authorization"

# OR - either term matches (default for multiple words)
./skill_split.py search "python OR javascript"

# NOT - exclude term
./skill_split.py search "search NOT vector"

# NEAR - terms within N words
./skill_split.py search "database NEAR/5 sql"
```

### Phrase Search

```bash
./skill_split.py search '"progressive disclosure"'
```

---

## Semantic Search (Requires API Key)

### Pure Vector Search

```bash
ENABLE_EMBEDDINGS=true ./skill_split.py search-semantic "code execution" --vector-weight 1.0
```

### Hybrid Search (Recommended)

```bash
ENABLE_EMBEDDINGS=true ./skill_split.py search-semantic "user authentication" --vector-weight 0.7
```

### Tunable Vector Weight

```bash
# More keyword focused
ENABLE_EMBEDDINGS=true ./skill_split.py search-semantic "query" --vector-weight 0.3

# More semantic focused
ENABLE_EMBEDDINGS=true ./skill_split.py search-semantic "concept" --vector-weight 0.9
```

---

## Navigation

### List All Sections in a File

```bash
./skill_split.py list README.md
```

Output:
```
README.md Section Tree:
├── [1] # skill-split
├── [2] ## Features
│   ├── [3] ### Progressive Disclosure
│   └── [4] ### Search Modes
└── [5] ## Installation
```

### Get Specific Section

```bash
./skill_split.py get-section 42
```

Output:
```
Section ID: 42
Heading: ## Installation
Level: 2
Parent: 1

Content:
Install skill-split using pip...
```

### Navigate to Next Sibling

```bash
./skill_split.py next 42 README.md
```

### Navigate to First Child

```bash
./skill_split.py next 42 README.md --child
```

---

## Composition

### Compose New Skill from Sections

```bash
./skill_split.py compose --sections 1,5,10,15 --output my_new_skill.md
```

### Compose with Frontmatter

```bash
./skill_split.py compose \
  --sections 42,57,103 \
  --name "Python Handler Guide" \
  --description "Complete guide to Python handlers" \
  --output python_guide.md
```

### Compose from Specific File

```bash
./skill_split.py compose \
  --sections 1,2,3 \
  --file source.md \
  --output new.md
```

---

## Supabase Integration

### Ingest Files to Supabase

```bash
export SUPABASE_URL="https://xxx.supabase.co"
export SUPABASE_KEY="your-key"

./skill_split.py ingest README.md
```

### Search Remote Library

```bash
./skill_split.py search-library "authentication"
```

### Checkout File from Library

```bash
./skill_split.py checkout README.md
```

### Check In Modified File

```bash
./skill_split.py checkin README.md
```

### List All Library Files

```bash
./skill_split.py list-library
```

### Check Status

```bash
./skill_split.py status
```

Output:
```
Library Status:
├── Files: 1,365
├── Sections: 19,207
├── Storage: Supabase
└── Last Sync: 2026-02-10 10:30:00
```

---

## Progressive Disclosure Workflow

### Step 1: Search for Topic

```bash
./skill_split.py search "handler"
```

### Step 2: Load Relevant Section

```bash
./skill_split.py get-section 57
```

### Step 3: Navigate Sequentially

```bash
./skill_split.py next 57 python_handler.md
```

### Step 4: Drill Deeper

```bash
./skill_split.py next 57 python_handler.md --child
```

---

## Token Savings Example

```bash
# Load full file: 2,500 tokens
cat README.md

# Load single section: 50 tokens (98% savings)
./skill_split.py get-section 42
```

---

## Performance Tips

### Use Limits for Faster Queries

```bash
./skill_split.py search "python" --limit 10
```

### Use File Path Filters

```bash
./skill_split.py search "authentication" --file-path "docs/api/"
```

### Batch Operations

```bash
# Store multiple files faster
./skill_split.py store docs/**/*.md
```

---

## Troubleshooting

### Database Locked

```bash
rm -f *.db-wal *.db-shm
```

### No Sections Found

```bash
./skill_split.py validate file.md
```

### Search Slow

```bash
./skill_split.py search "query" --limit 10
```

### Check Integrity

```bash
sqlite3 skill_split.db "PRAGMA integrity_check;"
```

---

## Aliases (Optional)

Add to `~/.bashrc` or `~/.zshrc`:

```bash
# skill-split aliases
alias ss='python /path/to/skill-split/skill_split.py'
alias ss-search='ss search'
alias ss-get='ss get-section'
alias ss-next='ss next'
alias ss-list='ss list'
alias ss-compose='ss compose'
```

Usage:

```bash
ss search "query"
ss get 42
ss next 42 file.md
ss list file.md
ss compose --sections 1,2,3 --output new.md
```

---

*For more information, see [QUICK_REFERENCE.md](./QUICK_REFERENCE.md)*
