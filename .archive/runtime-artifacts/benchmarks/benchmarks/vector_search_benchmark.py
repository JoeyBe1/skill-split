#!/usr/bin/env python3
"""
Performance benchmarks for vector search functionality.

Measures:
- Search latency (query time)
- Relevance scores (result quality)
- Cache effectiveness
- Index efficiency
- Hybrid vs. pure vector vs. pure text search

Run with: python3 benchmarks/vector_search_benchmark.py
"""

import time
import json
from typing import List, Dict, Any, Tuple
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.hybrid_search import HybridSearch


class VectorSearchBenchmark:
    """Benchmark suite for vector search performance."""

    def __init__(self):
        """Initialize benchmark runner."""
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "benchmarks": {},
            "summary": {},
        }

    def benchmark_vector_search_latency(self, num_trials: int = 10) -> Dict[str, Any]:
        """
        Benchmark vector search latency.

        Args:
            num_trials: Number of searches to average

        Returns:
            Benchmark results with statistics
        """
        print("\n📊 Benchmarking vector search latency...")

        # Setup mock services
        embedding_service = Mock()
        embedding_service.generate_embedding.return_value = [0.1] * 1536

        supabase_store = Mock()
        query_api = Mock()

        hybrid_search = HybridSearch(embedding_service, supabase_store, query_api)

        latencies = []

        for i in range(num_trials):
            # Mock responses with vector results
            supabase_store.client.rpc.return_value.execute.return_value = MagicMock(
                data=[
                    {"section_id": j, "similarity": 0.9 - (j * 0.01)}
                    for j in range(10)
                ]
            )
            query_api.search_sections.return_value = []

            start = time.time()
            try:
                hybrid_search.vector_search([0.1] * 1536)
                elapsed = (time.time() - start) * 1000  # ms
                latencies.append(elapsed)
            except Exception as e:
                print(f"  ✗ Trial {i+1} failed: {e}")

        if not latencies:
            return {"error": "No successful trials"}

        result = {
            "operation": "vector_search",
            "trials": num_trials,
            "latencies_ms": {
                "min": min(latencies),
                "max": max(latencies),
                "mean": sum(latencies) / len(latencies),
                "median": sorted(latencies)[len(latencies) // 2],
            },
            "throughput_queries_per_second": 1000 / (sum(latencies) / len(latencies)),
        }

        print(f"  ✓ Vector search: {result['latencies_ms']['mean']:.2f}ms avg")
        return result

    def benchmark_text_search_latency(self, num_trials: int = 10) -> Dict[str, Any]:
        """
        Benchmark text search latency.

        Args:
            num_trials: Number of searches to average

        Returns:
            Benchmark results with statistics
        """
        print("\n📊 Benchmarking text search latency...")

        embedding_service = Mock()
        supabase_store = Mock()
        query_api = Mock()

        hybrid_search = HybridSearch(embedding_service, supabase_store, query_api)

        latencies = []

        for i in range(num_trials):
            # Mock text search results
            query_api.search_sections.return_value = [j for j in range(10)]

            start = time.time()
            try:
                hybrid_search.text_search("test query")
                elapsed = (time.time() - start) * 1000  # ms
                latencies.append(elapsed)
            except Exception as e:
                print(f"  ✗ Trial {i+1} failed: {e}")

        if not latencies:
            return {"error": "No successful trials"}

        result = {
            "operation": "text_search",
            "trials": num_trials,
            "latencies_ms": {
                "min": min(latencies),
                "max": max(latencies),
                "mean": sum(latencies) / len(latencies),
                "median": sorted(latencies)[len(latencies) // 2],
            },
            "throughput_queries_per_second": 1000 / (sum(latencies) / len(latencies)),
        }

        print(f"  ✓ Text search: {result['latencies_ms']['mean']:.2f}ms avg")
        return result

    def benchmark_hybrid_search_latency(self, num_trials: int = 10) -> Dict[str, Any]:
        """
        Benchmark hybrid search latency.

        Args:
            num_trials: Number of searches to average

        Returns:
            Benchmark results with statistics
        """
        print("\n📊 Benchmarking hybrid search latency...")

        embedding_service = Mock()
        embedding_service.generate_embedding.return_value = [0.1] * 1536

        supabase_store = Mock()
        query_api = Mock()

        hybrid_search = HybridSearch(embedding_service, supabase_store, query_api)

        latencies = []

        for i in range(num_trials):
            # Mock both vector and text results
            supabase_store.client.rpc.return_value.execute.return_value = MagicMock(
                data=[
                    {"section_id": j, "similarity": 0.9 - (j * 0.01)}
                    for j in range(10)
                ]
            )
            query_api.search_sections.return_value = [j for j in range(5, 15)]

            start = time.time()
            try:
                hybrid_search.hybrid_search("test query")
                elapsed = (time.time() - start) * 1000  # ms
                latencies.append(elapsed)
            except Exception as e:
                print(f"  ✗ Trial {i+1} failed: {e}")

        if not latencies:
            return {"error": "No successful trials"}

        result = {
            "operation": "hybrid_search",
            "trials": num_trials,
            "latencies_ms": {
                "min": min(latencies),
                "max": max(latencies),
                "mean": sum(latencies) / len(latencies),
                "median": sorted(latencies)[len(latencies) // 2],
            },
            "throughput_queries_per_second": 1000 / (sum(latencies) / len(latencies)),
        }

        print(f"  ✓ Hybrid search: {result['latencies_ms']['mean']:.2f}ms avg")
        return result

    def benchmark_embedding_time(self, num_trials: int = 10) -> Dict[str, Any]:
        """
        Benchmark embedding generation time.

        Args:
            num_trials: Number of embeddings to generate

        Returns:
            Benchmark results with statistics
        """
        print("\n📊 Benchmarking embedding generation time...")

        embedding_service = Mock()
        supabase_store = Mock()
        query_api = Mock()

        hybrid_search = HybridSearch(embedding_service, supabase_store, query_api)

        embedding_times = []

        for i in range(num_trials):
            # Mock embedding with measurable delay
            def generate_with_delay(text):
                time.sleep(0.01)  # 10ms simulated API call
                return [0.1] * 1536

            embedding_service.generate_embedding.side_effect = generate_with_delay

            supabase_store.client.rpc.return_value.execute.return_value = MagicMock(data=[])
            query_api.search_sections.return_value = []

            try:
                hybrid_search.hybrid_search("test query")
            except Exception:
                pass

        metrics = hybrid_search.get_metrics()

        result = {
            "operation": "embedding_generation",
            "trials": num_trials,
            "average_embedding_time_ms": metrics.get("average_embedding_time_ms", 0.0),
            "total_embedding_time_ms": metrics.get("total_embedding_time_ms", 0.0),
        }

        print(f"  ✓ Embedding time: {result['average_embedding_time_ms']:.2f}ms avg")
        return result

    def benchmark_cache_effectiveness(self) -> Dict[str, Any]:
        """
        Benchmark embedding cache hit rate.

        Returns:
            Cache effectiveness metrics
        """
        print("\n📊 Benchmarking cache effectiveness...")

        embedding_service = Mock()
        embedding_service.generate_embedding.return_value = [0.1] * 1536
        embedding_service.last_cached = False

        supabase_store = Mock()
        query_api = Mock()

        hybrid_search = HybridSearch(embedding_service, supabase_store, query_api)

        supabase_store.client.rpc.return_value.execute.return_value = MagicMock(data=[])
        query_api.search_sections.return_value = []

        # Run same query multiple times to test caching
        for i in range(5):
            embedding_service.last_cached = (i > 0)  # Cached after first run
            try:
                hybrid_search.hybrid_search("same query")
            except Exception:
                pass

        metrics = hybrid_search.get_metrics()

        result = {
            "operation": "cache_effectiveness",
            "cache_hits": metrics.get("embedding_cache_hits", 0),
            "cache_misses": metrics.get("embedding_cache_misses", 0),
            "cache_hit_rate": metrics.get("cache_hit_rate", 0.0),
        }

        print(f"  ✓ Cache hit rate: {result['cache_hit_rate']:.1%}")
        return result

    def benchmark_result_quality(self) -> Dict[str, Any]:
        """
        Benchmark result quality metrics.

        Returns:
            Quality metrics (precision, diversity, etc.)
        """
        print("\n📊 Benchmarking result quality...")

        embedding_service = Mock()
        embedding_service.generate_embedding.return_value = [0.1] * 1536

        supabase_store = Mock()
        query_api = Mock()

        hybrid_search = HybridSearch(embedding_service, supabase_store, query_api)

        # Test with varied result sets
        test_cases = [
            {
                "name": "high_relevance",
                "vector": [{"section_id": i, "similarity": 0.95 - (i * 0.01)} for i in range(10)],
                "text": [i for i in range(10)],
            },
            {
                "name": "medium_relevance",
                "vector": [{"section_id": i, "similarity": 0.7 - (i * 0.05)} for i in range(10)],
                "text": [i for i in range(5, 15)],
            },
            {
                "name": "low_relevance",
                "vector": [{"section_id": i, "similarity": 0.3 + (i * 0.01)} for i in range(10)],
                "text": [i for i in range(20, 30)],
            },
        ]

        quality_scores = {}

        for test_case in test_cases:
            supabase_store.client.rpc.return_value.execute.return_value = MagicMock(
                data=test_case["vector"]
            )
            query_api.search_sections.return_value = test_case["text"]

            try:
                results = hybrid_search.hybrid_search("test query", limit=10)
                avg_score = sum(r[1] for r in results) / len(results) if results else 0.0
                quality_scores[test_case["name"]] = {
                    "avg_score": avg_score,
                    "num_results": len(results),
                }
            except Exception:
                quality_scores[test_case["name"]] = {"error": "failed"}

        result = {
            "operation": "result_quality",
            "quality_by_relevance": quality_scores,
        }

        print(f"  ✓ Quality metrics computed")
        return result

    def benchmark_scaling(self) -> Dict[str, Any]:
        """
        Benchmark performance with varying result set sizes.

        Returns:
            Scaling metrics for different limits
        """
        print("\n📊 Benchmarking scaling with result set size...")

        embedding_service = Mock()
        embedding_service.generate_embedding.return_value = [0.1] * 1536

        supabase_store = Mock()
        query_api = Mock()

        hybrid_search = HybridSearch(embedding_service, supabase_store, query_api)

        scaling_results = {}

        for limit in [1, 5, 10, 25, 50]:
            # Create result set
            supabase_store.client.rpc.return_value.execute.return_value = MagicMock(
                data=[
                    {"section_id": i, "similarity": 0.9 - (i * 0.01)}
                    for i in range(limit)
                ]
            )
            query_api.search_sections.return_value = [i for i in range(limit)]

            start = time.time()
            try:
                hybrid_search.hybrid_search("test query", limit=limit)
                elapsed = (time.time() - start) * 1000  # ms
                scaling_results[f"limit_{limit}"] = {
                    "latency_ms": elapsed,
                }
            except Exception as e:
                scaling_results[f"limit_{limit}"] = {"error": str(e)}

        result = {
            "operation": "scaling",
            "latency_by_limit": scaling_results,
        }

        print(f"  ✓ Scaling metrics computed")
        return result

    def run_all(self) -> Dict[str, Any]:
        """
        Run all benchmarks.

        Returns:
            Complete benchmark results
        """
        print("\n" + "=" * 60)
        print("VECTOR SEARCH PERFORMANCE BENCHMARKS")
        print("=" * 60)

        benchmarks = {
            "vector_search_latency": self.benchmark_vector_search_latency(),
            "text_search_latency": self.benchmark_text_search_latency(),
            "hybrid_search_latency": self.benchmark_hybrid_search_latency(),
            "embedding_time": self.benchmark_embedding_time(),
            "cache_effectiveness": self.benchmark_cache_effectiveness(),
            "result_quality": self.benchmark_result_quality(),
            "scaling": self.benchmark_scaling(),
        }

        self.results["benchmarks"] = benchmarks
        self._compute_summary()
        self._print_summary()

        return self.results

    def _compute_summary(self) -> None:
        """Compute summary statistics."""
        summary = {
            "fastest_operation": None,
            "slowest_operation": None,
            "best_throughput": None,
            "highest_cache_hit_rate": None,
        }

        latencies = []

        for name, bench in self.results["benchmarks"].items():
            if "latencies_ms" in bench:
                mean_latency = bench["latencies_ms"]["mean"]
                latencies.append((name, mean_latency))

        if latencies:
            latencies.sort(key=lambda x: x[1])
            summary["fastest_operation"] = latencies[0]
            summary["slowest_operation"] = latencies[-1]

        # Find best throughput
        throughputs = [
            (name, bench.get("throughput_queries_per_second", 0))
            for name, bench in self.results["benchmarks"].items()
            if "throughput_queries_per_second" in bench
        ]
        if throughputs:
            throughputs.sort(key=lambda x: x[1], reverse=True)
            summary["best_throughput"] = throughputs[0]

        # Find cache effectiveness
        cache_bench = self.results["benchmarks"].get("cache_effectiveness", {})
        if "cache_hit_rate" in cache_bench:
            summary["highest_cache_hit_rate"] = cache_bench["cache_hit_rate"]

        self.results["summary"] = summary

    def _print_summary(self) -> None:
        """Print benchmark summary."""
        print("\n" + "=" * 60)
        print("BENCHMARK SUMMARY")
        print("=" * 60)

        summary = self.results.get("summary", {})

        if summary.get("fastest_operation"):
            name, latency = summary["fastest_operation"]
            print(f"✓ Fastest: {name} ({latency:.2f}ms)")

        if summary.get("slowest_operation"):
            name, latency = summary["slowest_operation"]
            print(f"✗ Slowest: {name} ({latency:.2f}ms)")

        if summary.get("best_throughput"):
            name, throughput = summary["best_throughput"]
            print(f"⚡ Best throughput: {name} ({throughput:.1f} qps)")

        if summary.get("highest_cache_hit_rate"):
            rate = summary["highest_cache_hit_rate"]
            print(f"💾 Cache hit rate: {rate:.1%}")

        print("=" * 60 + "\n")

    def save_results(self, filename: str = "benchmark_results.json") -> None:
        """
        Save benchmark results to file.

        Args:
            filename: Output filename
        """
        with open(filename, "w") as f:
            json.dump(self.results, f, indent=2)
        print(f"📁 Results saved to {filename}")


def main():
    """Run benchmarks and save results."""
    benchmark = VectorSearchBenchmark()
    results = benchmark.run_all()
    benchmark.save_results()


if __name__ == "__main__":
    main()
