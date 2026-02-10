# Skill-Split Benchmark Suite

Comprehensive performance benchmarking for the skill-split project.

## Overview

This benchmark suite measures performance across critical operations:

1. **Parsing Performance** - File parsing across different sizes
2. **Database Operations** - Store and query throughput
3. **Search Performance** - BM25, Vector, and Hybrid search
4. **Memory Usage** - Peak memory and leak detection
5. **Throughput Analysis** - Operations per second

## Installation

Ensure dependencies are installed:

```bash
pip install -r requirements.txt
```

Required packages:
- `pytest>=7.0.0`
- `pytest-benchmark>=4.0.0`
- `pytest-cov>=4.0.0`

## Usage

### Run All Benchmarks

```bash
python -m pytest benchmark/bench.py --benchmark-only
```

### Run Specific Benchmark Classes

```bash
# Parsing benchmarks only
python -m pytest benchmark/bench.py::TestParsingBenchmarks --benchmark-only

# Database benchmarks only
python -m pytest benchmark/bench.py::TestDatabaseBenchmarks --benchmark-only

# Search benchmarks only
python -m pytest benchmark/bench.py::TestSearchBenchmarks --benchmark-only
```

### Run Specific Benchmarks

```bash
# Single benchmark
python -m pytest benchmark/bench.py::TestParsingBenchmarks::test_parse_small_file --benchmark-only

# By pattern
python -m pytest benchmark/bench.py -k "parse" --benchmark-only
```

### Save Benchmark Results

```bash
# Save as JSON
python -m pytest benchmark/bench.py --benchmark-only --benchmark-json=benchmark/results.json

# Save with histogram
python -m pytest benchmark/bench.py --benchmark-only --benchmark-histogram
```

### Compare with Previous Run

```bash
# Save baseline
python -m pytest benchmark/bench.py --benchmark-only --benchmark-autosave
# Then compare
python -m pytest benchmark/bench.py --benchmark-only --benchmark-compare
```

## Benchmark Categories

### 1. Parsing Benchmarks (`TestParsingBenchmarks`)

Measures parsing performance across file sizes:

- `test_parse_small_file` - ~1KB, 4 sections
- `test_parse_medium_file` - ~50KB, ~150 sections
- `test_parse_large_file` - ~500KB, ~1500 sections
- `test_extract_frontmatter` - Frontmatter extraction only
- `test_parse_xml_tags` - XML tag parsing

**Targets**:
- Small: < 5ms
- Medium: < 50ms
- Large: < 500ms

### 2. Database Benchmarks (`TestDatabaseBenchmarks`)

Measures database operation performance:

- `test_store_small_file` - Store small file
- `test_store_medium_file` - Store medium file
- `test_store_large_file` - Store large file
- `test_get_section` - Single section retrieval
- `test_get_section_tree` - Full tree retrieval
- `test_batch_store` - Multiple files

**Targets**:
- Store small: < 20ms
- Query: < 10ms

### 3. Search Benchmarks (`TestSearchBenchmarks`)

Measures search performance:

- `test_bm25_search_single_term` - Single keyword search
- `test_bm25_search_multi_term` - Multiple keywords
- `test_bm25_search_with_limit` - Limited results
- `test_bm25_search_empty_result` - No results case

**Targets**:
- BM25 search: < 20ms

### 4. Query Benchmarks (`TestQueryBenchmarks`)

Measures query operation performance:

- `test_get_next_section` - Sequential navigation
- `test_get_next_section_child` - Child navigation
- `test_list_sections` - List all sections

### 5. Memory Benchmarks (`TestMemoryBenchmarks`)

Measures memory usage patterns:

- `test_memory_parse_large_file` - Parse memory usage
- `test_memory_store_large_file` - Store memory usage

### 6. Throughput Benchmarks (`TestThroughputBenchmarks`)

Measures operations per second:

- `test_parse_throughput_small` - Small file throughput
- `test_parse_throughput_medium` - Medium file throughput
- `test_query_throughput` - Query throughput
- `test_search_throughput` - Search throughput

### 7. Complexity Benchmarks (`TestComplexityBenchmarks`)

