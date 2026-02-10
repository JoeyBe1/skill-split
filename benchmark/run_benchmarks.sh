#!/bin/bash
# Skill-Split Benchmark Runner
# Quick commands for running benchmarks

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Help message
show_help() {
    echo "Skill-Split Benchmark Runner"
    echo ""
    echo "Usage: ./benchmark/run_benchmarks.sh [command]"
    echo ""
    echo "Commands:"
    echo "  all              Run all benchmarks"
    echo "  parsing          Run parsing benchmarks only"
    echo "  database         Run database benchmarks only"
    echo "  search           Run search benchmarks only"
    echo "  quick            Run quick subset (parse + query)"
    echo "  baseline         Generate baseline report"
    echo "  report           Generate report from JSON"
    echo "  help             Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./benchmark/run_benchmarks.sh quick"
    echo "  ./benchmark/run_benchmarks.sh all --benchmark-json=results.json"
}

# Check dependencies
check_deps() {
    if ! python -c "import pytest_benchmark" 2>/dev/null; then
        echo -e "${RED}Error: pytest-benchmark not installed${NC}"
        echo "Install with: pip install pytest-benchmark"
        exit 1
    fi
}

# Run all benchmarks
run_all() {
    echo -e "${GREEN}Running all benchmarks...${NC}"
    python -m pytest benchmark/bench.py --benchmark-only "$@"
}

# Run parsing benchmarks
run_parsing() {
    echo -e "${GREEN}Running parsing benchmarks...${NC}"
    python -m pytest benchmark/bench.py::TestParsingBenchmarks --benchmark-only "$@"
}

# Run database benchmarks
run_database() {
    echo -e "${GREEN}Running database benchmarks...${NC}"
    python -m pytest benchmark/bench.py::TestDatabaseBenchmarks --benchmark-only "$@"
}

# Run search benchmarks
run_search() {
    echo -e "${GREEN}Running search benchmarks...${NC}"
    python -m pytest benchmark/bench.py::TestSearchBenchmarks --benchmark-only "$@"
}

# Run quick subset
run_quick() {
    echo -e "${GREEN}Running quick benchmarks...${NC}"
    python -m pytest \
        benchmark/bench.py::TestParsingBenchmarks::test_parse_small_file \
        benchmark/bench.py::TestParsingBenchmarks::test_parse_medium_file \
        benchmark/bench.py::TestDatabaseBenchmarks::test_get_section \
        --benchmark-only \
        --benchmark-json=benchmark/results.json "$@"
}

# Generate baseline
run_baseline() {
    echo -e "${GREEN}Generating baseline report...${NC}"
    run_quick
    if [ -f "benchmark/results.json" ]; then
        python benchmark/generate_report.py benchmark/results.json
        echo -e "${GREEN}Baseline report generated: benchmark/baseline_report.md${NC}"
    else
        echo -e "${RED}Error: benchmark/results.json not found${NC}"
        exit 1
    fi
}

# Generate report from existing JSON
run_report() {
    if [ -f "benchmark/results.json" ]; then
        echo -e "${GREEN}Generating report from benchmark/results.json...${NC}"
        python benchmark/generate_report.py benchmark/results.json
    else
        echo -e "${RED}Error: benchmark/results.json not found${NC}"
        echo "Run benchmarks first: ./benchmark/run_benchmarks.sh quick"
        exit 1
    fi
}

# Main script
main() {
    check_deps

    case "${1:-help}" in
        all)
            shift
            run_all "$@"
            ;;
        parsing)
            shift
            run_parsing "$@"
            ;;
        database)
            shift
            run_database "$@"
            ;;
        search)
            shift
            run_search "$@"
            ;;
        quick)
            shift
            run_quick "$@"
            ;;
        baseline)
            run_baseline
            ;;
        report)
            run_report
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            echo -e "${RED}Unknown command: $1${NC}"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

main "$@"
