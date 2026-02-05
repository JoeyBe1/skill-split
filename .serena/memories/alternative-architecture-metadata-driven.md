# Alternative Architecture Idea: Metadata-Driven Composition

**Date**: 2026-02-04
**Status**: IDEA FOR REVIEW (Not Implemented)
**Source**: User dictation during MVP completion

## Core Concept

Database tracks **composition metadata** (where things go for recomposition) rather than storing content directly.

## Key Principle

**Files remain what agent accesses** - database just tracks HOW they're put together.

## Architecture Overview

```
Database Role: Composition map
Agent Access: Direct to files (not database content)
Supabase: Heavy lifting behind scenes
Operations: Rapid composition/recomposition of file structures
```

## Differences from Current MVP

| Aspect | Current (Content Storage) | Alternative (Metadata Tracking) |
|--------|---------------------------|----------------------------------|
| Database stores | Section content | Composition metadata (locations) |
| Agent reads from | SQLite database | Files directly |
| Database tracks | Content itself | WHERE content lives |
| Use case | Progressive section loading | Rapid file structure operations |

## Enabled Capabilities

1. **Section-by-section loading** - Return only needed sections
2. **Function location** - Easy to locate specific functions
3. **Rapid thinking** - Fast file structure traversal
4. **Rapid finding** - Quick content location
5. **Rapid composition** - Assemble files on-demand
6. **Rapid recomposition** - Dynamic reorganization

## Parallel Development Strategy

- **Do NOT disrupt** current directory-based system
- **Maintain both** approaches during testing
- **Test thoroughly** before choosing
- **May merge** insights from both

## Testing Requirements

Need to evaluate:
- Performance: metadata-driven vs content-stored
- Token efficiency both approaches
- Complexity comparison
- Supabase integration overhead
- Rapid composition speed benchmarks

## Open Questions

1. How does Supabase tracking differ from SQLite storage?
2. What metadata enables rapid file composition?
3. When does direct file access beat database retrieval?
4. How to handle file changes (invalidate composition maps)?
5. Security: File access permissions vs database queries?

## Status

- Current MVP using content storage is COMPLETE and WORKING
- This is alternative exploration for parallel testing
- User will review and decide on next steps
- Both systems may coexist or inform hybrid approach
