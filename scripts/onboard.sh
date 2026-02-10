#!/usr/bin/env bash
# skill-split Developer Onboarding Script
# Sets up a complete development environment for new contributors

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Print header
print_header() {
    echo -e "${CYAN}"
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║                                                        ║"
    echo "║         skill-split Developer Onboarding                ║"
    echo "║                                                        ║"
    echo "║              Setting up your dev environment           ║"
    echo "║                                                        ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Check Python version
check_python() {
    echo -e "${BLUE}[1/8]${NC} Checking Python version..."
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | awk '{print $2}')
        PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
        PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

        if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 10 ]; then
            echo -e "${GREEN}✓${NC} Python $PYTHON_VERSION found"
        else
            echo -e "${YELLOW}⚠${NC} Python 3.10+ required, found $PYTHON_VERSION"
            echo "  Please install Python 3.10 or higher"
            exit 1
        fi
    else
        echo -e "${RED}✗${NC} Python 3 not found"
        exit 1
    fi
}

# Install dependencies
install_deps() {
    echo -e "\n${BLUE}[2/8]${NC} Installing dependencies..."
    if pip install -e ".[dev]"; then
        echo -e "${GREEN}✓${NC} Dependencies installed"
    else
        echo -e "${RED}✗${NC} Failed to install dependencies"
        exit 1
    fi
}

# Install pre-commit hooks
install_hooks() {
    echo -e "\n${BLUE}[3/8]${NC} Installing pre-commit hooks..."
    if pre-commit install; then
        echo -e "${GREEN}✓${NC} Pre-commit hooks installed"
    else
        echo -e "${YELLOW}⚠${NC} Failed to install pre-commit hooks (non-fatal)"
    fi
}

# Run initial tests
run_tests() {
    echo -e "\n${BLUE}[4/8]${NC} Running initial tests..."
    if python -m pytest test/ -q --tb=line; then
        echo -e "${GREEN}✓${NC} All tests passed"
    else
        echo -e "${YELLOW}⚠${NC} Some tests failed (check your setup)"
    fi
}

# Initialize database
init_db() {
    echo -e "\n${BLUE}[5/8]${NC} Initializing database..."
    if [ ! -f "./skill_split.db" ]; then
        python -c "from core.database import Database; db = Database(); print('Database initialized')" 2>/dev/null
        echo -e "${GREEN}✓${NC} Database ready"
    else
        echo -e "${GREEN}✓${NC} Database already exists"
    fi
}

# Create development config
create_config() {
    echo -e "\n${BLUE}[6/8]${NC} Creating development configuration..."
    if [ ! -f ".env" ]; then
        cat > .env <<EOF
# skill-split Development Environment

# Database (optional, defaults to ./skill_split.db)
# SKILL_SPLIT_DB=./skill_split.db

# OpenAI API Key (for vector search)
# OPENAI_API_KEY=sk-...

# Supabase (optional, for cloud storage)
# SUPABASE_URL=https://...
# SUPABASE_KEY=...

# Enable embeddings (default: false)
# ENABLE_EMBEDDINGS=false
EOF
        echo -e "${GREEN}✓${NC} Created .env file"
    else
        echo -e "${GREEN}✓${NC} .env file already exists"
    fi
}

# Run quality checks
quality_check() {
    echo -e "\n${BLUE}[7/8]${NC} Running quality checks..."
    echo "  This may take a moment..."
    if bash scripts/quality_gate.sh 2>/dev/null; then
        echo -e "${GREEN}✓${NC} Quality checks passed"
    else
        echo -e "${YELLOW}⚠${NC} Some quality checks failed (non-fatal)"
    fi
}

# Print success message
print_success() {
    echo -e "\n${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${NC} ${GREEN}Setup Complete! Your development environment is ready.${NC}   ${CYAN}║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${BLUE}Quick Start:${NC}"
    echo -e "  ${YELLOW}make test${NC}              - Run tests"
    echo -e "  ${YELLOW}make lint${NC}              - Check code quality"
    echo -e "  ${YELLOW}make demo${NC}              - Run demos"
    echo -e "  ${YELLOW}./skill_split.py --help${NC} - See CLI options"
    echo ""
    echo -e "${BLUE}Documentation:${NC}"
    echo -e "  ${YELLOW}README.md${NC}               - Main documentation"
    echo -e "  ${YELLOW}CONTRIBUTING.md${NC}         - Contribution guide"
    echo -e "  ${YELLOW}docs/DEVELOPMENT.md${NC}     - Developer guide"
    echo ""
    echo -e "${BLUE}Next Steps:${NC}"
    echo -e "  1. Read ${YELLOW}CONTRIBUTING.md${NC} for contribution guidelines"
    echo -e "  2. Explore ${YELLOW}examples/plugins/${NC} for plugin development"
    echo -e "  3. Run ${YELLOW}make demo${NC} to see skill-split in action"
    echo ""
}

# Main execution
main() {
    print_header
    check_python
    install_deps
    install_hooks
    run_tests
    init_db
    create_config
    quality_check
    print_success
}

main
