# skill-split Makefile
# Convenient commands for development and testing

.PHONY: help install test lint format clean benchmark demo release

# Default target
help:
	@echo "skill-split - Available Commands:"
	@echo ""
	@echo "Development:"
	@echo "  make install    Install dependencies"
	@echo "  make test       Run tests"
	@echo "  make lint       Run linters"
	@echo "  make format     Format code"
	@echo "  make clean      Remove generated files"
	@echo ""
	@echo "Quality:"
	@echo "  make benchmark   Run benchmarks"
	@echo "  make coverage   Generate coverage report"
	@echo "  make check      Run all quality checks"
	@echo ""
	@echo "Documentation:"
	@echo "  make docs        Generate documentation"
	@echo "  make readmeg     Generate README_COMPACT.md"
	@echo ""
	@echo "Demos:"
	@echo "  make demo        Run all demos"
	@echo "  make demo-token  Run token savings demo"
	@echo "  make demo-search  Run search comparison demo"
	@echo ""
	@echo "Utilities:"
	@echo "  make health      Run health check"
	@echo "  make backup      Backup database"
	@echo "  make migrate     Run database migrations"
	@echo ""

# Installation
install:
	pip install -e ".[dev]"
	pre-commit install

# Testing
test:
	python -m pytest test/ -v

test-cov:
	python -m pytest test/ --cov=. --cov-report=html --cov-report=term

test-unit:
	python -m pytest test/ -v -k "not integration"

test-integration:
	python -m pytest test/integration/ -v

# Code quality
lint:
	ruff check .
	mypy core/ handlers/ --ignore-missing-imports

format:
	ruff format .
	ruff check --fix .

lint-all: lint format

# Quality checks
check: test lint
	@echo "✅ All checks passed"

coverage: test-cov
	@echo "Coverage report: htmlcov/index.html"

# Benchmarking
benchmark:
	python -m pytest benchmark/bench.py --benchmark-only

baseline:
	python -m pytest benchmark/bench.py --benchmark-only --benchmark-compare-fail=mean:10%

# Documentation
docs:
	@echo "Documentation already complete in docs/"

readmeg:
	@echo "Generating compact README..."
	@cat README_COMPACT.md

# Demos
demo:
	cd demo && ./run_all_demos.sh

demo-token:
	cd demo && ./token_savings_demo.sh

demo-search:
	cd demo && ./search_relevance_demo.sh

demo-component:
	cd demo && ./component_deployment_demo.sh

demo-recovery:
	cd demo && ./disaster_recovery_demo.sh

demo-batch:
	cd demo && ./batch_processing_demo.sh

# Utilities
health:
	python scripts/health_check.py

health-json:
	python scripts/health_check.py --json

backup:
	python scripts/backup_database.sh ./backups

backup-restore:
	@echo "Restore from: $(BACKUP_PATH)"
	@echo "TODO: Implement restore from backup"

migrate:
	python scripts/migrate_database.py --list

migrate-apply:
	python scripts/migrate_database.py --apply

# Database
db-init:
	./skill_split.py init

db-import:
	./skill_split.py ingest docs/**/*.md

db-status:
	./skill_split.py status

# Clean
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.db" -delete
	find . -type f -name "*.db-wal" -delete
	find . -type f -name "*.db-shm" -delete
	rm -rf htmlcov/ .coverage .pytest_cache

# Release
release: check docs
	@echo "Creating release package..."
	python -m build
	twine check dist/*
	@echo "✅ Ready for PyPI release"
	@echo "Run: twine upload dist/*"

# Development helpers
dev-setup:
	pip install -e ".[dev]"
	pre-commit install
	@echo "✅ Development environment ready"

dev-test: install test lint
	@echo "✅ All development checks passed"

# CI/CD simulation
ci: install test lint benchmark
	@echo "✅ CI/CD simulation passed"

# Install extras
install-hooks:
	pre-commit install
	@echo "✅ Pre-commit hooks installed"

uninstall-hooks:
	pre-commit uninstall
	@echo "⚠️  Pre-commit hooks uninstalled"
