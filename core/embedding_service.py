"""Embedding service for generating and managing text embeddings using OpenAI API."""

from typing import List, Optional, Tuple, Dict, Any
import os
import json
from datetime import datetime

try:
    import openai
    from openai import OpenAI
except ModuleNotFoundError:  # pragma: no cover
    OpenAI = None
    openai = None


class EmbeddingService:
    """Service for generating and caching text embeddings using OpenAI API."""

    # OpenAI embedding model settings
    DEFAULT_MODEL = "text-embedding-3-small"
    EMBEDDING_DIMENSIONS = 1536  # text-embedding-3-small returns 1536-dimensional vectors

    # Token estimation (rough average ~100 tokens per 1000 characters for English text)
    TOKENS_PER_1K_CHARS = 0.1

    # OpenAI pricing (as of Feb 2025)
    PRICE_PER_1M_TOKENS = 0.00002  # $0.02 per 1M tokens for text-embedding-3-small

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        supabase_client: Optional[Any] = None
    ):
        """
        Initialize the embedding service.

        Args:
            api_key: OpenAI API key. If None, reads from OPENAI_API_KEY env var
            model: Embedding model to use (default: text-embedding-3-small)
            supabase_client: Optional Supabase client for storing embeddings

        Raises:
            ImportError: If OpenAI client is not available
            ValueError: If no API key provided and OPENAI_API_KEY env var not set
        """
        if OpenAI is None:
            raise ImportError(
                "OpenAI client not available. Install 'openai' package to use embedding features."
            )

        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenAI API key not provided. Set OPENAI_API_KEY environment variable."
            )

        self.model = model
        self.client = OpenAI(api_key=self.api_key)
        self.supabase_client = supabase_client
        self._embedding_cache: Dict[str, List[float]] = {}
        self._token_usage = 0

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text string.

        Args:
            text: Text to embed

        Returns:
            List of floats representing the embedding vector (1536 dimensions)

        Raises:
            ValueError: If text is empty
            RuntimeError: If OpenAI API call fails
        """
        if not text or not text.strip():
            raise ValueError("Cannot generate embedding for empty text")

        # Remove excessive whitespace for API call
        clean_text = " ".join(text.split())

        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=clean_text
            )

            # Track token usage
            if hasattr(response, 'usage'):
                self._token_usage += response.usage.prompt_tokens

            return response.data[0].embedding

        except Exception as e:
            raise RuntimeError(f"Failed to generate embedding: {str(e)}")

    def batch_generate(self, texts: List[str], max_batch_size: int = 100) -> List[List[float]]:
        """
        Generate embeddings in batch for efficiency.

        OpenAI API supports up to 100 texts per request.
        Larger batches are more efficient in terms of API calls.

        Args:
            texts: List of text strings to embed
            max_batch_size: Max texts per API call (OpenAI limit: 100)

        Returns:
            List of embedding vectors, same length as input

        Raises:
            ValueError: If texts list is empty or contains empty strings
            RuntimeError: If OpenAI API call fails
        """
        if not texts:
            raise ValueError("Cannot generate embeddings for empty list")

        # Validate inputs
        for i, text in enumerate(texts):
            if not text or not text.strip():
                raise ValueError(f"Text at index {i} is empty")

        embeddings = []

        # Process in batches
        for i in range(0, len(texts), max_batch_size):
            batch = texts[i:i + max_batch_size]
            clean_batch = [" ".join(text.split()) for text in batch]

            try:
                response = self.client.embeddings.create(
                    model=self.model,
                    input=clean_batch
                )

                # Track token usage
                if hasattr(response, 'usage'):
                    self._token_usage += response.usage.prompt_tokens

                # Embeddings come back in order
                for item in response.data:
                    embeddings.append(item.embedding)

            except Exception as e:
                raise RuntimeError(f"Failed to generate batch embedding: {str(e)}")

        return embeddings

    def get_or_generate_embedding(
        self,
        section_id: int,
        content: str,
        content_hash: str,
        force_regenerate: bool = False
    ) -> List[float]:
        """
        Get cached embedding or generate a new one.

        This method checks if an embedding already exists in the database
        for the given content hash. If it exists and matches, returns cached.
        If content changed (different hash) or not cached, generates new.

        Args:
            section_id: ID of the section being embedded
            content: Text content to embed
            content_hash: SHA256 hash of content for change detection
            force_regenerate: If True, always generate new embedding

        Returns:
            Embedding vector

        Raises:
            ValueError: If content is empty
            RuntimeError: If embedding generation fails
        """
        if not content or not content.strip():
            raise ValueError(f"Cannot embed empty content for section {section_id}")

        # Check cache first (in-memory)
        cache_key = f"{section_id}:{content_hash}"
        if cache_key in self._embedding_cache and not force_regenerate:
            return self._embedding_cache[cache_key]

        # Check database cache if Supabase client available
        if self.supabase_client and not force_regenerate:
            try:
                result = self.supabase_client.table("section_embeddings").select(
                    "embedding"
                ).eq("section_id", section_id).eq(
                    "model_name", self.model
                ).execute()

                if result.data and len(result.data) > 0:
                    embedding = result.data[0]["embedding"]
                    self._embedding_cache[cache_key] = embedding
                    return embedding
            except Exception as e:
                # Log error but continue - fallback to generating new
                print(f"Warning: Failed to retrieve cached embedding: {str(e)}")

        # Generate new embedding
        embedding = self.generate_embedding(content)

        # Store in memory cache
        self._embedding_cache[cache_key] = embedding

        # Store in database if client available
        if self.supabase_client:
            try:
                self.supabase_client.table("section_embeddings").upsert({
                    "section_id": section_id,
                    "embedding": embedding,
                    "model_name": self.model,
                    "created_at": datetime.now().isoformat()
                }, on_conflict="section_id,model_name").execute()
            except Exception as e:
                print(f"Warning: Failed to store embedding in database: {str(e)}")

        return embedding

    def clear_cache(self) -> None:
        """Clear in-memory embedding cache."""
        self._embedding_cache.clear()

    def get_token_usage(self) -> int:
        """Get total tokens used in this session."""
        return self._token_usage

    def reset_token_usage(self) -> None:
        """Reset token usage counter."""
        self._token_usage = 0

    def estimate_cost(self, tokens_used: Optional[int] = None) -> float:
        """
        Estimate cost of embeddings in USD.

        Args:
            tokens_used: Number of tokens used. If None, uses current session total.

        Returns:
            Estimated cost in USD
        """
        tokens = tokens_used if tokens_used is not None else self._token_usage
        return (tokens / 1_000_000) * self.PRICE_PER_1M_TOKENS

    def estimate_tokens(self, text: str) -> int:
        """
        Rough estimate of tokens in text.

        Note: This is a rough estimate. OpenAI's actual tokenization may differ.
        For exact token counts, use OpenAI's tokenizer library.

        Args:
            text: Text to estimate token count for

        Returns:
            Estimated token count
        """
        char_count = len(text)
        return max(1, int(char_count * self.TOKENS_PER_1K_CHARS))

    def update_metadata(
        self,
        supabase_client: Any,
        total_sections: int,
        embedded_sections: int,
        total_tokens: int
    ) -> None:
        """
        Update embedding metadata in database.

        Args:
            supabase_client: Supabase client for database access
            total_sections: Total number of sections
            embedded_sections: Number of sections with embeddings
            total_tokens: Total tokens used for embeddings

        Raises:
            RuntimeError: If database update fails
        """
        try:
            cost_usd = self.estimate_cost(total_tokens)

            # Try to update existing metadata
            result = supabase_client.table("embedding_metadata").select("id").execute()

            if result.data and len(result.data) > 0:
                # Update existing record
                supabase_client.table("embedding_metadata").update({
                    "total_sections": total_sections,
                    "embedded_sections": embedded_sections,
                    "total_tokens_used": total_tokens,
                    "estimated_cost_usd": float(cost_usd),
                    "last_batch_at": datetime.now().isoformat()
                }).eq("id", result.data[0]["id"]).execute()
            else:
                # Insert new metadata record
                supabase_client.table("embedding_metadata").insert({
                    "total_sections": total_sections,
                    "embedded_sections": embedded_sections,
                    "total_tokens_used": total_tokens,
                    "estimated_cost_usd": float(cost_usd),
                    "last_batch_at": datetime.now().isoformat()
                }).execute()

        except Exception as e:
            raise RuntimeError(f"Failed to update embedding metadata: {str(e)}")

    def get_metadata(self, supabase_client: Any) -> Optional[Dict[str, Any]]:
        """
        Retrieve embedding metadata from database.

        Args:
            supabase_client: Supabase client for database access

        Returns:
            Dictionary with metadata or None if no metadata exists

        Raises:
            RuntimeError: If database query fails
        """
        try:
            result = supabase_client.table("embedding_metadata").select("*").execute()

            if result.data and len(result.data) > 0:
                return result.data[0]

            return None

        except Exception as e:
            raise RuntimeError(f"Failed to retrieve embedding metadata: {str(e)}")
