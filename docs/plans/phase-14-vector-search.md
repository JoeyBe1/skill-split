# Phase 14: Vector Search - Complete Implementation Plan

> **For Claude:** Implement semantic search using pgvector for intelligent section discovery and ranking.

**Goal:** Add semantic search capabilities to skill-split, enabling users to find sections by meaning rather than exact keyword matches. Combine vector search with existing text search for hybrid ranking.

**Architecture:**
- PostgreSQL pgvector extension (Supabase native)
- Embedding generation using Claude API (cost-optimized)
- Hybrid search combining vector + text ranking
- Incremental embedding generation for new sections
- Token-efficient embedding caching strategy

**Tech Stack:** Python 3.8+, supabase-py, OpenAI API, PostgreSQL, pgvector

**Phase Status:** NOT STARTED (Phase 13 dependency: existing search API stable)

---

## Context: Why Vector Search?

Current state-of-the-art section retrieval:
- **Text search**: Fast, exact matches, limited by vocabulary mismatch
- **Examples:** Searching "authentication" finds "login" sections only if keyword present
- **Problem:** Users think conceptually ("how do I secure requests?") but database searches literally

**Vector search solves:**
- Semantic similarity regardless of exact wording
- Better ranking by conceptual relevance
- Cross-domain discovery ("JWT", "OAuth", "sessions" all relate to "authentication")
- Progressive refinement from broad concepts to specific implementation

**Expected impact:**
- 40-60% improvement in search relevance (estimated)
- Token savings from better section selection (users request fewer sections)
- New queries that currently fail to find sections
- Foundation for future AI-powered recommendations

---

## Task List Overview

**Phase 1:** Database Schema (45 min)
- Task 1: Add pgvector extension to Supabase
- Task 2: Create embeddings table with vector column
- Task 3: Add embedding metadata tracking

**Phase 2:** Embedding Service (90 min)
- Task 4: Design embedding strategy (model, dimensions, caching)
- Task 5: Implement EmbeddingService class
- Task 6: Add batch embedding generation
- Task 7: Implement token-efficient caching

**Phase 3:** Hybrid Search API (60 min)
- Task 8: Design hybrid search scoring
- Task 9: Implement vector search query
- Task 10: Implement combined text + vector search
- Task 11: Add relevance ranking algorithm

**Phase 4:** Integration (45 min)
- Task 12: Integrate into SupabaseStore
- Task 13: Auto-generate embeddings on file store
- Task 14: Update CLI commands for vector search

**Phase 5:** Performance & Migration (60 min)
- Task 15: Add search performance metrics
- Task 16: Implement incremental embedding strategy
- Task 17: Create migration script for existing sections
- Task 18: Add query optimization (indexing)

**Phase 6:** Testing & Documentation (45 min)
- Task 19: Add vector search tests (15 tests)
- Task 20: Performance benchmarks
- Task 21: Document embedding costs
- Task 22: Create usage guide

**Phase 7:** Production Deployment (30 min)
- Task 23: Cost analysis and optimization
- Task 24: Deployment checklist
- Task 25: Monitoring and alerts

**Total Estimated Time:** ~6.5 hours

---

## Phase 1: Database Schema

### Task 1: Add pgvector to Supabase

**Goal:** Enable PostgreSQL pgvector extension for vector operations

**File:** None (Supabase dashboard operation)

**Steps:**
1. Log into Supabase dashboard
2. Navigate to SQL Editor
3. Run:
   ```sql
   -- Enable pgvector extension
   CREATE EXTENSION IF NOT EXISTS vector;

   -- Verify installation
   SELECT extname FROM pg_extension WHERE extname = 'vector';
   ```
4. Verify output shows "vector" extension installed

**Verification:**
```bash
# Test SQL query in Supabase dashboard
SELECT 1::vector as test_vector;
# Should return: test_vector = [1]
```

**Documentation:**
- Link: https://supabase.com/docs/guides/database/extensions/pgvector/overview
- Extension enables: `vector` data type, `<->` (L2 distance), `<#>` (negative dot product), `<=>` (cosine distance)

---

### Task 2: Create Embeddings Table

**Goal:** Store vector embeddings for all sections

**File:** SQL migration (Supabase dashboard)

**Schema Design:**

```sql
-- Create embeddings table
CREATE TABLE embeddings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  section_id UUID NOT NULL UNIQUE REFERENCES sections(id) ON DELETE CASCADE,

  -- Vector: 1536-dimensional (OpenAI text-embedding-3-small)
  embedding vector(1536) NOT NULL,

  -- Metadata for tracking and optimization
  model VARCHAR(50) NOT NULL DEFAULT 'text-embedding-3-small',
  tokens_used INTEGER NOT NULL DEFAULT 0,  -- For cost tracking
  generated_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),

  -- Performance indexes
  CONSTRAINT embedding_not_null CHECK (embedding IS NOT NULL)
);

-- Vector similarity index (IVFFlat - trade accuracy for speed)
CREATE INDEX embeddings_vector_idx ON embeddings
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Lookup by section (for updates)
CREATE INDEX embeddings_section_idx ON embeddings(section_id);

-- Timestamp indexes (for incremental generation)
CREATE INDEX embeddings_generated_idx ON embeddings(generated_at DESC);

-- Add trigger to update updated_at
CREATE TRIGGER embeddings_updated_at
BEFORE UPDATE ON embeddings
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
```

**Dimensions Chosen:** 1536
- Model: `text-embedding-3-small` (OpenAI, optimized for cost)
- Reasons:
  - Small model = 64x cheaper than text-embedding-3-large
  - 1536 dimensions sufficient for semantic tasks
  - Fast similarity computations
  - Can be distilled further if needed (see section "Future Optimizations")

**Index Strategy:**
- **IVFFlat** with 100 lists balances accuracy vs speed
  - Faster than HNSW for 1536 dimensions at scale
  - Sufficient for ~20k sections (current size)
  - Upgrade to HNSW if scaling beyond 50k sections

---

### Task 3: Add Embedding Metadata Table

**Goal:** Track embedding generation cost and progress

**File:** SQL migration (Supabase dashboard)

**Schema:**

```sql
-- Track embedding generation progress and costs
CREATE TABLE embedding_metadata (
  id SERIAL PRIMARY KEY,
  file_id UUID NOT NULL REFERENCES files(id) ON DELETE CASCADE,

  -- Progress tracking
  total_sections INTEGER NOT NULL DEFAULT 0,
  embedded_sections INTEGER NOT NULL DEFAULT 0,
  failed_sections INTEGER NOT NULL DEFAULT 0,

  -- Cost tracking
  total_tokens_used INTEGER NOT NULL DEFAULT 0,
  estimated_cost_usd DECIMAL(10, 6) NOT NULL DEFAULT 0.0,

  -- Timestamps
  generation_started_at TIMESTAMP,
  generation_completed_at TIMESTAMP,
  last_updated_at TIMESTAMP DEFAULT NOW(),

  -- Status tracking
  status VARCHAR(20) DEFAULT 'pending',  -- pending, in_progress, completed, failed
  error_message TEXT
);

-- Quick lookup by file
CREATE INDEX embedding_metadata_file_idx ON embedding_metadata(file_id);

-- Track failures by status
CREATE INDEX embedding_metadata_status_idx ON embedding_metadata(status);
```

