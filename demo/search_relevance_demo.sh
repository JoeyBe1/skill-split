#!/usr/bin/env bash

#############################################################################
# Search Relevance Demo - Comparing Search Modes
#
# This demo compares the three search modes available in skill-split:
# 1. BM25 (Keywords) - FTS5 full-text search with BM25 ranking
# 2. Vector (Semantic) - OpenAI embeddings for semantic similarity
# 3. Hybrid (Combined) - Weighted combination of both approaches
#
# Value Proposition:
# - Different use cases for different search modes
# - Result quality differences demonstrated
# - Ranking scores compared
#############################################################################

set -e

DEMO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$DEMO_DIR")"
DB_PATH="$PROJECT_ROOT/demo.db"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

echo -e "${BLUE}═════════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Search Relevance Demo - Comparing Search Modes                   ${NC}"
echo -e "${BLUE}═════════════════════════════════════════════════════════════════════${NC}"
echo ""

# Check if database exists
if [ ! -f "$DB_PATH" ]; then
    echo -e "${YELLOW}Setting up demo database...${NC}"
    SAMPLE_FILE="$DEMO_DIR/sample_skill.md"
    cd "$PROJECT_ROOT"
    python3 skill_split.py store "$SAMPLE_FILE" --db "$DB_PATH" > /dev/null 2>&1
    echo -e "${GREEN}✓ Demo database ready${NC}"
    echo ""
fi

# Test queries that demonstrate different search behaviors
declare -a TEST_QUERIES=(
    "sentiment analysis"
    "text processing"
    "summarization"
    "machine learning"
    "API integration"
)

echo -e "${YELLOW}📋 Test Queries:${NC}"
for query in "${TEST_QUERIES[@]}"; do
    echo "  • $query"
done
echo ""

# Check if embeddings are enabled
ENABLE_EMBEDDINGS=${ENABLE_EMBEDDINGS:-false}
if [ "$ENABLE_EMBEDDINGS" = "true" ]; then
    echo -e "${GREEN}✓ Semantic search enabled (ENABLE_EMBEDDINGS=true)${NC}"
    echo ""
else
    echo -e "${YELLOW}⚠ Note: Semantic search requires ENABLE_EMBEDDINGS=true${NC}"
    echo -e "${YELLOW}  Run: ENABLE_EMBEDDINGS=true $0${NC}"
    echo ""
    echo -e "${CYAN}Demo will continue with BM25 keyword search only.${NC}"
    echo ""
fi

