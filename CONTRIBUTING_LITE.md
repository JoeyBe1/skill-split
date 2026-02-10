# Quick Contribution Guide

**For detailed guide, see [CONTRIBUTING.md](CONTRIBUTING.md)**

## Quick Start

1. **Fork and clone**
   ```bash
   git clone https://github.com/YOUR_USERNAME/skill-split.git
   cd skill-split
   ```

2. **Set up development environment**
   ```bash
   make install
   pre-commit install
   ```

3. **Run tests**
   ```bash
   make test
   make lint
   ```

## Making Changes

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write tests for new features
   - Ensure tests pass: `make test`
   - Check code quality: `make lint`

3. **Commit with conventional commits**
   ```bash
   git commit -m "feat: add new search feature"
   ```

4. **Push and create PR**
   ```bash
   git push origin feature/your-feature-name
   ```

## Commit Convention

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `test:` Test changes
- `refactor:` Code refactoring
- `perf:` Performance improvements

## Code Style

- Line length: 100 characters
- Use type hints
- Write docstrings for functions/classes
- Follow PEP 8

## Testing

- Write tests for all new features
- Aim for 95%+ coverage
- Use `pytest` fixtures for setup

## Questions?

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

---

*skill-split - Progressive disclosure for AI workflows*
