# Round-Trip Verification: Commands Directory

**Date**: 2026-02-04
**Status**: 220/224 passing (98.2%)
**Test File**: `tests/commands/test_roundtrip.py`

## Summary

Tested ALL 224 command files in `~/.claude/commands/` for byte-perfect round-trip.

## Results

| Category | Count | Status |
|----------|-------|--------|
| **Passing** | 220 | ✅ 100% byte-perfect |
| **Failing** | 4 | ❌ XML tag indentation issue |
| **Total** | 224 | 98.2% pass rate |

## Failing Files

All 4 failures are in `commands/gsd/` and use XML tag format:
1. `list-phase-assumptions.md`
2. `complete-milestone.md`
3. `pause-work.md`
4. `resume-work.md`

## Root Cause

**BUG**: XML closing tag indentation not preserved.

### Original File Format
```xml
<success_criteria>

- Phase validated against roadmap
- User knows next steps (discuss context, plan phase, or correct assumptions)
  </success_criteria>
```

Note the **2 spaces before `</success_criteria>`** on line 50.

### Recomposed Output
```xml
<success_criteria>

- Phase validated against roadmap
- User knows next steps (discuss context, plan phase, or correct assumptions)
</success_criteria>
```

The closing tag has **no indentation** - the leading spaces are lost.

### Technical Analysis

**Location**: `core/parser.py` lines 344-348

The parser matches closing tags using:
```python
if next_stripped.startswith("</") and depth > 1:
    closing_match = re.match(r"^</([a-z0-9_]*)>\s*$", next_line)
```

Problem: Uses `next_stripped` (stripped line) to match, but doesn't preserve the original indentation of the closing tag.

**Impact**: Any XML-tag formatted file with indented closing tags will fail round-trip.

## Fix Required

Modify parser to preserve closing tag indentation. Options:

1. **Store closing tag as part of content** - Treat the closing tag line as content (current behavior is inconsistent)
2. **Preserve indentation in metadata** - Add a `closing_indent` field to Section
3. **Match and store original closing tag** - Capture the exact closing tag line with indentation

## Test Command

```bash
python tests/commands/test_roundtrip.py
```

## Next Steps

1. Fix XML closing tag indentation preservation
2. Re-run tests to verify 224/224 passing
3. Move to next directory (agents/, skills/, etc.)

---

*Last Updated: 2026-02-04*
*Test Coverage: 224/224 files tested*