# For each test query, compare search modes
for QUERY in "${TEST_QUERIES[@]}"; do
    echo -e "${MAGENTA}═════════════════════════════════════════════════════════════════════${NC}"
    echo -e "${MAGENTA}  Query: \"$QUERY\"${NC}"
    echo -e "${MAGENTA}═════════════════════════════════════════════════════════════════════${NC}"
    echo ""

    # 1. BM25 Keyword Search
    echo -e "${CYAN}1️⃣  BM25 Keyword Search (FTS5 Full-Text Search)${NC}"
    echo -e "${CYAN}   ───────────────────────────────────────────────────────────${NC}"
    echo "   Characteristics:"
    echo "   • Fast, local search without API calls"
    echo "   • Exact keyword matching"
    echo "   • Boolean operators supported (AND, OR, NEAR)"
    echo ""

    cd "$PROJECT_ROOT"
    BM25_RESULTS=$(python3 skill_split.py search "$QUERY" --db "$DB_PATH" 2>&1)
    echo "$BM25_RESULTS" | head -8
    echo ""

    # 2. Vector Semantic Search (if enabled)
    if [ "$ENABLE_EMBEDDINGS" = "true" ]; then
        echo -e "${CYAN}2️⃣  Vector Semantic Search (OpenAI Embeddings)${NC}"
        echo -e "${CYAN}   ───────────────────────────────────────────────────────────${NC}"
        echo "   Characteristics:"
        echo "   • Semantic understanding (finds related concepts)"
        echo "   • Requires OPENAI_API_KEY"
        echo "   • Slower due to API call"
        echo ""

        VECTOR_RESULTS=$(python3 skill_split.py search-semantic "$QUERY" --vector-weight 1.0 --db "$DB_PATH" 2>&1)
        echo "$VECTOR_RESULTS" | head -8
        echo ""

        # 3. Hybrid Search (if enabled)
        echo -e "${CYAN}3️⃣  Hybrid Search (Combined: 70% Semantic + 30% Keyword)${NC}"
        echo -e "${CYAN}   ───────────────────────────────────────────────────────────${NC}"
        echo "   Characteristics:"
        echo "   • Balances semantic understanding with keyword precision"
        echo "   • Tunable vector weight (default: 0.7)"
        echo "   • Best of both approaches"
        echo ""

        HYBRID_RESULTS=$(python3 skill_split.py search-semantic "$QUERY" --vector-weight 0.7 --db "$DB_PATH" 2>&1)
        echo "$HYBRID_RESULTS" | head -8
        echo ""

        # Comparison
        echo -e "${YELLOW}📊 Result Comparison:${NC}"
        echo ""
        echo "   BM25:       Keyword matching, fast results"
        echo "   Vector:     Semantic similarity, concept discovery"
        echo "   Hybrid:     Balanced approach with tunable weights"
        echo ""
    else
        echo -e "${CYAN}2️⃣  Vector Semantic Search${NC}"
        echo -e "${CYAN}   ───────────────────────────────────────────────────────────${NC}"
        echo -e "${YELLOW}   ⚠ Not enabled (requires ENABLE_EMBEDDINGS=true)${NC}"
        echo ""
        echo "   To enable semantic search:"
        echo "   1. Set OPENAI_API_KEY in your environment"
        echo "   2. Run: ENABLE_EMBEDDINGS=true $0"
        echo ""
    fi

    echo ""
done

# Demonstrate advanced query features
echo -e "${MAGENTA}═════════════════════════════════════════════════════════════════════${NC}"
echo -e "${MAGENTA}  Advanced Query Features${NC}"
echo -e "${MAGENTA}═════════════════════════════════════════════════════════════════════${NC}"
echo ""

echo -e "${CYAN}Boolean Operators (BM25 only):${NC}"
echo ""

echo -e "${GREEN}AND Query:${NC} \"sentiment AND analysis\""
echo ""
AND_RESULTS=$(python3 skill_split.py search "sentiment AND analysis" --db "$DB_PATH" 2>&1 | head -5)
echo "$AND_RESULTS"
echo ""

echo -e "${GREEN}OR Query:${NC} \"sentiment OR keywords\""
echo ""
OR_RESULTS=$(python3 skill_split.py search "sentiment OR keywords" --db "$DB_PATH" 2>&1 | head -5)
echo "$OR_RESULTS"
echo ""

echo -e "${GREEN}NEAR Query:${NC} \"text NEAR analysis\""
echo ""
NEAR_RESULTS=$(python3 skill_split.py search "text NEAR analysis" --db "$DB_PATH" 2>&1 | head -5)
echo "$NEAR_RESULTS"
echo ""

# Search within specific file
echo -e "${CYAN}File-Specific Search:${NC}"
echo ""
echo -e "${GREEN}Search in specific file:${NC}"
echo ""
FILE_RESULTS=$(python3 skill_split.py search "API" --file "$DEMO_DIR/sample_skill.md" --db "$DB_PATH" 2>&1 | head -5)
echo "$FILE_RESULTS"
echo ""

# Performance comparison
echo -e "${MAGENTA}═════════════════════════════════════════════════════════════════════${NC}"
echo -e "${MAGENTA}  Performance Comparison${NC}"
echo -e "${MAGENTA}═════════════════════════════════════════════════════════════════════${NC}"
echo ""

