# Phase 11: SkillComposer API - Complete Implementation Plan

**Version**: 1.0
**Date**: 2026-02-05
**Status**: PLANNING (Ready for implementation)
**Estimated Duration**: 6-8 hours (5-6 person-days)
**Depends On**: Phases 1-10 complete, Production database verified

---

## Executive Summary

Phase 11 implements **SkillComposer**: a composable API for building new skills from existing section IDs stored in the database. Users can select sections, compose them into a new skill, generate appropriate frontmatter, validate the result, and deploy to filesystem or Supabase.

**Key Capability**: Users can now not only decompose skills into sections (Phases 1-10), but also **recompose custom skills** from selected sections, enabling:
- Progressive skill assembly from library components
- Custom skill generation with automatic metadata
- Round-trip validation with byte-perfect hashing
- One-click deployment to local filesystem or Supabase

**Design Principle**: Inverse of the Parser/Recomposer: instead of splitting files → database, now take database sections → rebuild files with automatic hierarchy and metadata.

---

## Architecture Overview

### System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                      SkillComposer API                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  SkillComposerAPI (core/skill_composer.py)                      │
│  ├─ compose()          → Select sections → build skill tree     │
│  ├─ generate_frontmatter() → Create metadata                    │
│  ├─ validate()         → Verify structure                       │
│  ├─ write_to_filesystem() → Save to disk                        │
│  └─ upload_to_supabase() → Push to cloud                        │
│                                                                 │
│  ComposedSkill (models.py)                                      │
│  ├─ section_ids: List[int]                                      │
│  ├─ sections: Dict[int, Section]                                │
│  ├─ output_path: str                                            │
│  ├─ frontmatter: str                                            │
│  ├─ title: str                                                  │
│  ├─ description: str                                            │
│  └─ composed_hash: str (SHA256 of output)                       │
│                                                                 │
│  SkillValidator (handlers/skill_validator.py - NEW)             │
│  ├─ validate_structure() → Check hierarchy                      │
│  ├─ validate_content() → Check for required sections            │
│  ├─ validate_metadata() → Check frontmatter                     │
│  └─ generate_errors() → Report issues                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
             ↓                              ↓
    ┌────────────────────────┐  ┌──────────────────────┐
    │   DatabaseStore        │  │   SupabaseStore      │
    │   (Retrieve sections)  │  │   (Upload composed)  │
    └────────────────────────┘  └──────────────────────┘
```

### Workflow Stages

```
Stage 1: SELECTION
  User selects section IDs: [101, 205, 310, 415]
       ↓
Stage 2: RETRIEVAL
  QueryAPI.get_section() × N → Load sections from DB
       ↓
Stage 3: HIERARCHY REBUILD
  SkillComposer._rebuild_hierarchy() → Create parent-child tree
       ↓
Stage 4: FRONTMATTER GENERATION
  SkillComposer.generate_frontmatter() → Create YAML metadata
       ↓
Stage 5: VALIDATION
  SkillValidator → Check structure, content, metadata
       ↓
Stage 6: SERIALIZATION
  Recomposer._build_sections_content() → Generate markdown
       ↓
Stage 7: OUTPUT
  write_to_filesystem() OR upload_to_supabase()
