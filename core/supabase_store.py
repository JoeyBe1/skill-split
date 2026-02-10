"""Supabase database store for parsed documents."""
from typing import List, Optional, Tuple, Dict, Any
import os
try:
    from supabase import create_client, Client
except ModuleNotFoundError:  # pragma: no cover - handled at runtime
    create_client = None
    Client = object
from models import ParsedDocument, FileMetadata, Section, FileType

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


class SupabaseStore:
    """Supabase database store for parsed documents and sections."""

    def __init__(
        self,
        url: Optional[str] = None,
        key: Optional[str] = None,
        secret_manager: Optional[Any] = None,
        use_secret_manager: bool = True
    ) -> None:
        """
        Initialize Supabase client.

        Args:
            url: Supabase project URL. If None, tries SecretManager then SUPABASE_URL env var
            key: Supabase API key. If None, tries SecretManager then SUPABASE_KEY env var
            secret_manager: Optional SecretManager instance for credential retrieval
            use_secret_manager: If True, try SecretManager before env vars (default: True)

        Raises:
            ImportError: If Supabase client is not available
            ValueError: If credentials not found from any source

        Credential priority order:
            1. url/key parameters (direct)
            2. SecretManager (if use_secret_manager=True)
            3. SUPABASE_URL/SUPABASE_KEY environment variables
        """
        if create_client is None:
            raise ImportError("Supabase client not available. Install 'supabase' package to use Supabase features.")

        # Ensure SecretManager imports if needed
        _ensure_secret_manager_imports()

        self._secret_manager = secret_manager
        self._url_source = None
        self._key_source = None

        # Try to get URL from various sources
        if url:
            # Direct parameter takes highest priority
            self.url = url
            self._url_source = "parameter"
        elif use_secret_manager and secret_manager:
            # Use provided SecretManager
            try:
                self.url, url_source_type = secret_manager.get_secret_with_source("SUPABASE_URL")
                self._url_source = url_source_type.value
            except Exception:
                # Try alternate key names
                try:
                    self.url, url_source_type = secret_manager.get_secret_with_source("supabase_url")
                    self._url_source = url_source_type.value
                except Exception:
                    # Fall back to environment
                    self.url = os.getenv("SUPABASE_URL")
                    if self.url:
                        self._url_source = "environment"
        elif use_secret_manager and SecretManager:
            # Create temporary SecretManager instance
            try:
                temp_manager = SecretManager()
                self.url, url_source_type = temp_manager.get_secret_with_source("SUPABASE_URL")
                self._url_source = url_source_type.value
                self._secret_manager = temp_manager
            except Exception:
                # Try alternate key name
                try:
                    self.url, url_source_type = temp_manager.get_secret_with_source("supabase_url")
                    self._url_source = url_source_type.value
                except Exception:
                    # Fall back to environment
                    self.url = os.getenv("SUPABASE_URL")
                    if self.url:
                        self._url_source = "environment"
        else:
            # Just use environment or parameter
            self.url = url or os.getenv("SUPABASE_URL")
            if self.url:
                self._url_source = "environment" if not url else "parameter"

        # Try to get key from various sources
        if key:
            # Direct parameter takes highest priority
            self.key = key
            self._key_source = "parameter"
        elif use_secret_manager and secret_manager:
            # Use provided SecretManager
            try:
                self.key, key_source_type = secret_manager.get_secret_with_source("SUPABASE_KEY")
                self._key_source = key_source_type.value
            except Exception:
                # Try alternate key names
                try:
                    self.key, key_source_type = secret_manager.get_secret_with_source("supabase_key")
                    self._key_source = key_source_type.value
                except Exception:
                    # Fall back to environment
                    self.key = self._get_supabase_key_from_env()
                    if self.key:
                        self._key_source = "environment"
        elif use_secret_manager and SecretManager:
            # Create temporary SecretManager instance
            try:
                temp_manager = SecretManager()
                self.key, key_source_type = temp_manager.get_secret_with_source("SUPABASE_KEY")
                self._key_source = key_source_type.value
            except Exception:
                # Try alternate key name
                try:
                    self.key, key_source_type = temp_manager.get_secret_with_source("supabase_key")
                    self._key_source = key_source_type.value
                except Exception:
                    # Fall back to environment
                    self.key = self._get_supabase_key_from_env()
                    if self.key:
                        self._key_source = "environment"
        else:
            # Just use environment or parameter
            self.key = key or self._get_supabase_key_from_env()
            if self.key:
                self._key_source = "environment" if not key else "parameter"

        # Validate credentials
        if not self.url:
            raise ValueError(
                "Supabase URL not found. Tried: url parameter, SecretManager (SUPABASE_URL, supabase_url), "
                "SUPABASE_URL environment variable. Provide url parameter or set SUPABASE_URL environment variable."
            )

        if not self.key:
            raise ValueError(
                "Supabase key not found. Tried: key parameter, SecretManager (SUPABASE_KEY, supabase_key), "
                "SUPABASE_KEY/SUPABASE_PUBLISHABLE_KEY/SUPABASE_SECRET_KEY environment variables. "
                "Provide key parameter or set SUPABASE_KEY environment variable."
            )

        self.client: Client = create_client(self.url, self.key)

    def _get_supabase_key_from_env(self) -> Optional[str]:
        """
        Get Supabase key from environment variables.

        Tries multiple environment variable names in order:
        SUPABASE_KEY, SUPABASE_PUBLISHABLE_KEY, SUPABASE_SECRET_KEY

        Returns:
            Key value or None if not found
        """
        return (
            os.getenv("SUPABASE_KEY")
            or os.getenv("SUPABASE_PUBLISHABLE_KEY")
            or os.getenv("SUPABASE_SECRET_KEY")
        )

    @classmethod
    def from_config(cls, config_path: Optional[str] = None) -> 'SupabaseStore':
        """
        Create SupabaseStore from SecretManager config.

        Args:
            config_path: Path to secrets config file (default: ~/.claude/secrets.json)

        Returns:
            SupabaseStore instance with credentials from SecretManager

        Raises:
            ImportError: If SecretManager not available
            ValueError: If credentials not found in config
        """
        _ensure_secret_manager_imports()
        if SecretManager is None:
            raise ImportError("SecretManager not available. Install core.secret_manager or provide url/key parameters.")

        secret_manager = SecretManager(config_path=config_path)
        return cls(secret_manager=secret_manager)

    def get_credential_source(self) -> Dict[str, Optional[str]]:
        """
        Get the source of Supabase credentials.

        Useful for debugging and logging to understand where
        credentials are coming from.

        Returns:
            Dictionary with 'url_source' and 'key_source' keys
        """
        return {
            'url_source': self._url_source,
            'key_source': self._key_source
        }

    def store_file(
        self, storage_path: str, name: str, doc: ParsedDocument, content_hash: str
    ) -> str:
        """
        Store or update file and sections in Supabase.

        Args:
            storage_path: Source path where file is stored
            name: File name
            doc: Parsed document
            content_hash: SHA256 hash of file content

        Returns:
            file_id (UUID string)
        """
        # Check if file already exists
        existing = self.client.table("files").select("id").eq("storage_path", storage_path).execute()

        if existing.data:
            # File exists - update it
            file_id = existing.data[0]["id"]

            # Delete all existing sections for this file
            self.client.table("sections").delete().eq("file_id", file_id).execute()

            # Update file metadata
            self.client.table("files").update({
                "name": name,
                "type": doc.file_type.value,
                "frontmatter": doc.frontmatter if doc.frontmatter else None,
                "hash": content_hash
            }).eq("id", file_id).execute()
        else:
            # New file - insert it
            result = self.client.table("files").insert({
                "name": name,
                "storage_path": storage_path,
                "type": doc.file_type.value,
                "frontmatter": doc.frontmatter if doc.frontmatter else None,
                "hash": content_hash
            }).execute()

            file_id = result.data[0]["id"]

        # Store sections recursively
        for order_index, section in enumerate(doc.sections):
            self._store_section_recursive(file_id, section, None, order_index)

        # Generate embeddings for sections if enabled
        if os.getenv('ENABLE_EMBEDDINGS', 'false') == 'true':
            try:
                self._generate_section_embeddings(file_id, doc.sections)
            except Exception as e:
                # Log but don't fail - embeddings are optional
                print(f"Warning: Failed to generate embeddings: {str(e)}", file=__import__('sys').stderr)

        return file_id

    def _store_section_recursive(
        self, file_id: str, section, parent_id: Optional[str], order_index: int
    ) -> str:
        """
        Recursively store a section and its children.

        Args:
            file_id: UUID of the parent file
            section: Section object to store
            parent_id: UUID of parent section (None for top-level)
            order_index: Order within parent's children

        Returns:
            section_id (UUID string)
        """
        # Insert section
        result = self.client.table("sections").insert({
            "file_id": file_id,
            "parent_id": parent_id,
            "level": section.level,
            "title": section.title,
            "content": section.content,
            "order_index": order_index,
            "line_start": section.line_start,
            "line_end": section.line_end
        }).execute()

        section_id = result.data[0]["id"]

        # Store children recursively
        for child_index, child in enumerate(section.children):
            self._store_section_recursive(file_id, child, section_id, child_index)

        return section_id

    def get_file(self, file_id: str) -> Optional[Tuple[FileMetadata, List[Section]]]:
        """
        Retrieve file with sections from Supabase.

        Args:
            file_id: UUID of the file to retrieve

        Returns:
            Tuple of (FileMetadata, List[Section]) or None if not found
        """
        # Get file metadata
        file_result = self.client.table("files").select("*").eq("id", file_id).execute()

        if not file_result.data:
            return None

        return self._build_file_from_row(file_result.data[0])

    def get_file_by_path(self, storage_path: str) -> Optional[Tuple[FileMetadata, List[Section]]]:
        """
        Retrieve file with sections from Supabase by storage path.

        Args:
            storage_path: Original storage path

        Returns:
            Tuple of (FileMetadata, List[Section]) or None if not found
        """
        file_result = self.client.table("files").select("*").eq("storage_path", storage_path).execute()

        if not file_result.data:
            return None

        return self._build_file_from_row(file_result.data[0])

    def list_files_by_prefix(self, prefix: str) -> List[Dict]:
        """
        List files whose storage_path starts with the given prefix.

        Args:
            prefix: Directory-like prefix

        Returns:
            List of file dictionaries
        """
        like_pattern = f"{prefix.rstrip('/')}/%"
        result = self.client.table("files").select("*").like("storage_path", like_pattern).execute()
        return result.data

    def _build_file_from_row(self, file_data: Dict) -> Tuple[FileMetadata, List[Section]]:
        """
        Build FileMetadata and section tree from a files row.
        """
        metadata = FileMetadata(
            path=file_data["storage_path"],
            type=FileType(file_data["type"]),
            frontmatter=file_data.get("frontmatter"),
            hash=file_data["hash"]
        )

        sections_result = self.client.table("sections").select("*").eq("file_id", file_data["id"]).execute()
        sections = self._build_section_tree(sections_result.data, file_data["id"], file_data["type"])
        return (metadata, sections)

    def _build_section_tree(self, sections_data: List[Dict], file_id: str, file_type: str) -> List[Section]:
        """
        Build hierarchical section tree from flat list.

        Args:
            sections_data: Flat list of section dictionaries from database
            file_id: File ID for metadata
            file_type: File type for metadata

        Returns:
            List of top-level Section objects with children populated
        """
        # Create Section objects indexed by ID
        sections_by_id: Dict[str, Section] = {}
        for data in sections_data:
            section = Section(
                level=data["level"],
                title=data["title"],
                content=data["content"],
                line_start=data.get("line_start", 0),
                line_end=data.get("line_end", 0),
                closing_tag_prefix=data.get("closing_tag_prefix", ""),
                file_id=file_id,
                file_type=FileType(file_type)
            )
            sections_by_id[data["id"]] = section

        # Build parent-child relationships
        top_level_sections = []
        for data in sections_data:
            section = sections_by_id[data["id"]]
            parent_id = data.get("parent_id")

            if parent_id is None:
                # Top-level section
                top_level_sections.append(section)
            else:
                # Child section - add to parent
                parent = sections_by_id.get(parent_id)
                if parent:
                    parent.add_child(section)

        return top_level_sections

    def checkout_file(
        self, file_id: str, user: str, target_path: str, notes: str = ""
    ) -> str:
        """
        Record file checkout in database.

        Args:
            file_id: UUID of file being checked out
            user: Username checking out the file
            target_path: Where file will be deployed
            notes: Optional notes about checkout

        Returns:
            checkout_id (UUID string)
        """
        result = self.client.table("checkouts").insert({
            "file_id": file_id,
            "section_id": None,
            "user_name": user,
            "target_path": target_path,
            "status": "active",
            "notes": notes if notes else None
        }).execute()

        return result.data[0]["id"]

    def checkin_file(self, checkout_id: str) -> None:
        """
        Mark checkout as returned (update status='returned', set checked_in_at).

        Args:
            checkout_id: UUID of checkout to mark as returned
        """
        from datetime import datetime, timezone

        self.client.table("checkouts").update({
            "status": "returned",
            "checked_in_at": datetime.now(timezone.utc).isoformat()
        }).eq("id", checkout_id).execute()

    def get_active_checkouts(self, user: Optional[str] = None) -> List[Dict]:
        """
        Get all active checkouts (optionally filtered by user).

        Args:
            user: Optional username to filter by

        Returns:
            List of checkout dictionaries
        """
        query = self.client.table("checkouts").select("*").eq("status", "active")

        if user:
            query = query.eq("user_name", user)

        result = query.execute()
        return result.data

    def get_checkout_info(self, target_path: str) -> Optional[Dict]:
        """
        Get checkout info for a deployed file by its path.

        Args:
            target_path: Path where file is deployed

        Returns:
            Checkout dictionary or None if not found
        """
        result = self.client.table("checkouts").select("*").eq("target_path", target_path).eq("status", "active").execute()

        if not result.data:
            return None

        return result.data[0]

    def search_files(self, query: str) -> List[Dict]:
        """
        Search files by name or type.

        Args:
            query: Search query string

        Returns:
            List of matching file dictionaries
        """
        # Search by name (case-insensitive substring match)
        result = self.client.table("files").select("*").ilike("name", f"%{query}%").execute()
        return result.data

    def get_section(self, section_id: str) -> Optional[Tuple[str, Section]]:
        """
        Get single section by ID with file_type metadata.

        Args:
            section_id: UUID of the section

        Returns:
            Tuple of (section_id, Section) with file_type populated if found, None otherwise
        """
        # Use Supabase's foreign key join to get file_type
        response = self.client.table("sections").select(
            "id, level, title, content, line_start, line_end, closing_tag_prefix, "
            "file_id, files!inner(type)"
        ).eq("id", section_id).execute()

        if not response.data:
            return None

        row = response.data[0]
        section = Section(
            level=row["level"],
            title=row["title"],
            content=row["content"],
            line_start=row.get("line_start", 0),
            line_end=row.get("line_end", 0),
            closing_tag_prefix=row.get("closing_tag_prefix", ""),
            file_id=row["file_id"],
            file_type=FileType(row["files"]["type"]) if "files" in row and "type" in row["files"] else None,
        )
        return (row["id"], section)

    def get_next_section(
        self, section_id: str, file_id: str
    ) -> Optional[Tuple[str, Section]]:
        """
        Get next section for progressive disclosure.

        Finds the section that follows the given section_id in the file,
        respecting the hierarchical order.

        Args:
            section_id: Current section ID (UUID)
            file_id: File ID (UUID) to search within

        Returns:
            Tuple of (next_section_id, Section) or None if no next section
        """
        # First get current section's order_index and parent_id
        current_response = self.client.table("sections").select(
            "parent_id, order_index"
        ).eq("id", section_id).eq("file_id", file_id).execute()

        if not current_response.data:
            return None

        current = current_response.data[0]
        parent_id = current.get("parent_id")
        order_index = current["order_index"]

        # Find next section by order_index within same file and parent
        # Handle NULL parent_id case for Supabase query
        if parent_id is None:
            # For top-level sections, look for NULL parent_id
            query = self.client.table("sections").select(
                "id, level, title, content, line_start, line_end, closing_tag_prefix, "
                "file_id, files!inner(type)"
            ).eq("file_id", file_id).is_("parent_id", None).gt("order_index", order_index)
        else:
            # For child sections, match parent_id
            query = self.client.table("sections").select(
                "id, level, title, content, line_start, line_end, closing_tag_prefix, "
                "file_id, files!inner(type)"
            ).eq("file_id", file_id).eq("parent_id", parent_id).gt("order_index", order_index)

        response = query.order("order_index", asc=True).limit(1).execute()

        if not response.data:
            return None

        row = response.data[0]
        section = Section(
            level=row["level"],
            title=row["title"],
            content=row["content"],
            line_start=row.get("line_start", 0),
            line_end=row.get("line_end", 0),
            closing_tag_prefix=row.get("closing_tag_prefix", ""),
            file_id=row["file_id"],
            file_type=FileType(row["files"]["type"]) if "files" in row and "type" in row["files"] else None,
        )
        return (row["id"], section)

    def search_sections(
        self, query: str, file_id: Optional[str] = None
    ) -> List[Tuple[str, Section]]:
        """
        Search sections by title/content.

        Performs case-insensitive search across section titles and content.
        If file_id is provided, restricts search to that file.

        Args:
            query: Search query string
            file_id: Optional file ID (UUID) to restrict search to

        Returns:
            List of (section_id, Section) tuples matching the query
        """
        # Build query with search in title and content
        query_builder = self.client.table("sections").select(
            "id, level, title, content, line_start, line_end, closing_tag_prefix, "
            "file_id, files!inner(type)"
        )

        # Add search filter (case-insensitive)
        query_builder = query_builder.or_(f"title.ilike.%{query}%,content.ilike.%{query}%")

        # Restrict to file if specified
        if file_id:
            query_builder = query_builder.eq("file_id", file_id)

        response = query_builder.execute()

        results = []
        for row in response.data:
            section = Section(
                level=row["level"],
                title=row["title"],
                content=row["content"],
                line_start=row.get("line_start", 0),
                line_end=row.get("line_end", 0),
                closing_tag_prefix=row.get("closing_tag_prefix", ""),
                file_id=row["file_id"],
                file_type=FileType(row["files"]["type"]) if "files" in row and "type" in row["files"] else None,
            )
            results.append((row["id"], section))

        return results

    def get_all_files(self) -> List[Dict]:
        """
        Get all files in the library.

        Returns:
            List of all file dictionaries
        """
        result = self.client.table("files").select("*").execute()
        return result.data

    def _generate_section_embeddings(self, file_id: str, sections: List[Section]) -> None:
        """
        Generate embeddings for all sections in a file using batch processing.

        This is called automatically when ENABLE_EMBEDDINGS=true during file storage.
        Embeddings are generated using OpenAI's text-embedding-3-small model.

        Args:
            file_id: UUID of the file being stored
            sections: List of sections to generate embeddings for

        Raises:
            Exception: If embedding generation fails (non-fatal, logged as warning)
        """
        try:
            from core.embedding_service import EmbeddingService
        except ImportError:
            # Embedding service not available
            return

        # Try to get OpenAI API key from SecretManager if available
        try:
            if self._secret_manager:
                embedding_service = EmbeddingService(secret_manager=self._secret_manager)
            else:
                # Fall back to environment
                openai_key = os.getenv('OPENAI_API_KEY')
                if not openai_key:
                    return
                embedding_service = EmbeddingService(openai_key)
        except Exception:
            # Embedding service initialization failed
            return

        # Flatten sections to process all (including children)
        def flatten_sections(section_list):
            """Recursively flatten section hierarchy."""
            flat = []
            for section in section_list:
                flat.append(section)
                if section.children:
                    flat.extend(flatten_sections(section.children))
            return flat

        all_sections = flatten_sections(sections)

        # Get section IDs from database
        result = self.client.table("sections").select("id, content").eq("file_id", file_id).execute()

        if not result.data:
            return

        # Collect sections that need embeddings
        sections_to_embed = []
        for db_section in result.data:
            section_id = db_section['id']
            content = db_section['content']

            if not content or not content.strip():
                continue

            # Check if embedding already exists
            existing = self.client.table("section_embeddings").select("section_id").eq(
                "section_id", section_id
            ).eq("model_name", "text-embedding-3-small").execute()

            if not existing.data:
                sections_to_embed.append({
                    'id': section_id,
                    'content': content
                })

        if not sections_to_embed:
            return

        # Progress callback
        def progress_callback(current: int, total: int):
            pct = (current / total) * 100
            print(f"Generating embeddings: {current}/{total} ({pct:.1f}%)", end='\r')

        # Collect texts and section IDs
        texts = [s['content'] for s in sections_to_embed]
        section_ids = [s['id'] for s in sections_to_embed]

        try:
            # Generate embeddings in parallel batches
            embeddings = embedding_service.batch_generate_parallel(
                texts,
                progress_callback=progress_callback
            )

            # Store results
            for section_id, embedding in zip(section_ids, embeddings):
                if embedding is not None:  # Skip failed embeddings
                    self.client.table("section_embeddings").upsert({
                        "section_id": section_id,
                        "embedding": embedding,
                        "model_name": "text-embedding-3-small"
                    }, on_conflict="section_id,model_name").execute()

            # Print final progress
            print(f"Generating embeddings: {len(texts)}/{len(texts)} (100.0%)")

        except Exception as e:
            # Log error but don't fail - embeddings are optional
            print(f"Warning: Failed to generate batch embeddings: {str(e)}", file=__import__('sys').stderr)

    def batch_generate_embeddings(
        self,
        sections: List[Dict[str, Any]],
        embedding_service: Any,
        force_regenerate: bool = False
    ) -> Dict[str, List[float]]:
        """
        Generate embeddings for multiple sections in batch.

        Args:
            sections: List of section dicts with id, content, content_hash
            embedding_service: EmbeddingService instance
            force_regenerate: If True, regenerate all embeddings

        Returns:
            Dict mapping section_id to embedding vector
        """
        # Filter sections that need embeddings
        sections_to_embed = []
        for section in sections:
            section_id = section['id']

            if force_regenerate:
                sections_to_embed.append(section)
            else:
                # Check if embedding already exists
                existing = self.client.table("section_embeddings").select("section_id").eq(
                    "section_id", section_id
                ).eq("model_name", "text-embedding-3-small").execute()

                if not existing.data:
                    sections_to_embed.append(section)

        if not sections_to_embed:
            return {}

        # Progress callback
        def progress_callback(current: int, total: int):
            pct = (current / total) * 100
            print(f"Generating embeddings: {current}/{total} ({pct:.1f}%)", end='\r')

        # Collect texts and indices
        texts = [s['content'] for s in sections_to_embed]

        # Generate embeddings in parallel
        embeddings = embedding_service.batch_generate_parallel(
            texts,
            progress_callback=progress_callback
        )

        # Store results
        section_embeddings: Dict[str, List[float]] = {}
        for section, embedding in zip(sections_to_embed, embeddings):
            if embedding is not None:  # Skip failed embeddings
                self.client.table("section_embeddings").upsert({
                    "section_id": section['id'],
                    "embedding": embedding,
                    "model_name": "text-embedding-3-small"
                }, on_conflict="section_id,model_name").execute()
                section_embeddings[section['id']] = embedding

        # Print final progress
        print(f"Generating embeddings: {len(texts)}/{len(texts)} (100.0%)")

        return section_embeddings

    def _has_embedding(self, section_id: str) -> bool:
        """
        Check if a section already has an embedding.

        Args:
            section_id: Section UUID to check

        Returns:
            True if embedding exists, False otherwise
        """
        try:
            result = self.client.table("section_embeddings").select("section_id").eq(
                "section_id", section_id
            ).eq("model_name", "text-embedding-3-small").execute()
            return len(result.data) > 0
        except Exception:
            return False

    def _store_embedding(self, section_id: str, embedding: List[float]) -> None:
        """
        Store an embedding for a section.

        Args:
            section_id: Section UUID
            embedding: Embedding vector
        """
        try:
            self.client.table("section_embeddings").upsert({
                "section_id": section_id,
                "embedding": embedding,
                "model_name": "text-embedding-3-small"
            }, on_conflict="section_id,model_name").execute()
        except Exception as e:
            print(f"Warning: Failed to store embedding for section {section_id}: {str(e)}", file=__import__('sys').stderr)
