#!/bin/bash
# Validate MVP setup works correctly

set -e
DB_PATH=~/.claude/databases/skill-split.db

echo "=== skill-split MVP Validation ==="
echo ""

# Test 1: Command routing
echo "✓ Testing command wrapper..."
if [ ! -x /Users/joey/.claude/commands/skill-split ]; then
    echo "  ❌ ERROR: skill-split command not executable"
    exit 1
fi

# Test 2: Parse works
echo "✓ Testing parse command..."
/Users/joey/working/skill-split/skill_split.py parse README.md > /dev/null

# Test 3: Database location
echo "✓ Testing database path..."
/Users/joey/working/skill-split/skill_split.py store README.md
if [ -f "$DB_PATH" ]; then
    echo "  Database created at: $DB_PATH"
else
    echo "  ❌ ERROR: Database not at expected location"
    exit 1
fi

# Test 4: Search works
echo "✓ Testing search command..."
/Users/joey/working/skill-split/skill_split.py search "progressive" > /dev/null

echo ""
echo "✅ MVP validation passed!"
echo ""
echo "Next: Run ingestion demo:"
echo "  /skill-split store ~/.claude/skills/creating-output-styles/SKILL.md"
echo "  /skill-split search 'format'"
