#!/usr/bin/env python3
"""Apply Supabase schema migration."""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get Supabase credentials
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

if not url or not key:
    print("Error: SUPABASE_URL and SUPABASE_KEY must be set", file=sys.stderr)
    sys.exit(1)

# Read migration SQL
with open("migrations/add_config_script_types.sql", "r") as f:
    sql = f.read()

print("=" * 70)
print("SUPABASE SCHEMA MIGRATION")
print("=" * 70)
print("\nMigration: Add config and script file types\n")
print("SQL to execute:")
print("-" * 70)
print(sql)
print("-" * 70)
print("\nTO APPLY THIS MIGRATION:")
print("\n1. Copy the SQL above")
print("2. Go to: https://supabase.com/dashboard/project/<your-project>/editor")
print("3. Paste into SQL Editor")
print("4. Click 'Run'")
print("\nOr use the Supabase CLI:")
print(f"   supabase db execute --file migrations/add_config_script_types.sql")
print("\nAfter applying, run: ./skill_split.py ingest ~/.claude/skills/")
print("=" * 70)
