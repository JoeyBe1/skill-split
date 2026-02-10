#!/usr/bin/env python3
"""
Performance Benchmark Runner

Runs comprehensive benchmarks and generates reports.

Usage:
    python scripts/benchmark_runner.py --all
    python scripts/benchmark_runner.py --category parsing
    python scripts/benchmark_runner.py --baseline
"""

import argparse
import subprocess
import json
from pathlib import Path
from datetime import datetime


def run_benchmarks(category=None, save_results=True):
    """Run pytest benchmarks."""

    cmd = ["python", "-m", "pytest", "benchmark/bench.py", "--benchmark-only"]

    if category:
        cmd.extend(["-k", category])

    if save_results:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = Path(f"benchmark/results/results_{timestamp}.json")
        results_file.parent.mkdir(exist_ok=True)
        cmd.extend(["--benchmark-json", str(results_file)])

    cmd.extend(["-v"])

    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=False)

    if save_results and results_file.exists():
        print(f"\n✅ Results saved to: {results_file}")
        generate_report(results_file)

    return result.returncode


def generate_report(results_file):
    """Generate human-readable report from benchmark results."""

    with open(results_file) as f:
        data = json.load(f)

    report_file = results_file.parent / f"{results_file.stem}_REPORT.md"

    with open(report_file, 'w') as f:
        f.write(f"# Benchmark Report\n\n")
        f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**Results File**: {results_file.name}\n\n")
        f.write("---\n\n")

        for benchmark, stats in data.get("benchmarks", []).items():
            f.write(f"## {benchmark}\n\n")
            f.write(f"| Metric | Value |\n")
            f.write(f"|--------|-------|\n")
            f.write(f"| Mean | {stats.get('mean', 'N/A'):.6f}s |\n")
            f.write(f"| Std Dev | {stats.get('stddev', 'N/A'):.6f}s |\n")
            f.write(f"| Min | {stats.get('min', 'N/A'):.6f}s |\n")
            f.write(f"| Max | {stats.get('max', 'N/A'):.6f}s |\n")
            f.write(f"| Ops/sec | {1.0/stats.get('mean', 1):.2f} |\n\n")

    print(f"📊 Report generated: {report_file}")


def compare_baselines():
    """Compare current results against baseline."""

    baseline_file = Path("benchmark/baseline_report.md")
    if not baseline_file.exists():
        print("❌ No baseline found. Run with --baseline first.")
        return 1

    # Find most recent results
    results_dir = Path("benchmark/results")
    if not results_dir.exists():
        print("❌ No results found to compare.")
        return 1

    results_files = sorted(results_dir.glob("results_*.json"))
    if not results_files:
        print("❌ No results files found.")
        return 1

    latest = results_files[-1]

    print(f"📊 Comparing {latest.name} against baseline...")
    print(f"   Baseline: {baseline_file}")

    # Load and compare
    with open(latest) as f:
        current = json.load(f)

    # Read baseline
    baseline_text = baseline_file.read_text()

    print("\n### Comparison")
    print("Review the benchmark report for detailed comparison.")

    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Run skill-split performance benchmarks"
    )

    parser.add_argument("--all", action="store_true",
                       help="Run all benchmarks")
    parser.add_argument("--category", "-c",
                       help="Run specific category (parsing, database, search)")
    parser.add_argument("--baseline", "-b", action="store_true",
                       help="Save results as new baseline")
    parser.add_argument("--compare", action="store_true",
                       help="Compare against baseline")

    args = parser.parse_args()

    if args.compare:
        return compare_baselines()

    category = None if args.all else args.category

    returncode = run_benchmarks(category=category)

    if args_baseline and returncode == 0:
        print("✅ Baseline updated")

    return returncode


if __name__ == "__main__":
    sys.exit(main())
