#!/usr/bin/env python3
"""
skill-split Cost Estimation Tool

Estimates OpenAI API costs for embeddings based on database size.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Pricing (as of 2025)
PRICING = {
    "text-embedding-3-small": 0.02,  # per 1M tokens
    "text-embedding-3-large": 0.13,
    "ada-002": 0.10,
}

AVG_SECTION_TOKENS = 150  # Average tokens per section


def estimate_embedding_cost(
    num_sections: int,
    model: str = "text-embedding-3-small"
) -> dict:
    """
    Estimate embedding costs for a database.

    Returns:
        dict with cost breakdown
    """
    if model not in PRICING:
        raise ValueError(f"Unknown model: {model}")

    price_per_m = PRICING[model]

    # Calculate total tokens
    total_tokens = num_sections * AVG_SECTION_TOKENS

    # Calculate cost
    cost_usd = (total_tokens / 1_000_000) * price_per_m

    return {
        "num_sections": num_sections,
        "model": model,
        "avg_tokens_per_section": AVG_SECTION_TOKENS,
        "total_tokens": total_tokens,
        "price_per_m_tokens": price_per_m,
        "cost_one_time": cost_usd,
        "cost_annual": cost_usd,  # embeddings are cached
    }


def print_comparison(num_sections: int):
    """Print cost comparison across models."""
    print(f"\nCost comparison for {num_sections:,} sections:")
    print("=" * 60)

    for model in PRICING.keys():
        est = estimate_embedding_cost(num_sections, model)
        print(f"\n{model}:")
        print(f"  One-time cost: ${est['cost_one_time']:.4f}")
        print(f"  Annual cost:   ${est['cost_annual']:.4f} (cached)")


def print_breakdown(est: dict):
    """Print detailed cost breakdown."""
    print("\n" + "=" * 60)
    print("EMBEDDING COST ESTIMATE")
    print("=" * 60)
    print(f"\nDatabase Size:")
    print(f"  Sections:       {est['num_sections']:,}")
    print(f"  Avg tokens/sec: {est['avg_tokens_per_section']}")
    print(f"  Total tokens:   {est['total_tokens']:,}")

    print(f"\nModel: {est['model']}")
    print(f"  Price: ${est['price_per_m_tokens']:.2f} per 1M tokens")

    print(f"\nCost:")
    print(f"  One-time: ${est['cost_one_time']:.4f}")
    print(f"  Annual:   ${est['cost_annual']:.4f} (with caching)")

    print("\n" + "=" * 60)

    # Show what you get for the cost
    print("\nValue per dollar:")
    if est['cost_one_time'] > 0:
        sections_per_dollar = int(est['num_sections'] / est['cost_one_time'])
        print(f"  {sections_per_dollar:,} sections per dollar")

    # Show token efficiency
    print("\nToken efficiency:")
    search_tokens = 10  # tokens for query embedding
    searches_per_dollar = int(1_000_000 / (search_tokens * est['price_per_m_tokens']))
    print(f"  {searches_per_dollar:,} searches per dollar (without caching)")


def main():
    """Run cost estimation."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Estimate OpenAI embedding costs for skill-split"
    )
    parser.add_argument(
        "sections",
        type=int,
        nargs="?",
        help="Number of sections in database"
    )
    parser.add_argument(
        "--model",
        choices=list(PRICING.keys()),
        default="text-embedding-3-small",
        help="Embedding model to use (default: text-embedding-3-small)"
    )
    parser.add_argument(
        "--compare",
        action="store_true",
        help="Compare all models"
    )
    parser.add_argument(
        "--database",
        help="Analyze existing database"
    )

    args = parser.parse_args()

    # Get section count
    if args.database:
        from core.database import Database
        db = Database(args.database)
        num_sections = len(db.list_sections())
        print(f"\nAnalyzing database: {args.database}")
        print(f"Found {num_sections:,} sections")
    elif args.sections:
        num_sections = args.sections
    else:
        # Default examples
        print("\nNo section count provided. Using examples:\n")
        for size in [100, 1000, 10000]:
            est = estimate_embedding_cost(size, args.model)
            print(f"{size:,} sections: ${est['cost_one_time']:.4f}")
        print("\nUse --sections N or --database PATH for specific estimates.")
        print("Use --compare to see all models.")
        return

    # Print comparison if requested
    if args.compare:
        print_comparison(num_sections)
        return

    # Print detailed breakdown
    est = estimate_embedding_cost(num_sections, args.model)
    print_breakdown(est)


if __name__ == "__main__":
    main()
