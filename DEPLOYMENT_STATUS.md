# Deployment Status: Quick Reference

**Last Updated:** 2026-02-05

---

## TL;DR

✅ **Single files:** PRODUCTION READY
❌ **Multi-file components:** INCOMPLETE (infrastructure exists, not connected)

---

## What Works Now

```yaml
checkout_single_files:
  - Skills (SKILL.md)
  - Commands (.md)
  - Scripts (.py, .js, .ts, .sh)
  features:
    - Creates nested directories
    - Byte-perfect reconstruction
    - Immediately runtime-ready

example:
  command: ./skill_split.py checkout 1 --target ~/.claude/skills/new/SKILL.md
  result: ✓ Works perfectly
```

---

## What Doesn't Work

```yaml
checkout_multi_file_components:
  - Plugins (plugin.json + .mcp.json + hooks.json)
  - Hooks (hooks.json + *.sh scripts)
  issue: Only deploys primary file, ignores related files

example:
  command: ./skill_split.py checkout 1 --target ~/.claude/plugins/foo/plugin.json
  result:
    - ✓ plugin.json deployed
    - ✗ .mcp.json MISSING
    - ✗ hooks.json MISSING
    - ✗ Scripts MISSING
    - ❌ Plugin non-functional
```

---

## The Gap

```
Infrastructure: 60% Complete
┌─────────────────────────────────────┐
│ ✓ Handlers detect related files    │
│ ✓ Paths resolved correctly         │
│ ✓ get_related_files() implemented  │
└─────────────────────────────────────┘
            ↓
            ↓ DISCONNECTED
            ↓
┌─────────────────────────────────────┐
│ ✗ CheckoutManager ignores them     │
│ ✗ Database doesn't track them      │
│ ✗ CLI has no --with-related flag   │
└─────────────────────────────────────┘
```

---

## Fix Required (1 Method)

**File:** `core/checkout_manager.py:15-54`

```python
def checkout_file(self, file_id: str, user: str, target_path: Optional[str] = None) -> str:
    # ... existing code ...

    # ADD THIS (3 lines):
    handler = HandlerFactory.create_handler(metadata.path, content)
    if hasattr(handler, 'get_related_files'):
        for related_path in handler.get_related_files():
            # Deploy each related file
            ...

    return str(target)
```

**Impact:** Unlocks multi-file component deployment

---

## Production Guidance

### Safe for Production:
- Progressive disclosure of skills
- Section-level browsing of commands
- Code snippet extraction from scripts

### NOT Safe for Production:
- Plugin deployment
- Hook deployment
- Automated multi-file restoration

### Workaround:
```bash
# 1. Deploy main file
./skill_split.py checkout 1 --target ~/.claude/skills/plugin/plugin.json

# 2. Manually copy related files
cp -r /original/plugin/{.mcp.json,hooks.json,*.sh} ~/.claude/skills/plugin/
```

---

## See Also

- **[FOLDER_RECREATION_INVESTIGATION.md](./FOLDER_RECREATION_INVESTIGATION.md)** - Full detailed analysis
- **[COMPONENT_HANDLERS.md](./COMPONENT_HANDLERS.md)** - Handler architecture
- **[CLAUDE.md](./CLAUDE.md)** - Project overview

---

**Status:** Single-file deployment READY | Multi-file deployment BLOCKED