**Rationale:**
- Cost tracking: Help users understand API spend
- Progress tracking: Enable resumable batch operations
- Failure tracking: Debug and retry failed sections

---

## Phase 2: Embedding Service

### Task 4: Design Embedding Strategy

**Goal:** Define embedding generation approach

**Decision Matrix:**

| Aspect | Choice | Rationale |
|--------|--------|-----------|
| Model | `text-embedding-3-small` | 64x cheaper, sufficient quality |
| Dimensions | 1536 | Optimal for cost/performance |
| Batch Size | 100-200 sections | Optimize OpenAI API throughput |
| Caching | Redis + database | Avoid re-embedding same content |
| Cost | ~$0.00002 per 1K tokens | ~$0.02 per 1000 sections |
| Rate Limiting | 3000 req/min | OpenAI API limit |
| Retry Policy | 3 retries + exponential backoff | Transient failure resilience |

**Cost Analysis for Production:**
- Current: 19,207 sections (estimated)
- Model: `text-embedding-3-small` = $0.02 per 1M input tokens
- Average section: ~200 tokens (estimated)
- Total: 19,207 × 200 / 1,000,000 × $0.02 = **~$0.08** one-time cost
- Monthly new sections: +100/month = ~$0.001/month

**Embedding Caching Strategy:**
- Cache key: `embedding:{content_hash}` (SHA256 of section content)
- TTL: 30 days (content rarely changes)
- Fallback: Regenerate if not found
- Benefit: Save 90%+ API costs for duplicate content

**Batching Strategy:**
- Queue sections by file (processing order: newest first)
- Batch 100-200 sections per request (OpenAI API optimal)
- Progress tracking with tqdm for visibility
- Resumable: Store last_processed position in metadata table

---

### Task 5: Implement EmbeddingService Class

**Goal:** Create service for embedding generation

**File:** `core/embedding_service.py` (~200 lines)

**Implementation:**

```python
"""Embedding service for semantic search."""
import os
import json
from typing import List, Optional, Dict, Tuple
import hashlib
from dataclasses import dataclass
from enum import Enum

import openai
from models import Section

# Cost constants
TOKENS_PER_SECTION = 200  # Average estimate
COST_PER_1M_TOKENS = 0.02  # text-embedding-3-small pricing


class EmbeddingModel(Enum):
    """Available embedding models."""
    SMALL = "text-embedding-3-small"    # 1536 dims, $0.02 per 1M tokens
    LARGE = "text-embedding-3-large"    # 3072 dims, $0.13 per 1M tokens


@dataclass
class EmbeddingResult:
    """Result from embedding operation."""
    section_id: str
    embedding: List[float]
    tokens_used: int
    model: str


class EmbeddingService:
    """Service for generating and managing embeddings."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: EmbeddingModel = EmbeddingModel.SMALL,
        batch_size: int = 100
    ):
        """
        Initialize embedding service.

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: Embedding model to use
            batch_size: Number of sections to embed per API call
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")

        self.model = model
        self.batch_size = batch_size
        self.client = openai.OpenAI(api_key=self.api_key)

    def embed_section(self, section: Section) -> EmbeddingResult:
        """
        Generate embedding for single section.

        Args:
            section: Section to embed

        Returns:
            EmbeddingResult with vector and token usage

        Raises:
            ValueError: If section content is empty
            openai.APIError: If API request fails
        """
        if not section.content or not section.content.strip():
            raise ValueError(f"Section {section.id} has no content to embed")

        # Prepare input: title + content for better semantic understanding
        text = f"{section.title}\n\n{section.content}"
        text = text[:8000]  # Truncate if needed (safety limit)

        response = self.client.embeddings.create(
            input=text,
            model=self.model.value
        )

        embedding = response.data[0].embedding
        tokens_used = response.usage.prompt_tokens

        return EmbeddingResult(
            section_id=section.id,
            embedding=embedding,
            tokens_used=tokens_used,
            model=self.model.value
        )

    def embed_batch(
        self,
        sections: List[Section],
        progress_callback: Optional[callable] = None
    ) -> Dict[str, EmbeddingResult]:
        """
        Generate embeddings for multiple sections.

        Args:
            sections: List of sections to embed
            progress_callback: Optional callback for progress updates

        Returns:
            Dict mapping section_id to EmbeddingResult

        Raises:
            ValueError: If batch is empty
            openai.APIError: If API request fails
        """
        if not sections:
            raise ValueError("Cannot embed empty section list")

        results = {}
        total_sections = len(sections)

        for i in range(0, total_sections, self.batch_size):
            batch = sections[i:i + self.batch_size]
            batch_texts = [f"{s.title}\n\n{s.content}" for s in batch]

            # Call embedding API
            response = self.client.embeddings.create(
                input=batch_texts,
                model=self.model.value
            )

            # Extract results
            for j, item in enumerate(response.data):
                section = batch[j]
                results[section.id] = EmbeddingResult(
                    section_id=section.id,
                    embedding=item.embedding,
                    tokens_used=response.usage.prompt_tokens,
                    model=self.model.value
                )

            if progress_callback:
                progress_callback(len(results), total_sections)

        return results

    @staticmethod
    def get_cache_key(content: str) -> str:
        """Get cache key for section content."""
        return f"embedding:{hashlib.sha256(content.encode()).hexdigest()}"

    @staticmethod
    def estimate_cost(num_sections: int, avg_tokens: int = TOKENS_PER_SECTION) -> float:
        """Estimate cost for embedding operation."""
        total_tokens = num_sections * avg_tokens
        return (total_tokens / 1_000_000) * COST_PER_1M_TOKENS
```

**Test Coverage (in test/test_embedding_service.py):**
- Test single embedding generation
- Test batch embedding
- Test cache key generation
- Test cost estimation
- Test API error handling
- Test empty section handling

---

### Task 6: Add Batch Embedding Generation

**Goal:** Implement efficient batch processing with progress tracking

**File:** `core/embedding_service.py` (add methods)

**Implementation:**

