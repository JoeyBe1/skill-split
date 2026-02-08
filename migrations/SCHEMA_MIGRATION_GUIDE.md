# Schema Migration Guide

## What This Fixes

This migration addresses schema constraints that prevent ingestion of certain file types:
- Enables storage of `config.json` and script files (`.py`, `.js`, `.ts`, `.sh`)
- Removes "files_type_check" constraint errors when ingesting these file types
- Allows component handlers (plugins, hooks, configs) to store in Supabase

**Error Before Migration**:
```
ERROR: new row for relation "files" violates check constraint "files_type_check"
DETAIL: Failing row contains (uuid, 'config', ..., 'config').
```

## Steps to Apply Migration

### Via Supabase Dashboard (Recommended)

1. **Login to Supabase**
   - Navigate to: https://supabase.com/dashboard/project/dnqbnwalycyoynbcpbpz/editor
   - Replace project ID if different

2. **Create New Query**
   - Click: `SQL Editor` (left sidebar)
   - Click: `New Query` (top-right)

3. **Copy SQL from Migration File**
   - Use SQL from: `migrations/add_config_script_types.sql`
   - Paste entire SQL into the editor window

4. **Execute Query**
   - Click: `Run` button (or Ctrl+Enter)
   - Wait for completion message

5. **Verify No Errors**
   - Check the "Query Results" panel
   - Should show: `SUCCESS` (no error messages)

### Via CLI (PostgreSQL client)

If you have `psql` installed:

```bash
# Set your Supabase connection details
export PGPASSWORD="your-postgres-password"

psql \
  -h dnqbnwalycyoynbcpbpz.supabase.co \
  -p 5432 \
  -U postgres \
  -d postgres \
  -f migrations/add_config_script_types.sql
```

## Verification Steps

### Quick Test (Recommended)

After migration, test file ingestion:

```bash
# Install dependencies (if needed)
pip install -r requirements.txt

# Set environment variables
export SUPABASE_URL="https://dnqbnwalycyoynbcpbpz.supabase.co"
export SUPABASE_KEY="your-anon-key"

# Try ingesting a config file
./skill_split.py ingest ~/.claude/skills/agent-browser/config.json

# Expected output:
# Storing: agent-browser/config.json
# Type: config, Format: json
# File stored (ID: <uuid>, 19 sections)
```

### Detailed Verification

Check the database directly:

```bash
# Via Supabase dashboard SQL editor:
SELECT type, COUNT(*) as count FROM files GROUP BY type;

# Should return rows including 'config', 'plugin', 'hook', 'script'
```

## What the Migration Does

The migration file `migrations/add_config_script_types.sql` performs these steps:

1. **Drops existing constraint**:
   ```sql
   ALTER TABLE files DROP CONSTRAINT files_type_check;
   ```

2. **Adds new constraint with allowed types**:
   ```sql
   ALTER TABLE files
   ADD CONSTRAINT files_type_check
   CHECK (type IN ('skill', 'command', 'reference', 'config', 'plugin', 'hook', 'script'));
   ```

This extends the allowed file types from the original 3 to 7 types.

## Rollback Instructions (If Needed)

If you need to revert the migration:

1. **Navigate to SQL Editor** in Supabase dashboard

2. **Run rollback SQL**:
   ```sql
   -- Revert to original constraint
   ALTER TABLE files DROP CONSTRAINT files_type_check;

   ALTER TABLE files
   ADD CONSTRAINT files_type_check
   CHECK (type IN ('skill', 'command', 'reference'));
   ```

3. **Note**: This will fail if you have config/plugin/hook/script files stored.
   - Delete those files first (or update their type to a valid value)

## Troubleshooting

### "Constraint already exists" Error

If you see: `ERROR: constraint "files_type_check" already exists`

- Migration may have already been applied
- Verify by checking file types:
  ```sql
  SELECT DISTINCT type FROM files;
  ```

### "Table does not exist" Error

- Ensure Supabase project is set up correctly
- Check project ID matches your environment
- Verify database connection is working

### Connection Timeout

- Check your internet connection
- Verify Supabase service is operational
- Try accessing the dashboard directly: https://supabase.com/dashboard

## Summary

| Step | Time | Action |
|------|------|--------|
| 1 | 1 min | Open Supabase dashboard |
| 2 | 1 min | Create new SQL query |
| 3 | 1 min | Copy/paste migration SQL |
| 4 | 1 min | Execute query |
| 5 | 2 min | Verify with test file ingest |
| **Total** | **~5 min** | **Schema migration complete** |

Once complete, you can immediately ingest config, plugin, hook, and script files to Supabase.

---

**Last Updated**: 2026-02-05
**Status**: Ready for User Action
