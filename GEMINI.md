# GEMINI.md

Context and guidelines for Gemini agents working on **skill-split**.

## 1. Project Overview

**skill-split** is a tool to intelligently split YAML and Markdown files into discrete sections and store them in a SQLite database for progressive disclosure. This solves the token inefficiency problem when working with large documentation or skill files.

*   **Core Problem**: Large files consume too many tokens.
*   **Solution**: Parse files into sections, store in SQLite, retrieve only what's needed.
*   **Key Feature**: Byte-perfect round-trip integrity (SHA256 verification).

## 2. Current Status

*   **Phases Completed**: 1-10 (Core, Database, CLI, Supabase, Component Handlers).
*   **Current Phase**: Phase 11 - Skill Composition (Implementing `SkillComposer`).
*   **Tests**: ~214 tests passing.
*   **Active Task**: Implementing `SkillComposer` to stitch sections back into valid skill files.

## 3. Core Mandates (from AGENTS.md)

*   **Byte-Perfect Integrity**: Never normalize or reformat stored content. Round-trip hashes MUST match.
*   **Scope**: Do not redesign or rewrite; only close specific gaps.
*   **Conventions**: Respect existing conventions and file structure.
*   **Verification**: Use targeted tests that prove the change.

## 4. Architecture

*   **Parser (`core/parser.py`)**: Detects formats (YAML, MD, XML) and splits content.
*   **Database (`core/database.py`)**: SQLite storage for files and sections.
*   **Recomposer (`core/recomposer.py`)**: Reconstructs files ensuring exact byte matching.
*   **Handlers (`handlers/`)**: Specialized support for Plugins, Hooks, and Configs.
*   **CLI (`skill_split.py`)**: Main entry point.

## 5. Quick Reference

*   **CLI Command**: `./skill_split.py`
*   **Run Tests**: `pytest -v`
*   **Key Docs**:
    *   `README.md`: General usage.
    *   `COMPONENT_HANDLERS.md`: Guide for non-markdown components.
    *   `AGENTS.md`: Agent rules.
    *   `CLAUDE.md`: Project status tracking.
    *   `prd.json`: Detailed task tracking.

## 6. Component Types
The system supports:
*   Markdown (`.md`)
*   Plugins (`plugin.json`)
*   Hooks (`hooks.json`)
*   Configs (`settings.json`, `mcp_config.json`)

## 7. Next Steps
Focus on `core/skill_composer.py` to enable composing new skills from selected database sections.
