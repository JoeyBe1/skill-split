"""Benchmark suite for skill-split performance testing.

Run benchmarks with:
    pytest benchmark/bench.py --benchmark-only

Generate report with:
    pytest benchmark/bench.py --benchmark-only --benchmark-json=benchmark/results.json
"""

# Benchmark configuration
BENCHMARK_ITERATIONS = {
    "small": 1000,   # <1KB files
    "medium": 100,   # 10KB files
    "large": 10,     # 100KB files
}

BENCHMARK_OUTPUT = "benchmark/results"
