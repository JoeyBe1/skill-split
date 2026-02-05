#!/bin/bash
# Setup SkillBank schema

echo "📋 Copying schema.sql to clipboard..."
cat schema.sql | pbcopy

echo "✅ Schema copied to clipboard!"
echo ""
echo "Next steps:"
echo "1. Open: https://supabase.com/dashboard/project/dnqbnwalycyoynbcpbpz/sql/new"
echo "2. Paste (Cmd+V)"
echo "3. Click 'Run'"
echo ""
echo "Then test: skill-split list-library"