```

---

## Files to Create

### 1. Core API: `core/skill_composer.py` (380 lines)

**Purpose**: Main orchestration for skill composition

**Key Classes**:

```python
class SkillComposer:
    """
    Compose new skills from section IDs.

    Enables progressive skill assembly from library components:
    1. Select section IDs from database
    2. Retrieve and rebuild hierarchy
    3. Generate frontmatter (title, description, tags, etc.)
    4. Validate structure
    5. Write to filesystem or upload to Supabase
    """

    def __init__(self, db_path: str):
        """Initialize with database access."""
        self.db = DatabaseStore(db_path)
        self.query = QueryAPI(db_path)

    def compose(
        self,
        section_ids: List[int],
        title: str,
        description: str = "",
        tags: List[str] = None,
        author: str = "SkillComposer",
        source_files: List[str] = None
    ) -> "ComposedSkill":
        """
        Compose skill from section IDs.

        Args:
            section_ids: List of database section IDs to include
            title: Skill title for frontmatter
            description: Brief description for metadata
            tags: Skill tags (e.g., ["python", "cli"])
            author: Author name
            source_files: Original files these sections came from

        Returns:
            ComposedSkill object (not yet written)

        Raises:
            ValueError: If section_ids invalid or hierarchy broken
        """
        pass

    def _retrieve_sections(self, section_ids: List[int]) -> Dict[int, Section]:
        """Load sections from database."""
        pass

    def _rebuild_hierarchy(self, sections: Dict[int, Section]) -> List[Section]:
        """Rebuild parent-child tree from flat section list."""
        pass

    def generate_frontmatter(
        self,
        skill: "ComposedSkill",
        template: str = None
    ) -> str:
        """
        Generate YAML frontmatter for composed skill.

        Default template:
        ```yaml
        title: "..."
        description: "..."
        author: "SkillComposer"
        composed_from: [list of source files]
        source_section_ids: [list of database IDs]
        created_at: "2026-02-05T12:00:00Z"
        tags: [list]
        ```
        """
        pass

    def write_to_filesystem(
        self,
        skill: "ComposedSkill",
        output_dir: str = None
    ) -> str:
        """
        Write composed skill to filesystem.

        Returns:
            Path to written file

        Raises:
            IOError: If write fails
        """
        pass

    def upload_to_supabase(
        self,
        skill: "ComposedSkill"
    ) -> bool:
        """
        Upload composed skill to Supabase.

        Returns:
            True if successful

        Raises:
            ValueError: If Supabase credentials missing
        """
        pass

    def validate(self, skill: "ComposedSkill") -> ValidationResult:
        """
        Validate composed skill structure.

        Checks:
        - All sections present
        - Hierarchy is valid
        - No orphaned content
        - Frontmatter valid YAML
        - Required fields present

        Returns:
            ValidationResult with errors/warnings
        """
        pass
```

**Responsibilities**:
- Orchestrate composition workflow
- Manage database/Supabase access
- Generate frontmatter from metadata
- Validate composed skills
- Handle filesystem and cloud writes

**Dependencies**:
- `core.database.DatabaseStore`
- `core.query.QueryAPI`
- `core.recomposer.Recomposer`
- `handlers.skill_validator.SkillValidator`
- `core.hashing.compute_file_hash`
- `models.ComposedSkill, ValidationResult`

---

### 2. Data Model: Updates to `models.py` (120 lines)

**New Classes**:

```python
@dataclass
class ComposedSkill:
    """
    A skill composed from database sections.

    Represents the intermediate state of a skill being built,
    before writing to filesystem or Supabase.

    Attributes:
        section_ids: List of database section IDs included
        sections: Dict[id -> Section] for quick lookup
        title: Skill title (for metadata)
        description: Skill description
        author: Author name
        tags: List of skill tags
        source_files: Original files these sections came from
        frontmatter: Generated YAML frontmatter (empty until generated)
        composed_hash: SHA256 of final output (empty until written)
        output_path: Path where skill will be written (optional)
    """
    section_ids: List[int]
    sections: Dict[int, Section]
    title: str
    description: str = ""
    author: str = "SkillComposer"
    tags: List[str] = field(default_factory=list)
    source_files: List[str] = field(default_factory=list)
    frontmatter: str = ""
    composed_hash: str = ""
    output_path: str = ""

    def get_section(self, id: int) -> Optional[Section]:
        """Get section by ID."""
        return self.sections.get(id)

    def get_all_sections(self) -> List[Section]:
        """Get sections in order."""
        return [self.sections[sid] for sid in self.section_ids]

    def add_section(self, section_id: int, section: Section) -> None:
        """Add section to composed skill."""
        self.section_ids.append(section_id)
        self.sections[section_id] = section

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "section_ids": self.section_ids,
            "title": self.title,
            "description": self.description,
            "author": self.author,
            "tags": self.tags,
            "source_files": self.source_files,
            "composed_hash": self.composed_hash,
        }


@dataclass
class CompositionOptions:
    """
    Options for skill composition.

    Attributes:
        generate_toc: Auto-generate table of contents
        preserve_line_numbers: Keep original line_start/line_end in metadata
        auto_title_hierarchy: Auto-adjust heading levels to start at #
        include_metadata_comments: Add section ID comments for tracking
        validate_before_write: Run full validation before write
    """
    generate_toc: bool = False
    preserve_line_numbers: bool = False
    auto_title_hierarchy: bool = True
    include_metadata_comments: bool = False
    validate_before_write: bool = True
