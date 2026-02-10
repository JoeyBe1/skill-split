#!/usr/bin/env bash

#############################################################################
# Master Demo Runner - Run All Skill-Split Demos
#
# This script runs all available demo scenarios to showcase the complete
# capabilities of the skill-split system.
#
# Usage:
#   ./run_all_demos.sh [demo_name]
#
# Examples:
#   ./run_all_demos.sh              # Run all demos
#   ./run_all_demos.sh token        # Run only token savings demo
#   ./run_all_demos.sh search       # Run only search relevance demo
#############################################################################

set -e

DEMO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$DEMO_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Demo definitions
declare -A DEMOS=(
    ["token"]="token_savings_demo.sh"
    ["search"]="search_relevance_demo.sh"
    ["component"]="component_deployment_demo.sh"
    ["recovery"]="disaster_recovery_demo.sh"
    ["batch"]="batch_processing_demo.sh"
)

declare -a DEMO_ORDER=("token" "search" "component" "recovery" "batch")

# Function to print header
print_header() {
    echo ""
    echo -e "${MAGENTA}╔═════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${MAGENTA}║${NC}       ${BOLD}Skill-Split Comprehensive Demo Suite${NC}                       ${MAGENTA}║${NC}"
    echo -e "${MAGENTA}║                                                                   ║${NC}"
    echo -e "${MAGENTA}║${NC}  ${CYAN}Showcasing Real-World Value of Progressive Disclosure${NC}        ${MAGENTA}║${NC}"
    echo -e "${MAGENTA}╚═════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# Function to list available demos
list_demos() {
    echo -e "${BOLD}Available Demos:${NC}"
    echo ""

    for demo_name in "${DEMO_ORDER[@]}"; do
        demo_file="${DEMOS[$demo_name]}"
        demo_path="$DEMO_DIR/$demo_file"

        if [ -f "$demo_path" ]; then
            case "$demo_name" in
                "token")
                    description="Token Savings - Progressive Disclosure Value"
                    ;;
                "search")
                    description="Search Relevance - Compare BM25, Vector, Hybrid"
                    ;;
                "component")
                    description="Component Deployment - Multi-file Checkout"
                    ;;
                "recovery")
                    description="Disaster Recovery - Backup/Restore Workflow"
                    ;;
                "batch")
                    description="Batch Processing - Handle 1000+ Files"
                    ;;
            esac
            echo -e "  ${CYAN}$demo_name${NC}  $description"
        fi
    done
    echo ""
}

# Function to run a specific demo
run_demo() {
    local demo_name=$1
    local demo_file="${DEMOS[$demo_name]}"
    local demo_path="$DEMO_DIR/$demo_file"

    if [ ! -f "$demo_path" ]; then
        echo -e "${RED}Error: Demo not found: $demo_name${NC}"
        return 1
    fi

    echo ""
    echo -e "${BLUE}═════════════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  Running: $demo_name${NC}"
    echo -e "${BLUE}═════════════════════════════════════════════════════════════════════${NC}"
    echo ""

    # Run the demo
    bash "$demo_path"

    echo ""
    echo -e "${GREEN}✓ Demo '$demo_name' completed${NC}"
    echo ""

    # Pause between demos
    if [ "$RUN_ALL" = "true" ]; then
        echo -e "${YELLOW}Press Enter to continue to next demo (or Ctrl+C to exit)...${NC}"
        read
    fi
}

# Main execution
main() {
    local requested_demo=$1

    print_header

    # Check if skill-split is available
    if [ ! -f "$PROJECT_ROOT/skill_split.py" ]; then
        echo -e "${RED}Error: skill_split.py not found in $PROJECT_ROOT${NC}"
        exit 1
    fi

    echo -e "${GREEN}✓ Skill-split found at: $PROJECT_ROOT${NC}"
    echo ""

    # Check Python dependencies
    if ! python3 -c "import sqlite3" 2>/dev/null; then
        echo -e "${RED}Error: Python 3 with sqlite3 required${NC}"
        exit 1
    fi

    # Run specific demo or list
    if [ -n "$requested_demo" ]; then
        if [ "${DEMOS[$requested_demo]+exists}" ]; then
            run_demo "$requested_demo"
        else
            echo -e "${RED}Error: Unknown demo '$requested_demo'${NC}"
            echo ""
            list_demos
            exit 1
        fi
    else
        # Show menu
        list_demos

        if [ "$INTERACTIVE" != "false" ]; then
            echo -e "${BOLD}Select a demo to run (or 'all' to run all):${NC}"
            echo -n ">> "
            read -r choice

            if [ "$choice" = "all" ]; then
                RUN_ALL="true"
                for demo_name in "${DEMO_ORDER[@]}"; do
                    run_demo "$demo_name"
                done

                # Final summary
                echo ""
                echo -e "${MAGENTA}╔═════════════════════════════════════════════════════════════════════╗${NC}"
                echo -e "${MAGENTA}║${NC}                    ${BOLD}All Demos Complete!${NC}                         ${MAGENTA}║${NC}"
                echo -e "${MAGENTA}╚═════════════════════════════════════════════════════════════════════╝${NC}"
                echo ""
            elif [ -n "$choice" ] && [ "${DEMOS[$choice]+exists}" ]; then
                run_demo "$choice"
            else
                echo -e "${RED}Invalid choice. Exiting.${NC}"
                exit 1
            fi
        else
            echo -e "${YELLOW}Usage: $0 [demo_name]${NC}"
            echo ""
            echo "Specify a demo name or run in interactive mode"
            exit 0
        fi
    fi
}

# Check for flags
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "Usage: $0 [demo_name] [options]"
    echo ""
    echo "Demo names:"
    for demo_name in "${DEMO_ORDER[@]}"; do
        echo "  $demo_name"
    done
    echo ""
    echo "Options:"
    echo "  --help, -h     Show this help message"
    echo "  --non-interactive  Run without interactive prompts"
    exit 0
fi

if [ "$1" = "--non-interactive" ]; then
    INTERACTIVE="false"
    shift
fi

# Run main
main "$@"
