# Documentation Index

Quick reference for all skill-split documentation.

---

## Getting Started (Start Here!)

| Doc | Purpose | Audience |
|-----|---------|----------|
| [README.md](README.md) | Overview, features, installation, quick start | Everyone |
| [DEPLOYMENT_STATUS.md](DEPLOYMENT_STATUS.md) | Current system status and capabilities | Operators |
| [EXAMPLES.md](EXAMPLES.md) | Real-world usage scenarios with output | Users |

---

## User Guides

| Doc | Purpose | Audience |
|-----|---------|----------|
| [COMPONENT_COMPOSITION.md](COMPONENT_COMPOSITION.md) | How to compose custom components from sections | Users building skills |
| [SUPABASE_SETUP.md](SUPABASE_SETUP.md) | Cloud integration and Supabase configuration | Users |
| [VECTOR_SEARCH_GUIDE.md](VECTOR_SEARCH_GUIDE.md) | Vector search setup, costs, and optimization | Advanced users |
| [INGESTION_GUIDE.md](INGESTION_GUIDE.md) | Batch ingestion of multiple files | Operators |

---

## Developer Documentation

| Doc | Purpose | Audience |
|-----|---------|----------|
| [CLAUDE.md](CLAUDE.md) | Project state, architecture, production readiness | Developers |
| [COMPONENT_HANDLERS.md](COMPONENT_HANDLERS.md) | Component handler architecture and implementation | Contributors |
| [HANDLER_INTEGRATION.md](HANDLER_INTEGRATION.md) | Integrating handlers into existing systems | Contributors |

---

## Operations & Deployment

| Doc | Purpose | Audience |
|-----|---------|----------|
| [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) | Pre-deployment verification checklist | Operators |
| [migrations/SCHEMA_MIGRATION_GUIDE.md](migrations/SCHEMA_MIGRATION_GUIDE.md) | Database schema changes and migrations | DBAs |

---

## Testing & Verification

| Doc | Purpose | Audience |
|-----|---------|----------|
| [test/MANUAL_ROUNDTRIP_TEST.md](test/MANUAL_ROUNDTRIP_TEST.md) | Manual testing and round-trip verification | QA |

---

## Technical References

| Doc | Purpose |
|-----|---------|
| [docs/VECTOR_SEARCH_COSTS.md](docs/VECTOR_SEARCH_COSTS.md) | Vector search cost analysis and benchmarks |
| [demo/sample_skill.md](demo/sample_skill.md) | Example skill file demonstrating structure |

---

## Internal Rules & Standards

| Doc | Purpose | Audience |
|-----|---------|----------|
| [CODEX.md](CODEX.md) | Project init checklist and guardrails | Developers |
| [AGENT.md](AGENT.md) | Rules for Claude Code agent interaction | Claude agents |

---

## Development History (Archived)

All development artifacts from Phases 1-14 and Waves 1-8:

- [.archive/wave-reports/](/.archive/wave-reports/) - Completion reports from implementation waves
- [.archive/phase-plans/](/.archive/phase-plans/) - Phase planning documents
- [.archive/task-reports/](/.archive/task-reports/) - Task execution records
- [.archive/testing-docs/](/.archive/testing-docs/) - Testing procedures
- [.archive/test-reports/](/.archive/test-reports/) - Test results
- [.archive/investigations/](/.archive/investigations/) - Technical investigations
- [.archive/strategy-docs/](/.archive/strategy-docs/) - Strategy and handoff docs
- [.archive/user-guides/](/.archive/user-guides/) - User and developer workflow guides

See [.archive/README.md](/.archive/README.md) for full archive documentation.

---

## Quick Navigation by Role

### For New Users
1. Start with [README.md](README.md)
2. Follow [DEPLOYMENT_STATUS.md](DEPLOYMENT_STATUS.md) for current capabilities
3. Try examples in [EXAMPLES.md](EXAMPLES.md)

### For Operators
1. Read [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) before deploying
2. Check [DEPLOYMENT_STATUS.md](DEPLOYMENT_STATUS.md) for capabilities
3. Reference [migrations/SCHEMA_MIGRATION_GUIDE.md](migrations/SCHEMA_MIGRATION_GUIDE.md) for upgrades
4. Use [INGESTION_GUIDE.md](INGESTION_GUIDE.md) for batch operations

### For Developers
1. Start with [CLAUDE.md](CLAUDE.md) for architecture
2. Read [COMPONENT_HANDLERS.md](COMPONENT_HANDLERS.md) for handler details
3. Review [HANDLER_INTEGRATION.md](HANDLER_INTEGRATION.md) for integration patterns

### For Contributors
1. Read [AGENT.md](AGENT.md) and [CODEX.md](CODEX.md)
2. Review [COMPONENT_HANDLERS.md](COMPONENT_HANDLERS.md)
3. Check [test/MANUAL_ROUNDTRIP_TEST.md](test/MANUAL_ROUNDTRIP_TEST.md) for testing

---

## Documentation Status

| Status | Count | Examples |
|--------|-------|----------|
| Current | 18 | README, CLAUDE, EXAMPLES, deployment docs |
| Archived | 44 | Phase plans, wave reports, test reports |
| Total | 62 | |

Last updated: 2026-02-06
