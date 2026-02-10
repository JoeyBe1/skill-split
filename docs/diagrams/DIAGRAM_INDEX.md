# Architecture Diagrams Quick Reference

This document provides a quick visual reference to all architecture diagrams in the skill-split project.

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          SKILL-SPLIT SYSTEM                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐             │
│  │   INPUT      │───▶│   PARSING    │───▶│   STORAGE    │             │
│  │              │    │              │    │              │             │
│  │ • CLI        │    │ • Parser     │    │ • SQLite     │             │
│  │ • Files      │    │ • Detectors  │    │ • Supabase   │             │
│  │              │    │ • Handlers   │    │              │             │
│  └──────────────┘    └──────────────┘    └──────────────┘             │
│           │                                    │                       │
│           ▼                                    ▼                       │
│  ┌──────────────┐                    ┌──────────────┐                │
│  │   OUTPUT     │◀───────────────────│   QUERY      │                │
│  │              │                    │              │                │
│  │ • Recomposer │                    │ • Search     │                │
│  │ • Composer   │                    │ • Navigate   │                │
│  │ • Checkout   │                    │ • Retrieve   │                │
│  └──────────────┘                    └──────────────┘                │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## Search Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                        THREE-TIER SEARCH                               │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  USER QUERY                                                            │
│       │                                                                │
│       ▼                                                                │
│  ┌─────────┐     ┌─────────────┐     ┌─────────────┐                 │
│  │  TIER 1 │────▶│   TIER 2    │────▶│   TIER 3    │                 │
│  │         │     │             │     │             │                 │
│  │ BM25    │     │   Vector    │     │   Hybrid    │                 │
│  │ Keywords│     │   Similarity│     │   Fusion    │                 │
│  │         │     │   (Semantic)│     │             │                 │
│  │ FTS5    │     │   pgvector  │     │   Weighted  │                 │
│  │ ~10ms   │     │   ~100ms    │     │   Average   │                 │
│  └─────────┘     └─────────────┘     └─────────────┘                 │
│       │                │                      │                        │
│       │                │                      │                        │
│       ▼                ▼                      ▼                        │
│  ┌─────────┐     ┌─────────────┐     ┌─────────────┐                 │
│  │ Fast    │     │  Semantic   │     │   Best      │                 │
│  │ Precise │     │  Discovery  │     │   Overall   │                 │
│  │ No API  │     │  Requires   │     │   Tunable   │                 │
│  └─────────┘     │  OpenAI API │     │   Config    │                 │
│                  └─────────────┘     └─────────────┘                 │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

## Progressive Disclosure Flow

```
┌────────────────────────────────────────────────────────────────────────┐
│                    PROGRESSIVE DISCLOSURE                              │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  SEARCH ──▶ RESULTS ──▶ LOAD SECTION ──▶ DISPLAY CONTENT              │
│    │             │             │                │                     │
│    │             │             │                ▼                     │
│    │             │             │          204 tokens                  │
│    │             │             │          (99% savings!)              │
│    │             │             │                                     │
│    │             │             └──────────────────┐                   │
│    │             │                                │                   │
│    ▼             ▼                                ▼                   │
│ BM25 / Vector   List with IDs            NAVIGATE SECTIONS             │
│   Ranked        Section Titles              │                         │
│                                            ▼                         │
│                                    ┌─────────────┐                   │
│                                    │  Next       │                   │
│                                    │  Sibling    │                   │
│                                    │             │                   │
│                                    │  Child      │                   │
│                                    │  Section    │                   │
│                                    └─────────────┘                   │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

## Component Handler Hierarchy

```
┌────────────────────────────────────────────────────────────────────────┐
│                     COMPONENT HANDLERS                                 │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│                      BaseHandler (Abstract)                            │
│                              │                                         │
│        ┌─────────────────────┼─────────────────────┐                  │
│        ▼                     ▼                     ▼                  │
│  ┌──────────┐          ┌──────────┐          ┌──────────┐            │
│  │  Plugin  │          │   Hook   │          │  Config  │            │
│  │ Handler  │          │ Handler  │          │ Handler  │            │
│  │          │          │          │          │          │            │
│  │ plugin.  │          │ hooks.   │          │ settings. │            │
│  │ json     │          │ json     │          │ json      │            │
│  │ + .mcp   │          │ + .sh    │          │ mcp_config│            │
│  └──────────┘          └──────────┘          └──────────┘            │
│                                                    │                  │
│        ▲                                           │                  │
│        │                                           ▼                  │
│  ┌──────────┐                                ┌──────────┐            │
│  │  Script  │◀───────────────────────────────│  Script  │            │
│  │ Handler  │                                │ Handler  │            │
│  │(Abstract)│                                │(Abstract)│            │
│  └──────────┘                                └──────────┘            │
│        │                                           │                  │
│        └──────────────┬────────────────────────────┘                  │
│                       ▼                                               │
│        ┌─────────────────────────────────┐                            │
│        │                                 │                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐            │
│  │  Python  │  │Java-     │  │Type-     │  │  Shell   │            │
│  │ Handler  │  │Script    │  │Script    │  │ Handler  │            │
│  │          │  │Handler   │  │Handler   │  │          │            │
│  │ .py      │  │.js/.jsx  │  │.ts/.tsx  │  │ .sh      │            │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘            │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

