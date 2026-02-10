"""Embedding service for generating and managing text embeddings using OpenAI API."""

from typing import List, Optional, Tuple, Dict, Any, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import json
import time
from datetime import datetime

try:
    import openai
    from openai import OpenAI
except ModuleNotFoundError:  # pragma: no cover
    OpenAI = None
    openai = None

# Lazy import for SecretManager
SecretManager = None


def _ensure_secret_manager_imports():
    """Lazy load SecretManager when needed."""
    global SecretManager
    if SecretManager is None:
        try:
            from core.secret_manager import SecretManager as SM
            SecretManager = SM
        except ImportError:
            SecretManager = None


class RateLimitError(Exception):
    """Raised when OpenAI rate limit is exceeded."""
    pass


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
        supabase_client: Optional[Any] = None,
        secret_manager: Optional[Any] = None,
        use_secret_manager: bool = True
    ):
        """
        Initialize the embedding service.

        Args:
            api_key: OpenAI API key. If None, tries SecretManager then env var
            model: Embedding model to use (default: text-embedding-3-small)
            supabase_client: Optional Supabase client for storing embeddings
            secret_manager: Optional SecretManager instance for credential retrieval
            use_secret_manager: If True, try SecretManager before env var (default: True)

        Raises:
            ImportError: If OpenAI client is not available
            ValueError: If no API key found from any source

        Credential priority order:
            1. api_key parameter (direct)
            2. SecretManager (if use_secret_manager=True and secret_manager provided or available)
            3. OPENAI_API_KEY environment variable
        """
        if OpenAI is None:
            raise ImportError(
                "OpenAI client not available. Install 'openai' package to use embedding features."
            )

        # Ensure SecretManager imports if needed
        _ensure_secret_manager_imports()

        self._secret_manager = secret_manager
        self._api_key_source = None  # Track where key came from for debugging

        # Try to get API key from various sources
        # Priority: api_key parameter > SecretManager > environment
        if api_key:
            # Direct parameter takes highest priority
            self.api_key = api_key
            self._api_key_source = "parameter"
        elif use_secret_manager and secret_manager:
            # Use provided SecretManager
            try:
                self.api_key, source_type = secret_manager.get_secret_with_source("OPENAI_API_KEY")
                # Map SecretSourceType to string
                self._api_key_source = source_type.value
            except Exception:
                # SecretManager failed, fall back to environment
                self.api_key = os.getenv("OPENAI_API_KEY")
                if self.api_key:
                    self._api_key_source = "environment"
        elif use_secret_manager and SecretManager:
            # Create temporary SecretManager instance
            try:
                temp_manager = SecretManager()
                self.api_key, source_type = temp_manager.get_secret_with_source("OPENAI_API_KEY")
                # Map SecretSourceType to string
                self._api_key_source = source_type.value
                self._secret_manager = temp_manager
            except Exception:
                # SecretManager failed, fall back to environment
                self.api_key = os.getenv("OPENAI_API_KEY")
                if self.api_key:
                    self._api_key_source = "environment"
        else:
            # Just use environment or parameter
            self.api_key = api_key or os.getenv("OPENAI_API_KEY")
            if self.api_key:
                self._api_key_source = "environment" if not api_key else "parameter"

        if not self.api_key:
            sources = ["api_key parameter", "SecretManager", "OPENAI_API_KEY environment variable"]
            raise ValueError(
                f"OpenAI API key not found. Tried: {', '.join(sources)}. "
                f"Set OPENAI_API_KEY environment variable or provide api_key parameter."
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

    def batch_generate(
        self,
        texts: List[str],
        max_batch_size: int = 2048,
        max_tokens_per_batch: int = 8000
    ) -> List[List[float]]:
        """
        Generate embeddings in batch for efficiency.

        OpenAI API supports up to 2048 texts per request.
        Also limited by 8191 tokens per request.

        Args:
            texts: List of text strings to embed
            max_batch_size: Max texts per API call (OpenAI limit: 2048)
            max_tokens_per_batch: Max tokens per batch (OpenAI limit: 8191)

        Returns:
            List of embedding vectors, same length as input

        Raises:
            ValueError: If texts list is empty or contains empty strings
            ValueError: If max_batch_size exceeds 2048
            RuntimeError: If OpenAI API call fails
        """
        # Validate batch size
        if max_batch_size > 2048:
            raise ValueError("max_batch_size cannot exceed 2048 (OpenAI API limit)")
        if not texts:
            raise ValueError("Cannot generate embeddings for empty list")

        # Validate inputs
        for i, text in enumerate(texts):
            if not text or not text.strip():
                raise ValueError(f"Text at index {i} is empty")

        embeddings = []

        # Create batches with token awareness
        batches = self._create_token_aware_batches(texts, max_batch_size, max_tokens_per_batch)

        # Process each batch
        for batch_info in batches:
            batch_texts = batch_info['texts']
            clean_batch = [" ".join(text.split()) for text in batch_texts]

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

    @property
    def api_key_source(self) -> Optional[str]:
        """
        Get the source of the API key.

        Returns:
            Source string: "secret_manager", "parameter", "environment", or None
        """
        return self._api_key_source

    def get_api_key_source(self) -> Optional[str]:
        """
        Get the source of the API key.

        Useful for debugging and logging to understand where
        credentials are coming from.

        Returns:
            Source string: "secret_manager", "parameter", "environment", or None
        """
        return self._api_key_source

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

    def _create_token_aware_batches(
        self,
        texts: List[str],
        max_batch_size: int,
        max_tokens_per_batch: int = 8000
    ) -> List[Dict[str, Any]]:
        """
        Create batches with token count awareness.

        Ensures that no batch exceeds either the text count limit or the token limit.
        This is critical for staying within OpenAI's 8191 token per request limit.

        Args:
            texts: List of text strings to batch
            max_batch_size: Maximum number of texts per batch
            max_tokens_per_batch: Maximum tokens per batch (default: 8000, stay under 8191)

        Returns:
            List of batch dictionaries with 'texts', 'indices', and 'tokens' keys
        """
        batches = []
        current_batch = []
        current_tokens = 0
        current_indices = []

        for i, text in enumerate(texts):
            text_tokens = self.estimate_tokens(text)

            # Check if adding this text would exceed limits
            if (len(current_batch) >= max_batch_size or
                current_tokens + text_tokens > max_tokens_per_batch):
                # Start new batch
                if current_batch:
                    batches.append({
                        'texts': current_batch,
                        'indices': current_indices,
                        'tokens': current_tokens
                    })
                current_batch = []
                current_tokens = 0
                current_indices = []

            current_batch.append(text)
            current_tokens += text_tokens
            current_indices.append(i)

        # Add final batch
        if current_batch:
            batches.append({
                'texts': current_batch,
                'indices': current_indices,
                'tokens': current_tokens
            })

        return batches

    def _process_batch(self, batch_info: Dict[str, Any]) -> List[List[float]]:
        """
        Process a single batch and return embeddings.

        Args:
            batch_info: Dictionary with 'texts' and 'tokens' keys

        Returns:
            List of embedding vectors
        """
        return self.batch_generate(batch_info['texts'], max_batch_size=len(batch_info['texts']))

    def batch_generate_parallel(
        self,
        texts: List[str],
        max_batch_size: int = 2048,
        max_workers: int = 5,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[Optional[List[float]]]:
        """
        Generate embeddings in parallel batches for maximum speed.

        Processes multiple batches concurrently using ThreadPoolExecutor.
        Maximizes throughput while respecting OpenAI rate limits.

        Args:
            texts: List of text strings to embed
            max_batch_size: Max texts per API call (default: 2048)
            max_workers: Max concurrent API calls (default: 5)
            progress_callback: Optional callback(current, total) for progress updates

        Returns:
            List of embedding vectors, same length as input.
            Failed embeddings are None (partial success handling).
        """
        if not texts:
            return []

        # Create batches with token awareness
        batches = self._create_token_aware_batches(texts, max_batch_size)

        embeddings: List[Optional[List[float]]] = [None] * len(texts)
        completed = 0

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all batch jobs
            future_to_batch = {
                executor.submit(self._process_batch, batch): batch
                for batch in batches
            }

            # Collect results as they complete
            for future in as_completed(future_to_batch):
                batch_info = future_to_batch[future]
                try:
                    result = future.result()
                    # Map results back to original indices
                    for idx, embedding in zip(batch_info['indices'], result):
                        embeddings[idx] = embedding
                    completed += len(batch_info['indices'])
                    if progress_callback:
                        progress_callback(completed, len(texts))
                except Exception as e:
                    # Store error for this batch, continue with others
                    print(f"Warning: Batch failed: {str(e)}")
                    for idx in batch_info['indices']:
                        embeddings[idx] = None  # Mark as failed

        return embeddings

    def batch_generate_with_retry(
        self,
        texts: List[str],
        max_retries: int = 3,
        backoff_base: float = 1.0
    ) -> List[List[float]]:
        """
        Generate embeddings with automatic retry on rate limit.

        Implements exponential backoff for rate limit errors.

        Args:
            texts: List of text strings to embed
            max_retries: Max retry attempts per batch
            backoff_base: Base for exponential backoff (seconds)

        Returns:
            List of embedding vectors, same length as input

        Raises:
            RuntimeError: If all retries exhausted
        """
        embeddings = []
        batches = self._create_token_aware_batches(texts, 2048)

        for batch in batches:
            retries = 0
            while retries < max_retries:
                try:
                    result = self._process_batch(batch)
                    embeddings.extend(result)
                    break
                except Exception as e:
                    error_str = str(e).lower()
                    if ('rate_limit' in error_str or '429' in error_str) and retries < max_retries - 1:
                        wait_time = backoff_base * (2 ** retries)
                        print(f"Rate limited. Waiting {wait_time:.1f}s...")
                        time.sleep(wait_time)
                        retries += 1
                    else:
                        raise RuntimeError(f"Failed to generate batch embedding after {retries} retries: {str(e)}")

        return embeddings

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