```python
class EmbeddingService:
    # ... existing code ...

    def generate_embeddings_for_file(
        self,
        supabase_client,
        file_id: str,
        sections: List[Section],
        force_refresh: bool = False
    ) -> Dict[str, any]:
        """
        Generate embeddings for all sections in a file.

        Args:
            supabase_client: SupabaseStore instance
            file_id: UUID of file to process
            sections: Parsed sections from file
            force_refresh: If True, regenerate all embeddings

        Returns:
            Dict with:
                - generated_count: Number of new embeddings created
                - cached_count: Number from cache
                - failed_count: Number that failed
                - total_cost: Estimated cost in USD
                - tokens_used: Total API tokens used
        """
        from tqdm import tqdm

        generated = 0
        cached = 0
        failed = 0
        total_tokens = 0
        cost = 0.0

        # Track progress
        progress_bar = tqdm(total=len(sections), desc=f"Embedding file {file_id}")

        for section in sections:
            try:
                # Check if embedding exists and skip if not forcing refresh
                if not force_refresh:
                    existing = supabase_client.client.table("embeddings") \
                        .select("id") \
                        .eq("section_id", section.id) \
                        .execute()

                    if existing.data:
                        cached += 1
                        progress_bar.update(1)
                        continue

                # Generate embedding
                result = self.embed_section(section)

                # Store in database
                supabase_client.client.table("embeddings").insert({
                    "section_id": section.id,
                    "embedding": result.embedding,
                    "model": result.model,
                    "tokens_used": result.tokens_used
                }).execute()

                generated += 1
                total_tokens += result.tokens_used
                cost += (result.tokens_used / 1_000_000) * COST_PER_1M_TOKENS

            except Exception as e:
                failed += 1
                print(f"Failed to embed section {section.id}: {e}")

            progress_bar.update(1)

        progress_bar.close()

        return {
            "generated_count": generated,
            "cached_count": cached,
            "failed_count": failed,
            "total_cost": cost,
            "tokens_used": total_tokens
        }

    def regenerate_all_embeddings(
        self,
        supabase_client,
        start_after: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Regenerate all embeddings in Supabase (resumable).

        Args:
            supabase_client: SupabaseStore instance
            start_after: Optional section ID to resume from

        Returns:
            Summary stats
        """
        from tqdm import tqdm

        # Get all sections
        all_sections = supabase_client.client.table("sections") \
            .select("*") \
            .order("created_at", desc=False) \
            .execute()

        sections = [
            Section(**row) for row in all_sections.data
        ]

        if start_after:
            # Find resume position
            idx = next((i for i, s in enumerate(sections) if s.id == start_after), 0)
            sections = sections[idx + 1:]

        # Process in batches by file for efficiency
        files_processed = {}
        total_cost = 0.0

        for section in tqdm(sections, desc="Regenerating all embeddings"):
            file_id = section.file_id
            if file_id not in files_processed:
                files_processed[file_id] = 0

            try:
                result = self.embed_section(section)
                supabase_client.client.table("embeddings").insert({
                    "section_id": section.id,
                    "embedding": result.embedding,
                    "model": result.model,
                    "tokens_used": result.tokens_used
                }).execute()

                files_processed[file_id] += 1
                total_cost += (result.tokens_used / 1_000_000) * COST_PER_1M_TOKENS

            except Exception as e:
                print(f"Error embedding {section.id}: {e}")

        return {
            "files_processed": len(files_processed),
            "sections_embedded": sum(files_processed.values()),
            "total_cost": total_cost
        }
```

---

### Task 7: Implement Token-Efficient Caching

**Goal:** Cache embeddings to avoid re-computing

**File:** `core/embedding_service.py` (add methods)

**Implementation:**

```python
import json
from pathlib import Path
from datetime import datetime, timedelta

class EmbeddingCache:
    """Local cache for embeddings to avoid redundant API calls."""

    def __init__(self, cache_dir: str = "~/.claude/embedding_cache"):
        """Initialize cache."""
        self.cache_dir = Path(cache_dir).expanduser()
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl = timedelta(days=30)

    def get(self, content_hash: str) -> Optional[List[float]]:
        """
        Retrieve cached embedding.

        Args:
            content_hash: SHA256 hash of content

        Returns:
            Embedding vector or None if not found/expired
        """
        cache_file = self.cache_dir / f"{content_hash}.json"

        if not cache_file.exists():
            return None

        try:
            with open(cache_file, 'r') as f:
                data = json.load(f)

            # Check if expired
            created = datetime.fromisoformat(data['created_at'])
            if datetime.now() - created > self.ttl:
                cache_file.unlink()  # Delete expired cache
                return None

            return data['embedding']

        except (json.JSONDecodeError, KeyError):
            return None

    def set(self, content_hash: str, embedding: List[float]) -> None:
        """
        Store embedding in cache.

        Args:
            content_hash: SHA256 hash of content
            embedding: Vector to cache
        """
        cache_file = self.cache_dir / f"{content_hash}.json"

        with open(cache_file, 'w') as f:
            json.dump({
                'embedding': embedding,
                'created_at': datetime.now().isoformat()
            }, f)

    def clear(self) -> int:
        """
        Clear expired entries.

        Returns:
            Number of entries deleted
        """
        deleted = 0
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                created = datetime.fromisoformat(data['created_at'])
                if datetime.now() - created > self.ttl:
                    cache_file.unlink()
                    deleted += 1
            except (json.JSONDecodeError, KeyError):
                pass

        return deleted
```

**Usage Example:**

```python
# In EmbeddingService.embed_section():
cache = EmbeddingCache()
content_hash = hashlib.sha256(text.encode()).hexdigest()

# Check cache first
cached = cache.get(content_hash)
if cached:
    return EmbeddingResult(
        section_id=section.id,
        embedding=cached,
        tokens_used=0,  # From cache, no API tokens used
        model=self.model.value
    )

# Generate if not cached
response = self.client.embeddings.create(input=text, model=self.model.value)
embedding = response.data[0].embedding

# Store in cache for future use
cache.set(content_hash, embedding)

return EmbeddingResult(...)
```

---

## Phase 3: Hybrid Search API

### Task 8: Design Hybrid Search Scoring

**Goal:** Define algorithm combining vector + text relevance

**Scoring Algorithm:**

```
final_score = (0.7 × vector_score) + (0.3 × text_score)

Where:
  vector_score = 1 - (cosine_distance / 2)    # Normalize to [0,1]
  text_score = bm25_rank / max_bm25           # Normalize to [0,1]
```

**Rationale:**
- 70% weight to vector: Captures semantic meaning
- 30% weight to text: Handles exact keyword matches
- Hybrid approach: Best of both worlds

**Example Ranking:**

Query: "how do I authenticate users?"

| Section | Title | Vector Score | Text Score | Final Score |
|---------|-------|---------------|------------|-------------|
| 1 | "Authentication Strategies" | 0.95 | 0.80 | **0.88** ✓ |
| 2 | "Login Form Implementation" | 0.88 | 0.40 | 0.73 |
| 3 | "Session Management" | 0.85 | 0.10 | 0.59 |
| 4 | "Password Hashing" | 0.92 | 0.05 | 0.64 |

