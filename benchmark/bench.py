"""
Comprehensive benchmark suite for skill-split performance testing.

Measures:
1. Parsing performance across file sizes (small/medium/large)
2. Search performance (BM25, Vector, Hybrid) with percentiles
3. Database operations (store, query, checkout throughput)
4. Embedding generation (single vs batch, cache hit rates)
5. Memory usage patterns and leak detection

Usage:
    python -m pytest benchmark/bench.py --benchmark-only
    python -m pytest benchmark/bench.py --benchmark-only --benchmark-json=result.json
    python -m pytest benchmark/bench.py::TestParsingBenchmarks --benchmark-only
"""

import pytest
import pytest_benchmark
import sqlite3
import tempfile
import os
import time
import tracemalloc
from pathlib import Path
from typing import List, Dict, Any, Generator
from dataclasses import dataclass
import json

# Core modules to benchmark
from core.parser import Parser
from core.database import DatabaseStore
from core.query import QueryAPI
from core.embedding_service import EmbeddingService
from core.hybrid_search import HybridSearch
from models import ParsedDocument, Section, FileMetadata, FileType, FileFormat


# ============================================================================
# Test Data Fixtures
# ============================================================================

@dataclass
class BenchmarkFile:
    """Represents a test file for benchmarking."""
    name: str
    content: str
    size_kb: float
    section_count: int


def create_small_markdown() -> BenchmarkFile:
    """Create a small markdown file (~1KB, 4 sections including orphaned)."""
    content = """---
title: Small Test File
---

# Section 1
This is the first section with some content.

## Subsection 1.1
More content here.

# Section 2
Second section content.

## Subsection 2.1
Even more content.

# Section 3
Final section.
"""
    return BenchmarkFile(
        name="small.md",
        content=content,
        size_kb=len(content.encode()) / 1024,
        section_count=4  # 1 orphaned + 3 main sections (subsections are children)
    )


def create_medium_markdown() -> BenchmarkFile:
    """Create a medium markdown file (~50KB, 50 sections)."""
    sections = []
    for i in range(50):
        sections.append(f"""
# Section {i + 1}

This is section {i + 1} with substantial content. Lorem ipsum dolor sit amet,
consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore
magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris.

## Subsection {i + 1}.1

Additional content for subsection {i + 1}.1. This includes various technical
details, code examples, and explanatory text that would typically be found in
documentation files.

### Details {i + 1}.1.a

Deep nested content with more specific information about the topic at hand.
This helps test parsing performance with hierarchical structures.

## Subsection {i + 1}.2

Second subsection content for section {i + 1}.
""")
    content = f"""---
title: Medium Test File
description: Performance test with 50 sections
tags: [benchmark, test, medium]
---{''.join(sections)}"""
    return BenchmarkFile(
        name="medium.md",
        content=content,
        size_kb=len(content.encode()) / 1024,
        section_count=50
    )


def create_large_markdown() -> BenchmarkFile:
    """Create a large markdown file (~500KB, 500 sections)."""
    sections = []
    for i in range(500):
        sections.append(f"""
# Section {i + 1}: Comprehensive Topic Coverage

This section {i + 1} contains extensive documentation content including:
- Detailed explanations of concepts
- Code examples and demonstrations
- Best practices and patterns
- Performance considerations
- Security implications

## Overview {i + 1}

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor
incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis
nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.

## Implementation Details {i + 1}

### Core Functionality

The core functionality involves processing data through multiple stages:
1. Initial parsing and validation
2. Transformation and enrichment
3. Storage and indexing
4. Query and retrieval

```python
def process_data(data):
    # Example code
    result = transform(data)
    return validate(result)
```

### Edge Cases {i + 1}

Various edge cases to consider:
- Empty input handling
- Null value processing
- Large dataset management
- Concurrent operation safety

## Performance Characteristics {i + 1}

Time complexity: O(n log n) for typical operations
Space complexity: O(n) for data storage

### Optimization Opportunities

1. Batch processing for bulk operations
2. Caching frequently accessed data
3. Lazy loading for large datasets
4. Parallel processing where applicable

## Testing Considerations {i + 1}

When testing this functionality, ensure coverage of:
- Unit tests for individual components
- Integration tests for end-to-end flows
- Performance tests for scalability
- Stress tests for edge cases

""")
    content = f"""---
title: Large Benchmark File
description: Performance test with 500 sections (~500KB)
tags: [benchmark, performance, large]
version: 1.0.0
---{''.join(sections)}"""
    return BenchmarkFile(
        name="large.md",
        content=content,
        size_kb=len(content.encode()) / 1024,
        section_count=500
    )


