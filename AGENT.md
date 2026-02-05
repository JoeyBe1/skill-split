# AGENT.md

Agent-wide rules for this repository.

## Non-Negotiables
- Do not redesign or rewrite; only close specific gaps in the existing codebase.
- Preserve byte-perfect behavior; never normalize or reformat stored content.
- Prefer minimal, in-place changes with tight scope.
- Read `CODEX.md` and `CLAUDE.md` before making changes.

## Verification Expectations
- Use targeted tests that prove the change.
- If tests are not run, say so explicitly.

## Working Style
- Small diffs, clear reasoning, no feature drift.
- Respect existing conventions and file structure.
