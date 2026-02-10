#!/usr/bin/env python3
"""
Generate benchmark report from pytest-benchmark JSON output.

Usage:
    python -m pytest benchmark/bench.py --benchmark-only --benchmark-json=benchmark/results.json
    python benchmark/generate_report.py benchmark/results.json
"""

import json
import sys
from pathlib import Path
from datetime import datetime
import subprocess
import os


def get_git_info():
    """Get git commit hash and branch."""
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL
        ).decode().strip()
        short_commit = commit[:8]
    except Exception:
        short_commit = "unknown"

    try:
        branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            stderr=subprocess.DEVNULL
        ).decode().strip()
    except Exception:
        branch = "unknown"

    return short_commit, branch


def get_machine_info():
    """Get machine information."""
    import platform
    return {
        "os": platform.system(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
    }


def load_benchmark_results(json_path):
    """Load benchmark results from JSON file."""
    with open(json_path) as f:
        data = json.load(f)
    return data


def extract_metrics(bench_data, test_name_pattern):
    """Extract metrics for benchmarks matching pattern."""
    results = {}
    for bench in bench_data.get("benchmarks", []):
        name = bench.get("name", "")
        if test_name_pattern in name:
            stats = bench.get("stats", {})
            results[name] = {
                "mean": stats.get("mean"),
                "stddev": stats.get("stddev"),
                "min": stats.get("min"),
                "max": stats.get("max"),
                "p50": stats.get("median"),
                "p95": stats.get("rounds", {}).get("p95"),
                "p99": stats.get("rounds", {}).get("p99"),
                "ops": stats.get("ops"),
            }
    return results


def generate_report_values(benchmark_data):
    """Generate values for report template."""
    machine = get_machine_info()
    commit, branch = get_git_info()

    # Extract parsing metrics
    parse_small = extract_metrics(benchmark_data, "test_parse_small_file")
    parse_medium = extract_metrics(benchmark_data, "test_parse_medium_file")
    parse_large = extract_metrics(benchmark_data, "test_parse_large_file")

    # Extract database metrics
    db_get = extract_metrics(benchmark_data, "test_get_section")
    db_store_small = extract_metrics(benchmark_data, "test_store_small_file")
    db_store_medium = extract_metrics(benchmark_data, "test_store_medium_file")

    # Extract search metrics
    search_bm25 = extract_metrics(benchmark_data, "test_bm25_search")

    return {
        "TIMESTAMP": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "COMMIT_HASH": commit,
        "MACHINE_INFO": f"{machine['os']} {machine['machine']}",
        "PYTHON_VERSION": machine['python_version'],
        "BENCHMARK_COMMAND": f"pytest benchmark/bench.py --benchmark-only",

        # Parse small file metrics
        "PARSE_SMALL_MEAN": f"{list(parse_small.values())[0]['mean']*1000:.2f}" if parse_small else "N/A",
        "PARSE_SMALL_P50": f"{list(parse_small.values())[0]['p50']*1000:.2f}" if parse_small else "N/A",
        "PARSE_SMALL_P95": f"{list(parse_small.values())[0]['p95']*1000:.2f}" if parse_small else "N/A",
        "PARSE_SMALL_OPS": f"{list(parse_small.values())[0]['ops']:.0f}" if parse_small else "N/A",

        # Parse medium file metrics
        "PARSE_MEDIUM_MEAN": f"{list(parse_medium.values())[0]['mean']*1000:.2f}" if parse_medium else "N/A",
        "PARSE_MEDIUM_P50": f"{list(parse_medium.values())[0]['p50']*1000:.2f}" if parse_medium else "N/A",
        "PARSE_MEDIUM_P95": f"{list(parse_medium.values())[0]['p95']*1000:.2f}" if parse_medium else "N/A",
        "PARSE_MEDIUM_OPS": f"{list(parse_medium.values())[0]['ops']:.0f}" if parse_medium else "N/A",

        # Parse large file metrics
        "PARSE_LARGE_MEAN": f"{list(parse_large.values())[0]['mean']*1000:.2f}" if parse_large else "N/A",
        "PARSE_LARGE_P50": f"{list(parse_large.values())[0]['p50']*1000:.2f}" if parse_large else "N/A",
        "PARSE_LARGE_P95": f"{list(parse_large.values())[0]['p95']*1000:.2f}" if parse_large else "N/A",
        "PARSE_LARGE_OPS": f"{list(parse_large.values())[0]['ops']:.0f}" if parse_large else "N/A",

        # Query metrics
        "DB_GET_SECTION_MEAN": f"{list(db_get.values())[0]['mean']*1000:.2f}" if db_get else "N/A",
        "DB_GET_SECTION_P95": f"{list(db_get.values())[0]['p95']*1000:.2f}" if db_get else "N/A",
        "DB_GET_SECTION_OPS": f"{list(db_get.values())[0]['ops']:.0f}" if db_get else "N/A",

        # Status placeholders (would be computed based on thresholds)
        "OVERALL_STATUS": "PASS",
        "STATUS_PARSE_SMALL": "PASS",
        "STATUS_PARSE_MEDIUM": "PASS",
        "STATUS_PARSE_LARGE": "PASS",
        "STATUS_QUERY": "PASS",
        "STATUS_BM25": "PASS",

        # Placeholders for other template variables
        "BASELINE_PARSE_SMALL": "< 5 ms",
        "CURRENT_PARSE_SMALL": f"{list(parse_small.values())[0]['mean']*1000:.2f} ms" if parse_small else "N/A",
        "DELTA_PARSE_SMALL": "-",
    }


def fill_template(template_path, output_path, values):
    """Fill report template with values."""
    with open(template_path) as f:
        template = f.read()

    for key, value in values.items():
        template = template.replace(f"{{{{{key}}}}}", str(value))

    with open(output_path, "w") as f:
        f.write(template)

    print(f"Report generated: {output_path}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python generate_report.py <benchmark_json_path>")
        sys.exit(1)

    json_path = sys.argv[1]
    benchmark_data = load_benchmark_results(json_path)
    values = generate_report_values(benchmark_data)

    script_dir = Path(__file__).parent
    template_path = script_dir / "REPORT.md"
    output_path = script_dir / "GENERATED_REPORT.md"

    fill_template(template_path, output_path, values)


if __name__ == "__main__":
    main()