TEST_QUERY="analysis"
ITERATIONS=5

echo -e "${YELLOW}Timing $ITERATIONS searches for: \"$TEST_QUERY\"${NC}"
echo ""

# BM25 timing
echo -e "${CYAN}BM25 Search:${NC}"
total_time_bm25=0
for i in $(seq 1 $ITERATIONS); do
    start=$(date +%s%N)
    python3 skill_split.py search "$TEST_QUERY" --db "$DB_PATH" > /dev/null 2>&1
    end=$(date +%s%N)
    elapsed=$(( (end - start) / 1000000 ))
    total_time_bm25=$((total_time_bm25 + elapsed))
done
avg_bm25=$((total_time_bm25 / ITERATIONS))
echo "  Total: ${total_time_bm25}ms | Average: ${avg_bm25}ms"
echo ""

if [ "$ENABLE_EMBEDDINGS" = "true" ]; then
    # Vector timing
    echo -e "${CYAN}Vector Search:${NC}"
    total_time_vector=0
    for i in $(seq 1 $ITERATIONS); do
        start=$(date +%s%N)
        python3 skill_split.py search-semantic "$TEST_QUERY" --vector-weight 1.0 --db "$DB_PATH" > /dev/null 2>&1
        end=$(date +%s%N)
        elapsed=$(( (end - start) / 1000000 ))
        total_time_vector=$((total_time_vector + elapsed))
    done
    avg_vector=$((total_time_vector / ITERATIONS))
    echo "  Total: ${total_time_vector}ms | Average: ${avg_vector}ms"
    echo ""

    # Hybrid timing
    echo -e "${CYAN}Hybrid Search:${NC}"
    total_time_hybrid=0
    for i in $(seq 1 $ITERATIONS); do
        start=$(date +%s%N)
        python3 skill_split.py search-semantic "$TEST_QUERY" --vector-weight 0.7 --db "$DB_PATH" > /dev/null 2>&1
        end=$(date +%s%N)
        elapsed=$(( (end - start) / 1000000 ))
        total_time_hybrid=$((total_time_hybrid + elapsed))
    done
    avg_hybrid=$((total_time_hybrid / ITERATIONS))
    echo "  Total: ${total_time_hybrid}ms | Average: ${avg_hybrid}ms"
    echo ""

    # Speedup calculation
    speedup=$((avg_vector / avg_bm25))
    echo -e "${GREEN}✓ BM25 is ${speedup}x faster than vector search${NC}"
    echo ""
fi

# Summary
echo -e "${BLUE}═════════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  SEARCH MODE SUMMARY${NC}"
echo -e "${BLUE}═════════════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${CYAN}BM25 (Keywords)${NC}"
echo "  ✓ Fast, local search"
echo "  ✓ No API costs"
echo "  ✓ Boolean operators (AND, OR, NEAR)"
echo "  ✓ Exact keyword matching"
echo "  Best for: Specific terms, code searches, exact phrases"
echo ""

if [ "$ENABLE_EMBEDDINGS" = "true" ]; then
    echo -e "${CYAN}Vector (Semantic)${NC}"
    echo "  ✓ Semantic understanding"
    echo "  ✓ Finds related concepts"
    echo "  ✓ Works across languages"
    echo "  Requires: OPENAI_API_KEY"
    echo "  Best for: Concept discovery, synonyms, related topics"
    echo ""

    echo -e "${CYAN}Hybrid (Combined)${NC}"
    echo "  ✓ Balances keyword + semantic"
    echo "  ✓ Tunable vector weight (0.0-1.0)"
    echo "  ✓ Best overall results"
    echo "  Default: 70% semantic, 30% keyword"
    echo "  Best for: General searches, discovery scenarios"
    echo ""
fi

echo -e "${BLUE}═════════════════════════════════════════════════════════════════════${NC}"
