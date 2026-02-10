# skill-split Interactive Tutorial

**Learn progressive disclosure by doing**

---

## Lesson 1: Understanding the Problem

### The Challenge

You have a large documentation file:
- `API.md` - 695 lines, ~20KB, ~5,000 tokens
- You need to answer: "How do I authenticate?"

### Traditional Approach

```bash
# Load entire file
cat API.md  # 5,000 tokens to AI
# Expensive, slow, wasteful
```

### skill-split Approach

```bash
# 1. Search for relevant section
./skill_split.py search "authentication"
# Returns: Section 42 - "Authentication"
# Cost: 0 tokens (local search)

# 2. Load only that section
./skill_split.py get-section 42
# Returns: 50 tokens
# Savings: 99%
```

---

## Lesson 2: Basic Commands

### Parse a File

```bash
# Parse structure
./skill_split.py parse README.md

# Output:
# Parsed 23 sections from README.md
# Title: skill-split
# Author: contributors
```

### Store in Database

```bash
# Store for searching
./skill_split.py store README.md

# Output:
# Stored 23 sections in database
```

### List Sections

```bash
# Show hierarchy
./skill_split.py list README.md

# Output:
# [1] Introduction (level 1)
#   [5] Features (level 2)
# [12] Installation (level 1)
#   [18] Quick Start (level 2)
```

---

## Lesson 3: Search Modes

### BM25 Search (Keyword)

```bash
# Fast, exact matches
./skill_split.py search "authentication"

# Output:
# [42] Authentication (score: 0.95)
#   To authenticate, use your API key...
```

### Vector Search (Semantic)

```bash
# Concept-based search
./skill_split.py search-semantic "login security" --vector-weight 1.0

# Output:
# [42] Authentication (score: 0.87)
# [127] OAuth Setup (score: 0.76)
```

### Hybrid Search (Combined)

```bash
# Best of both (default)
./skill_split.py search-semantic "auth" --vector-weight 0.7

# Output:
# Top results combining keyword and semantic matching
```

---

## Lesson 4: Progressive Disclosure

### Navigate Sequentially

```bash
# Get next sibling
./skill_split.py next 42 README.md

# Output:
# [45] Authentication Methods
```

### Drill Down

```bash
# Get first child
./skill_split.py next 42 README.md --child

# Output:
# [44] API Key Authentication
```

### Build Context Incrementally

```bash
# Start with overview
section = $(./skill_split.py get-section 1)
echo "$section"

# Then get details
next = $(./skill_split.py next 1 README.md)
echo "$next"
```

---

## Lesson 5: Python API

### Basic Usage

```python
from skill_split import SkillSplit
from core.database import Database
from core.query import QueryAPI

# Initialize
ss = SkillSplit()
db = Database()
query = QueryAPI(db)

# Parse and store
doc = ss.parse_file("README.md")
db.store_document(doc)

# Search
results = query.search_sections("authentication")

# Get section
section = query.get_section(results[0].section.id)
print(section.content)
```

### Workflow Example

```python
# 1. Find relevant sections
results = query.search_sections("API")

# 2. Load only what you need
for result in results[:3]:  # Top 3 only
    section = result.section
    print(f"[{section.id}] {section.heading}")
    print(section.content[:100])  # Preview
```

---

## Lesson 6: Advanced Features

### Compose New Skills

```bash
# Combine sections from different files
./skill-split.py compose \
  --sections 42,127,256 \
  --output authentication_guide.md
```

### Backup and Restore

```bash
# Backup
./skill_split.py backup ./backups

# Restore
./skill_split.py restore ./backups/latest.sql
```

### Health Check

```bash
# Check system status
./skill_split.py status

# Output:
# Database: ~/.claude/databases/skill-split.db
# Sections: 19,207
# Files: 1,365
# Search: FTS5 enabled
# Embeddings: Generated
```

---

## Lesson 7: Real-World Workflow

### Scenario: Answer User Question

**Question:** "How do I set up OAuth?"

```bash
# Step 1: Search
./skill_split.py search "OAuth setup"
# Returns: Section 127

# Step 2: Get section
./skill_split.py get-section 127
# Returns: Complete OAuth setup instructions

# Step 3: Get related sections
./skill_split.py next 127 README.md --child
# Returns: OAuth provider-specific steps
```

### Scenario: Code Generation

**Task:** Generate authentication code

```python
from skill_split import SkillSplit

# 1. Find examples
ss = SkillSplit()
results = ss.search("authentication handler python")

# 2. Load examples (only what we need)
examples = [ss.get_section(r.id) for r in results[:3]]

# 3. Generate code
code = llm.code_generation(examples)

# Token cost: ~150 (vs 15,000 for full codebase)
```

---

## Lesson 8: Best Practices

### DO:

✅ Search before loading
✅ Use BM25 for exact matches
✅ Use Vector for concepts
✅ Cache frequently used sections
✅ Load specific sections only

### DON'T:

❌ Load entire files
❌ Skip the search step
❌ Use Vector for exact matches
❌ Load sections you won't use

---

## Exercises

### Exercise 1: Basic Search

```bash
# Task: Find documentation about "database"
./skill_split.py search "database"

# How many results did you get?
# Which result is most relevant?
```

### Exercise 2: Progressive Disclosure

```bash
# Task: Learn about search without loading everything
./skill_split.py list README.md
./skill_split.py get-section <ID>
./skill_split.py next <ID> README.md

# How much did you load vs full file?
```

### Exercise 3: Python API

```python
# Task: Create a simple search function
def find_and_load(query):
    results = query.search_sections(query)
    if results:
        section = query.get_section(results[0].section.id)
        return section.content
    return None

# Test it
print(find_and_load("authentication"))
```

---

## Next Steps

1. **Run demos:** `make demo`
2. **Read docs:** `docs/API_QUICK_REF.md`
3. **Build plugin:** `examples/plugins/`
4. **Contribute:** `CONTRIBUTING.md`

---

**Progressive disclosure is a skill. Practice it.**

*skill-split - Progressive disclosure for AI workflows*
