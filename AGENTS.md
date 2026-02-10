# AGENTS.md

Agent-wide rules and workflow guardrails for skill-split development.

## Core Workflow: Auto-Full-Auto Loop

**Goal:** FULL, FINISHED PROJECT - not docs and claims, but WORKING CODE

### 5-Step Process

```
1. PLAN (3-5 comprehensive plans)
   └─> Output: .planning/phases/<phase>/0*-PLAN.md files

2. VERIFY (Each plan independently)
   └─> Output: .planning/phases/<phase>/VERIFICATION.md

3. UNIFY (Combine plans)
   └─> Output: VERIFICATION.md updated with execution order

4. VERIFY (Unified plan)
   └─> Output: Final approval check

5. EXECUTE (With verifier agents)
   └─> Wave 1 → /clear → Wave 2 → /clear → Wave 3 → /clear
   └─> Each executor → Independent verifier → Approval → Commit
```

### Context Management Between Phases

**Critical Rule:** Use `/clear` or `/compact` between major phases

```bash
# AFTER planning complete
/clear

# AFTER verification complete
/clear

# AFTER each wave of execution
/clear
```

**Why:** Fresh context prevents hallucination, keeps focus on current work

### Internal Communication Format

**Use YAML for all internal reasoning:**

```yaml
thinking:
  step_1: "Understand the requirement"
  step_2: "Check existing code"
  step_3: "Form solution"
  step_4: "Implement with verification"

status: "in_progress|completed|blocked"
next_action: "Specific next step"
```

### Verifier Agent Rule

**CRITICAL:** No agent ever verifies its own work

```
Executor Agent (Plan N) ──> Verifier Agent (Independent)
                              ├─> Code quality check
                              ├─> Architecture review
                              ├─> Security check
                              └─> Approval → Commit
```

### Verifier Agents Available

- `compound-engineering:review:kieran-python-reviewer` - Python code quality
- `compound-engineering:review:architecture-strategist` - Architecture review
- `compound-engineering:review:security-sentinel` - Security check
- `compound-engineering:review:performance-oracle` - Performance analysis
- `compound-engineering:review:code-simplicity-reviewer` - Simplicity check

## Execution Commands

### To Plan
```bash
/gsd:plan-phase --gaps
```

### To Execute
```bash
/gsd:execute-phase <phase-name>
```

### To Verify
```bash
/gsd:verify-work
```

### To Check Status
```bash
/gsd:status
```

## File Structure

```
.planning/
├── phases/
│   ├── <phase-name>/
│   │   ├── 01-PLAN.md      # Detailed task list
│   │   ├── 02-PLAN.md      # Detailed task list
│   │   ├── VERIFICATION.md # Unified verification
│   │   └── EXECUTE.md      # Execution command
│   └── ...
├── research/
│   └── <topic>-investigation.md
├── GSD_WORKFLOW.md         # Detailed workflow
├── PROJECT.md
├── ROADMAP.md
└── STATE.md
```

## Success Criteria

### Plan Quality
- [ ] 3-5 comprehensive plans
- [ ] All tasks fully specified (no stubs)
- [ ] Test coverage planned
- [ ] Dependencies mapped
- [ ] Verification criteria defined

### Execution Quality
- [ ] All plans executed successfully
- [ ] All tests pass
- [ ] No regressions
- [ ] Verifier agents approve
- [ ] Documentation complete

### Project Quality
- [ ] Code works, not just docs
- [ ] Tests verify functionality
- [ ] User can use the feature
- [ ] No TODOs left behind
- [ ] Ready for production

---

*See: .planning/GSD_WORKFLOW.md for detailed workflow*
