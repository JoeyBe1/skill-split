#!/usr/bin/env python3
"""
Monitor embedding usage and costs for vector search integration.

Tracks:
- Embedded sections count
- Total tokens used
- Estimated cost
- Failed embeddings
- Embedding generation rate
"""

import os
import sys
import json
from datetime import datetime, timedelta
from typing import Dict, Tuple, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class EmbeddingMonitor:
    """Monitor and report on embedding metrics and costs."""

    def __init__(self, supabase_url: str = None, supabase_key: str = None):
        """Initialize embedding monitor.

        Args:
            supabase_url: Supabase project URL
            supabase_key: Supabase API key
        """
        self.supabase_url = supabase_url or os.getenv('SUPABASE_URL')
        self.supabase_key = supabase_key or os.getenv('SUPABASE_KEY')

        # Cost constants
        self.cost_per_1k_tokens = 0.00002  # text-embedding-3-small
        self.tokens_per_section = 100  # Average estimate

        # Initialize Supabase if credentials available
        self.supabase_client = None
        if self.supabase_url and self.supabase_key:
            try:
                from supabase import create_client
                self.supabase_client = create_client(self.supabase_url, self.supabase_key)
            except ImportError:
                print("⚠️  Supabase client not installed. Install with: pip install supabase")

    def get_embedding_stats(self) -> Dict[str, Any]:
        """Fetch embedding statistics from Supabase.

        Returns:
            Dictionary with embedding metrics or None if unavailable
        """
        if not self.supabase_client:
            return self._get_demo_stats()

        try:
            # Get total sections
            sections_response = self.supabase_client.table('sections').select('COUNT(*)').execute()
            total_sections = sections_response.count if hasattr(sections_response, 'count') else 0

            # Get embedded sections count
            embeddings_response = self.supabase_client.table('section_embeddings').select('COUNT(*)').execute()
            embedded_sections = embeddings_response.count if hasattr(embeddings_response, 'count') else 0

            # Get embedding metadata (if exists)
            metadata_response = self.supabase_client.table('embedding_metadata').select('*').execute()
            metadata = metadata_response.data[0] if metadata_response.data else {}

            return {
                'total_sections': total_sections,
                'embedded_sections': embedded_sections,
                'failed_embeddings': metadata.get('failed_sections', 0),
                'total_tokens_used': metadata.get('total_tokens_used', 0),
                'estimated_cost_usd': metadata.get('estimated_cost_usd', 0.0),
                'last_batch_at': metadata.get('last_batch_at', 'Never'),
                'coverage_percent': (embedded_sections / total_sections * 100) if total_sections > 0 else 0
            }
        except Exception as e:
            print(f"⚠️  Error fetching embedding stats: {e}")
            return self._get_demo_stats()

    def _get_demo_stats(self) -> Dict[str, Any]:
        """Return demo statistics for testing without Supabase.

        Returns:
            Dictionary with sample metrics
        """
        return {
            'total_sections': 19207,
            'embedded_sections': 0,
            'failed_embeddings': 0,
            'total_tokens_used': 0,
            'estimated_cost_usd': 0.0,
            'last_batch_at': 'Never',
            'coverage_percent': 0.0
        }

    def calculate_batch_cost(self, section_count: int) -> Tuple[int, float]:
        """Calculate tokens and cost for embedding sections.

        Args:
            section_count: Number of sections to embed

        Returns:
            Tuple of (tokens_needed, cost_usd)
        """
        tokens = section_count * self.tokens_per_section
        cost = (tokens / 1000) * self.cost_per_1k_tokens
        return tokens, cost

    def estimate_monthly_cost(self, new_sections_per_month: int = 50) -> float:
        """Estimate monthly embedding cost.

        Args:
            new_sections_per_month: Expected new sections per month (default: 50)

        Returns:
            Estimated monthly cost in USD
        """
        tokens = new_sections_per_month * self.tokens_per_section
        return (tokens / 1000) * self.cost_per_1k_tokens

    def estimate_query_cost(self, queries_per_month: int = 3000) -> float:
        """Estimate monthly query cost.

        Args:
            queries_per_month: Expected queries per month (default: 3000)

        Returns:
            Estimated monthly cost in USD
        """
        # Each query embeds the query text (~20 tokens) + vector search (no cost)
        tokens = queries_per_month * 20  # Query text is small
        return (tokens / 1000) * self.cost_per_1k_tokens

    def format_cost(self, cost: float) -> str:
        """Format cost as currency string.

        Args:
            cost: Cost in USD

        Returns:
            Formatted currency string
        """
        if cost < 0.01:
            return f"${cost:.4f}"
        return f"${cost:.2f}"

    def print_summary(self, stats: Dict[str, Any] = None):
        """Print formatted summary of embedding metrics.

        Args:
            stats: Statistics dictionary (fetches if not provided)
        """
        if stats is None:
            stats = self.get_embedding_stats()

        print("\n" + "=" * 70)
        print("EMBEDDING MONITORING REPORT")
        print("=" * 70)
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        # Section Coverage
        print("📊 SECTION COVERAGE")
        print(f"  Total Sections:      {stats['total_sections']:>10,}")
        print(f"  Embedded Sections:   {stats['embedded_sections']:>10,}")
        print(f"  Coverage:            {stats['coverage_percent']:>10.1f}%")
        if stats['failed_embeddings'] > 0:
            print(f"  Failed Embeddings:   {stats['failed_embeddings']:>10,} ⚠️")
        print()

        # Token Usage
        print("🔤 TOKEN USAGE")
        total_tokens = stats['total_tokens_used']
        print(f"  Total Tokens Used:   {total_tokens:>10,}")
        if total_tokens > 0:
            avg_tokens = total_tokens / max(1, stats['embedded_sections'])
            print(f"  Avg per Section:     {avg_tokens:>10.0f}")
        print()

        # Costs
        print("💰 COST ANALYSIS")
        current_cost = stats['estimated_cost_usd']
        print(f"  Current Cost:        {self.format_cost(current_cost):>10}")

        # Projected costs
        monthly_new = self.estimate_monthly_cost(50)
        monthly_query = self.estimate_query_cost(3000)
        monthly_total = monthly_new + monthly_query

        print(f"  Monthly (50 new):    {self.format_cost(monthly_new):>10}")
        print(f"  Monthly (3K queries):{self.format_cost(monthly_query):>10}")
        print(f"  Monthly Total:       {self.format_cost(monthly_total):>10}")

        # ROI
        if stats['embedded_sections'] > 0 and stats['estimated_cost_usd'] > 0:
            cost_per_section = stats['estimated_cost_usd'] / stats['embedded_sections']
            print(f"  Cost/Section:        {self.format_cost(cost_per_section):>10}")
        print()

        # Status
        print("⏱️  TIMING")
        print(f"  Last Batch:          {stats['last_batch_at']:>20}")
        print()

        # Recommendations
        print("📋 RECOMMENDATIONS")
        if stats['coverage_percent'] < 50:
            print("  • Run initial batch embedding to reach 100% coverage")
            tokens, cost = self.calculate_batch_cost(stats['total_sections'] - stats['embedded_sections'])
            print(f"    Estimated cost: {self.format_cost(cost)} for {tokens:,} tokens")
        elif stats['coverage_percent'] < 100:
            remaining = stats['total_sections'] - stats['embedded_sections']
            tokens, cost = self.calculate_batch_cost(remaining)
            print(f"  • {remaining:,} sections still need embeddings ({self.format_cost(cost)})")
        else:
            print("  ✓ All sections have embeddings - vector search fully operational")

        if stats['failed_embeddings'] > 0:
            print(f"  ⚠️  {stats['failed_embeddings']} failed embeddings - investigate and retry")

        if monthly_total < 0.05:
            print("  ✓ Monthly cost is negligible - no action needed")
        elif monthly_total < 0.20:
            print("  ✓ Monthly cost is reasonable - continue monitoring")
        else:
            print("  ⚠️  Monthly cost exceeds budget - review usage patterns")

        print()
        print("=" * 70)

    def print_batch_estimate(self, section_count: int):
        """Print cost estimate for batch embedding.

        Args:
            section_count: Number of sections to embed
        """
        tokens, cost = self.calculate_batch_cost(section_count)

        print("\n" + "=" * 70)
        print("BATCH EMBEDDING COST ESTIMATE")
        print("=" * 70)
        print(f"Sections to Embed:   {section_count:>10,}")
        print(f"Tokens Needed:       {tokens:>10,} (avg {self.tokens_per_section}/section)")
        print(f"Estimated Cost:      {self.format_cost(cost):>10}")
        print("=" * 70)
        print()


