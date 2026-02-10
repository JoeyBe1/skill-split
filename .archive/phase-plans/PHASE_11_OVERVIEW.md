# Phase 11: SkillComposer API - Quick Reference

**Status**: Planning Document Complete ✓
**Location**: `docs/plans/phase-11-skillcomposer.md` (1,157 lines)
**Ready**: Yes, for implementation

---

## What is Phase 11?

**SkillComposer** is the inverse of the Parser/Recomposer:
- **Phases 1-10**: Split files into sections → Store in database
- **Phase 11**: Select sections from database → Compose new skills

Enables users to build custom skills from existing library sections with automatic metadata generation and validation.

---

## Files to Create (1,330 lines)

| File | Lines | Purpose |
|------|-------|---------|
| `core/skill_composer.py` | 380 | Main API orchestration |
| `models.py` (updates) | 120 | ComposedSkill dataclass |
| `handlers/skill_validator.py` | 250 | Validation logic |
| `skill_split.py` (updates) | 200 | 4 new CLI commands |
| `test/test_skill_composer.py` | 320 | 50 unit tests |
| `test/test_skill_composer_cli.py` | 180 | 20 CLI tests |

---

## New API: SkillComposer

```python
from core.skill_composer import SkillComposer

# Initialize
composer = SkillComposer("~/.claude/databases/skill-split.db")

# Compose from section IDs
skill = composer.compose(
    section_ids=[101, 205, 310],
    title="Python Debugging Guide",
    description="Complete debugging reference",
    tags=["python", "debugging"],
    author="Claude"
)

# Generate metadata (YAML frontmatter)
skill = composer.generate_frontmatter(skill)

# Validate structure
validation = composer.validate(skill)
if not validation.is_valid:
    print(validation.errors)

# Write to filesystem or cloud
composer.write_to_filesystem(skill, "~/.claude/skills/debug-guide/")
composer.upload_to_supabase(skill)  # Optional
```

---

## New Data Model: ComposedSkill

```python
@dataclass
class ComposedSkill:
    section_ids: List[int]           # Database IDs
    sections: Dict[int, Section]     # Loaded sections
    title: str                       # Skill title
    description: str                 # Metadata
    author: str                      # Author name
    tags: List[str]                  # Skill tags
    source_files: List[str]          # Original sources
    frontmatter: str                 # Generated YAML
    composed_hash: str               # SHA256 of output
    output_path: str                 # Write destination
```

---

## New CLI Commands

```bash
# 1. Compose from section IDs
./skill_split.py compose \
    --section-ids 101,205,310 \
    --title "Python Debugging" \
    --tags python,debugging \
    --write-filesystem

# 2. Interactive composition
./skill_split.py compose-interactive

# 3. Compose from search results
./skill_split.py compose-from-search \
    --query "python debugging" \
    --title "Debug Guide" \
    --auto-select

# 4. Validate composed skill
./skill_split.py validate-composition /path/to/skill.md
```

---

## Validation: SkillValidator

```python
from handlers.skill_validator import SkillValidator

validator = SkillValidator()

# Check hierarchy
result = validator.validate_structure(skill)

# Check content
result = validator.validate_content(skill)

# Check metadata (YAML)
result = validator.validate_metadata(skill)

# Test byte-perfect round-trip
result = validator.validate_recomposability(skill)

# Run all checks
result = validator.validate_all(skill)

if result.is_valid:
    print("✓ Valid skill")
else:
    for error in result.errors:
        print(f"✗ {error}")
```

---

## Workflow Stages

```
Selection (User)
    ↓
Retrieval (QueryAPI)
    ↓
Hierarchy Rebuild (SkillComposer)
    ↓
Frontmatter Generation (SkillComposer)
    ↓
Validation (SkillValidator)
    ↓
Serialization (Recomposer)
    ↓
Output (Filesystem or Supabase)
```

---

## Generated Frontmatter

Default template (customizable):

```yaml
---
title: "Python Debugging Guide"
description: "Complete debugging reference"
author: "Claude"
created_at: "2026-02-05T12:00:00Z"
tags:
  - python
  - debugging
source_files:
  - ~/.claude/skills/python-basics/SKILL.md
source_section_ids:
  - 101
  - 205
  - 310
---
```

---

## Time Estimate: 7.5 Hours

| Phase | Task | Time |
|-------|------|------|
| A | Core API (SkillComposer) | 2.0 h |
| B | Validation (SkillValidator) | 1.5 h |
| C | CLI Integration | 1.5 h |
| D | Documentation | 1.0 h |
| E | Integration Testing | 1.5 h |

---

## Test Coverage: 81 Tests

| Category | Count |
|----------|-------|
| SkillComposer unit tests | 30 |
| SkillValidator unit tests | 15 |
| Model tests | 5 |
| CLI tests | 20 |
| Integration tests | 11 |
| **Total** | **81** |

Target: 90%+ coverage, <10s runtime

---

## Success Criteria

- ✅ Compose from any section IDs
- ✅ Auto-generate valid YAML frontmatter
- ✅ Rebuild hierarchies correctly
- ✅ Validate structure, content, metadata
- ✅ Write to filesystem
- ✅ Upload to Supabase
- ✅ Byte-perfect round-trip
- ✅ 90%+ code coverage
- ✅ 81 tests passing

---

## Dependencies

**Depends On**:
- Phases 1-10 (complete)
- DatabaseStore (SQLite)
- QueryAPI (section retrieval)
- Recomposer (proven algorithm)

**Enables**:
- Phase 12: Progressive Disclosure UI
- Phase 13: Smart Section Selection
- Phase 14: Batch Composition

---

## Key Risk Mitigations

| Risk | Mitigation | Test |
|------|-----------|------|
| Hierarchy breaks | Comprehensive validation | 5 tests |
| Round-trip fails | Reuse proven Recomposer | 3 tests |
| Invalid YAML | PyYAML library + tests | 5 tests |
| Write failures | Check perms early | Filesystem tests |

---

## Plan Document

**Full Details**: `docs/plans/phase-11-skillcomposer.md`

Includes:
- Complete architecture diagrams
- Detailed API specifications
- Full file specifications (380-250 lines each)
- Comprehensive test strategy
- Implementation checklist
- Risk assessment
- Success criteria

---

## Next Steps

1. Review plan document
2. Adjust estimates/scope as needed
3. Begin Phase A implementation (Core API)
4. Run tests continuously
5. Document progress

**Ready for Implementation** ✨

---

*Plan created: 2026-02-05*
