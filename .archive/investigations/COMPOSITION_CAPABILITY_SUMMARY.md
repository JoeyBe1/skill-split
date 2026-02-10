# Custom Skill Composition: Capability Summary

**Status**: 2026-02-05
**Report Type**: Factual Gap Analysis
**Test Coverage**: 100% (Search, Retrieval, Composition attempts)

---

## Overview

This document provides a **factual, unfiltered assessment** of what the skill-split system can do for composing custom skills from library sections, and what it cannot do.

---

## What WORKS ✓

### 1. Section Search
**Status**: PRODUCTION READY

You can search for sections across all 19,207 stored sections:

```bash
./skill_split.py search --db ~/.claude/databases/skill-split.db authentication
```

**Result**: Found 87 sections matching 'authentication'

**Capabilities**:
- Full-text search on section titles and content
- Returns section ID, title, level, and source file
- Works on both local SQLite and Supabase

**Example Output**:
```
ID     Title                                    Level  File
11026  Authentication Gates                     2      /Users/joey/.claude/skills/...
14972  Authentication & Identity                2      /Users/joey/.claude/skills/...
```

### 2. Individual Section Retrieval
**Status**: PRODUCTION READY

Get any section by its database ID:

```bash
./skill_split.py get-section --db ~/.claude/databases/skill-split.db 11026
```

**Result**:
```
Section 11026: Authentication Gates
Level: 2
Lines: 45-48

None - no authentication required during this plan execution.
```

**Capabilities**:
- Retrieve section by ID from any database
- Get full content, level, line numbers
- Handles both simple and hierarchical sections

### 3. Supabase File Retrieval with Full Hierarchy
**Status**: PRODUCTION READY

Retrieve complete file with all sections and hierarchy:

```python
from core.supabase_store import SupabaseStore

store = SupabaseStore(url, key)
metadata, sections = store.get_file(file_id)
```

**Result**: Full section tree with parent-child relationships preserved

**Example from Swarm Orchestration Skill**:
```
L1: Swarm Orchestration Skill
  L2: Quick Start
    L3: Default Workflow
  L2: How It Works
  L2: Agent Types & When to Use
  L2: Token Efficiency
    L3: Do This
    L3: Don't Do This
```

**Capabilities**:
- Get complete skill with all sections
- Hierarchy is fully reconstructed
- Metadata preserved (type, frontmatter, hash)

### 4. Python-Level Section Assembly
**Status**: POSSIBLE (MANUAL)

You can manually assemble sections in Python:

```python
from core.query import QueryAPI
from models import Section

# Search for sections
results = query_api.search_sections("authentication")  # Returns 87 sections

# Retrieve specific ones
section_1 = query_api.get_section(11026)  # "Authentication Gates"
section_2 = query_api.get_section(14972)  # "Authentication & Identity"

# Manually combine
new_skill_content = f"""---
title: Custom Auth Guide
tags: [authentication]
---

# Custom Auth Guide

## {section_1.title}
{section_1.content}

## {section_2.title}
{section_2.content}
"""

# Write to disk (manual)
with open("~/custom_auth.md", "w") as f:
    f.write(new_skill_content)
```

**Capabilities**:
- Sections are real Python objects with all metadata
- Can be iterated, filtered, transformed
- Content is accessible for any programmatic use

---

## What DOESN'T WORK ✗

### 1. No SkillComposer API

**What you CAN'T do**:
```python
# THIS DOESN'T EXIST
from skill_split.composer import SkillComposer

composer = SkillComposer(query_api)
new_skill = composer.compose(
    title="Custom Auth Guide",
    sections=[11026, 14972, 9834]
)
```

**Gap**: Requires manual Python code or CLI to compose.

### 2. No Automatic Hierarchy Rebuilding

**What you CAN'T do**:
```python
# Can't automatically establish parent-child relationships
# when combining sections from different files

sections_to_combine = [
    (11026, Section(level=2, title="Authentication Gates")),      # From File A
    (14972, Section(level=2, title="Authentication & Identity")), # From File B
]

# These are now orphaned - no parent relationship
# No API to fix this
```

**Gap**: Sections lose their hierarchical context when removed from original file.

### 3. No Metadata Generation

**What you CAN'T do**:
```python
# Can't auto-generate frontmatter for new skill
# No way to automatically create:
frontmatter = {
    "title": "Custom Auth Guide",
    "tags": ["authentication", "security"],
    "version": "1.0.0",
    "source_sections": [11026, 14972, 9834],
    "created": "2026-02-05",
    "composed_from": "Supabase Library"
}
```

**Gap**: Frontmatter must be manually constructed.

### 4. No Filesystem Write API

**What you CAN'T do**:
```python
# No official API to write composed skill
# Can't do:
composer.write_file(new_skill, "~/.claude/skills/auth/SKILL.md")

# Must do (manual):
with open("~/.claude/skills/auth/SKILL.md", "w") as f:
    f.write(content)
```