## Database Schema Overview

```
┌────────────────────────────────────────────────────────────────────────┐
│                     DATABASE SCHEMA                                    │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  FILES                                                                  │
│  ├── id (PK)                                                           │
│  ├── path (UK) ──────────────────────┐                                 │
│  ├── type                             │                                 │
│  ├── frontmatter                      │                                 │
│  ├── hash                             │                                 │
│  └── timestamps                       │                                 │
│                                      │                                  │
│                                      ▼                                  │
│  SECTIONS  ◄─────────────────────────┘                                 │
│  ├── id (PK)                                                           │
│  ├── file_id (FK) ───────┐                                            │
│  ├── parent_id (FK) ──────┼───────┐                                   │
│  ├── level                │       │                                   │
│  ├── title                │       │                                   │
│  ├── content              │       ▼                                   │
│  ├── order_index    ┌─────┴────────────────┐                           │
│  ├── line_range     │                       │                           │
│  └── closing_prefix │                       │                           │
│                    ▼                       ▼                           │
│            SECTIONS_FTS            CHECKOUTS                            │
│            ├── rowid              ├── id                               │
│            ├── title              ├── file_id                          │
│            └── content            ├── user_name                       │
│                                 ├── target_path                       │
│                                 ├── status                            │
│                                 └── timestamps                       │
│                                                                        │
│  CASCADE: Deleting file → Auto-deletes all sections                   │
│  FTS5: Full-text search index on title + content                      │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

## File Types and Handlers Matrix

```
┌────────────────────────────────────────────────────────────────────────┐
│                  FILE TYPES AND HANDLERS                               │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  File Type      │ Handler        │ Extensions  │ Multi-File           │
│  ───────────────┼────────────────┼─────────────┼────────────────────  │
│  SKILL          │ Core Parser    │ .md         │ No                   │
│  COMMAND        │ Core Parser    │ .md         │ No                   │
│  REFERENCE      │ Core Parser    │ .md         │ No                   │
│  PLUGIN         │ PluginHandler  │ .json       │ Yes (.mcp, hooks)    │
│  HOOK           │ HookHandler    │ .json       │ Yes (.sh scripts)     │
│  CONFIG         │ ConfigHandler  │ .json       │ No                   │
│  SCRIPT_PY      │ PythonHandler  │ .py         │ No                   │
│  SCRIPT_JS      │ JSHandler      │ .js, .jsx   │ No                   │
│  SCRIPT_TS      │ TSHandler      │ .ts, .tsx   │ No                   │
│  SCRIPT_SH      │ ShellHandler   │ .sh         │ No                   │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

## Search Mode Comparison

