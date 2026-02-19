# skill-split - Quick Reference Card

**One-page reference for common tasks**

---

## Installation

```bash
pip install skill-split
```

## Basic Commands

### Parse & Store
```bash
./skill_split.py parse README.md
./skill_split.py store README.md
```

### Search
```bash
# Keyword (fast, free)
./skill_split.py search "authentication"

# Semantic (concepts)
./skill-split.py search-semantic "login" --vector-weight 1.0

# Hybrid (balanced)
./skill-split.py search-semantic "auth" --vector-weight 0.7
```

### Navigate
```bash
# List sections
./skill_split.py list README.md

# Get section
./skill_split.py get-section 42

# Next section
./skill_split.py next 42 README.md
```

## Python API

```python
from skill_split import SkillSplit
from core.query import QueryAPI

ss = SkillSplit()
query = QueryAPI(ss.db)

# Search
results = query.search_sections("query")

# Get section
section = query.get_section(42)
```

## Token Savings

| Method | Tokens | Savings |
|--------|--------|---------|
| Full file | 5,000 | 0% |
| Progressive | 50 | **99%** |

## Cost (Annual, 1K queries/day)

| Method | Cost | Savings |
|--------|------|---------|
| Full load | $27,375 | - |
| skill-split | $547 | **$26,828** |

## Performance

| Operation | Time |
|-----------|------|
| Parse 1KB | 0.013ms |
| Parse 50KB | 0.67ms |
| Search 10K | 5.8ms |

## Documentation

- Full docs: `docs/`
- API: `API.md`
- Tutorial: `docs/tutorials/`
- Troubleshooting: `docs/TROUBLESHOOTING.md`

## Support

- Issues: https://github.com/user/skill-split/issues
- Security: security@skill-split.dev

---

**Progressive disclosure for AI workflows**

*skill-split v1.0.0*
