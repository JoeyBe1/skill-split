#!/usr/bin/env bash
# skill-split Release Creation Script
# Automates the release process for new versions

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Functions
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Get version from VERSION file or argument
VERSION=${1:-$(cat VERSION 2>/dev/null || echo "1.0.0")}

log_info "Creating release for v${VERSION}"

# Step 1: Run tests
log_info "Step 1: Running tests..."
if python -m pytest test/ -q --tb=line; then
    log_success "All tests passed"
else
    log_error "Tests failed. Aborting release."
    exit 1
fi

# Step 2: Run linters
log_info "Step 2: Running linters..."
if make lint-all > /dev/null 2>&1; then
    log_success "All linters passed"
else
    log_warn "Linters found issues. Review with 'make lint-all'"
fi

# Step 3: Build distribution
log_info "Step 3: Building distribution packages..."
rm -rf dist/
if python -m build; then
    log_success "Distribution built"
else
    log_error "Build failed. Aborting release."
    exit 1
fi

# Step 4: Check distribution
log_info "Step 4: Checking distribution..."
if twine check dist/*; then
    log_success "Distribution check passed"
else
    log_error "Distribution check failed. Aborting release."
    exit 1
fi

# Step 5: Create git tag
log_info "Step 5: Creating git tag..."
if git rev-parse "v${VERSION}" >/dev/null 2>&1; then
    log_warn "Tag v${VERSION} already exists. Skipping."
else
    if git tag -a "v${VERSION}" -m "Release v${VERSION}"; then
        log_success "Tag v${VERSION} created"
    else
        log_error "Failed to create tag. Aborting release."
        exit 1
    fi
fi

# Step 6: Generate release notes
log_info "Step 6: Generating release notes..."
cat > "RELEASE_NOTES_${VERSION}.md" <<EOF
# skill-split v${VERSION} Release Notes

**Released:** $(date +%Y-%m-%d)

## Download

- **PyPI:** \`pip install skill-split==${VERSION}\`
- **Source:** https://github.com/user/skill-split/archive/refs/tags/v${VERSION}.tar.gz

## What's New

See [CHANGELOG.md](CHANGELOG.md) for complete changes.

## Installation

\`\`\`bash
pip install skill-split==${VERSION}
\`\`\`

## Quick Start

\`\`\`bash
skill-split --help
\`\`\`

## Verification

\`\`\`bash
# Verify installation
python -c "import skill_split; print(skill_split.__version__)"

# Run tests
pytest test/
\`\`\`

## Checksums

\`\`\`
$(shasum -a 256 dist/*)
\`\`\`
EOF
log_success "Release notes generated"

# Summary
log_info "Release v${VERSION} created successfully!"
echo ""
echo "Next steps:"
echo "  1. Review release notes: RELEASE_NOTES_${VERSION}.md"
echo "  2. Push tag: git push origin v${VERSION}"
echo "  3. Publish to PyPI: twine upload dist/*"
echo "  4. Create GitHub release with release notes"
echo ""
