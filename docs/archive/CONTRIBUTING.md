# Contributing Guide

**Last Updated:** 2026-02-10

Thank you for your interest in contributing to skill-split!

---

## Quick Start

### 1. Fork and Clone

```bash
git clone https://github.com/YOUR_USERNAME/skill-split.git
cd skill-split
```

### 2. Set Up Development Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### 3. Run Tests

```bash
# Verify everything works
python -m pytest test/ -v
```

## Development Workflow

### Branch Strategy

- **main:** Production-ready code
- **develop:** Development branch (if used)
- **feature/***: New features
- **fix/***: Bug fixes
- **docs/***: Documentation changes
- **test/***: Test additions or updates

### Creating a Feature Branch

```bash
# Sync with upstream
git fetch upstream
git checkout main
git merge upstream/main

# Create feature branch
git checkout -b feature/your-feature-name
```

### Making Changes

1. **Write Tests First** (TDD approach)
2. **Implement the Feature**
3. **Run Tests**
4. **Update Documentation**

### Commit Messages

Follow conventional commits format:

```
type(scope): subject

body (optional)

footer (optional)
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Test changes
- `refactor`: Code refactoring
- `style`: Code style changes
- `chore`: Maintenance tasks

**Examples:**

```bash
git commit -m "feat(parser): add support for YAML frontmatter"

git commit -m "fix(database): resolve CASCADE delete issue"

git commit -m "docs(readme): update installation instructions"
```

## Testing

### Running Tests

```bash
# Run all tests
python -m pytest test/ -v

# Run specific test file
python -m pytest test/test_parser.py -v

# Run with coverage
python -m pytest test/ --cov=core --cov=handlers --cov-report=html

# Run specific test
python -m pytest test/test_parser.py::test_yaml_frontmatter -v
```

### Writing Tests

Follow these patterns:

```python
# test/test_parser.py

def test_yaml_frontmatter():
    """Test YAML frontmatter extraction."""
    content = """---
name: test-skill
version: 1.0.0
---

# Content here
"""
    doc = parse_document(content, "test.md")
    assert doc.frontmatter == "name: test-skill\nversion: 1.0.0\n"
```

### Test Categories

- **Parser Tests:** YAML, Markdown, XML parsing
- **Database Tests:** Storage, retrieval, FTS5 search
- **Query Tests:** Progressive disclosure API
- **CLI Tests:** Command-line interface
- **Handler Tests:** Component-specific parsing
- **Integration Tests:** End-to-end workflows

### Test Fixtures

Place test files in `test/fixtures/`:

```
test/fixtures/
  simple_skill.md
  yaml_frontmatter.md
  xml_tags.md
  plugin.json
  hooks.json
```

## Code Style

### Python Style Guide

Follow PEP 8 with these additions:

```python
# Use type hints for function signatures
def parse_document(content: str, path: str) -> ParsedDocument:
    """Parse a document into structured sections.

    Args:
        content: The file content to parse
        path: The file path for error reporting

    Returns:
        A ParsedDocument with sections and metadata
    """
    pass

# Use dataclasses for data models
@dataclass
class Section:
    level: int
    title: str
    content: str
    line_start: int
    line_end: int

# Use descriptive names
def get_section_by_id(section_id: int) -> Optional[Section]:
    pass

# Keep functions focused
def parse_frontmatter(content: str) -> tuple[str, str]:
    """Extract YAML frontmatter from content.

    Returns:
        Tuple of (frontmatter, remaining_content)
    """
    pass
```

### Documentation

- Docstrings for all public functions
- Inline comments for complex logic
- Type hints for function signatures
- Examples in docstrings

### File Organization

```
skill-split/
  core/           # Core functionality
    parser.py
    database.py
    query.py
  handlers/       # Component handlers
    base.py
    plugin_handler.py
    script_handler.py
  test/           # Tests
    test_parser.py
    test_database.py
    fixtures/      # Test data
  docs/           # Documentation
```

## Submitting Changes

### Before Submitting

1. **Run Tests:** Ensure all tests pass
2. **Check Style:** Run linter if configured
3. **Update Docs:** Update README and relevant docs
4. **Add Tests:** Include tests for new features

### Pull Request Process

```bash
# Push your changes
git push origin feature/your-feature-name

# Create pull request on GitHub
# Fill in the PR template
```

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tests added/updated
- [ ] All tests passing

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No new warnings generated

## Related Issues
Fixes #123
Related to #456
```

### Review Process

1. **Automated Checks:** CI runs tests
2. **Code Review:** Maintainer reviews code
3. **Feedback:** Address review comments
4. **Approval:** Merge after approval

## Reporting Issues

### Bug Reports

Include:

1. **Description:** Clear description of the bug
2. **Steps to Reproduce:**
   ```bash
   ./skill_split.py store test.md
   # Error: ...
   ```
3. **Expected Behavior:** What should happen
4. **Actual Behavior:** What actually happens
5. **Environment:**
   - OS: macOS 14.0
   - Python: 3.11.0
   - skill-split: 1.0.0

### Feature Requests

Include:

1. **Use Case:** Describe the problem you're solving
2. **Proposed Solution:** How you envision it working
3. **Alternatives:** Other approaches considered
4. **Examples:** Code or usage examples

## Development Areas

### High Priority

- [ ] Performance optimization for large files
- [ ] Additional script language handlers
- [ ] Enhanced error messages
- [ ] More test coverage

### Medium Priority

- [ ] Web UI for browsing sections
- [ ] Export to other formats (PDF, HTML)
- [ ] Advanced search filters
- [ ] Batch operations

### Low Priority

- [ ] Plugin system for custom parsers
- [ ] Cloud sync (beyond Supabase)
- [ ] GUI application
- [ ] Mobile app

## Resources

### Documentation

- [README.md](README.md) - Main documentation
- [API.md](API.md) - Programmatic API
- [EXAMPLES.md](EXAMPLES.md) - Usage examples
- [ARCHITECTURE.md](ARCHITECTURE.md) - System design

### External Resources

- [SQLite Documentation](https://www.sqlite.org/docs.html)
- [FTS5 Full-Text Search](https://www.sqlite.org/fts5.html)
- [Click Documentation](https://click.palletsprojects.com/)

## Recognition

Contributors will be recognized in:

- CONTRIBUTORS.md file
- Release notes for significant contributions
- Project documentation

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for contributing to skill-split!**
