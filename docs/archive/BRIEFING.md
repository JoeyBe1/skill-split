# ELITE COMPOSITION IMPLEMENTATION PLAN

**Role**: Senior System Architect
**Objective**: Implement the Elite Composition Layer for `skill-split`.
**Baseline**: 499 passing tests. Core byte-perfect parsing is SOLVED.

## Task 1: Metadata Enrichment
- **Action**: Refactor `core/skill_composer.py`. Replace basic string-building in `_generate_frontmatter` with a call to `core/frontmatter_generator.py:generate_frontmatter()`.
- **Outcome**: Composed skills must contain auto-extracted tags, dependencies, and statistics.

## Task 2: Pre-Composition Validation
- **Action**: In `SkillComposer.compose_from_sections`, instantiate `core/skill_validator.py:SkillValidator`.
- **Target**: Validate the `ComposedSkill` content. If `is_valid` is False, raise a `ValueError` with detailed errors. Do not allow "junk" skills to be created.

## Task 3: Multi-File Component Support
- **Action**: Enable `SkillComposer` to handle `FileType.PLUGIN`.
- **Logic**: If the selected sections belong to a Plugin, the composer must be able to recreate the directory structure, placing `plugin.json` and associated `.sh` scripts in their relative paths.

## Task 4: CLI Polish
- **Action**: Update `skill_split.py:cmd_compose`.
- **Add Flags**:
  - `--validate/--no-validate`: Run strict validation (default: True).
  - `--enrich/--no-enrich`: Force deep metadata extraction (default: True).

## Verification Mandate
1. Create `test/test_elite_composition.py`.
2. **Target Test**: Compose a new Skill from 3 different source IDs. Verify that the output hash is deterministic and that `Validator.validate()` returns `True`.
3. Ensure final test count hits **500+**.

**EXECUTION INSTRUCTION**:
Read the codebase (`core/skill_composer.py`, `core/frontmatter_generator.py`, `core/skill_validator.py`, `skill_split.py`).
Then implement the changes step-by-step, running tests after each step.
Finally, run `pytest -v` to confirm 500+ tests pass.
