"""Manages file checkout/checkin operations with physical file copying."""
from pathlib import Path
from typing import Optional
from core.supabase_store import SupabaseStore
from core.recomposer import Recomposer
from handlers.factory import HandlerFactory


class CheckoutManager:
    """Manages file checkout/checkin operations with physical file copying."""

    def __init__(self, store: SupabaseStore) -> None:
        """Initialize with a SupabaseStore."""
        self.store = store
        self.recomposer = Recomposer(store)

    def checkout_file(
        self, file_id: str, user: str, target_path: Optional[str] = None
    ) -> str:
        """
        Checkout a file (copy from storage to target path).

        Args:
            file_id: UUID of file to checkout
            user: Username checking out the file
            target_path: Where to deploy the file (creates directories if needed)

        Returns:
            target_path where file was deployed
        """
        # Get file from Supabase
        result = self.store.get_file(file_id)
        if not result:
            raise ValueError(f"File not found: {file_id}")

        metadata, sections = result

        # Recompose file content
        content = self._recompose_from_sections(metadata, sections)

        # Create target directory if needed
        target = Path(target_path)
        target.parent.mkdir(parents=True, exist_ok=True)

        # Write file to target
        target.write_text(content)

        # Deploy related files (plugins need .mcp.json, hooks need scripts)
        handler = HandlerFactory.create_handler(metadata.path)
        if hasattr(handler, 'get_related_files'):
            for related_path in handler.get_related_files():
                related_content = Path(related_path).read_text()
                related_target = target.parent / Path(related_path).name
                related_target.write_text(related_content)

        # Record checkout in database
        self.store.checkout_file(
            file_id=file_id,
            user=user,
            target_path=str(target),
            notes=""
        )

        return str(target)

    def _recompose_from_sections(self, metadata, sections) -> str:
        """
        Recompose file content from metadata and sections.

        Args:
            metadata: FileMetadata object
            sections: List of Section objects

        Returns:
            Full file content as string
        """
        content = ""

        # Add frontmatter if present
        if metadata.frontmatter:
            content += "---\n"
            content += metadata.frontmatter
            if not metadata.frontmatter.endswith("\n"):
                content += "\n"
            content += "---\n\n"

        # Add sections
        for section in sections:
            content += section.get_all_content()

        return content

    def checkin(self, target_path: str) -> None:
        """
        Checkin a file (remove from target path, update database).

        Args:
            target_path: Path where file is currently deployed
        """
        # Look up checkout by target_path
        checkout_info = self.store.get_checkout_info(target_path)
        if not checkout_info:
            raise ValueError(f"No active checkout found for path: {target_path}")

        # Delete file from target path
        target = Path(target_path)
        if target.exists():
            target.unlink()

        # Update checkout status to 'returned'
        self.store.checkin_file(checkout_info["id"])
