#!/usr/bin/env bash
# skill-split Quality Gate Script
# Runs all quality checks before committing

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PASSED=0
FAILED=0

check() {
    local name=$1
    local command=$2

    echo -e "${BLUE}[CHECK]${NC} $name..."
    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}[PASS]${NC} $name"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}[FAIL]${NC} $name"
        ((FAILED++))
        return 1
    fi
}

warn() {
    local name=$1
    local command=$2

    echo -e "${BLUE}[CHECK]${NC} $name..."
    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}[PASS]${NC} $name"
    else
        echo -e "${YELLOW}[WARN]${NC} $name (non-blocking)"
    fi
}

echo "╔════════════════════════════════════════════════╗"
echo "║     skill-split Quality Gate v1.0.0           ║"
echo "╚════════════════════════════════════════════════╝"
echo ""

# Required checks
check "Python 3.10+" "python3 --version | grep -E '3\.(10|11|12|13)'"
check "Dependencies installed" "python -c 'import yaml, supabase, openai'"
check "Core tests pass" "python -m pytest test/ -q --tb=line"

# Code quality checks
check "Ruff format" "ruff format --check ."
check "Ruff lint" "ruff check ."
check "MyPy type check" "mypy core/ handlers/ --ignore-missing-imports"

# Security checks
warn "Bandit security" "bandit -r core/ handlers/ -q"

# Documentation checks
check "README exists" "test -f README.md"
check "CHANGELOG exists" "test -f CHANGELOG.md"
warn "All docs referenced" "grep -r 'docs/.*.md' README.md | wc -l"

# Build checks
check "pyproject.toml valid" "python -c 'import tomllib; tomllib.load(open(\"pyproject.toml\", \"rb\"))'"
warn "Can build package" "python -m build --version 2>/dev/null"

# Version consistency
VERSION=$(cat VERSION 2>/dev/null || echo "")
if [ -n "$VERSION" ]; then
    warn "VERSION in pyproject.toml" "grep -q \"$VERSION\" pyproject.toml"
fi

echo ""
echo "╔════════════════════════════════════════════════╗"
echo "║              Quality Gate Results              ║"
echo "╚════════════════════════════════════════════════╝"
echo ""
echo -e "  ${GREEN}Passed:${NC} $PASSED"
echo -e "  ${RED}Failed:${NC} $FAILED"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ Quality gate PASSED${NC}"
    echo "Safe to commit!"
    exit 0
else
    echo -e "${RED}❌ Quality gate FAILED${NC}"
    echo "Fix failures before committing."
    exit 1
fi