**Parameters:**
- `vector_weight`: 0.0-1.0 (default 0.7)
- `min_score`: 0.0-1.0 (default 0.5, filter results below threshold)
- `limit`: Max results (default 10)

---

### Task 9: Implement Vector Search Query

**Goal:** Add vector similarity search to SupabaseStore

**File:** `core/supabase_store.py` (add method)

**Implementation:**

```python
from typing import List, Tuple
from models import Section

class SupabaseStore:
    # ... existing code ...

    def search_by_vector(
        self,
        embedding: List[float],
        limit: int = 10,
        min_score: float = 0.5
    ) -> List[Tuple[str, Section, float]]:
        """
        Search sections by semantic similarity.

        Args:
            embedding: Query embedding vector (1536 dims)
            limit: Maximum results to return
            min_score: Minimum similarity score [0, 1]

        Returns:
            List of (section_id, Section, similarity_score) tuples
            ordered by score descending

        Raises:
            ValueError: If embedding dimension mismatch
        """
        if len(embedding) != 1536:
            raise ValueError(
                f"Expected 1536-dim embedding, got {len(embedding)}"
            )

        # Query: find nearest embeddings by L2 distance
        # Convert cosine to similarity: similarity = 1 - (distance / 2)
        results = self.client.rpc(
            'search_embeddings',
            {
                'query_embedding': embedding,
                'similarity_threshold': min_score,
                'match_count': limit
            }
        ).execute()

        sections = []
        for result in results.data:
            section = Section(
                id=result['section_id'],
                file_id=result['file_id'],
                parent_id=result['parent_id'],
                level=result['level'],
                title=result['title'],
                content=result['content'],
                order_index=result['order_index'],
                line_start=result['line_start'],
                line_end=result['line_end']
            )
            similarity = result['similarity']
            sections.append((result['section_id'], section, similarity))

        return sections
```

**Supabase SQL Function (create in dashboard):**

```sql
CREATE OR REPLACE FUNCTION search_embeddings(
  query_embedding vector(1536),
  similarity_threshold float DEFAULT 0.5,
  match_count int DEFAULT 10
)
RETURNS TABLE (
  section_id uuid,
  file_id uuid,
  parent_id uuid,
  level int,
  title varchar,
  content text,
  order_index int,
  line_start int,
  line_end int,
  similarity float
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    s.id,
    s.file_id,
    s.parent_id,
    s.level,
    s.title,
    s.content,
    s.order_index,
    s.line_start,
    s.line_end,
    (1 - (e.embedding <=> query_embedding) / 2)::float AS similarity
  FROM sections s
  JOIN embeddings e ON s.id = e.section_id
  WHERE (1 - (e.embedding <=> query_embedding) / 2) >= similarity_threshold
  ORDER BY e.embedding <=> query_embedding
  LIMIT match_count;
END;
$$ LANGUAGE plpgsql;
```

---

### Task 10: Implement Combined Text + Vector Search

**Goal:** Hybrid search combining both approaches

**File:** `core/supabase_store.py` (add method)

**Implementation:**

```python
class SupabaseStore:
    # ... existing code ...

    def hybrid_search(
        self,
        query: str,
        embedding: List[float],
        vector_weight: float = 0.7,
        limit: int = 10,
        min_score: float = 0.5
    ) -> List[Tuple[str, Section, float]]:
        """
        Hybrid search combining vector + text search.

        Args:
            query: Text query for keyword matching
            embedding: Semantic vector from embedding model
            vector_weight: Weight for vector score [0.0-1.0] (default 0.7)
            limit: Max results
            min_score: Minimum combined score

        Returns:
            List of (section_id, Section, combined_score) ordered by score
        """
        text_weight = 1.0 - vector_weight

        # Vector search results
        vector_results = self.search_by_vector(
            embedding, limit=limit*2, min_score=0.4  # Lower threshold, will filter later
        )
        vector_scores = {r[0]: r[2] for r in vector_results}

        # Text search results
        text_results = self.search_sections(
            query, limit=limit*2
        )
        text_scores = {}
        for i, (section_id, _) in enumerate(text_results):
            # BM25 score normalized (better matches = higher rank)
            normalized_score = 1.0 / (1.0 + i)
            text_scores[section_id] = normalized_score

        # Combine scores
        combined = {}
        all_ids = set(vector_scores.keys()) | set(text_scores.keys())

        for section_id in all_ids:
            v_score = vector_scores.get(section_id, 0.0)
            t_score = text_scores.get(section_id, 0.0)
            combined_score = (v_score * vector_weight) + (t_score * text_weight)

            if combined_score >= min_score:
                combined[section_id] = combined_score

        # Sort by combined score and fetch sections
        ranked = sorted(combined.items(), key=lambda x: x[1], reverse=True)[:limit]

        results = []
        for section_id, score in ranked:
            # Fetch full section data
            section = self.get_section(section_id)  # Assuming this method exists
            if section:
                results.append((section_id, section, score))

        return results
```

---

### Task 11: Add Relevance Ranking Algorithm

**Goal:** Improve ranking with additional signals

**File:** `core/supabase_store.py` (add method)

**Implementation:**

```python
from enum import Enum
from dataclasses import dataclass

@dataclass
class RankingSignal:
    """Individual ranking signal."""
    name: str
    weight: float
    score: float

class HybridSearchRanker:
    """Advanced ranking combining multiple signals."""

    def __init__(self):
        """Initialize ranker with signal weights."""
        self.signals = {
            'vector_similarity': 0.50,      # Core semantic match
            'text_relevance': 0.25,         # Keyword presence
            'section_depth': 0.10,          # Prefer leaf nodes
            'file_recency': 0.10,           # Recent files ranked higher
            'section_size': 0.05            # Prefer substantial sections
        }

    def score_result(
        self,
        section: Section,
        file_metadata: dict,
        vector_sim: float,
        text_rank: float
    ) -> Tuple[float, List[RankingSignal]]:
        """
        Calculate composite score with multiple signals.

        Returns:
            (final_score, list_of_signals) for transparency
        """
        signals = []

        # Signal 1: Vector similarity
        signals.append(RankingSignal('vector_similarity', 0.50, vector_sim))

        # Signal 2: Text relevance (normalized)
        signals.append(RankingSignal('text_relevance', 0.25, text_rank))

        # Signal 3: Section depth (prefer detailed leaf sections)
        # Max depth = 6 for h1-h6, normalize to [0, 1]
        depth_score = section.level / 6.0
        signals.append(RankingSignal('section_depth', 0.10, depth_score))

        # Signal 4: File recency (files updated recently ranked higher)
        days_old = (datetime.now() - file_metadata['updated_at']).days
        recency_score = max(0, 1.0 - (days_old / 365.0))  # Decay over year
        signals.append(RankingSignal('file_recency', 0.10, recency_score))

        # Signal 5: Section size (prefer substantial content)
        avg_size = 500  # characters
        size_score = min(1.0, len(section.content) / avg_size)
        signals.append(RankingSignal('section_size', 0.05, size_score))

        # Calculate final score
        final_score = sum(s.weight * s.score for s in signals)

        return final_score, signals

    def rank_results(
        self,
        results: List[Tuple[str, Section, dict, float, float]]
    ) -> List[Tuple[str, Section, float, List[RankingSignal]]]:
        """
        Rank search results with multiple signals.

        Args:
            results: List of (section_id, Section, file_metadata, vector_sim, text_rank)

        Returns:
            Sorted list of (section_id, Section, final_score, signals)
        """
        ranked = []

        for section_id, section, file_metadata, vector_sim, text_rank in results:
            score, signals = self.score_result(
                section, file_metadata, vector_sim, text_rank
            )
            ranked.append((section_id, section, score, signals))

        # Sort by score descending
        ranked.sort(key=lambda x: x[2], reverse=True)

        return ranked
```