def main():
    """Main entry point for monitoring script."""
    import argparse

    parser = argparse.ArgumentParser(description='Monitor embedding usage and costs')
    parser.add_argument('--estimate', type=int, metavar='N',
                       help='Estimate cost for embedding N sections')
    parser.add_argument('--monthly-sections', type=int, default=50,
                       help='Expected new sections per month (default: 50)')
    parser.add_argument('--monthly-queries', type=int, default=3000,
                       help='Expected queries per month (default: 3000)')
    parser.add_argument('--json', action='store_true',
                       help='Output stats as JSON')

    args = parser.parse_args()

    # Initialize monitor
    monitor = EmbeddingMonitor()

    # Handle batch estimate
    if args.estimate:
        monitor.print_batch_estimate(args.estimate)
        return 0

    # Get and display stats
    stats = monitor.get_embedding_stats()

    if args.json:
        # JSON output mode
        output = {
            **stats,
            'timestamp': datetime.now().isoformat(),
            'monthly_cost_estimate': monitor.estimate_monthly_cost(args.monthly_sections),
            'monthly_query_cost': monitor.estimate_query_cost(args.monthly_queries)
        }
        print(json.dumps(output, indent=2))
    else:
        # Formatted output mode
        monitor.print_summary(stats)

        # Show monthly projections
        print("📈 MONTHLY PROJECTIONS")
        print(f"  New Sections/Month:  {args.monthly_sections:>10}")
        monthly_new = monitor.estimate_monthly_cost(args.monthly_sections)
        print(f"  Embedding Cost:      {monitor.format_cost(monthly_new):>10}")

        monthly_query = monitor.estimate_query_cost(args.monthly_queries)
        print(f"  Queries/Month:       {args.monthly_queries:>10}")
        print(f"  Query Cost:          {monitor.format_cost(monthly_query):>10}")

        total_monthly = monthly_new + monthly_query
        print(f"  Total Monthly:       {monitor.format_cost(total_monthly):>10}")
        print()

    return 0


if __name__ == '__main__':
    sys.exit(main())
