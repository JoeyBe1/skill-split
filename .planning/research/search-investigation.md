# Search Investigation Research

**Date:** 2026-02-08
**Goal:** Fix skill-split search to work as "NetworkX for Claude Code" with BM25 + Vector + Hybrid

## Problem Statement

User expects THREE search modes:
1. **BM25 (Keywords)**: Fast text search with relevance ranking
2. **Vector (Semantic)**: Semantic similarity using embeddings
3. **Hybrid**: Combined BM25 + Vector for best results

**Current State:**
- `search` command uses LIKE (not BM25) ❌
- `search-semantic` command uses HybridSearch ✅
- No unified search interface ❌
- No local vector search option ❌

## Root Cause Analysis

### TWO Search Methods Exist

**OLD Method (Still Used by CLI):**
- `search_sections()` in `core/query.py` and `core/database.py`
- Uses SQL `LIKE '%query%'`
- CLI command `search` uses this via `cmd_search_sections_query()`
- Requires exact contiguous phrase match
- **Example:** "github repository" finds nothing unless those words appear together

**NEW Method (Implemented Phase 1, NOT Used by CLI):**
- `search_sections_with_rank()` in `core/query.py` and `core/database.py`
- Uses SQLite FTS5 with BM25 ranking
- Does relevance-based scoring
- **Example:** "github repository" finds sections containing both words (implicit AND)

### Evidence

```python
# CLI search command (OLD) - skill_split.py:1026
cursor = conn.execute(
    """
    SELECT s.id, s.level, s.title, s.content,
           s.line_start, s.line_end, f.path
    FROM sections s
    JOIN files f ON s.file_id = f.id
    WHERE LOWER(s.title) LIKE ? OR LOWER(s.content) LIKE ?
    ORDER BY s.id
    """,
    (f"%{query_lower}%", f"%{query_lower}%"),
)

# FTS5 search (NEW, unused) - core/database.py:630
cursor = conn.execute(
    """
    SELECT s.id, bm25(sections_fts) as rank
    FROM sections_fts
    JOIN sections s ON sections_fts.rowid = s.id
    WHERE sections_fts MATCH ?
    ORDER BY rank
    """,
    (query,)
)
```

### Test Results

```
OLD search_sections("github repository"): 2 results (phrase must match exactly)
NEW search_sections_with_rank("github repository"): 4 results (BM25 ranks relevance)

FTS5 "python OR handler": 8 results (explicit OR works)
FTS5 "github AND repository": 4 results (explicit AND works)
```

## FTS5 Query Syntax

FTS5 MATCH syntax supports:
- Simple query: `"python"` - finds "python"
- Implicit AND: `"python handler"` - finds sections with BOTH words
- Explicit OR: `"python OR handler"` - finds sections with EITHER word
- Explicit AND: `"python AND handler"` - same as implicit
- Phrase: `"\"python handler\""` - finds exact phrase

**Default behavior:** Multi-word queries use implicit AND

## Solution Options

### Option 1: Use FTS5 by Default
Replace `search_sections()` with `search_sections_with_rank()` in CLI.

**Pros:**
- Simple change, FTS5 already implemented
- BM25 ranking provides better relevance
- Phase 1 work gets utilized

**Cons:**
- Changes search semantics (implicit AND vs phrase match)
- May break user expectations if they rely on exact phrase

### Option 2: Smart Query Processing
Parse user query and apply appropriate FTS5 syntax:
- Single word: direct match
- Multi-word: convert to OR for broader results
- Quoted phrases: use phrase match

**Pros:**
- Preserves exact phrase search with quotes
- Better multi-word search by default
- User controls search behavior

**Cons:**
- More complex implementation
- Need to document query syntax

### Option 3: Hybrid Approach
Add `--ranked` flag to `search` command for FTS5 search, keep old as default.

**Pros:**
- Backward compatible
- Users can opt-in to better search

**Cons:**
- Two search behaviors confuse users
- Old search never gets improved

### Option 4: Fuzzy Matching with OR
Convert multi-word queries to OR searches automatically.

**Pros:**
- "github repository" finds sections with either word
- Broader results = more discoveries

**Cons:**
- May return too many irrelevant results
- Loses precision

### Option 5: Query Expansion
Expand "github repository" to: `(github OR repository) AND (github NEAR repository)`

**Pros:**
- Finds broad matches but ranks proximity higher
- Best of both worlds

**Cons:**
- Complex FTS5 syntax
- Performance impact

## Recommendation

**Option 2: Smart Query Processing** with these rules:
1. Single word: direct FTS5 match
2. Quoted phrase `"exact words"`: phrase search
3. Multi-word unquoted: OR search for broad discovery
4. AND/OR operators respected if user provides them

Implementation:
```python
def preprocess_fts5_query(query: str) -> str:
    """Convert user query to FTS5 MATCH syntax."""
    # Remove extra whitespace
    query = ' '.join(query.split())

    # Check for user-provided operators
    if ' OR ' in query or ' AND ' in query or ' NEAR ' in query:
        return query  # User knows FTS5 syntax

    # Quoted phrase - use as-is
    if query.startswith('"') and query.endswith('"'):
        return query

    # Single word - direct match
    if ' ' not in query:
        return query

    # Multi-word unquoted - convert to OR for discovery
    words = query.split()
    return ' OR '.join(f'"{w}"' for w in words)
```

## Related Issues

1. **FTS sync edge cases** - Orphaned FTS entries possible
2. **Progressive disclosure "next" behavior** - May confuse users
3. **CLI bypasses QueryAPI** - Direct SQL instead of using API layer

## Files to Modify

1. `skill_split.py` - Update `cmd_search_sections_query()` to use `search_sections_with_rank()`
2. `core/database.py` - Add query preprocessing function
3. `test/test_database.py` - Add tests for query preprocessing
4. `test/test_query.py` - Add tests for CLI integration

## Success Criteria

1. User searches "github repository" and finds relevant sections
2. User searches "python handler" and finds Python-related sections
3. Exact phrase search still works with quotes
4. All 485 existing tests continue passing
5. New tests cover query preprocessing edge cases