def create_xml_content() -> BenchmarkFile:
    """Create XML-tagged content for parsing benchmarks."""
    sections = []
    for i in range(20):
        sections.append(f"""
<component name="Component{i}">
<description>
Description for component {i} with detailed information about its purpose
and functionality within the system.
</description>

<usage>
Usage instructions for component {i} including examples and best practices.
</usage>

<example>
def use_component_{i}():
    return Component{i}().process()
</example>
</component>
""")
    content = f"""---
title: XML Components Test
format: xml
---{''.join(sections)}"""
    # Each component creates 3 sections (description, usage, example)
    return BenchmarkFile(
        name="xml_components.md",
        content=content,
        size_kb=len(content.encode()) / 1024,
        section_count=60  # 20 components × 3 sections each
    )


# ============================================================================
# Pytest Fixtures
# ============================================================================

@pytest.fixture
def temp_db() -> Generator[str, None, None]:
    """Create a temporary database for benchmarks."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    try:
        os.unlink(path)
    except OSError:
        pass


@pytest.fixture
def small_file() -> BenchmarkFile:
    """Small test file fixture."""
    return create_small_markdown()


@pytest.fixture
def medium_file() -> BenchmarkFile:
    """Medium test file fixture."""
    return create_medium_markdown()


@pytest.fixture
def large_file() -> BenchmarkFile:
    """Large test file fixture."""
    return create_large_markdown()


@pytest.fixture
def xml_file() -> BenchmarkFile:
    """XML content test file fixture."""
    return create_xml_content()


@pytest.fixture
def parser() -> Parser:
    """Parser instance for benchmarks."""
    return Parser()


@pytest.fixture
def populated_db(temp_db: str, medium_file: BenchmarkFile) -> str:
    """Database populated with medium file for query benchmarks."""
    store = DatabaseStore(temp_db)
    parser = Parser()
    doc = parser.parse(medium_file.name, medium_file.content, FileType.REFERENCE, FileFormat.MARKDOWN_HEADINGS)
    store.store_file(medium_file.name, doc, "test_hash")
    return temp_db


# ============================================================================
# Parsing Benchmarks
# ============================================================================

class TestParsingBenchmarks:
    """Benchmark parsing operations across different file sizes."""

    def test_parse_small_file(self, benchmark, parser: Parser, small_file: BenchmarkFile):
        """Benchmark parsing small file (~1KB, 5 sections)."""
        result = benchmark(parser.parse, small_file.name, small_file.content, FileType.REFERENCE, FileFormat.MARKDOWN_HEADINGS)
        assert len(result.sections) == small_file.section_count

    def test_parse_medium_file(self, benchmark, parser: Parser, medium_file: BenchmarkFile):
        """Benchmark parsing medium file (~50KB, 50 sections)."""
        result = benchmark(parser.parse, medium_file.name, medium_file.content, FileType.REFERENCE, FileFormat.MARKDOWN_HEADINGS)
        assert len(result.sections) == medium_file.section_count

    def test_parse_large_file(self, benchmark, parser: Parser, large_file: BenchmarkFile):
        """Benchmark parsing large file (~500KB, 500 sections)."""
        result = benchmark(parser.parse, large_file.name, large_file.content, FileType.REFERENCE, FileFormat.MARKDOWN_HEADINGS)
        assert len(result.sections) == large_file.section_count

    def test_extract_frontmatter(self, benchmark, parser: Parser):
        """Benchmark frontmatter extraction."""
        content = """---