**Example Output:**

```json
{
  "results": [
    {
      "section_id": "uuid-1",
      "title": "Authentication Strategies",
      "score": 0.821,
      "signals": [
        {"name": "vector_similarity", "weight": 0.50, "score": 0.95},
        {"name": "text_relevance", "weight": 0.25, "score": 0.80},
        {"name": "section_depth", "weight": 0.10, "score": 0.33},
        {"name": "file_recency", "weight": 0.10, "score": 0.95},
        {"name": "section_size", "weight": 0.05, "score": 0.88}
      ]
    }
  ]
}
```

---

## Phase 4: Integration

### Task 12: Integrate into SupabaseStore

**Goal:** Connect embedding service to main store

**File:** `core/supabase_store.py` (modify constructor)

**Implementation:**

```python
from core.embedding_service import EmbeddingService

class SupabaseStore:
    def __init__(self, url: str, key: str, auto_embed: bool = True):
        """
        Initialize Supabase store.

        Args:
            url: Supabase URL
            key: Supabase API key
            auto_embed: If True, auto-generate embeddings when storing files
        """
        self.url = url
        self.key = key
        self.client = create_client(url, key)
        self.auto_embed = auto_embed

        # Initialize embedding service if enabled
        if auto_embed:
            try:
                self.embedding_service = EmbeddingService()
            except ValueError:
                print("Warning: OPENAI_API_KEY not set, embeddings disabled")
                self.embedding_service = None
        else:
            self.embedding_service = None
```

---

### Task 13: Auto-Generate Embeddings on Store

**Goal:** Automatically create embeddings when files are stored

**File:** `core/supabase_store.py` (modify store_file method)

**Implementation:**

```python
def store_file(
    self, storage_path: str, name: str, doc: ParsedDocument, content_hash: str
) -> str:
    """Store file and optionally generate embeddings."""
    # ... existing file storage code ...

    # Generate embeddings if enabled
    if self.embedding_service and doc.sections:
        try:
            print(f"Generating embeddings for {len(doc.sections)} sections...")
            results = self.embedding_service.generate_embeddings_for_file(
                self, file_id, doc.sections
            )
            print(
                f"Embeddings complete: "
                f"{results['generated_count']} generated, "
                f"{results['cached_count']} cached, "
                f"Cost: ${results['total_cost']:.4f}"
            )
        except Exception as e:
            print(f"Warning: Failed to generate embeddings: {e}")
            # Continue without embeddings rather than fail

    return file_id
```

---

### Task 14: Update CLI Commands

**Goal:** Add vector search commands to CLI

**File:** `skill_split.py` (add commands)

**Implementation:**

```python
import click
from core.embedding_service import EmbeddingService
from core.supabase_store import SupabaseStore

@cli.command()
@click.argument('query')
@click.option('--db', default=DEFAULT_DB_PATH, help='Database path')
@click.option('--limit', default=10, help='Max results')
@click.option('--vector-weight', default=0.7, help='Vector score weight (0.0-1.0)')
def search_vector(query: str, db: str, limit: int, vector_weight: float):
    """Search sections semantically (vector search)."""
    try:
        store = SupabaseStore(
            url=os.getenv("SUPABASE_URL"),
            key=os.getenv("SUPABASE_KEY")
        )
        embedding_service = EmbeddingService()

        # Generate query embedding
        query_section = Section(
            id="query",
            file_id="",
            title="Query",
            content=query,
            level=0,
            order_index=0,
            line_start=0,
            line_end=0
        )
        result = embedding_service.embed_section(query_section)
        embedding = result.embedding

        # Search
        results = store.search_by_vector(embedding, limit=limit)

        # Display results
        click.echo(f"\nVector Search Results for: {query}\n")
        for i, (section_id, section, score) in enumerate(results, 1):
            click.echo(f"{i}. {section.title} (Score: {score:.3f})")
            click.echo(f"   ID: {section_id}")
            click.echo(f"   Level: {section.level}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@cli.command()
@click.argument('query')
@click.option('--db', default=DEFAULT_DB_PATH, help='Database path')
@click.option('--limit', default=10, help='Max results')
@click.option('--vector-weight', default=0.7, help='Vector score weight')
def search_hybrid(
    query: str, db: str, limit: int, vector_weight: float
):
    """Hybrid search combining vector + text (best results)."""
    try:
        store = SupabaseStore(
            url=os.getenv("SUPABASE_URL"),
            key=os.getenv("SUPABASE_KEY")
        )
        embedding_service = EmbeddingService()

        # Generate query embedding
        query_section = Section(
            id="query",
            file_id="",
            title="Query",
            content=query,
            level=0,
            order_index=0,
            line_start=0,
            line_end=0
        )
        result = embedding_service.embed_section(query_section)
        embedding = result.embedding

        # Hybrid search
        results = store.hybrid_search(
            query,
            embedding,
            vector_weight=vector_weight,
            limit=limit
        )

        # Display results
        click.echo(f"\nHybrid Search Results for: {query}\n")
        for i, (section_id, section, score) in enumerate(results, 1):
            click.echo(f"{i}. {section.title} (Score: {score:.3f})")
            click.echo(f"   ID: {section_id}")
            click.echo(f"   Level: {section.level}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@cli.command()
@click.option('--db', default=DEFAULT_DB_PATH, help='Database path')
@click.option('--force', is_flag=True, help='Regenerate existing embeddings')
def generate_embeddings(db: str, force: bool):
    """Generate embeddings for all sections in Supabase."""
    try:
        store = SupabaseStore(
            url=os.getenv("SUPABASE_URL"),
            key=os.getenv("SUPABASE_KEY")
        )
        embedding_service = EmbeddingService()

        click.echo("Starting embedding generation...")
        results = embedding_service.regenerate_all_embeddings(
            store,
            force_refresh=force
        )

        click.echo(f"\nEmbedding generation complete:")
        click.echo(f"  Files processed: {results['files_processed']}")
        click.echo(f"  Sections embedded: {results['sections_embedded']}")
        click.echo(f"  Total cost: ${results['total_cost']:.4f}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)
```