```

**Rationale**:
- `ComposedSkill` bridges database sections and filesystem output
- Intermediate state allows step-by-step composition workflow
- `CompositionOptions` enables flexible composition behaviors

---

### 3. Validation: `handlers/skill_validator.py` (250 lines)

**Purpose**: Validate composed skills for correctness

**Key Classes**:

```python
class SkillValidator:
    """
    Validate composed skills.

    Checks:
    - Hierarchical structure (no orphaned sections)
    - Content integrity (no empty sections unless intentional)
    - Metadata completeness (required frontmatter fields)
    - Format compatibility (sections can be recomposed)
    """

    def validate_structure(self, skill: ComposedSkill) -> ValidationResult:
        """
        Validate skill hierarchical structure.

        Checks:
        - Parent sections exist before children
        - No circular parent-child relationships
        - Heading levels progress logically (# → ## → ###)
        - All sections accessible
        """
        pass

    def validate_content(self, skill: ComposedSkill) -> ValidationResult:
        """
        Validate skill content.

        Checks:
        - No completely empty sections
        - Content doesn't exceed reasonable size
        - Special characters handled correctly
        - Code blocks not malformed
        """
        pass

    def validate_metadata(self, skill: ComposedSkill) -> ValidationResult:
        """
        Validate frontmatter and metadata.

        Checks:
        - Required fields: title, description
        - Valid YAML syntax
        - Tags are non-empty strings
        - Created date is valid ISO8601
        """
        pass

    def validate_recomposability(self, skill: ComposedSkill) -> ValidationResult:
        """
        Validate that skill can be recomposed byte-perfectly.

        This is the inverse of Recomposer validation:
        - Test recomposition → hash → compare
        """
        pass

    def validate_all(self, skill: ComposedSkill) -> ValidationResult:
        """Run all validations and combine results."""
        pass
```

**Responsibilities**:
- Verify composed skill is structurally sound
- Check content integrity
- Validate metadata/frontmatter
- Test byte-perfect recomposability

**Dependencies**:
- `models.ComposedSkill, ValidationResult`
- `core.hashing.compute_file_hash`
- `core.recomposer.Recomposer` (for round-trip test)

---

### 4. CLI Integration: Updates to `skill_split.py` (200 lines)

**New Commands**:

```python
def cmd_compose(args) -> int:
    """
    Compose new skill from section IDs.

    Usage:
        ./skill_split.py compose \
            --section-ids 101,205,310 \
            --title "My Custom Skill" \
            --description "A skill I composed" \
            --tags python,automation \
            --output-dir ~/.claude/skills/my-skill/ \
            --db <database>

    Then either:
    - Write to filesystem: --write-filesystem
    - Upload to Supabase: --upload-supabase
    """
    pass


def cmd_compose_interactive(args) -> int:
    """
    Interactive composition workflow.

    Usage:
        ./skill_split.py compose-interactive

    Prompts:
    1. Search sections: "Show me sections about Python"
    2. Select sections: "Which ones do you want? (1,2,3)"
    3. Enter metadata: "Title? Description? Tags?"
    4. Validate: Show structure
    5. Output: Filesystem or Supabase?
    """
    pass


def cmd_compose_from_search(args) -> int:
    """
    Compose skill from search results.

    Usage:
        ./skill_split.py compose-from-search \
            --query "python debugging" \
            --title "Python Debug Guide" \
            --limit 10 \
            --auto-select \
            --write-filesystem

    Selects top N matching sections and composes automatically.
    """
    pass


def cmd_validate_composition(args) -> int:
    """
    Validate a composed skill file.

    Usage:
        ./skill_split.py validate-composition /path/to/skill.md

    Runs full composition validation without writing output.
    """
    pass
