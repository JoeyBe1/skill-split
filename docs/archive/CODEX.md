# CODEX.md

Purpose: concise, high-signal instructions for Codex working in this repo.

## /init Checklist
- Read `CLAUDE.md`, `DEPLOYMENT_STATUS.md`, `COMPONENT_HANDLERS.md`, `HANDLER_INTEGRATION.md`.
- Run `git status -sb` to understand the working tree.
- Do not redesign or rewrite; only targeted fixes that preserve intent and existing behavior.
- Keep byte-perfect round-trip guarantees intact.

## Project Intent (Short)
- `skill-split` provides progressive disclosure for large files by splitting into sections and storing them in SQLite (and optionally Supabase).
- Recomposer must be byte-perfect: recomposed output must exactly match the source input.
- Component handlers support multi-file components (plugins, hooks, configs, scripts) with combined hashing and related file deployment.

## Golden Rules
- Preserve exact file content; no normalization or simplification that changes bytes.
- Prefer minimal, in-place changes; avoid sweeping refactors.
- Keep tests aligned with intended behavior, not vice versa.
- If unsure, read the docs before touching code.

## Core Surfaces
- CLI entry: `skill_split.py`
- Core logic: `core/`
- Handlers: `handlers/`
- Tests: `test/`

## Verification
- Functional: `./skill_split.py parse|validate|store|verify <file>`
- Tests: `pytest test/ -v` (or scoped subsets)

## Where to Track Gaps
- `GAPS_AND_TASKS.yaml`
- `PHASE_10_GAP_ANALYSIS.md`
- `PHASE_10_CLOSURE_PLAN.md`