```
┌────────────────────────────────────────────────────────────────────────┐
│                    SEARCH MODE COMPARISON                              │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  Mode          │ Use Case        │ Speed   │ Accuracy │ API Required  │
│  ──────────────┼─────────────────┼─────────┼──────────┼─────────────── │
│  BM25          │ Exact terms     │ Fastest │ High     │ No             │
│  (Keywords)    │ Technical       │ (~10ms) │ for      │                │
│                │ queries         │         │ precise  │                │
│                │                 │         │ terms    │                │
│  ──────────────┼─────────────────┼─────────┼──────────┼─────────────── │
│  Vector        │ Semantic        │ Fast    │ High     │ Yes            │
│  (Semantic)    │ Similarity      │ (~100ms)│ for      │ (OpenAI)       │
│                │ Synonyms        │         │ meaning  │                │
│                │ Concepts        │         │         │                │
│  ──────────────┼─────────────────┼─────────┼──────────┼─────────────── │
│  Hybrid        │ Best overall    │ Medium  │ Highest  │ Yes            │
│  (Combined)    │ Flexible        │(~110ms) │ overall  │ (OpenAI)       │
│                │ Tunable         │         │         │                │
│                                                                        │
│  Default: Hybrid with vector_weight = 0.7                              │
│  (70% semantic, 30% keyword)                                           │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

## Extension Points

```
┌────────────────────────────────────────────────────────────────────────┐
│                     EXTENSION POINTS                                   │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  1. ADD NEW HANDLER                                                    │
│     ├── Create handler class extending BaseHandler                     │
│     ├── Add FileType enum value                                       │
│     ├── Register in ComponentDetector                                 │
│     └── Register in HandlerFactory                                    │
│                                                                        │
│  2. ADD NEW SEARCH BACKEND                                             │
│     ├── Extend DatabaseStore class                                    │
│     ├── Implement search_sections_with_rank()                          │
│     └── Add to HybridSearch as option                                 │
│                                                                        │
│  3. ADD NEW VALIDATION RULE                                            │
│     ├── Create validation function                                    │
│     ├── Add to skill_validator.py                                     │
│     └── Integrate into validate_skill()                               │
│                                                                        │
│  4. ADD NEW CLI COMMAND                                                │
│     ├── Add command function in skill_split.py                        │
│     ├── Add argument parser subcommand                                │
│     ├── Update documentation                                           │
│     └── Add tests                                                     │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

## Performance Metrics

```
┌────────────────────────────────────────────────────────────────────────┐
│                    PERFORMANCE METRICS                                 │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  TOKEN EFFICIENCY                                                      │
│  ├── Original File: 21,000 tokens                                     │
│  ├── Section Average: 204 tokens                                      │
│  └── Context Savings: 99.03%                                          │
│                                                                        │
│  SEARCH PERFORMANCE (Local)                                            │
│  ├── BM25 Search: ~10ms                                               │
│  ├── Vector Search: N/A (requires cloud)                              │
│  ├── Hybrid Search: ~110ms                                            │
│  └── Section Retrieval: ~1ms                                          │
│                                                                        │
│  SEARCH PERFORMANCE (Cloud)                                            │
│  ├── BM25 Search: ~50ms                                               │
│  ├── Vector Search: ~100ms                                            │
│  ├── Hybrid Search: ~150ms                                            │
│  └── Section Retrieval: ~20ms                                         │
│                                                                        │
│  SCALABILITY                                                           │
│  ├── Files per Database: 1,365+                                       │
│  ├── Sections per File: 92+                                           │
│  ├── Total Sections: 19,207+                                          │
│  └── Search Index: FTS5 handles full corpus efficiently               │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

---

## Quick Links

- **Main Architecture**: [ARCHITECTURE.md](../ARCHITECTURE.md)
- **PlantUML Sources**: [diagrams/](./) directory
- **ADR Records**: [ADR-001](./ADR-001-sqlite-fts5.md) through [ADR-005](./ADR-005-factory-pattern.md)
- **Rendering**: See [README.md](./README.md) for PlantUML setup instructions
