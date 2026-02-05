"""Supabase database store for parsed documents."""
from typing import List, Optional, Tuple, Dict
from supabase import create_client, Client
from models import ParsedDocument, FileMetadata, Section, FileType


class SupabaseStore:
    """Supabase database store for parsed documents and sections."""

    def __init__(self, url: str, key: str) -> None:
        """Initialize Supabase client."""
        self.url = url
        self.key = key
        self.client: Client = create_client(url, key)

    def store_file(
        self, storage_path: str, name: str, doc: ParsedDocument, content_hash: str
    ) -> str:
        """
        Store file and sections in Supabase.

        Args:
            storage_path: Source path where file is stored
            name: File name
            doc: Parsed document
            content_hash: SHA256 hash of file content

        Returns:
            file_id (UUID string)
        """
        # Insert file metadata
        result = self.client.table("files").insert({
            "name": name,
            "storage_path": storage_path,
            "type": doc.file_type.value,
            "frontmatter": doc.frontmatter if doc.frontmatter else None,
            "hash": content_hash
        }).execute()

        # Get the UUID from the inserted row
        file_id = result.data[0]["id"]

        # Store sections recursively
        for order_index, section in enumerate(doc.sections):
            self._store_section_recursive(file_id, section, None, order_index)

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

        file_data = file_result.data[0]

        # Create FileMetadata
        metadata = FileMetadata(
            path=file_data["storage_path"],
            type=FileType(file_data["type"]),
            frontmatter=file_data.get("frontmatter"),
            hash=file_data["hash"]
        )

        # Get all sections for this file
        sections_result = self.client.table("sections").select("*").eq("file_id", file_id).execute()

        # Build section tree
        sections = self._build_section_tree(sections_result.data)

        return (metadata, sections)

    def _build_section_tree(self, sections_data: List[Dict]) -> List[Section]:
        """
        Build hierarchical section tree from flat list.

        Args:
            sections_data: Flat list of section dictionaries from database

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
                line_start=data["line_start"],
                line_end=data["line_end"]
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

    def get_all_files(self) -> List[Dict]:
        """
        Get all files in the library.

        Returns:
            List of all file dictionaries
        """
        result = self.client.table("files").select("*").execute()
        return result.data