Analyzes algorithmic complexity:

- `test_parse_scaling` - Parse time vs file size
- `test_database_store_scaling` - Store time vs sections

### 8. Regression Benchmarks (`TestRegressionBenchmarks`)

Detects performance regressions:

- `test_critical_path_parse_store_query` - Full workflow
- `test_full_text_search_latency` - Search latency

## Report Generation

### Generate Report from Results

```bash
# Run benchmarks first
python -m pytest benchmark/bench.py --benchmark-only --benchmark-json=benchmark/results.json

# Generate report
python benchmark/generate_report.py benchmark/results.json
```

### Report Template

The `REPORT.md` template provides a comprehensive report structure with:

- Executive summary
- Performance metrics by category
- Percentile analysis (p50, p95, p99)
- Memory usage patterns
- Scalability projections
- Optimization recommendations

## Performance Targets

| Operation | Target | Priority |
|-----------|--------|----------|
| Parse small (1KB) | < 5ms | High |
| Parse medium (50KB) | < 50ms | High |
| Parse large (500KB) | < 500ms | Medium |
| Query section | < 10ms | High |
| BM25 search | < 20ms | High |
| Vector search | < 500ms | Medium |
| Store operation | < 100ms | Medium |

## Interpreting Results

### Benchmark Output

```
Name (time in us)            Min          Max     Mean    StdDev  Median     IQR  Outliers  OPS (Kops/s)  Rounds  Iterations
test_parse_small_file     9.0830  26,659.2500  12.3603  197.3378  9.7500  0.4170   70;1006       80.9042   18335           1
```

**Key Metrics**:
- **Min/Max**: Fastest/slowest execution time
- **Mean**: Average execution time
- **Median**: Middle value (p50)
- **StdDev**: Standard deviation (consistency)
- **OPS**: Operations per second

### Percentiles

pytest-benchmark automatically collects:
- **p50** (Median): 50th percentile
- **p95**: 95th percentile (95% of requests faster)
- **p99**: 99th percentile (99% of requests faster)

### Outliers

Outliers are marked as:
- **1 Standard Deviation** from Mean
- **1.5 IQR** (Interquartile Range) from Q1/Q3

Many outliers indicate inconsistent performance.

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Benchmarks

on: [push, pull_request]

jobs:
  benchmark:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.13'
      - run: pip install -r requirements.txt
      - run: python -m pytest benchmark/bench.py --benchmark-only --benchmark-json=results.json
      - uses: benchmark-action/github-action-benchmark@v1
        with:
          tool: 'pytest'
          output-file-path: results.json
          github-token: ${{ secrets.GITHUB_TOKEN }}
          auto-push: true
```

### Regression Detection

Compare against baseline:

```bash
# Save baseline
python -m pytest benchmark/bench.py --benchmark-only --benchmark-save=baseline

# Check for regression
python -m pytest benchmark/bench.py --benchmark-only --benchmark-compare=baseline
```

## Troubleshooting

### Benchmarks Too Slow

- Reduce `--benchmark-max-time` (default 1.0s)
- Reduce `--benchmark-min-rounds` (default 5)

### Inconsistent Results

- Increase `--benchmark-min-rounds` for more iterations
- Check for background processes
- Ensure consistent machine state

### Memory Benchmarks Fail

- Ensure `tracemalloc` is available
- Check for sufficient memory
- Run with fewer concurrent benchmarks

## Best Practices

1. **Run on consistent hardware** - Results vary by machine
2. **Close other applications** - Reduce background noise
3. **Use warm-up rounds** - Let JIT compilers optimize
4. **Save baselines** - Track performance over time
5. **Automate in CI** - Catch regressions early
6. **Profile before optimizing** - Measure, don't guess

## Contributing

When adding new benchmarks:

1. Follow existing naming patterns
2. Add clear docstrings
3. Set appropriate targets
4. Update this README
5. Run full suite before committing

## Files

- `bench.py` - Main benchmark suite
- `generate_report.py` - Report generator
- `REPORT.md` - Report template
- `baseline_report.md` - Example baseline report
- `README.md` - This file

## License

Same as parent project.