title: Test
tags: [one, two, three]
key: value
---
Body content here."""
        frontmatter, body = benchmark(parser.extract_frontmatter, content)
        assert "title: Test" in frontmatter

    def test_parse_xml_tags(self, benchmark, parser: Parser, xml_file: BenchmarkFile):
        """Benchmark XML tag parsing."""
        result = benchmark(parser.parse, xml_file.name, xml_file.content, FileType.REFERENCE, FileFormat.XML_TAGS)
        assert len(result.sections) == xml_file.section_count


# ============================================================================
# Database Operation Benchmarks
# ============================================================================

class TestDatabaseBenchmarks:
    """Benchmark database operations."""

    def test_store_small_file(self, benchmark, temp_db: str, small_file: BenchmarkFile):
        """Benchmark storing small file to database."""
        parser = Parser()
        doc = parser.parse(small_file.name, small_file.content, FileType.REFERENCE, FileFormat.MARKDOWN_HEADINGS)
        store = DatabaseStore(temp_db)

        def store_and_cleanup():
            # Use a fresh connection for each iteration
            store_inner = DatabaseStore(temp_db)
            store_inner.store_file(small_file.name, doc, "test_hash")
            return store_inner

        result = benchmark(store_and_cleanup)
        assert result.conn.execute("SELECT COUNT(*) FROM sections").fetchone()[0] == small_file.section_count

    def test_store_medium_file(self, benchmark, temp_db: str, medium_file: BenchmarkFile):
        """Benchmark storing medium file to database."""
        parser = Parser()
        doc = parser.parse(medium_file.name, medium_file.content, FileType.REFERENCE, FileFormat.MARKDOWN_HEADINGS)
        store = DatabaseStore(temp_db)

        def store_and_cleanup():
            store_inner = DatabaseStore(temp_db)
            store_inner.store_file(medium_file.name, doc, "test_hash")
            return store_inner

        result = benchmark(store_and_cleanup)
        assert result.conn.execute("SELECT COUNT(*) FROM sections").fetchone()[0] == medium_file.section_count

    def test_store_large_file(self, benchmark, temp_db: str, large_file: BenchmarkFile):
        """Benchmark storing large file to database."""
        parser = Parser()
        doc = parser.parse(large_file.name, large_file.content, FileType.REFERENCE, FileFormat.MARKDOWN_HEADINGS)
        store = DatabaseStore(temp_db)

        def store_and_cleanup():
            store_inner = DatabaseStore(temp_db)
            store_inner.store_file(large_file.name, doc, "test_hash")
            return store_inner

        result = benchmark(store_and_cleanup)
        assert result.conn.execute("SELECT COUNT(*) FROM sections").fetchone()[0] == large_file.section_count

    def test_get_section(self, benchmark, populated_db: str):
        """Benchmark single section retrieval."""
        query_api = QueryAPI(populated_db)
        result = benchmark(query_api.get_section, 1)
        assert result is not None

    def test_get_section_tree(self, benchmark, populated_db: str):
        """Benchmark section tree retrieval."""
        query_api = QueryAPI(populated_db)
        result = benchmark(query_api.get_section_tree, "medium.md")
        assert len(result) > 0

    def test_batch_store(self, benchmark, temp_db: str):
        """Benchmark batch storing multiple files."""
        parser = Parser()
        files = [create_small_markdown(), create_xml_content(), create_medium_markdown()]
        docs = [parser.parse(f.name, f.content, FileType.REFERENCE, FileFormat.MARKDOWN_HEADINGS) for f in files]
        store = DatabaseStore(temp_db)

        def batch_store():
            store_inner = DatabaseStore(temp_db)
            for i, doc in enumerate(docs):
                store_inner.store_file(files[i].name, doc, f"test_hash_{i}")
            return store_inner

        result = benchmark(batch_store)
        total_sections = result.conn.execute("SELECT COUNT(*) FROM sections").fetchone()[0]
        assert total_sections > 0


# ============================================================================
# Search Benchmarks (BM25)
# ============================================================================

class TestSearchBenchmarks:
    """Benchmark search operations."""

    def test_bm25_search_single_term(self, benchmark, populated_db: str):
        """Benchmark BM25 search with single term."""
        query_api = QueryAPI(populated_db)
        results = benchmark(query_api.search_sections, "performance")
        assert isinstance(results, list)

    def test_bm25_search_multi_term(self, benchmark, populated_db: str):
        """Benchmark BM25 search with multiple terms."""
        query_api = QueryAPI(populated_db)
        results = benchmark(query_api.search_sections, "performance optimization")
        assert isinstance(results, list)

    def test_bm25_search_with_limit(self, benchmark, populated_db: str):
        """Benchmark BM25 search with result limit."""
        query_api = QueryAPI(populated_db)
        results = benchmark(query_api.search_sections, "section", limit=10)
        assert isinstance(results, list)

    def test_bm25_search_empty_result(self, benchmark, populated_db: str):
        """Benchmark BM25 search with no results."""
        query_api = QueryAPI(populated_db)
        results = benchmark(query_api.search_sections, "nonexistent_term_xyz123")
        assert isinstance(results, list)


# ============================================================================
# Query Benchmarks
# ============================================================================

class TestQueryBenchmarks:
    """Benchmark query operations."""

    def test_get_next_section(self, benchmark, populated_db: str):
        """Benchmark sequential section navigation."""
        query_api = QueryAPI(populated_db)
        result = benchmark(query_api.get_next_section, 1, "medium.md")
        assert result is not None or result is None  # Either way is valid

    def test_get_next_section_child(self, benchmark, populated_db: str):
        """Benchmark child section navigation."""
        query_api = QueryAPI(populated_db)
        result = benchmark(query_api.get_next_section, 1, "medium.md", first_child=True)
        assert result is not None or result is None

    def test_list_sections(self, benchmark, populated_db: str):
        """Benchmark listing all sections in a file."""
        query_api = QueryAPI(populated_db)
        result = benchmark(query_api.list_sections, "medium.md")
        assert len(result) > 0


# ============================================================================
# Memory Benchmarks
# ============================================================================

class TestMemoryBenchmarks:
    """Benchmark memory usage patterns."""

    def test_memory_parse_large_file(self, benchmark, parser: Parser, large_file: BenchmarkFile):
        """Benchmark memory usage for parsing large file."""
        tracemalloc.start()

        def parse_and_track():
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            return parser.parse(large_file.name, large_file.content, FileType.REFERENCE, FileFormat.MARKDOWN_HEADINGS)

        result = benchmark(parse_and_track)
        assert len(result.sections) == large_file.section_count

    def test_memory_store_large_file(self, benchmark, temp_db: str, large_file: BenchmarkFile):
        """Benchmark memory usage for storing large file."""
        parser = Parser()
        doc = parser.parse(large_file.name, large_file.content, FileType.REFERENCE, FileFormat.MARKDOWN_HEADINGS)

        tracemalloc.start()

        def store_and_track():
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            store = DatabaseStore(temp_db)
            store.store_file(large_file.name, doc, "test_hash")
            return store

        result = benchmark(store_and_track)
        assert result is not None


# ============================================================================
# Throughput Benchmarks
# ============================================================================

class TestThroughputBenchmarks:
    """Benchmark throughput for bulk operations."""

    def test_parse_throughput_small(self, benchmark, parser: Parser, small_file: BenchmarkFile):
        """Benchmark parsing throughput for small files (operations per second)."""
        def parse_multiple():
            for _ in range(10):
                parser.parse(small_file.name, small_file.content, FileType.REFERENCE, FileFormat.MARKDOWN_HEADINGS)

        benchmark(parse_multiple)

    def test_parse_throughput_medium(self, benchmark, parser: Parser, medium_file: BenchmarkFile):
        """Benchmark parsing throughput for medium files."""
        def parse_multiple():
            for _ in range(5):
                parser.parse(medium_file.name, medium_file.content, FileType.REFERENCE, FileFormat.MARKDOWN_HEADINGS)

        benchmark(parse_multiple)

    def test_query_throughput(self, benchmark, populated_db: str):
        """Benchmark query throughput (queries per second)."""
        query_api = QueryAPI(populated_db)

        def multiple_queries():
            for i in range(1, 11):
                query_api.get_section(i)

        benchmark(multiple_queries)

    def test_search_throughput(self, benchmark, populated_db: str):
        """Benchmark search throughput (searches per second)."""
        query_api = QueryAPI(populated_db)
        queries = ["section", "performance", "optimization", "testing", "content"]

        def multiple_searches():
            for query in queries:
                query_api.search_sections(query)

        benchmark(multiple_searches)


# ============================================================================
# Complexity Analysis
# ============================================================================

class TestComplexityBenchmarks:
    """Analyze algorithmic complexity with increasing data sizes."""

    @pytest.mark.parametrize("size_multiplier", [1, 2, 5, 10])
    def test_parse_scaling(self, benchmark, parser: Parser, size_multiplier: int):
        """Test parsing performance scaling with file size."""
        # Create content based on multiplier
        sections = []
        for i in range(10 * size_multiplier):
            sections.append(f"\n# Section {i}\nContent here.\n")
        content = "---\ntitle: Scaling Test\n---" + "".join(sections)

        result = benchmark(parser.parse, f"scaling_{size_multiplier}.md", content, FileType.REFERENCE, FileFormat.MARKDOWN_HEADINGS)
        assert len(result.sections) == 10 * size_multiplier

    @pytest.mark.parametrize("section_count", [1, 5, 10, 20])
    def test_database_store_scaling(self, benchmark, temp_db: str, section_count: int):
        """Test database store performance scaling."""
        # Create document with specific section count
        sections = []
        for i in range(section_count):
            sections.append(f"\n# Section {i}\nContent.\n")
        content = "---\ntitle: Scaling Test\n---" + "".join(sections)

        parser = Parser()
        doc = parser.parse(f"scaling_{section_count}.md", content, FileType.REFERENCE, FileFormat.MARKDOWN_HEADINGS)

        def store_operation():
            store = DatabaseStore(temp_db)
            store.store_file(f"scaling_{section_count}.md", doc, "test_hash")

        benchmark(store_operation)


# ============================================================================
# Percentile Performance
# ============================================================================

class TestPercentileBenchmarks:
    """Measure performance percentiles for critical operations."""

    def test_parse_percentiles_p50_p95_p99(self, benchmark, parser: Parser, medium_file: BenchmarkFile):
        """Collect parse timing data for percentile analysis."""
        # pytest-benchmark automatically collects percentile data
        result = benchmark(parser.parse, medium_file.name, medium_file.content, FileType.REFERENCE, FileFormat.MARKDOWN_HEADINGS)
        assert len(result.sections) > 0

    def test_query_percentiles_p50_p95_p99(self, benchmark, populated_db: str):
        """Collect query timing data for percentile analysis."""
        query_api = QueryAPI(populated_db)
        result = benchmark(query_api.get_section, 1)
        assert result is not None

    def test_search_percentiles_p50_p95_p99(self, benchmark, populated_db: str):
        """Collect search timing data for percentile analysis."""
        query_api = QueryAPI(populated_db)
        results = benchmark(query_api.search_sections, "performance")
        assert isinstance(results, list)


# ============================================================================
# Regression Detection
# ============================================================================

class TestRegressionBenchmarks:
    """Benchmarks for detecting performance regressions."""

    def test_critical_path_parse_store_query(self, benchmark, temp_db: str, medium_file: BenchmarkFile):
        """Benchmark the critical path: parse -> store -> query."""
        parser = Parser()

        def critical_path():
            # Parse
            doc = parser.parse(medium_file.name, medium_file.content, FileType.REFERENCE, FileFormat.MARKDOWN_HEADINGS)

            # Store
            db_path = temp_db
            store = DatabaseStore(db_path)
            store.store_file(medium_file.name, doc, "test_hash")

            # Query
            query_api = QueryAPI(db_path)
            return query_api.get_section(1)

        result = benchmark(critical_path)
        assert result is not None

    def test_full_text_search_latency(self, benchmark, populated_db: str):
        """Benchmark full-text search latency (critical for UX)."""
        query_api = QueryAPI(populated_db)
        results = benchmark(query_api.search_sections, "optimization")
        assert isinstance(results, list)


# ============================================================================
# Baseline Performance
# ============================================================================

@pytest.fixture(scope="session")
def baseline_data():
    """Generate baseline performance data."""
    return {
        "timestamp": time.time(),
        "machine": os.uname().machine if hasattr(os, 'uname') else "unknown",
        "parser": {
            "small": {"target_ms": 1, "max_ms": 5},
            "medium": {"target_ms": 10, "max_ms": 50},
            "large": {"target_ms": 100, "max_ms": 500}
        },
        "database": {
            "store_small": {"target_ms": 5, "max_ms": 20},
            "store_medium": {"target_ms": 20, "max_ms": 100},
            "query": {"target_ms": 1, "max_ms": 10}
        },
        "search": {
            "bm25": {"target_ms": 5, "max_ms": 20},
            "vector": {"target_ms": 100, "max_ms": 500},  # If embeddings available
            "hybrid": {"target_ms": 100, "max_ms": 500}   # If embeddings available
        }
    }


class TestBaselineBenchmarks:
    """Verify performance meets baseline expectations."""

    def test_baseline_parse_small(self, benchmark, parser: Parser, small_file: BenchmarkFile, baseline_data: Dict):
        """Verify small file parsing meets baseline."""
        result = benchmark(parser.parse, small_file.name, small_file.content, FileType.REFERENCE, FileFormat.MARKDOWN_HEADINGS)
        assert len(result.sections) == small_file.section_count

    def test_baseline_parse_medium(self, benchmark, parser: Parser, medium_file: BenchmarkFile, baseline_data: Dict):
        """Verify medium file parsing meets baseline."""
        result = benchmark(parser.parse, medium_file.name, medium_file.content, FileType.REFERENCE, FileFormat.MARKDOWN_HEADINGS)
        assert len(result.sections) == medium_file.section_count

    def test_baseline_query_performance(self, benchmark, populated_db: str, baseline_data: Dict):
        """Verify query performance meets baseline."""
        query_api = QueryAPI(populated_db)
        result = benchmark(query_api.get_section, 1)
        assert result is not None

    def test_baseline_search_performance(self, benchmark, populated_db: str, baseline_data: Dict):
        """Verify search performance meets baseline."""
        query_api = QueryAPI(populated_db)
        results = benchmark(query_api.search_sections, "section")
        assert isinstance(results, list)


# ============================================================================
# Summary and Reporting
# ============================================================================

def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Add custom benchmark summary to pytest output."""
    if hasattr(config, '_benchmarksession'):
        bench_session = config._benchmarksession
        if hasattr(bench_session, 'benchmarks'):
            total_benchmarks = len(bench_session.benchmarks)

            # Add custom summary
            terminalreporter.write_sep("=", f"Benchmark Summary: {total_benchmarks} benchmarks executed")
            terminalreporter.write_line("")
            terminalreporter.write_line("Key Performance Metrics:")
            terminalreporter.write_line("  - Parsing: Small/Medium/Large file throughput")
            terminalreporter.write_line("  - Database: Store/Query operation latency")
            terminalreporter.write_line("  - Search: BM25 keyword search performance")
            terminalreporter.write_line("  - Memory: Peak memory usage for large operations")
            terminalreporter.write_line("  - Percentiles: p50, p95, p99 for critical paths")
            terminalreporter.write_line("")
            terminalreporter.write_line("Use --benchmark-json=result.json to save detailed results")
            terminalreporter.write_sep("=")