```

**Integration Points**:
- `argparse` parser additions for new commands
- Lazy imports for SkillComposer (like SupabaseStore)
- Reuse existing `_get_default_db_path()` logic
- Consistent error handling patterns

---

### 5. Tests: `test/test_skill_composer.py` (320 lines)

**Test Coverage**:

```python
class TestSkillComposer:
    """Test SkillComposer core API."""

    def test_compose_single_section(self):
        """Compose skill from 1 section."""
        pass

    def test_compose_multiple_sections(self):
        """Compose skill from N sections."""
        pass

    def test_compose_with_hierarchy(self):
        """Compose preserves parent-child relationships."""
        pass

    def test_compose_invalid_section_ids(self):
        """Reject non-existent section IDs."""
        pass

    def test_compose_empty_skill(self):
        """Error when no sections provided."""
        pass

    def test_generate_frontmatter_default(self):
        """Generate default YAML frontmatter."""
        pass

    def test_generate_frontmatter_custom_template(self):
        """Use custom frontmatter template."""
        pass

    def test_frontmatter_includes_metadata(self):
        """Frontmatter includes title, description, tags, etc."""
        pass

    def test_write_to_filesystem(self):
        """Write composed skill to disk."""
        pass

    def test_write_creates_directory(self):
        """Auto-create output directory if missing."""
        pass

    def test_write_preserves_structure(self):
        """Written file maintains section hierarchy."""
        pass

    def test_validate_composition_valid(self):
        """Valid skill passes validation."""
        pass

    def test_validate_composition_missing_title(self):
        """Invalid skill detected (missing title)."""
        pass

    def test_validate_composition_orphaned_section(self):
        """Invalid skill detected (orphaned section)."""
        pass

    def test_validate_recomposability(self):
        """Composed skill can be recomposed byte-perfectly."""
        pass

    def test_round_trip_composed_skill(self):
        """Parse → Database → Compose → Verify round-trip."""
        pass

    def test_compose_mixed_file_types(self):
        """Compose from sections of different source files."""
        pass

    def test_compose_with_code_blocks(self):
        """Preserve code blocks in composition."""
        pass

    def test_compose_with_special_chars(self):
        """Handle special characters correctly."""
        pass


class TestSkillValidator:
    """Test SkillValidator."""

    def test_validate_structure_valid(self):
        """Valid hierarchy passes."""
        pass

    def test_validate_structure_circular_parent(self):
        """Detect circular parent-child."""
        pass

    def test_validate_structure_orphaned_child(self):
        """Detect orphaned child section."""
        pass

    def test_validate_content_empty_section(self):
        """Warn about empty sections."""
        pass

    def test_validate_metadata_required_fields(self):
        """Check required frontmatter fields."""
        pass

    def test_validate_metadata_invalid_yaml(self):
        """Reject invalid YAML."""
        pass

    def test_validate_all(self):
        """Run all validators."""
        pass


class TestCompositionEdgeCases:
    """Test edge cases."""

    def test_compose_very_deep_hierarchy(self):
        """Handle deeply nested sections."""
        pass

    def test_compose_very_wide_hierarchy(self):
        """Handle many sections at same level."""
        pass

    def test_compose_large_content(self):
        """Handle large section content."""
        pass

    def test_compose_unicode_content(self):
        """Preserve Unicode correctly."""
        pass

    def test_compose_maintains_heading_levels(self):
        """Heading levels stay consistent."""
        pass
```

**Total Tests**: ~45 unit tests
**Coverage Target**: 90%+
**Execution Time**: ~5 seconds

---

### 6. CLI Tests: `test/test_skill_composer_cli.py` (180 lines)

**Test Coverage**:

```python
class TestComposeCLI:
    """Test compose CLI commands."""

    def test_cmd_compose_basic(self):
        """./skill_split.py compose --section-ids 1,2,3 --title Test"""
        pass

    def test_cmd_compose_with_tags(self):
        """Compose with tags."""
        pass

    def test_cmd_compose_write_filesystem(self):
        """Write composed skill to filesystem."""
        pass

    def test_cmd_compose_invalid_args(self):
        """Reject missing required arguments."""
        pass

    def test_cmd_compose_nonexistent_db(self):
        """Error on bad database path."""
        pass

    def test_cmd_validate_composition_valid(self):
        """Validate valid composed skill."""
        pass

    def test_cmd_validate_composition_invalid(self):
        """Detect invalid composed skill."""
        pass


class TestComposeInteractiveCLI:
    """Test interactive compose workflow (mock stdin)."""

    def test_interactive_compose_full_workflow(self):
        """Complete interactive workflow."""
        pass


class TestComposeFromSearchCLI:
    """Test compose-from-search command."""

    def test_compose_from_search_query(self):
        """Find sections matching query and compose."""
        pass

    def test_compose_from_search_auto_select(self):
        """Auto-select top N results."""
        pass
