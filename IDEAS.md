# skill-split Architecture Ideas

This document tracks alternative architectural approaches for consideration.

---

## Idea 1: Metadata-Driven Composition Architecture

**Date Proposed**: 2026-02-04
**Status**: Under Review
**Proposer**: Joey (dictated during MVP completion)

### Summary

Alternative to current content-storage approach: Database tracks **composition metadata** while agents access files directly.

### Current Implementation (MVP - In Production)

```
User Query
  ↓
SQLite Database (stores section content)
  ↓
Retrieve section content from DB
  ↓
Return to agent
```

**Storage Model:**
- Sections stored as rows in database
- Content duplicated (file + database)
- Query returns content directly

### Alternative Architecture (Proposed)

```
User Query
  ↓
Database (stores composition map)
  ↓
Map indicates: File X, Lines Y-Z
  ↓
Agent accesses File X directly
  ↓
Supabase manages file structures
```

**Storage Model:**
- Database stores WHERE content lives (metadata)
- Files remain source of truth
- Database tracks HOW to recompose
- Rapid file structure loading/unloading

### Key Design Differences

| Aspect | Current (MVP) | Alternative Idea |
|--------|---------------|------------------|
| **Content Location** | Database | Files directly |
| **Database Role** | Content store | Composition map |
| **Query Result** | Section content | File path + byte range |
| **File Access** | Once (during store) | Every retrieval |
| **Supabase Role** | Optional (team sharing) | Core (heavy lifting) |
| **Recomposition** | From DB sections | From file locations |

### Claimed Benefits

1. **Rapid thinking** - Fast file structure traversal via metadata
2. **Rapid finding** - Quick location of functions/sections
3. **Rapid composition** - On-demand file assembly
4. **Rapid recomposition** - Dynamic reorganization
5. **Function location** - Easy to locate specific code
6. **No duplication** - Files are single source of truth

### Use Cases Enabled

**Scenario 1: Find function across skills**
```
Query: "Where is authenticate_user() defined?"
  ↓
Database: auth-skill.md, lines 45-67
  ↓
Agent reads lines 45-67 from file
```

**Scenario 2: Compose skill subset**
```
Query: "Load only authentication sections from all skills"
  ↓
Database returns: [(skill1, lines 20-40), (skill2, lines 100-150)]
  ↓
Agent reads specified ranges from files
  ↓
Composes unified view
```

**Scenario 3: Recompose on file change**
```
File updated externally
  ↓
Database metadata still valid (points to new content)
  ↓
No re-parsing required (unlike current approach)
```

### Open Questions

1. **Performance**: File I/O vs database query - which is faster?
2. **Token efficiency**: Does metadata approach save more tokens?
3. **Supabase role**: What heavy lifting does it provide?
4. **File watching**: How to detect file changes for metadata invalidation?
5. **Byte ranges**: UTF-8 safe? How to handle multi-byte characters?
6. **Concurrency**: Multiple agents reading same file simultaneously?
7. **Caching**: Where to cache frequently accessed file segments?

### Testing Plan (When Approved)

**Phase 1: Prototype**
- Design metadata schema (file_path, byte_start, byte_end, section_id)
- Implement file range reader
- Test with creating-output-styles skill

**Phase 2: Benchmark**
- Compare query speed: metadata lookup + file read vs DB content retrieval
- Measure token usage: metadata approach vs current approach
- Profile Supabase integration overhead

**Phase 3: Evaluate**
- Document findings
- Identify scenarios where each approach wins
- Recommend: pure metadata, pure content, or hybrid

### Implementation Strategy

**Parallel Development:**
- Keep current SQLite content-storage system (MVP)
- Build metadata-driven system alongside
- Do NOT disrupt working directory-based approach
- Test both thoroughly before choosing

**Migration Path (If Approved):**
- Could support both modes via config flag
- Could use hybrid: small sections in DB, large files via metadata
- Could migrate gradually: content → metadata per file type

### Next Steps

- [ ] **User reviews this document**
- [ ] **User approves exploration** (or rejects idea)
- [ ] If approved: Design metadata schema
- [ ] If approved: Prototype with 1 skill file
- [ ] If approved: Benchmark vs current approach
- [ ] Document decision and rationale

---

## Notes

- This idea came during MVP completion session
- MVP is complete and working (current content-storage approach)
- This is exploration of alternative, not replacement yet
- Both approaches may coexist or insights may merge

**Last Updated**: 2026-02-04