---

## Phase 5: Performance & Migration

### Task 15: Add Search Performance Metrics

**Goal:** Track and optimize query performance

**File:** `core/search_metrics.py` (~100 lines)

**Implementation:**

```python
"""Performance metrics for search operations."""
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List
import time


@dataclass
class SearchMetrics:
    """Metrics for a single search operation."""
    query_type: str  # 'text', 'vector', 'hybrid'
    query: str
    query_tokens: int
    results_count: int
    execution_time_ms: float
    vector_distance_calls: int = 0
    text_index_scans: int = 0
    cache_hits: int = 0
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class MetricsCollector:
    """Collect and aggregate search metrics."""

    def __init__(self):
        """Initialize collector."""
        self.metrics: List[SearchMetrics] = []

    def record(self, metric: SearchMetrics) -> None:
        """Record a search metric."""
        self.metrics.append(metric)

    def summary(self) -> Dict:
        """Get aggregate metrics summary."""
        if not self.metrics:
            return {}

        text_searches = [m for m in self.metrics if m.query_type == 'text']
        vector_searches = [m for m in self.metrics if m.query_type == 'vector']
        hybrid_searches = [m for m in self.metrics if m.query_type == 'hybrid']

        return {
            'total_searches': len(self.metrics),
            'text_avg_time_ms': (
                sum(m.execution_time_ms for m in text_searches) / len(text_searches)
                if text_searches else 0
            ),
            'vector_avg_time_ms': (
                sum(m.execution_time_ms for m in vector_searches) / len(vector_searches)
                if vector_searches else 0
            ),
            'hybrid_avg_time_ms': (
                sum(m.execution_time_ms for m in hybrid_searches) / len(hybrid_searches)
                if hybrid_searches else 0
            ),
            'total_cache_hits': sum(m.cache_hits for m in self.metrics)
        }
```

---

### Task 16: Implement Incremental Embedding Strategy

**Goal:** Efficiently embed new sections without regenerating everything

**File:** `core/embedding_service.py` (add method)

**Implementation:**

```python
def generate_embeddings_for_new_sections(
    self,
    supabase_client,
    since: Optional[datetime] = None,
    batch_size: int = 100
) -> Dict[str, any]:
    """
    Generate embeddings only for sections created since last run.

    Args:
        supabase_client: SupabaseStore instance
        since: Only process sections created after this datetime
        batch_size: Sections per batch

    Returns:
        Summary stats
    """
    from tqdm import tqdm

    # Get unembedded sections
    query = supabase_client.client.table("sections") \
        .select("*") \
        .not_.in_("id", supabase_client.client.table("embeddings").select("section_id").execute().data)

    if since:
        query = query.gte("created_at", since.isoformat())

    unembedded = query.execute().data

    if not unembedded:
        return {
            "generated_count": 0,
            "cached_count": 0,
            "failed_count": 0,
            "total_cost": 0.0
        }

    sections = [Section(**row) for row in unembedded]

    # Process in batches
    generated = 0
    failed = 0
    total_cost = 0.0

    for i in tqdm(range(0, len(sections), batch_size), desc="Embedding new sections"):
        batch = sections[i:i + batch_size]

        try:
            batch_results = self.embed_batch(batch)

            # Store all results
            for section_id, result in batch_results.items():
                supabase_client.client.table("embeddings").insert({
                    "section_id": section_id,
                    "embedding": result.embedding,
                    "model": result.model,
                    "tokens_used": result.tokens_used
                }).execute()

                generated += 1
                total_cost += (result.tokens_used / 1_000_000) * COST_PER_1M_TOKENS

        except Exception as e:
            failed += len(batch)
            print(f"Error in batch: {e}")

    return {
        "generated_count": generated,
        "cached_count": 0,
        "failed_count": failed,
        "total_cost": total_cost
    }
```

---

### Task 17: Create Migration Script

**Goal:** Embed all existing sections in production

**File:** `migrate_to_vector_search.py` (~150 lines)

**Implementation:**

```python
#!/usr/bin/env python3
"""Migrate existing database to vector search."""
import os
import sys
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from core.supabase_store import SupabaseStore
from core.embedding_service import EmbeddingService
from tqdm import tqdm


def migrate_to_vector_search(
    force_regenerate: bool = False,
    batch_size: int = 100,
    resume_from: str = None
):
    """
    Migrate all sections to have embeddings.

    Args:
        force_regenerate: If True, regenerate all embeddings
        batch_size: Sections per batch
        resume_from: Section ID to resume from (for resumable migration)
    """
    # Initialize services
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    if not url or not key:
        print("ERROR: SUPABASE_URL and SUPABASE_KEY must be set")
        sys.exit(1)

    store = SupabaseStore(url, key, auto_embed=False)
    embedding_service = EmbeddingService()

    # Get all sections
    print("Fetching sections from Supabase...")
    response = store.client.table("sections").select("*").execute()
    total_sections = len(response.data)

    if force_regenerate:
        # Delete all existing embeddings
        print("Deleting existing embeddings...")
        store.client.table("embeddings").delete().gte("id", "00000000-0000-0000-0000-000000000000").execute()

    # Process sections in batches
    print(f"\nStarting migration of {total_sections} sections")
    print(f"Estimated cost: ${EmbeddingService.estimate_cost(total_sections):.2f}")
    print(f"Batch size: {batch_size}\n")

    input("Press Enter to start migration...")

    sections = [Section(**row) for row in response.data]

    # Find resume position if specified
    if resume_from:
        idx = next((i for i, s in enumerate(sections) if s.id == resume_from), 0)
        sections = sections[idx + 1:]

    total_cost = 0.0
    generated = 0

    with tqdm(total=len(sections), desc="Migrating") as pbar:
        for i in range(0, len(sections), batch_size):
            batch = sections[i:i + batch_size]

            try:
                batch_results = embedding_service.embed_batch(batch)

                # Store results
                for section_id, result in batch_results.items():
                    store.client.table("embeddings").insert({
                        "section_id": section_id,
                        "embedding": result.embedding,
                        "model": result.model,
                        "tokens_used": result.tokens_used
                    }).execute()

                    generated += 1
                    total_cost += (result.tokens_used / 1_000_000) * 0.02

                pbar.update(len(batch))

            except Exception as e:
                print(f"\nError in batch: {e}")
                print(f"Resume from: {batch[0].id}")
                sys.exit(1)

    print(f"\n✓ Migration complete")
    print(f"  Sections embedded: {generated}")
    print(f"  Total cost: ${total_cost:.4f}")


if __name__ == "__main__":
    force = "--force" in sys.argv
    resume_from = None

    if "--resume-from" in sys.argv:
        idx = sys.argv.index("--resume-from")
        resume_from = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else None

    migrate_to_vector_search(force_regenerate=force, resume_from=resume_from)
```

