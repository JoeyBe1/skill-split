# Ralph Wiggum Loop: Usage Guide

## Quick Start

### 1. Current Project State

Your `prd.json` is already created with 11 tasks mapped out. Here's how to execute them autonomously:

```bash
# In skill-split directory
cd /Users/joey/working/skill-split

# Start fresh Claude session
claude-model glm
claude "Read prd.json. Execute active_task_id. Run verification. Update status and advance. EXIT when done."
```

OR use the skill:

```bash
/ralph-loop
```

### 2. What Happens Next

**First Execution (TASK-001: QueryAPI)**
```yaml
session_1:
  reads: "prd.json"
  identifies: "TASK-001 (QueryAPI Implementation)"
  checks: "learning_log (4 previous entries)"
  executes: "Create core/query.py with 4 methods"
  verifies: "python -c 'from core.query import QueryAPI; print(\"OK\")'"
  updates:
    - status: "done"
    - active_task_id: "TASK-002"
    - learning: "QueryAPI implemented with get_section, get_next_section, get_section_tree, search_sections"
  exits: "✓ Session complete"
```

**Second Execution (TASK-002: Tests)**
```yaml
session_2:
  reads: "prd.json (updated)"
  identifies: "TASK-002 (QueryAPI Tests)"
  sees: "Previous learning: QueryAPI implemented"
  checks: "Dependency TASK-001 = done ✓"
  executes: "Create test/test_query.py with 15+ tests"
  verifies: "pytest test/test_query.py -v"
  updates:
    - status: "done"
    - active_task_id: "TASK-003"
    - learning: "15 tests created covering all QueryAPI methods"
  exits: "✓ Session complete"
```

### 3. Parallel Execution (Wave 1)

Wave 1 has 5 parallel-safe tasks:

```bash
# Terminal 1
cd /Users/joey/working/skill-split
claude-model glm
claude "/prd-execute --task TASK-001" &  # QueryAPI

# Terminal 2
claude-model glm
claude "/prd-execute --task TASK-004" &  # README

# Terminal 3
claude-model glm
claude "/prd-execute --task TASK-005" &  # EXAMPLES

# Terminal 4
claude-model glm
claude "/prd-execute --task TASK-006" &  # Demo

# Terminal 5
claude-model glm
claude "/prd-execute --task TASK-009" &  # Skill wrapper

# Wait for all to complete
wait

echo "Wave 1 complete!"
```

### 4. Monitor Progress

```bash
# Check current state
cat prd.json | jq '.active_task_id'

# Check completed tasks
cat prd.json | jq '.roadmap[] | select(.status == "done") | .id'

# Check learning log
cat prd.json | jq '.learning_log[]'

# Check wave status
cat prd.json | jq '.execution_waves.wave_1[] as $id | .roadmap[] | select(.id == $id) | {id, status}'
```

### 5. Full Automation Script

```bash
#!/bin/bash
# auto_execute.sh - Run all waves sequentially

PROJECT_DIR="/Users/joey/working/skill-split"
cd "$PROJECT_DIR"

echo "Starting Ralph Wiggum Loop automation..."

# Wave 1 (5 parallel tasks)
echo "=== WAVE 1: Parallel execution ==="
for task in TASK-001 TASK-004 TASK-005 TASK-006 TASK-009; do
  echo "Launching $task..."
  claude-model glm
  claude "/prd-execute --task $task" &
done
wait
echo "Wave 1 complete!"

# Wave 2 (2 parallel tasks)
echo "=== WAVE 2: Parallel execution ==="
for task in TASK-002 TASK-003; do
  echo "Launching $task..."
  claude-model glm
  claude "/prd-execute --task $task" &
done
wait
echo "Wave 2 complete!"

# Wave 3 (integration)
echo "=== WAVE 3: Integration testing ==="
claude-model glm
claude "/prd-execute --task TASK-007"
echo "Wave 3 complete!"

# Wave 4 (documentation)
echo "=== WAVE 4: Documentation update ==="
claude-model glm
claude "/prd-execute --task TASK-008"
echo "Wave 4 complete!"

# Wave 5 (skill installation)
echo "=== WAVE 5: Skill installation ==="
claude-model glm
claude "/prd-execute --task TASK-010"
echo "Wave 5 complete!"

# Wave 6 (final testing)
echo "=== WAVE 6: End-to-end testing ==="
claude-model glm
claude "/prd-execute --task TASK-011"
echo "Wave 6 complete!"

echo "✓ All tasks complete! Check prd.json for final state."
```