```

**Total Tests**: ~15 CLI tests
**Mocking Strategy**: Use `unittest.mock` for user input, filesystem operations

---

## Implementation Strategy

### Phase A: Core API (2 hours)

1. **models.py changes** (30 min)
   - Add `ComposedSkill` dataclass
   - Add `CompositionOptions` dataclass
   - Update docstrings

2. **skill_composer.py creation** (90 min)
   - Implement `SkillComposer.__init__()`
   - Implement `compose()` workflow
   - Implement `_retrieve_sections()` and `_rebuild_hierarchy()`
   - Implement `generate_frontmatter()`
   - Implement `write_to_filesystem()` and `upload_to_supabase()`
   - Implement `validate()`

3. **Testing** (30 min)
   - Create test_skill_composer.py
   - Write 30 core unit tests
   - Verify all pass

### Phase B: Validation (1.5 hours)

1. **skill_validator.py creation** (60 min)
   - Implement structure validation
   - Implement content validation
   - Implement metadata validation
   - Implement recomposability testing

2. **Testing** (30 min)
   - Write 15 validator tests
   - Edge case coverage

### Phase C: CLI Integration (1.5 hours)

1. **skill_split.py updates** (60 min)
   - Add 4 new commands: `compose`, `compose-interactive`, `compose-from-search`, `validate-composition`
   - Wire up argparse
   - Add error handling

2. **CLI Testing** (30 min)
   - Write 15 CLI tests
   - Test with real database

### Phase D: Documentation (1 hour)

1. **Update EXAMPLES.md** (30 min)
   - Add composition examples
   - Show interactive workflow
   - Show search-based composition

2. **Update README.md** (20 min)
   - Add SkillComposer section
   - Document API usage

3. **Create SKILL_COMPOSER.md** (10 min)
   - Comprehensive API reference
   - Architecture diagram
   - Troubleshooting guide

### Phase E: Integration Testing (1 hour)

1. **End-to-end tests** (30 min)
   - Parse → Database → Compose → Verify round-trip
   - Filesystem write and read-back
   - Supabase upload (optional: skip if no credentials)

2. **Production testing** (30 min)
   - Test with real ~/.claude/databases/skill-split.db
   - Compose actual skills from library sections
   - Verify byte-perfect round-trip

---

## Time Estimates

| Task | Estimate | Status |
|------|----------|--------|
| models.py changes | 30 min | PLANNING |
| skill_composer.py | 90 min | PLANNING |
| skill_validator.py | 60 min | PLANNING |
| skill_split.py CLI | 60 min | PLANNING |
| test_skill_composer.py | 60 min | PLANNING |
| test_skill_composer_cli.py | 45 min | PLANNING |
| Documentation | 60 min | PLANNING |
| Integration testing | 60 min | PLANNING |
| **TOTAL** | **7.5 hours** | |

**Wall Clock**: 1-2 days (depending on parallelization and testing complexity)

---

## Dependencies

### Phase 11 Depends On

- ✅ Phase 1-10 complete and passing
- ✅ DatabaseStore fully functional
- ✅ QueryAPI fully functional
- ✅ Recomposer byte-perfect round-trip verified
- ✅ ValidationResult model available
- ✅ FileType and FileFormat enums stable

### Phase 11 Enables

- Phase 12: Progressive Disclosure UI (web interface)
- Phase 13: Skill Recommendations (suggest sections to compose)
- Phase 14: Batch Composition (compose multiple skills at once)

---

## API Design Details

### SkillComposer.compose() Workflow

```python
# Minimal usage
composer = SkillComposer("~/.claude/databases/skill-split.db")
skill = composer.compose(
    section_ids=[101, 205, 310],
    title="Python Debugging Guide"
)

# Write to filesystem
path = composer.write_to_filesystem(skill, "~/.claude/skills/debug-guide/")
print(f"Written to {path}")

# Or upload to Supabase
composer.upload_to_supabase(skill)

# Validate before writing
validation = composer.validate(skill)
if validation.is_valid:
    composer.write_to_filesystem(skill)
else:
    print("\n".join(validation.errors))
