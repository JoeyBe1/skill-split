#!/usr/bin/env bash
# skill-split Quick Start Script
# One-command setup for first-time users

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print header
echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         skill-split v1.0.0 - Quick Start               ║${NC}"
echo -e "${BLUE}║    Progressive disclosure for AI documentation         ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check Python version
echo -e "${YELLOW}Checking Python version...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 not found. Please install Python 3.10+${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | awk '{print $2}')
echo -e "${GREEN}✓ Found Python $PYTHON_VERSION${NC}"
echo ""

# Install dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
if ! pip install -e ".[dev]" 2>/dev/null; then
    echo -e "${YELLOW}Trying pip3...${NC}"
    pip3 install -e ".[dev]"
fi
echo -e "${GREEN}✓ Dependencies installed${NC}"
echo ""

# Run tests
echo -e "${YELLOW}Running tests to verify installation...${NC}"
if python -m pytest test/ -q --tb=line 2>/dev/null; then
    echo -e "${GREEN}✓ All tests passed${NC}"
else
    echo -e "${YELLOW}⚠ Some tests failed, but installation may still work${NC}"
fi
echo ""

# Initialize database
echo -e "${YELLOW}Initializing skill-split database...${NC}"
if [ ! -f "./skill_split.db" ]; then
    python -c "from core.database import Database; db = Database(); print('✓ Database initialized')"
else
    echo -e "${GREEN}✓ Database already exists${NC}"
fi
echo ""

# Display next steps
echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                    Installation Complete!              ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}Quick Start Commands:${NC}"
echo -e "  ${YELLOW}./skill_split.py parse README.md${NC}    # Parse a file"
echo -e "  ${YELLOW}./skill_split.py store README.md${NC}     # Store in database"
echo -e "  ${YELLOW}./skill_split.py search \"query\"${NC}      # BM25 keyword search"
echo -e "  ${YELLOW}./skill_split.py list README.md${NC}      # Show section tree"
echo ""
echo -e "${GREEN}Documentation:${NC}"
echo -e "  ${BLUE}README.md${NC}           - Main documentation"
echo -e "  ${BLUE}INSTALLATION.md${NC}     - Detailed installation guide"
echo -e "  ${BLUE}docs/QUICK_REFERENCE.md${NC} - Command reference"
echo ""
echo -e "${GREEN}Examples:${NC}"
echo -e "  ${YELLOW}make demo${NC}              - Run all demo scripts"
echo -e "  ${YELLOW}make benchmark${NC}         - Run performance benchmarks"
echo ""
echo -e "${GREEN}Testing:${NC}"
echo -e "  ${YELLOW}make test${NC}              - Run all tests"
echo -e "  ${YELLOW}make coverage${NC}          - Generate coverage report"
echo ""
echo -e "${YELLOW}For more information, see:${NC} https://github.com/user/skill-split"
echo ""
