---
status: investigating
trigger: "Find bugs in skill-split that prevent it from being a 'NetworkX for Claude Code'"
created: 2026-02-08T14:30:00Z
updated: 2026-02-08T14:55:00Z
---

## Current Focus

hypothesis: "Multi-word search limitation is the main issue preventing 'NetworkX for Claude Code' usability"
test: "Verify search works for single words but fails for multi-word phrases"
expecting: "Confirmed - search_sections uses LIKE '%query%' requiring exact phrase match"
next_action: "Document findings and potential fixes"

## Symptoms

expected: skill-split handles all Claude Code components (skills, agents, commands, plugins, hooks, settings) with perfect accuracy
actual: User reports "there are bugs but we are close" - 485 tests passing but real-world usage has issues
errors: Unknown - need to discover through testing
reproduction: Need to test with real ~/.claude/ files
started: User feedback on 2026-02-08

## Evidence

- timestamp: 2026-02-08T14:55:00Z
  checked: FTS5 full-text search integrity
  found: sections_fts table has entries for non-existent sections (row 42 missing from sections table)
  implication: FTS index not kept in sync with main table on DELETE operations
  evidence: "fts5: missing row 42 from content table 'main'.'sections'" when querying FTS
  severity: HIGH - causes search errors and index corruption

- timestamp: 2026-02-08T14:35:00Z
  checked: Parsing real Claude Code files
  found: All component types parse correctly (skills, commands, hooks, configs, scripts)
  implication: Parser works for real-world files

- timestamp: 2026-02-08T14:36:00Z
  checked: Search functionality with multi-word queries
  found: search_sections uses LIKE '%query%' requiring exact phrase match
  implication: "github repository setup" finds nothing even though content has both words

- timestamp: 2026-02-08T14:37:00Z
  checked: Round-trip verification
  found: SHA256 hash matches perfectly for skill file
  implication: Round-trip works correctly

- timestamp: 2026-02-08T14:38:00Z
  checked: Composition
  found: Can compose new skills from sections correctly
  implication: Composition works

- timestamp: 2026-02-08T14:39:00Z
  checked: Section retrieval (get-section)
  found: Works correctly with database IDs
  implication: Progressive disclosure works

- timestamp: 2026-02-08T14:40:00Z
  checked: search-semantic fallback
  found: Falls back to search_sections which has same multi-word limitation
  implication: Semantic search fallback has same limitation as regular search

- timestamp: 2026-02-08T14:45:00Z
  checked: Progressive disclosure "next" command
  found: "next" from top-level heading (69) returns nothing because it looks for siblings with same parent_id (NULL)
  implication: Expected behavior but could be confusing - users might expect first child

- timestamp: 2026-02-08T14:46:00Z
  checked: Cross-file search
  found: Works correctly across skills, commands, hooks, and configs
  implication: Search finds sections across all file types

- timestamp: 2026-02-08T14:47:00Z
  checked: All 485 tests
  found: All tests passing
  implication: Core functionality is solid

- timestamp: 2026-02-08T14:48:00Z
  checked: Handler coverage
  found: Python, JavaScript, TypeScript, Shell, plugin, hook, config handlers all working
  implication: All Claude Code component types supported

- timestamp: 2026-02-08T14:49:00Z
  checked: checkout/checkin commands
  found: Require Supabase (cloud-only), not --db parameter for local SQLite
  implication: Checkout/checkin are cloud-only features, local users need different workflow

- timestamp: 2026-02-08T14:51:00Z
  checked: Agent file parsing
  found: Agent files parse correctly with "mixed" format (XML + markdown)
  implication: Agent system is supported

- timestamp: 2026-02-08T14:52:00Z
  checked: Section 128 (XML tag with empty title)
  found: XML sections have level=-1 and empty titles, which is expected
  implication: Not a bug - this is correct behavior for XML tag sections

- timestamp: 2026-02-08T14:53:00Z
  checked: Composition frontmatter
  found: Has both "sections" and "sections_count" fields (intentional for compatibility)
  implication: Not a bug - intentional design for backward compatibility

## Eliminated

- hypothesis: Parser fails on real Claude Code files
  evidence: Tested skills, commands, hooks, configs, scripts - all parse correctly
  timestamp: 2026-02-08T14:50:00Z

- hypothesis: Round-trip loses data
  evidence: SHA256 verification passes for complex files
  timestamp: 2026-02-08T14:50:00Z

- hypothesis: Search doesn't find relevant content
  evidence: Single-word search works well; multi-word has known limitation
  timestamp: 2026-02-08T14:50:00Z

## Resolution

root_cause:
**ISSUE 1: Multi-word search limitation (LOW severity)**
- search_sections() uses LIKE '%query%' requiring exact phrase match
- "github repository setup" finds nothing even though content has both words
- search_sections_with_rank() exists with FTS5 but not used by default
- Impact: Poor search experience for natural language queries

**ISSUE 2: Potential FTS index sync issue (MEDIUM severity)**
- External content FTS table requires manual sync
- Current code uses INSERT OR REPLACE which should work
- May have issues with orphaned entries in some scenarios
- The "fts5: missing row" error seen earlier suggests potential sync issues
- Impact: Search errors, corrupted index

**ISSUE 3: Progressive disclosure "next" behavior (LOW severity)**
- At top-level heading, "next" finds siblings not children
- Technically correct but may confuse users
- Impact: Minor UX confusion

**ISSUE 4: Checkout/checkin cloud-only (DESIGN decision)**
- Require Supabase, no local SQLite support
- May be intentional design choice
- Impact: Local users can't use checkout/checkin

fix:
**HIGH PRIORITY:** Verify FTS sync mechanism is robust
- Consider adding explicit DELETE from sections_fts when deleting sections
- Add error handling for FTS sync failures
- Add test for re-store scenario

**MEDIUM PRIORITY:** Improve search experience
- Use FTS5 search by default instead of LIKE
- Or split query words and use OR logic

**LOW PRIORITY:** Improve "next" command UX
- Add flag for --child vs --sibling navigation
- Or document behavior clearly

verification:
- All 485 tests passing
- Real Claude Code files parse correctly
- Core functionality works
- Search works for single words
- FTS search may have edge cases

files_changed: []
