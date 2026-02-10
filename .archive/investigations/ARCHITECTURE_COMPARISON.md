# Architecture Comparison: Content Storage vs Metadata Tracking

**Purpose**: Compare current implementation with proposed alternative architecture.

---

## Architecture A: Content Storage (Current MVP)

### Data Flow
```
skill_split.py store skill.md
  ↓
Parser extracts sections
  ↓
SQLite stores section content
  ↓
Query: get-section 5
  ↓
SQLite returns content from database
  ↓
Agent receives section content
```

### Database Schema
```sql
CREATE TABLE files (
  id INTEGER PRIMARY KEY,
  path TEXT,
  hash TEXT
);

CREATE TABLE sections (
  id INTEGER PRIMARY KEY,
  file_id INTEGER,
  title TEXT,
  content TEXT,        -- ← Content stored here
  level INTEGER,
  start_line INTEGER,
  end_line INTEGER
);
```

### Pros
- ✅ Fast retrieval (no file I/O during query)
- ✅ Content immutable once stored
- ✅ Works offline (no file access needed)
- ✅ Hash verification ensures integrity
- ✅ Simple query model

### Cons
- ❌ Content duplication (file + database)
- ❌ Stale if file changes externally
- ❌ Requires re-parse on file update
- ❌ Database grows with content size

---

## Architecture B: Metadata Tracking (Proposed Idea)

### Data Flow
```
skill_split.py index skill.md
  ↓
Parser maps section locations
  ↓
Database stores composition metadata
  ↓
Query: get-section 5
  ↓
Database returns: (skill.md, bytes 450-890)
  ↓
Agent reads bytes 450-890 from skill.md
  ↓
Agent receives section content
```

### Database Schema (Proposed)
```sql
CREATE TABLE files (
  id INTEGER PRIMARY KEY,
  path TEXT,
  hash TEXT,
  last_indexed TIMESTAMP
);

CREATE TABLE section_map (
  id INTEGER PRIMARY KEY,
  file_id INTEGER,
  title TEXT,
  -- content NOT stored, just location metadata:
  byte_start INTEGER,  -- ← Metadata only
  byte_end INTEGER,    -- ← Metadata only
  level INTEGER
);
```

### Pros
- ✅ No content duplication
- ✅ Files remain source of truth
- ✅ Metadata stays valid if content updates
- ✅ Smaller database size
- ✅ Direct file access (no parsing overhead)

### Cons
- ❌ File I/O on every query
- ❌ Requires file availability
- ❌ Byte ranges complex with UTF-8
- ❌ File changes can invalidate byte positions
- ❌ Concurrent file access complexity

---

## Comparison Matrix

| Criterion | Content Storage (A) | Metadata Tracking (B) |
|-----------|---------------------|----------------------|
| **Query Speed** | Fast (DB only) | Medium (DB + file I/O) |
| **Storage Size** | Large (duplicates content) | Small (metadata only) |
| **File Updates** | Requires re-parse | Metadata may stay valid |
| **Offline Use** | ✅ Works | ❌ Needs files |
| **Complexity** | Low | Medium-High |
| **Token Efficiency** | Same | Same (both return content) |
| **Supabase Integration** | Optional | Required (per idea) |
| **Recomposition Speed** | Fast (DB query) | Fast (metadata + file read) |

---

## Hybrid Approach (Potential)

### Smart Storage Strategy
```yaml
small_sections:
  size: < 1KB
  storage: Database content (Arch A)
  reason: Fast access, minimal duplication

large_sections:
  size: > 1KB
  storage: Metadata pointers (Arch B)
  reason: Avoid DB bloat, files are source

frequently_accessed:
  storage: Database content (Arch A)
  caching: In-memory cache
  reason: Performance optimization

rarely_accessed:
  storage: Metadata pointers (Arch B)
  reason: Save space
```

---

## Testing Criteria (When Approved)

### Performance Benchmarks
```bash
# Test 1: Query 100 sections
time skill-split get-section [file] [1..100]

# Test 2: Cross-file search
time skill-split search "authentication"

# Test 3: Tree generation
time skill-split tree [large-file.md]

# Test 4: Cold cache performance
# (clear file cache, measure first query)

# Test 5: Concurrent access
# (10 parallel queries, measure throughput)
```

### Metrics to Compare
- Query latency (ms)
- Database size (MB)
- Memory usage (MB)
- Token efficiency (tokens per operation)
- Complexity (lines of code)
- Reliability (error rate with file changes)

---

## Decision Framework

**Choose Content Storage (A) if:**
- Query speed is critical
- Offline use required
- Files change infrequently
- Database size acceptable

**Choose Metadata Tracking (B) if:**
- Storage size critical
- Files update frequently
- Direct file access preferred
- Supabase heavy lifting justified

**Choose Hybrid if:**
- Different file sizes need different strategies
- Both benefits desired
- Complexity acceptable

---

## Current Status

- **Architecture A (Content Storage)**: ✅ Implemented, tested, working
- **Architecture B (Metadata Tracking)**: 💡 Idea stage, not prototyped
- **Decision**: Pending user review

**Last Updated**: 2026-02-04