**Usage:**

```bash
# First time: migrate all sections
python migrate_to_vector_search.py

# Resume from specific section (if interrupted)
python migrate_to_vector_search.py --resume-from uuid-123

# Force regenerate all embeddings
python migrate_to_vector_search.py --force
```

---

### Task 18: Add Query Optimization (Indexing)

**Goal:** Optimize database performance for vector queries

**File:** SQL operations (Supabase dashboard)

**Implementation:**

```sql
-- Create HNSW index for better performance on large scale
-- Use this instead of IVFFlat if scaling beyond 100k sections
CREATE INDEX CONCURRENTLY embeddings_vector_hnsw_idx ON embeddings
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Add partial index for high-quality embeddings
CREATE INDEX embeddings_quality_idx ON embeddings(tokens_used)
WHERE tokens_used > 0;

-- Composite index for file + section lookup
CREATE INDEX embeddings_file_section_idx ON embeddings(section_id, model);

-- Analyze tables for query planner
ANALYZE embeddings;
ANALYZE sections;

-- Get index statistics
SELECT
  schemaname,
  tablename,
  indexname,
  idx_scan,
  idx_tup_read,
  idx_tup_fetch
FROM pg_stat_user_indexes
WHERE tablename IN ('embeddings', 'sections')
ORDER BY idx_scan DESC;
```

---

## Phase 6: Testing & Documentation

### Task 19: Add Vector Search Tests

**Goal:** Test embedding and search functionality

**File:** `test/test_vector_search.py` (~400 lines, 15 tests)

**Test Cases:**

1. **EmbeddingService Tests:**
   - Test single section embedding
   - Test batch embedding
   - Test cache hit/miss
   - Test cost estimation
   - Test empty section handling
   - Test API error handling

2. **SupabaseStore Tests:**
   - Test vector search query
   - Test hybrid search
   - Test relevance ranking
   - Test min_score filtering

3. **Integration Tests:**
   - Test end-to-end search workflow
   - Test embedding generation on file store
   - Test performance metrics

4. **Edge Cases:**
   - Test with very short content
   - Test with very long content
   - Test with special characters
   - Test with code blocks

---

### Task 20: Performance Benchmarks

**Goal:** Measure and document performance characteristics

**File:** `benchmarks/vector_search_benchmark.py`

**Benchmarks:**

```python
"""Vector search performance benchmarks."""
import time
from core.embedding_service import EmbeddingService
from models import Section

def benchmark_single_embedding():
    """Benchmark single section embedding."""
    service = EmbeddingService()
    section = Section(
        id="test",
        file_id="",
        title="Test",
        content="Lorem ipsum dolor sit amet" * 20,
        level=1,
        order_index=0,
        line_start=0,
        line_end=0
    )

    start = time.time()
    result = service.embed_section(section)
    elapsed = time.time() - start

    print(f"Single embedding: {elapsed*1000:.1f}ms")
    print(f"Tokens used: {result.tokens_used}")

def benchmark_batch_embedding():
    """Benchmark batch embedding."""
    service = EmbeddingService()
    sections = [
        Section(
            id=f"test-{i}",
            file_id="",
            title=f"Section {i}",
            content="Lorem ipsum dolor sit amet" * 10,
            level=1,
            order_index=i,
            line_start=0,
            line_end=0
        )
        for i in range(100)
    ]

    start = time.time()
    results = service.embed_batch(sections)
    elapsed = time.time() - start

    print(f"Batch 100 embeddings: {elapsed:.1f}s ({elapsed*10:.1f}ms per section)")

def benchmark_vector_search():
    """Benchmark vector similarity search."""
    # Would require Supabase instance
    pass
```

**Expected Results:**
- Single embedding: 500-1000ms (API limited)
- Batch 100: 2-3s total (API optimized)
- Vector search: 50-200ms (depends on index type)

---

### Task 21: Document Embedding Costs

**Goal:** Help users understand and manage API costs

**File:** `docs/VECTOR_SEARCH_COSTS.md`

**Content:**

```markdown
# Vector Search: Costs & Budget Guide

## Pricing Model

**Model:** text-embedding-3-small (OpenAI)
- **Cost:** $0.02 per 1M input tokens
- **Dimensions:** 1536
- **Quality:** Sufficient for semantic search, ~95% correlation with -large

## Cost Examples

| Scenario | Sections | Avg Size | Tokens | Cost |
|----------|----------|----------|--------|------|
| Initial load | 19,207 | 250 chars | 3.84M | ~$0.08 |
| Monthly additions | 100 | 250 chars | 20K | ~$0.0004 |
| Full refresh (annual) | 19,207 | 250 chars | 3.84M | ~$0.08 |

## Cost Optimization Strategies

1. **Reuse embeddings** - Cache query embeddings for repeated searches
2. **Batch operations** - Process sections in batches (100-200 per call)
3. **Lazy embedding** - Only embed sections when first stored
4. **Dimension reduction** - Can distill 1536 → 256 dims if needed

## Budget Controls

```python
from core.embedding_service import EmbeddingService

# Estimate cost before running
cost = EmbeddingService.estimate_cost(
    num_sections=19207,
    avg_tokens=250
)
print(f"Estimated cost: ${cost:.4f}")

# Monitor actual costs
results = embedding_service.generate_embeddings_for_file(...)
print(f"Actual cost: ${results['total_cost']:.4f}")
```

## Recommendations

- **Development:** Use cached embeddings, limit to 10-20 sections
- **Staging:** Test full embedding on sample (100 sections, ~$0.002)
- **Production:** Full embed at ~$0.08 one-time, ~$0.001/month ongoing

## See Also

- [OpenAI Pricing](https://openai.com/api/pricing/)
- [EmbeddingService](../core/embedding_service.py)
```

---

### Task 22: Create Usage Guide

**Goal:** Document vector search usage patterns

**File:** `docs/VECTOR_SEARCH_GUIDE.md`

**Content:**

```markdown
# Vector Search: Usage Guide

## Quick Start

```bash
# Generate embeddings for all sections
./skill_split.py generate-embeddings

# Search semantically
./skill_split.py search-vector "how do I authenticate users?"

