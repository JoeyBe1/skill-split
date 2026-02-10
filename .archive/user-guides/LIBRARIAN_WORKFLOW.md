# Librarian Workflow

Concise reference for checkout/checkin operations with Supabase library.

## Checkout Flow

**Supabase → Local File System**

```python
# 1. Get file from Supabase by UUID
metadata, sections = store.get_file(file_id)

# 2. Recompose content
content = ""
if metadata.frontmatter:
    content += "---\n" + metadata.frontmatter + "---\n\n"
for section in sections:
    content += section.get_all_content()

# 3. Write to target path
Path(target_path).parent.mkdir(parents=True, exist_ok=True)
Path(target_path).write_text(content)

# 4. Record checkout in database
store.checkout_file(file_id, user, target_path, notes="")
```

**Database Record**
```python
# checkouts table
{
    "id": "<uuid>",
    "file_id": file_id,
    "user_name": user,
    "target_path": "/Users/joey/.claude/skills/ripgrep.md",
    "status": "active",
    "checked_out_at": "2026-02-04T12:00:00Z",
    "notes": ""
}
```

## Checkin Flow

**Delete File + Update Database**

```python
# 1. Lookup checkout by target path
checkout_info = store.get_checkout_info(target_path)
# Returns: {"id": "<uuid>", "file_id": "...", "user_name": "...", ...}

# 2. Delete file from filesystem
Path(target_path).unlink()

# 3. Update checkout status to 'returned'
store.checkin_file(checkout_info["id"])
# Sets: status='returned', checked_in_at=<timestamp>
```

## Fast Lookup Patterns

### By Target Path
```python
# Get active checkout at path
checkout = store.get_checkout_info("/Users/joey/.claude/skills/ripgrep.md")
# Query: WHERE target_path = ? AND status = 'active'
```

### By User
```python
# Get all active checkouts for user
checkouts = store.get_active_checkouts(user="joey")
# Query: WHERE user_name = ? AND status = 'active'
```

### By File Name
```python
# Search library by name
files = store.search_files("ripgrep")
# Query: WHERE name ILIKE '%ripgrep%'
```

## Example: ~/.claude/skills/ Workflow

```bash
# Checkout skill to local filesystem
./skill_split.py checkout \
    --file-id "123e4567-e89b-12d3-a456-426614174000" \
    --user joey \
    --target ~/.claude/skills/ripgrep.md

# File deployed to: /Users/joey/.claude/skills/ripgrep.md
# Database tracks: who=joey, where=~/.claude/skills/ripgrep.md, status=active

# User edits file locally...

# Checkin when done
./skill_split.py checkin ~/.claude/skills/ripgrep.md

# File deleted from: /Users/joey/.claude/skills/ripgrep.md
# Database updated: status=returned, checked_in_at=<timestamp>
```

## Database Tables

**files**
- `id` (uuid, primary key)
- `name` (text)
- `storage_path` (text) - original source path
- `hash` (text) - SHA256 of content

**sections**
- `id` (uuid, primary key)
- `file_id` (uuid, foreign key → files)
- `parent_id` (uuid, nullable) - for hierarchy
- `level`, `title`, `content`, `order_index`

**checkouts**
- `id` (uuid, primary key)
- `file_id` (uuid, foreign key → files)
- `user_name` (text)
- `target_path` (text) - where file is deployed
- `status` (text) - 'active' or 'returned'
- `checked_out_at`, `checked_in_at` (timestamps)

## Key Properties

- **Lookup by path**: Fast query on `target_path` for checkin
- **Track ownership**: `user_name` + `status='active'` for "who has what"
- **Audit trail**: `checked_out_at` + `checked_in_at` timestamps
- **Physical delete**: Files removed from filesystem on checkin (not archived)
- **Section preservation**: Original sections remain in Supabase for re-checkout