Make it executable:
```bash
chmod +x auto_execute.sh
./auto_execute.sh
```

## Benefits You're Getting

### 1. No More Amnesia
```yaml
problem: "AI forgets what it was doing after 50 messages"
solution: "prd.json persists state forever"
result: "Pick up exactly where you left off"
```

### 2. Peak Performance Every Time
```yaml
problem: "AI gets 'dumber' as context fills up"
solution: "Kill session after each task = fresh AI"
result: "Always get the AI's best thinking"
```

### 3. Verification Gates
```yaml
problem: "AI says 'done' but tests fail"
solution: "Tasks can't advance without passing verification"
result: "No false completions"
```

### 4. Learning Persistence
```yaml
problem: "AI repeats same mistakes across sessions"
solution: "learning_log captures lessons"
result: "Each session learns from previous ones"
```

### 5. Audit Trail
```yaml
problem: "What did the AI actually do?"
solution: "Every change logged in learning_log"
result: "Full transparency and history"
```

## Advanced Usage

### Manual Task Override

```bash
# Skip to specific task
claude "/prd-execute --task TASK-005"

# Run specific task without advancing active_task_id
claude "/prd-execute --task TASK-003 --no-advance"
```

### Custom Verification

Add to prd.json:

```json
{
  "id": "TASK-XXX",
  "verification": "npm test && npm run build && ./scripts/verify_deployment.sh"
}
```

### Parallel + Sequential Mix

```bash
# Launch parallel wave
claude "/prd-execute --task TASK-001" &
claude "/prd-execute --task TASK-004" &
wait

# Then sequential
claude "/prd-execute"  # Runs next available task
```

### Learning Log Queries

```bash
# Find specific learning
cat prd.json | jq '.learning_log[] | select(contains("OAuth"))'

# Count total learnings
cat prd.json | jq '.learning_log | length'

# Last 3 learnings
cat prd.json | jq '.learning_log[-3:]'
```

## Troubleshooting

### Verification Fails

```yaml
error: "Verification command failed"
action:
  - Check verification command is correct
  - Run manually to see actual error
  - Fix code
  - Re-run /ralph-loop (stays on same task)
outcome: "Task doesn't advance until verification passes"
```

### Missing Dependencies

```yaml
error: "Task blocked by TASK-XXX"
action:
  - Check dependencies array
  - Execute blocking task first
  - Then retry current task
outcome: "Dependencies enforce proper order"
```

### No More Tasks

```yaml
status: "active_task_id points to completed task"
action:
  - All tasks done!
  - Check metadata.status = "complete"
  - Celebrate 🎉
outcome: "Project finished"
```

## Next Steps

1. **Execute Wave 1** - Run 5 parallel tasks
2. **Monitor** - Watch prd.json updates in real-time
3. **Wave 2** - After Wave 1 completes
4. **Continue** - Through all 6 waves
5. **Done** - skill-split fully complete and usable

## Files Created

```
/Users/joey/working/skill-split/prd.json           # State machine
/Users/joey/.claude/skills/custom/ralph-loop.md    # Documentation skill
/Users/joey/.claude/skills/custom/prd-execute.md   # Executor skill
/Users/joey/working/skill-split/RALPH_USAGE.md     # This file
```

---

**Ready to execute?**

```bash
cd /Users/joey/working/skill-split
/ralph-loop
```

**Or parallel wave 1:**

```bash
./auto_execute.sh
```

---

**Last Updated**: 2026-02-03
