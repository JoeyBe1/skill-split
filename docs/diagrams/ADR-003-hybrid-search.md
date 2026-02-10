# ADR-003: Hybrid Search with Configurable Weights

**Status**: Accepted
**Date**: 2025-02-10
**Context**: Phase 02 - Search Fix Implementation

## Context

Users have different search needs depending on their use case:
- **Precise queries**: "git checkout command" (exact term matching)
- **Conceptual queries**: "how to undo changes" (semantic understanding)
- **Discovery queries**: "setup configuration" (broad exploration)

Single-mode search (keyword-only or vector-only) cannot satisfy all these needs effectively.

## Decision

Implement hybrid search that combines BM25 keyword ranking and vector similarity scores with a configurable weight parameter.

### Technical Details

- **Dual Search**: Run both FTS5 BM25 and pgvector searches in parallel
- **Score Normalization**: Normalize both scores to [0, 1] range
- **Weighted Average**: `hybrid_score = (w × vector_score) + ((1 - w) × text_score)`
- **Configurable Weight**: `vector_weight` parameter (0.0 = text-only, 1.0 = vector-only)

### Implementation

```python
def hybrid_search(
    query: str,
    limit: int = 10,
    vector_weight: float = 0.7
) -> List[Tuple[int, float]]:
    # Generate query embedding
    query_embedding = embedding_service.generate_embedding(query)

    # Parallel search
    vector_results = vector_search(query_embedding, limit * 2)
    text_results = text_search(query, limit * 2)

    # Merge and normalize
    vector_dict = {sid: score for sid, score in vector_results}
    text_dict = {sid: score for sid, score in text_results}

    # Calculate hybrid scores
    scored_results = []
    for section_id in set(vector_dict.keys()) | set(text_dict.keys()):
        vector_score = vector_dict.get(section_id, 0.0)
        text_score = text_dict.get(section_id, 0.0)
        combined = hybrid_score(vector_score, text_score, vector_weight)
        scored_results.append((section_id, combined))

    # Sort and return top N
    scored_results.sort(key=lambda x: x[1], reverse=True)
    return scored_results[:limit]

def hybrid_score(
    vector_similarity: float,
    text_score: float,
    vector_weight: float = 0.7
) -> float:
    return (vector_weight * vector_similarity) + ((1 - vector_weight) * text_score)
```

### Weight Presets

| Weight | Mode | Use Case |
|--------|------|----------|
| 0.0 | Keyword-only | Technical queries, exact terms |
| 0.3 | Keyword-biased | Documentation search, API references |
| 0.7 | **Default** | General purpose, balanced results |
| 1.0 | Vector-only | Conceptual queries, synonyms |

## Rationale

### Advantages

1. **Flexibility**: Single API supports multiple search modes
2. **Best of Both**: Precision from keywords, discovery from vectors
3. **Tunable**: Adjust weight based on use case
4. **Fallback**: Can use text-only when API unavailable
5. **Improved Relevance**: Combines signals for better ranking

### Alternatives Considered

1. **Separate Commands** (`search` vs `search-semantic`)
   - Rejected: Forces users to choose mode upfront
   - Harder to compare results
   - More complex CLI

2. **Automatic Mode Selection**
   - Rejected: Difficult to predict user intent
   - Unpredictable behavior
   - No user control

3. **Boost-Based Fusion** (vector results boost text results)
   - Rejected: Less flexible than weighted average
   - Harder to tune
   - Asymmetric influence

## Consequences

### Positive

- Single search API for all use cases
- Tunable balance between precision and discovery
- Parallel execution maintains performance (~110ms local, ~150ms cloud)
- Graceful degradation when vector unavailable

### Negative

- More complex implementation
- Requires API key for vector search (except weight=0.0)
- Slightly slower than single-mode search
- More parameters to understand

### Mitigation

- Sensible default (0.7) works for most cases
- Clear documentation of weight presets
- Automatic fallback to text-only on API failure
- Performance metrics tracking

## Usage Examples

```bash
# Default hybrid search (70% vector, 30% keyword)
./skill_split.py search-semantic "how to configure git"

# Keyword-biased search (30% vector, 70% keyword)
./skill_split.py search-semantic "git checkout" --vector-weight 0.3

# Pure keyword search (no API call)
./skill_split.py search-semantic "git checkout" --vector-weight 0.0

# Pure vector search (semantic only)
./skill_split.py search-semantic "version control undo" --vector-weight 1.0
```

## Related Decisions

- [ADR-001](./ADR-001-sqlite-fts5.md): SQLite FTS5 for keyword search
- [ADR-002](./ADR-002-supabase-pgvector.md): Supabase + pgvector for vector search

## References

- [Hybrid Search Implementation](../../core/hybrid_search.py)
- [Query API](../../core/query.py)
