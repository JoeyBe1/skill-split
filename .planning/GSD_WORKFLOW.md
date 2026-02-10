# GSD Workflow: Plan-Verify-Unify-Verify

**Date:** 2026-02-08
**Purpose:** Capture Joey's workflow for future sessions

## Core Workflow

```
1. PLAN (3-5 comprehensive plans)
   ├── Research codebase first
   ├── Create detailed plans with full tasks
   ├── No stubs - build everything completely
   └── More atomic tasks = bigger phases possible

2. VERIFY (Each plan independently)
   ├── Check against user requirements
   ├── Verify no regressions
   ├── Test coverage planned
   └── Document dependencies

3. UNIFY (Combine plans)
   ├── Resolve cross-plan dependencies
   ├── Create execution order
   ├── Identify parallelizable work
   └── Create unified success criteria

4. VERIFY (Unified plan)
   ├── Check all plans work together
   ├── Verify end-to-end flow
   ├── Confirm no conflicts
   └── Final approval check

5. EXECUTE (With verifier agents)
   ├── Execute plans in dependency order
   ├── Each agent verified by independent agent
   ├── No agent verifies its own work
   ├── Parallel execution when possible
   └── Checkpoints between waves
```

## Key Principles

### Planning Phase
- **Research first**: Use codegraph, grep, read to understand codebase
- **3-5 plans**: Comprehensive coverage, not too fragmented
- **Full tasks**: Each task is complete, no "TODO later"
- **Atomic**: Tasks can be executed independently
- **Testable**: Each plan has verification criteria

### Verification Phase
- **Independent verification**: Different agent verifies work
- **No self-verification**: Agent never reviews its own work
- **Test coverage**: Unit + integration tests
- **Regression check**: All existing tests must pass

### Unification Phase
- **Dependency mapping**: Which plans depend on others
- **Parallel execution**: Independent plans run simultaneously
- **Wave structure**: Group plans by dependencies
- **Rollback planning**: Each plan commits separately

### Execution Phase
- **Verifier agents**: After each plan, verifier checks work
- **Checkpoints**: Stop between waves for user review
- **Atomic commits**: Each plan = one git commit
- **Context management**: `/clear` or `/compact` between phases

## Agent Types

### Primary Agents
- **gsd-planner**: Creates detailed plans from requirements
- **gsd-executor**: Executes plans with atomic tasks
- **gsd-verifier**: Verifies completed work independently

### Verifier Agents (Never self-verify)
- **compound-engineering:review:code-simplicity-reviewer**: Checks for over-engineering
- **compound-engineering:review:architecture-strategist**: Reviews architectural changes
- **compound-engineering:review:security-sentinel**: Security review
- **compound-engineering:review:kieran-python-reviewer**: Python code review
- **compound-engineering:review:performance-oracle**: Performance analysis

## Execution Pattern

### Wave 1 (Parallel)
```
Plan A ──→ Exec A ──→ Verify A ──→ Commit A
Plan B ──→ Exec B ──→ Verify B ──→ Commit B
Plan C ──→ Exec C ──→ Verify C ──→ Commit C
```

### Wave 2 (After Wave 1)
```
Plan D (depends on A) ──→ Exec D ──→ Verify D ──→ Commit D
Plan E (depends on B) ──→ Exec E ──→ Verify E ──→ Commit E
```

### Wave 3 (After Waves 1-2)
```
Plan F (depends on D, E) ──→ Exec F ──→ Verify F ──→ Commit F
```

## Commands

### Planning
```bash
/gsd:plan-phase --gaps
```

### Execution
```bash
/gsd:execute-phase <phase-name>
```

### Verification
```bash
/gsd:verify-work
```

### Context Management
```bash
/clear    # Clear context between major phases
/compact  # Compact context to save key info
```

## Success Criteria

### Plan Quality
- [ ] 3-5 comprehensive plans
- [ ] All tasks fully specified
- [ ] Test coverage planned
- [ ] Dependencies mapped
- [ ] Verification criteria defined

### Execution Quality
- [ ] All plans executed successfully
- [ ] All tests pass
- [ ] No regressions
- [ ] Verifier agents approve
- [ ] Documentation complete

### Unification Quality
- [ ] Plans work together
- [ ] No conflicts between plans
- [ ] End-to-end flow verified
- [ ] User goals achieved

## File Structure

```
.planning/
├── phases/
│   ├── <phase-name>/
│   │   ├── 01-PLAN.md
│   │   ├── 02-PLAN.md
│   │   └── VERIFICATION.md
│   └── ...
├── research/
│   └── <topic>-investigation.md
├── PROJECT.md
├── ROADMAP.md
└── STATE.md
```

## Memory Updates

After each phase:
1. Update STATE.md with completion status
2. Update ROADMAP.md with progress
3. Update MEMORY.md with lessons learned
4. Create SUMMARY.md in phase directory

## Session Continuation

To continue work in new session:
1. Read STATE.md for current position
2. Read phase plan files
3. Use `/gsd:execute-phase` to continue
4. Use verifier agents after each completion

---

**Created by:** Joey's instruction
**Last updated:** 2026-02-08
**Version:** 1.0
