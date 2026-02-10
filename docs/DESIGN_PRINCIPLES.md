# skill-split Design Principles

**Core philosophy guiding development and architecture**

---

## 1. Big-O Philosophy

### The 3 AM Rule

> "Would I understand this at 3 AM?"

Code should be self-evident. Future-you (tired, debugging at 3 AM) should immediately understand:
- What the code does
- Why it exists
- How to modify it safely

### Single Responsibility Principle

Each component has ONE job:
- `Parser` - Extracts structure from files
- `Database` - Stores and retrieves sections
- `QueryAPI` - Searches and navigates sections
- `Recomposer` - Reconstructs files from sections

**Bad:** A class that parses AND stores AND searches
**Good:** Separate classes for each concern

### The Junior Developer Principle

> "A junior developer should be able to contribute safely on day one"

- Clear code organization
- Comprehensive tests
- Explicit error handling
- No "clever" code that saves 2 lines but costs 2 hours

---

## 2. Progressive Disclosure

### Load Only What You Need

```python
# Bad: Load entire 100KB file
content = read_file("large_doc.md")  # 25,000 tokens

# Good: Load specific section
section = query.get_section(42)  # 50 tokens
```

### Token Efficiency Hierarchy

1. **Search first** - Find relevant sections
2. **Load specific** - Get only the section you need
3. **Navigate progressively** - Move to siblings/children as needed

### 99% Savings

Typical workflow saves 99% of tokens:
- Full file: 2,500 tokens
- One section: 25 tokens
- **Savings: 99%**

---

## 3. Byte-Perfect Integrity

### SHA256 Verification

Every section has a hash:
```python
section.hash = hashlib.sha256(content.encode()).hexdigest()
```

### Round-Trip Guarantee

```
Original File → Parse → Store → Retrieve → Recompose → Original File
                                                      ↓
                                                SHA256 Match
```

### Never Trust Assumptions

```python
# Bad: Assume reconstruction works
recomposed = join_sections(sections)

# Good: Verify reconstruction
recomposed = join_sections(sections)
assert verify_sha256(original, recomposed), "Round-trip failed!"
```

---

## 4. Fail Explicitly

### Error Messages > Exceptions

```python
# Bad:
raise ValueError("Error")

# Good:
raise ValueError(
    f"Invalid heading level: {level}. "
    f"Expected 1-6, got {level}. "
    f"File: {file_path}, Line: {line_number}"
)
```

### Validation at Boundaries

- **Input validation** - When data enters the system
- **Output validation** - Before data leaves the system
- **Storage validation** - Before writing to database
- **Retrieval validation** - After reading from database

---

## 5. Test-Driven Confidence

### 100% Coverage Goal

Every line of production code has a corresponding test.

### Test Categories

1. **Unit tests** - Test individual functions/classes
2. **Integration tests** - Test component interactions
3. **Round-trip tests** - Verify parse/recompose integrity
4. **Benchmark tests** - Ensure performance doesn't regress

### Test Quality

```python
# Bad: Tests implementation details
def test_parser_uses_regex():
    assert parser._pattern == ".*"

# Good: Tests behavior
def test_parser_extracts_headings():
    doc = parser.parse("# Heading")
    assert doc.sections[0].heading == "Heading"
```

---

## 6. SQLite First, Cloud Later

### Local-First Development

- SQLite works offline
- No API keys required
- Fast and reliable
- Easy to test

### Cloud as Enhancement

Supabase adds:
- Remote access
- Collaboration
- Backup/restore
- Vector search at scale

**But:** The core works perfectly without it.

---

## 7. Factory Pattern for Extensibility

### Handler Factory

```python
class HandlerFactory:
    @staticmethod
    def create(file_type: FileType) -> BaseHandler:
        handlers = {
            FileType.PYTHON: PythonHandler,
            FileType.JAVASCRIPT: JavaScriptHandler,
            # ...
        }
        return handlers[file_type]()
```

### Adding New Handlers

1. Create handler class inheriting `BaseHandler`
2. Implement `parse()` and `validate()`
3. Register in factory
4. No changes to core logic required

---

## 8. Document for Users, Not Developers

### User-First Documentation

```markdown
<!-- Bad: Developer-focused -->
This function uses the FTS5 extension with BM25 ranking...

<!-- Good: User-focused -->
Search your documentation by keyword. Finds exact matches
even if you don't use the exact words...
```

### Examples > Explanations

```python
# Bad: Explains parameters
# limit: Maximum number of results to return

# Good: Shows usage
results = search("query", limit=10)  # Get top 10 results
```

---

## 9. Performance is a Feature

### Benchmarks Define Success

- Parse 1KB: < 0.1ms
- Parse 50KB: < 1ms
- Search 10K sections: < 10ms
- Round-trip 100KB: < 5ms

### If It's Slow, It's Broken

Performance issues are bugs, not features.

### Optimization Order

1. **Measure first** - Use benchmarks
2. **Profile** - Find the bottleneck
3. **Fix the hotspot** - Optimize the slow part
4. **Verify** - Ensure it's actually faster

---

## 10. Security by Default

### No Hardcoded Secrets

```python
# Bad
API_KEY = "sk-..."

# Good
API_KEY = os.getenv("OPENAI_API_KEY")
```

### SQL Injection Prevention

```python
# Bad: String concatenation
query = f"SELECT * FROM sections WHERE id = {user_input}"

# Good: Parameterized queries
query = "SELECT * FROM sections WHERE id = ?", (user_input,)
```

### Input Validation

Validate everything:
- File paths (directory traversal)
- Section IDs (SQL injection)
- User queries (XSS, injection)

---

## Applying These Principles

### Code Review Checklist

- [ ] Is the purpose obvious? (Big-O)
- [ ] Does it have a single responsibility? (SRP)
- [ ] Is it token-efficient? (Progressive Disclosure)
- [ ] Does it verify integrity? (SHA256)
- [ ] Are errors explicit? (Fail Explicitly)
- [ ] Is it tested? (TDD)
- [ ] Does it work locally? (SQLite First)
- [ ] Is it extensible? (Factory Pattern)
- [ ] Is it user-friendly? (Document for Users)
- [ ] Is it performant? (Performance is a Feature)
- [ ] Is it secure? (Security by Default)

### When Principles Conflict

1. **Security > Performance** - Never sacrifice security for speed
2. **Integrity > Convenience** - Always verify round-trips
3. **Clarity > Cleverness** - Clear code beats clever code

---

**These principles guide every decision in skill-split.**

*skill-split - Progressive disclosure for AI workflows*