```

### ComposedSkill Structure

```
ComposedSkill(
    section_ids=[101, 205, 310],
    sections={
        101: Section(level=1, title="Python Debugging", ...),
        205: Section(level=2, title="Using pdb", ...),
        310: Section(level=2, title="Remote Debugging", ...),
    },
    title="Python Debugging Guide",
    description="Comprehensive guide to Python debugging tools",
    author="SkillComposer",
    tags=["python", "debugging", "tools"],
    source_files=["~/.claude/skills/python-basics/SKILL.md"],
)
```

### Frontmatter Template

```yaml
---
title: "Python Debugging Guide"
description: "Comprehensive guide to Python debugging tools"
author: "SkillComposer"
created_at: "2026-02-05T12:00:00Z"
tags:
  - python
  - debugging
  - tools
source_files:
  - ~/.claude/skills/python-basics/SKILL.md
source_section_ids:
  - 101
  - 205
  - 310
---
```

### Error Handling

**Invalid Section IDs**:
```python
try:
    skill = composer.compose(section_ids=[999, 1000])
except ValueError as e:
    # "Section IDs not found: [999, 1000]"
    pass
```

**Hierarchy Broken**:
```python
# If parent section (101) comes after child (205)
try:
    skill = composer.compose(section_ids=[205, 101])
except ValueError as e:
    # "Hierarchy broken: Child section before parent"
    pass
```

**Validation Failure**:
```python
validation = composer.validate(skill)
if not validation.is_valid:
    for error in validation.errors:
        print(f"ERROR: {error}")
    for warning in validation.warnings:
        print(f"WARNING: {warning}")
```

---

## Testing Strategy

### Unit Testing

- **Core API**: 30 tests for SkillComposer
- **Validation**: 15 tests for SkillValidator
- **Models**: 5 tests for ComposedSkill
- **Total**: 50 unit tests

### Integration Testing

- **Parse → Database → Compose → Verify**: 5 tests
- **Filesystem operations**: 3 tests
- **Supabase integration**: 3 tests (optional)
- **Total**: 11 integration tests

### CLI Testing

- **All 4 new commands**: 15 tests
- **Error handling**: 5 tests
- **Total**: 20 CLI tests

### Coverage Requirements

- **Line Coverage**: 90%+
- **Branch Coverage**: 85%+
- **Edge Cases**: All major paths covered

### Test Execution

```bash
# Unit tests only
pytest test/test_skill_composer.py -v
pytest test/test_skill_composer_cli.py -v

# All tests
pytest test/ -v --cov=core/skill_composer --cov=handlers/skill_validator