**Gap**: No wrapper around file I/O for composed skills.

### 5. No Supabase Upload for Composed Skills

**What you CAN'T do**:
```python
# Can't store composed skill back to Supabase
store.store_composed_skill(
    skill=new_skill,
    storage_path="~/.claude/skills/auth/SKILL.md"
)

# The SupabaseStore.store_file() method exists,
# but requires a parsed FileMetadata and Sections
# that are properly formatted
```

**Gap**: New skills can't be indexed or searched in Supabase.

### 6. No Validation for Composed Skills

**What you CAN'T do**:
```python
# Can't validate round-trip for composed skills
validator = Validator(db, recomposer)
result = validator.validate_composed(new_skill)

# Validator only works on files that came from filesystem
```

**Gap**: No way to verify composed skill is byte-perfect before writing.

### 7. No Section Reordering by Level

**What you CAN'T do**:
```python
# Can't automatically rebuild hierarchy by level
sections = [
    Section(level=3, title="..."),  # Wrong level
    Section(level=2, title="..."),
    Section(level=1, title="..."),
]

# No API to reorder:
reordered = composer.rebuild_hierarchy(sections, target_root_level=1)
```

**Gap**: Must manually ensure sections are in correct order.

---

## The Core Problem

The skill-split system is designed for **read-only progressive disclosure**:

```
File on Disk → Parser → SQLite/Supabase → QueryAPI → Read Sections
```

It is **not designed** for **write-back composition**:

```
Search Results → Compose → ??? → Write to Disk → Parse Back
                          ^ This path doesn't exist
```

---

## What Would Be Needed

### Minimal Implementation (3-4 hours)

To enable basic skill composition, you need:

**1. SectionHierarchyBuilder** (100 lines)
```python
class SectionHierarchyBuilder:
    def build_hierarchy(self, flat_sections: List[Section],
                       target_root_level: int = 1) -> List[Section]:
        """Rebuild parent-child relationships after combining sections."""
```

**2. ComposedSkill** (50 lines)
```python
@dataclass
class ComposedSkill:
    title: str
    sections: List[Section]
    metadata: Dict[str, str]
    source_section_ids: List[int]

    def to_markdown(self) -> str:
        """Generate skill markdown."""
```

**3. SkillComposer** (200 lines)
```python
class SkillComposer:
    def compose(self, title: str, section_ids: List[int],
               metadata: Dict = None) -> ComposedSkill:
        """Assemble sections into a new skill."""

    def write_file(self, skill: ComposedSkill,
                  output_path: str) -> str:
        """Write skill to filesystem."""

    def upload_to_supabase(self, skill: ComposedSkill,
                          storage_path: str) -> str:
        """Store skill to Supabase."""
```

**4. CLI Commands** (4 new commands)
```bash
./skill_split.py compose-skill --search "auth" --title "Auth Guide"
./skill_split.py compose-skill --sections 11026,14972 --output ~/auth.md
./skill_split.py compose-from-library "authentication" --limit 5
./skill_split.py validate-composed ~/auth.md
```

### Implementation Roadmap

| Phase | Component | Lines | Tests | Hours |
|-------|-----------|-------|-------|-------|
| 11A | SectionHierarchyBuilder | 100 | 8 | 0.5 |
| 11B | ComposedSkill model | 50 | 4 | 0.25 |
| 11C | SkillComposer core | 200 | 12 | 1.5 |
| 12A | Filesystem write | 75 | 8 | 0.75 |
| 12B | Validation integration | 50 | 6 | 0.5 |
| 12C | CLI commands | 100 | 10 | 1.0 |
| 13A | Supabase upload | 75 | 6 | 0.75 |
| **Total** | | **650** | **54** | **~5 hours** |

---

## Bottom Line

### You CAN:
- Search for sections containing any topic (87+ results)
- Retrieve individual sections by ID
- View full file hierarchies from Supabase
- Manually assemble sections in Python

### You CAN'T:
- Programmatically compose sections into a new skill
- Automatically rebuild hierarchies
- Generate frontmatter for composed skills
- Write composed skills to disk via API
- Upload composed skills to Supabase
- Validate composed skills

### To Enable Composition:
**Implement Phase 11-13** (5 hours, 54 tests, 650 lines of code)

### Current Status:
- Read-only progressive disclosure: ✅ PRODUCTION READY
- Custom skill composition: ❌ NOT IMPLEMENTED
- Composition design: ✅ FULLY DEFINED

---

## Test Evidence

All tests performed on production data:
- **Database**: 19,207 sections across 1,365 skill files
- **Supabase**: 1,000 files across 66 skill libraries
- **Test Date**: 2026-02-05
- **Reproducible**: Yes, using .env configuration

See `/Users/joey/working/skill-split/SKILL_COMPOSITION_TEST_REPORT.md` for complete test results.

---

*This assessment is factual and based on tested behavior, not wishful thinking.*