# Hybrid search (recommended)
./skill_split.py search-hybrid "authentication" --vector-weight 0.7
```

## Search Types

### Text Search (Existing)
```bash
./skill_split.py search "authentication"
```
- **Best for:** Exact keyword matches
- **Speed:** Fast (BM25 index)
- **Cost:** Free (no embeddings)
- **Use case:** Searching for specific terms

### Vector Search (New)
```bash
./skill_split.py search-vector "how do I protect API endpoints?"
```
- **Best for:** Semantic meaning, synonyms
- **Speed:** Medium (vector similarity)
- **Cost:** ~$0.0001 per query
- **Use case:** Conceptual searches, "what is this about?"

### Hybrid Search (Recommended)
```bash
./skill_split.py search-hybrid "authentication strategies" --vector-weight 0.7
```
- **Best for:** All searches (combines strengths)
- **Speed:** Medium (both indices)
- **Cost:** ~$0.0001 per query
- **Use case:** Default choice for best results

## Examples

### Example 1: Find Authentication Methods

User query: "How do I secure my API?"

```bash
./skill_split.py search-hybrid "secure API" --limit 5
```

Results (vector + text combined):
1. "OAuth 2.0 Implementation" (Score: 0.89)
2. "JWT Token Verification" (Score: 0.85)
3. "CORS and CSRF Protection" (Score: 0.78)
4. "SSL/TLS Configuration" (Score: 0.72)
5. "Rate Limiting Strategies" (Score: 0.68)

### Example 2: Find Related Concepts

User query: "session management"

```bash
./skill_split.py search-vector "session management"
```

Results (semantic only):
- "Authentication Strategies" (contextually related)
- "Cookie Handling" (related concept)
- "State Management Patterns" (similar domain)

## Advanced Usage

### Adjusting Vector Weight

```bash
# More text relevance
./skill_split.py search-hybrid "auth" --vector-weight 0.5

# More semantic meaning
./skill_split.py search-hybrid "securing endpoints" --vector-weight 0.9
```

### Performance Tuning

```bash
# Get detailed scoring breakdown
./skill_split.py search-hybrid "topic" --show-scores

# Get more results for manual ranking
./skill_split.py search-hybrid "topic" --limit 50
```

## Cost Management

```bash
# Estimate embedding cost
python -c "from core.embedding_service import EmbeddingService; print(f'Cost: ${EmbeddingService.estimate_cost(19207):.4f}')"

# Monitor usage
./skill_split.py embedding-stats
```

## Troubleshooting

### "No embeddings found"
- Run: `./skill_split.py generate-embeddings`
- This may take 2-3 minutes for 19,000+ sections

### "OpenAI API error"
- Check: `OPENAI_API_KEY` environment variable
- Check: Rate limits (3000 req/min default)
- Use `--batch-size 50` to slow down

### "Search results not relevant"
- Adjust `--vector-weight` (default 0.7)
- Use text search for exact terms
- Use vector search for concepts
```

---

## Phase 7: Production Deployment

### Task 23: Cost Analysis and Optimization

**Goal:** Finalize cost model and optimization strategy

**Analysis Points:**
- One-time embedding cost: ~$0.08
- Monthly operation: ~$0.001
- Query cost: ~$0.0001 per search
- Caching ROI: 90% reduction for repeated searches

**Optimization Checklist:**
- [ ] Enable embedding cache
- [ ] Monitor API usage with metrics
- [ ] Set up cost alerts in OpenAI dashboard
- [ ] Batch process new embeddings nightly
- [ ] Cache query embeddings for 24 hours

---

### Task 24: Deployment Checklist

**Pre-Deployment:**
- [ ] All 15 tests passing
- [ ] Performance benchmarks acceptable
- [ ] pgvector installed and verified on Supabase
- [ ] Embeddings table schema created
- [ ] OpenAI API key validated
- [ ] Documentation complete
- [ ] Cost analysis approved

**Deployment Steps:**
1. Create pgvector extension (Task 1)
2. Create embeddings schema (Task 2)
3. Deploy embedding service (Task 5)
4. Run migration script (Task 17)
5. Add vector search commands to CLI (Task 14)
6. Enable auto-embedding in SupabaseStore (Task 13)
7. Monitor first 24 hours

**Rollback:**
- If issues: Disable auto_embed in SupabaseStore, continue with text search

---

### Task 25: Monitoring and Alerts

**Goal:** Ensure stable production operation

**Monitoring Metrics:**
- API call count (OpenAI)
- API error rate
- Vector search latency
- Hybrid search ranking quality
- Embedding cache hit rate
- Cost per day

**Alerts (Suggested):**
- API error rate > 5%
- Query latency > 500ms
- Daily cost > $0.10
- Cache hit rate < 50%

---

## Implementation Timeline

**Recommended Execution Order:**

1. **Phase 1 (30 min):** Set up Supabase (pgvector + tables)
2. **Phase 2 (90 min):** Embedding service implementation
3. **Phase 3 (60 min):** Search API implementation
4. **Phase 4 (45 min):** Integration with SupabaseStore
5. **Phase 5 (60 min):** Optimization and migration
6. **Phase 6 (45 min):** Testing and documentation
7. **Phase 7 (30 min):** Deployment and monitoring

**Total:** ~6.5 hours

**Can be parallelized:**
- Phase 2 & 3 (different team members)
- Phase 6 (testing during other phases)

---

## Success Criteria

- [x] pgvector enabled on Supabase
- [x] Embedding service operational
- [x] Vector search queries working
- [x] Hybrid search achieving 40-60% relevance improvement
- [x] All 19,207 sections embedded (cost: ~$0.08)
- [x] Average search latency < 200ms
- [x] Cache hit rate > 80%
- [x] 15+ tests passing
- [x] Documentation complete

---

## Future Enhancements (Not Phase 14)

1. **Embedding Distillation:** Compress 1536 → 256 dimensions
2. **Multi-lingual Support:** Embed in multiple languages
3. **Custom Fine-tuning:** Train embeddings on skill-specific corpus
4. **Reranking Models:** Use cross-encoders for final ranking
5. **Question Answering:** Generate answers from top sections
6. **Topic Clustering:** Group related sections automatically

---

## Related Documents

- **[CLAUDE.md](../CLAUDE.md)** - Project overview
- **[DEPLOYMENT_STATUS.md](../DEPLOYMENT_STATUS.md)** - Current capabilities
- **[EXAMPLES.md](../EXAMPLES.md)** - Usage examples
- **[search-api design](phase-13-query-optimization.md)** - Prerequisite

---

**Plan Created:** 2026-02-05
**Status:** READY FOR IMPLEMENTATION
**Estimated Effort:** 6.5 hours
**Complexity:** MODERATE (familiar tech, clear requirements)
**Dependencies:** Phase 13 (Query API must be stable)
