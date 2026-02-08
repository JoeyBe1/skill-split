#!/usr/bin/env python3
"""
Generate embeddings for all existing sections in Supabase.

This script performs batch embedding generation for all sections in the
database, tracking progress, cost, and any failures. It's designed to be
run once to initialize the vector search system and can be resumed if
interrupted.

Features:
- Batch processing (100 sections at a time)
- Progress tracking and resumable processing
- Cost estimation and tracking
- Error handling and failure reporting
- Cache awareness to skip already-embedded sections
"""

import os
import sys
import json
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from core.supabase_store import SupabaseStore
from core.embedding_service import EmbeddingService
from core.database import DatabaseStore


class EmbeddingMigration:
    """Manages batch embedding generation and migration."""

    def __init__(self, supabase_store: SupabaseStore, embedding_service: EmbeddingService):
        """
        Initialize migration manager.

        Args:
            supabase_store: SupabaseStore instance for database access
            embedding_service: EmbeddingService for generating embeddings
        """
        self.supabase_store = supabase_store
        self.embedding_service = embedding_service
        self.stats = {
            "total_sections": 0,
            "already_embedded": 0,
            "newly_embedded": 0,
            "failed_sections": [],
            "total_tokens_used": 0,
            "start_time": None,
            "end_time": None,
            "estimated_cost_usd": 0.0,
        }

    def count_uneeded_embeddings(self) -> int:
        """
        Count sections that need embeddings generated.

        Returns:
            Number of sections without embeddings
        """
        try:
            result = self.supabase_store.client.table('sections').select(
                'id',
                count='exact'
            ).execute()

            total = result.count if hasattr(result, 'count') else len(result.data or [])
            return total

        except Exception as e:
            print(f"Error counting sections: {e}")
            return 0

    def get_uneeded_sections(self, batch_size: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get sections that need embeddings in batches.

        Args:
            batch_size: Number of sections per batch
            offset: Starting offset for pagination

        Returns:
            List of section dictionaries with id, content, content_hash
        """
        try:
            result = self.supabase_store.client.table('sections').select(
                'id, content, content_hash'
            ).range(offset, offset + batch_size - 1).execute()

            return result.data or []

        except Exception as e:
            print(f"Error fetching sections: {e}")
            return []

    def check_existing_embeddings(self, section_ids: List[int]) -> Dict[int, bool]:
        """
        Check which sections already have embeddings.

        Args:
            section_ids: List of section IDs to check

        Returns:
            Dictionary mapping section_id to has_embedding (bool)
        """
        try:
            result = self.supabase_store.client.table('section_embeddings').select(
                'section_id'
            ).in_('section_id', section_ids).execute()

            embedded_ids = {row['section_id'] for row in (result.data or [])}
            return {sid: sid in embedded_ids for sid in section_ids}

        except Exception as e:
            print(f"Error checking existing embeddings: {e}")
            return {sid: False for sid in section_ids}

    def generate_batch_embeddings(self, sections: List[Dict[str, Any]]) -> List[tuple]:
        """
        Generate embeddings for a batch of sections.

        Args:
            sections: List of section dictionaries

        Returns:
            List of (section_id, embedding) tuples
        """
        embeddings = []

        for section in sections:
            try:
                section_id = section['id']
                content = section.get('content', '')

                # Skip empty content
                if not content or not content.strip():
                    print(f"⊘ Skipping section {section_id}: empty content")
                    continue

                # Generate embedding
                embedding = self.embedding_service.generate_embedding(content)
                embeddings.append((section_id, embedding))

                # Estimate tokens (roughly 1 token per 4 characters)
                tokens = len(content) // 4
                self.stats["total_tokens_used"] += tokens

                print(f"✓ Embedded section {section_id} ({tokens} tokens)")

            except Exception as e:
                print(f"✗ Failed to embed section {section['id']}: {e}")
                self.stats["failed_sections"].append({
                    "section_id": section['id'],
                    "error": str(e)
                })

        return embeddings

    def store_embeddings_batch(self, embeddings: List[tuple]) -> int:
        """
        Store batch of embeddings to Supabase.

        Args:
            embeddings: List of (section_id, embedding) tuples

        Returns:
            Number of successfully stored embeddings
        """
        stored_count = 0

        for section_id, embedding in embeddings:
            try:
                result = self.supabase_store.client.table('section_embeddings').insert({
                    'section_id': section_id,
                    'embedding': embedding,
                    'model_name': self.embedding_service.model,
                }).execute()

                stored_count += 1
                self.stats["newly_embedded"] += 1

            except Exception as e:
                # If embedding already exists, count as existing
                if "unique" in str(e).lower() or "duplicate" in str(e).lower():
                    self.stats["already_embedded"] += 1
                else:
                    print(f"Error storing embedding for section {section_id}: {e}")

        return stored_count

    def calculate_cost(self) -> float:
        """
        Calculate estimated cost based on tokens used.

        OpenAI text-embedding-3-small pricing: $0.02 per 1M tokens
        """
        cost = (self.stats["total_tokens_used"] / 1_000_000) * 0.02
        return cost

    def update_metadata(self) -> None:
        """Update embedding metadata in database."""
        try:
            metadata = {
                'total_sections': self.stats["total_sections"],
                'embedded_sections': self.stats["newly_embedded"] + self.stats["already_embedded"],
                'last_batch_at': datetime.now().isoformat(),
                'total_tokens_used': self.stats["total_tokens_used"],
                'estimated_cost_usd': self.stats["estimated_cost_usd"],
            }

            # Try to update existing metadata, or create new record
            self.supabase_store.client.table('embedding_metadata').upsert(metadata).execute()

        except Exception as e:
            print(f"Warning: Could not update metadata: {e}")

    def run(self, resume_from: int = 0) -> Dict[str, Any]:
        """
        Execute the embedding migration.

        Args:
            resume_from: Section offset to resume from (for resuming interrupted runs)

        Returns:
            Dictionary with migration statistics
        """
        print("\n" + "=" * 60)
        print("EMBEDDING MIGRATION - Generating embeddings for all sections")
        print("=" * 60 + "\n")

        self.stats["start_time"] = datetime.now().isoformat()

        try:
            # Get total count
            total = self.count_uneeded_embeddings()
            self.stats["total_sections"] = total
            print(f"📊 Total sections to process: {total}")
            print(f"📊 Starting from offset: {resume_from}\n")

            batch_size = 100
            processed = 0
            offset = resume_from

            while offset < total:
                print(f"\n📦 Processing batch: {offset}-{min(offset + batch_size, total)} / {total}")

                # Fetch sections
                sections = self.get_uneeded_sections(batch_size, offset)
                if not sections:
                    break

                section_ids = [s['id'] for s in sections]

                # Check which ones already have embeddings
                existing = self.check_existing_embeddings(section_ids)
                sections_to_embed = [s for s in sections if not existing.get(s['id'], False)]

                self.stats["already_embedded"] += len(section_ids) - len(sections_to_embed)

                if sections_to_embed:
                    # Generate embeddings
                    embeddings = self.generate_batch_embeddings(sections_to_embed)

                    # Store embeddings
                    stored = self.store_embeddings_batch(embeddings)
                    print(f"💾 Stored {stored} embeddings in this batch")
                else:
                    print(f"⊘ All {len(section_ids)} sections in this batch already embedded")

                processed += len(sections)
                offset += batch_size

                # Small delay to avoid rate limiting
                time.sleep(1)

            # Calculate cost and update stats
            self.stats["estimated_cost_usd"] = self.calculate_cost()
            self.stats["end_time"] = datetime.now().isoformat()

            # Update metadata in database
            self.update_metadata()

            # Print summary
            self._print_summary()

            return self.stats

        except Exception as e:
            print(f"\n❌ Migration failed: {e}")
            self.stats["end_time"] = datetime.now().isoformat()
            raise

    def _print_summary(self) -> None:
        """Print migration summary."""
        print("\n" + "=" * 60)
        print("MIGRATION SUMMARY")
        print("=" * 60)
        print(f"✓ Total sections processed: {self.stats['total_sections']}")
        print(f"✓ Newly embedded: {self.stats['newly_embedded']}")
        print(f"✓ Already embedded: {self.stats['already_embedded']}")
        print(f"✗ Failed: {len(self.stats['failed_sections'])}")
        print(f"📊 Total tokens used: {self.stats['total_tokens_used']:,}")
        print(f"💰 Estimated cost: ${self.stats['estimated_cost_usd']:.4f}")
        print(f"⏱ Duration: {self._calculate_duration()}")
        print("=" * 60 + "\n")

        if self.stats["failed_sections"]:
            print("Failed sections:")
            for failure in self.stats["failed_sections"]:
                print(f"  - Section {failure['section_id']}: {failure['error']}")
            print()

    def _calculate_duration(self) -> str:
        """Calculate and format duration."""
        if self.stats["start_time"] and self.stats["end_time"]:
            start = datetime.fromisoformat(self.stats["start_time"])
            end = datetime.fromisoformat(self.stats["end_time"])
            duration = end - start
            return str(duration).split('.')[0]
        return "N/A"


def main():
    """Main entry point."""
    load_dotenv()

    # Check required environment variables
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    if not all([supabase_url, supabase_key, openai_key]):
        print("Error: Missing required environment variables:")
        if not supabase_url:
            print("  - SUPABASE_URL")
        if not supabase_key:
            print("  - SUPABASE_KEY")
        if not openai_key:
            print("  - OPENAI_API_KEY")
        sys.exit(1)

    # Initialize services
    supabase_store = SupabaseStore(supabase_url, supabase_key)
    embedding_service = EmbeddingService(openai_key)

    # Run migration
    migration = EmbeddingMigration(supabase_store, embedding_service)

    try:
        stats = migration.run()
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