# Performance test
pytest test/ -v --timeout=5  # All tests complete in <5s
```

---

## Implementation Checklist

### Pre-Implementation

- [ ] Review all existing code (Phases 1-10)
- [ ] Verify Phases 1-10 tests pass
- [ ] Confirm database schema is stable
- [ ] Test QueryAPI with real database

### Phase A: Core API

- [ ] Add ComposedSkill to models.py
- [ ] Add CompositionOptions to models.py
- [ ] Create skill_composer.py
- [ ] Implement SkillComposer.__init__()
- [ ] Implement compose() workflow
- [ ] Implement _retrieve_sections()
- [ ] Implement _rebuild_hierarchy()
- [ ] Implement generate_frontmatter()
- [ ] Implement write_to_filesystem()
- [ ] Implement upload_to_supabase()
- [ ] Implement validate()
- [ ] Write 30+ unit tests
- [ ] All tests pass

### Phase B: Validation

- [ ] Create skill_validator.py
- [ ] Implement structure validation
- [ ] Implement content validation
- [ ] Implement metadata validation
- [ ] Implement recomposability testing
- [ ] Write 15+ validator tests
- [ ] All tests pass

### Phase C: CLI Integration

- [ ] Add cmd_compose() to skill_split.py
- [ ] Add cmd_compose_interactive()
- [ ] Add cmd_compose_from_search()
- [ ] Add cmd_validate_composition()
- [ ] Update argparse with 4 new commands
- [ ] Write 15+ CLI tests
- [ ] All tests pass
- [ ] Test with real database

### Phase D: Documentation

- [ ] Update EXAMPLES.md with composition examples
- [ ] Update README.md with SkillComposer section
- [ ] Create SKILL_COMPOSER.md with API reference
- [ ] Add troubleshooting guide
- [ ] Verify all examples are copy-pasteable

### Phase E: Integration & Verification

- [ ] End-to-end round-trip tests
- [ ] Filesystem write and read verification
- [ ] Supabase upload verification (if credentials available)
- [ ] Test with real ~/.claude/databases/skill-split.db
- [ ] Compose 3-5 actual skills and verify byte-perfect round-trip
- [ ] All 50+ unit tests pass
- [ ] All 20+ CLI tests pass
- [ ] Coverage >90%
- [ ] No warnings or errors

### Post-Implementation

- [ ] Update CLAUDE.md with Phase 11 completion
- [ ] Update version number in CODEX.md
- [ ] Commit changes with clear message
- [ ] Create git tag for Phase 11

---

## Success Criteria

### Functional

- ✅ Compose skills from arbitrary section IDs
- ✅ Auto-generate valid frontmatter (YAML)
- ✅ Rebuild section hierarchies correctly
- ✅ Validate composed skills (structure, content, metadata)
- ✅ Write to filesystem with proper directory creation
- ✅ Upload to Supabase (with existing credentials)
- ✅ Byte-perfect round-trip verification (parse → db → compose → verify)
- ✅ All 4 CLI commands work end-to-end

### Quality

- ✅ 90%+ code coverage
- ✅ 50+ unit tests pass
- ✅ 20+ CLI tests pass
- ✅ No warnings or errors
- ✅ All existing tests still pass (Phases 1-10)

### Documentation

- ✅ EXAMPLES.md includes composition examples
- ✅ README.md documents SkillComposer API
- ✅ SKILL_COMPOSER.md provides reference guide
- ✅ Troubleshooting guide included
- ✅ All examples copy-pasteable and tested

### Deployment

- ✅ Works with production database (~1,365 files)
- ✅ Works with Supabase (optional)
- ✅ Works with real ~/.claude/skills/* paths
- ✅ No data loss in any operation

---

## Risk Assessment

### High Risk

**Risk**: Hierarchy rebuild algorithm creates orphaned sections
- **Mitigation**: Comprehensive hierarchy validation before output
- **Test**: 5+ hierarchy-specific tests
- **Fallback**: Reject composition if hierarchy broken

**Risk**: Byte-perfect round-trip fails after composition
- **Mitigation**: Reuse proven Recomposer logic; validate before write
- **Test**: 3+ round-trip integration tests
- **Fallback**: Warn user if composed output differs from expected

### Medium Risk

**Risk**: Frontmatter generation creates invalid YAML
- **Mitigation**: Use proven YAML library (PyYAML); test all metadata values
- **Test**: 5+ frontmatter tests
- **Fallback**: Provide raw frontmatter option

**Risk**: Filesystem write permission issues
- **Mitigation**: Check perms early; create directories with safe modes
- **Test**: Filesystem permission tests
- **Fallback**: Provide Supabase upload option

### Low Risk

**Risk**: CLI argument parsing has issues
- **Mitigation**: Reuse existing argparse patterns; thorough CLI tests
- **Test**: 15+ CLI tests
- **Fallback**: Provide Python API usage guide

---

## Future Considerations (Phase 12+)

### Batch Composition

```python
# Compose multiple skills in one operation
composer.compose_batch([
    {"section_ids": [1, 2, 3], "title": "Skill 1"},
    {"section_ids": [4, 5, 6], "title": "Skill 2"},
])
```

### Progressive Disclosure UI

```python
# Web interface for visual composition
composer.export_for_ui()  # Returns interactive JSON structure
```

### Smart Section Selection

```python
# Auto-suggest sections for composition
composer.suggest_sections(query="Python debugging")
# Returns: [101, 205, 310, ...] with relevance scores
```

### Version Control Integration

```python
# Track composed skill origin
skill.source_commit = "e1ef687"
skill.source_branch = "main"
```

---

## References

- **Phase 10 (Script Handlers)**: `PHASE_10_CLOSURE_PLAN.md`
- **Recomposer**: `core/recomposer.py` (proven byte-perfect algorithm)
- **QueryAPI**: `core/query.py` (section retrieval patterns)
- **Existing Tests**: `test/test_roundtrip.py` (validation patterns)
- **Deployment**: `DEPLOYMENT_STATUS.md` (Supabase integration)

---

## Sign-Off

**Created**: 2026-02-05
**Author**: Claude Code (Planning)
**Status**: READY FOR IMPLEMENTATION
**Next Step**: Begin Phase A (Core API) implementation

This plan is comprehensive, realistic, and achievable in 6-8 hours with proper implementation discipline. All major risk areas have mitigation strategies. Success is measurable via test coverage and real-world validation.

---

*Last Updated: 2026-02-05 | Phase 11 Planning Complete*
