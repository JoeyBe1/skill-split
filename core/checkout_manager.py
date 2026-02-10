"""Manages file checkout/checkin operations with physical file copying."""
import json
import logging
from pathlib import Path
from typing import Optional, List, Set
from core.supabase_store import SupabaseStore
from core.recomposer import Recomposer
from models import FileType


logger = logging.getLogger(__name__)


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
        Checkout a file (copy from storage to target path) with transaction safety.

        Implements compensating actions for filesystem operations since database
        transactions cannot rollback file writes.

        Args:
            file_id: UUID of file to checkout
            user: Username checking out the file
            target_path: Where to deploy the file (creates directories if needed)

        Returns:
            target_path where file was deployed

        Raises:
            ValueError: If file not found or checkout fails
            IOError: If filesystem operations fail with rollback attempted
        """
        # Track all files deployed for compensating actions
        deployed_files: Set[Path] = set()

        try:
            # Step 1: Get file from Supabase (no side effects)
            result = self.store.get_file(file_id)
            if not result:
                raise ValueError(f"File not found: {file_id}")

            metadata, sections = result

            # Step 2: Recompose file content (in-memory)
            content = self._recompose_from_sections(metadata, sections)

            # Step 3: Create target directory if needed
            target = Path(target_path)
            target.parent.mkdir(parents=True, exist_ok=True)

            # Step 4: Write primary file to target (filesystem - cannot rollback)
            target.write_text(content)
            deployed_files.add(target)

            # Step 5: Deploy related files for multi-file components (filesystem)
            related_targets = self._deploy_related_files(metadata, target)
            deployed_files.update(related_targets)

            # Step 6: Record checkout in database (can fail)
            # If this fails, we need to rollback filesystem writes
            try:
                self.store.checkout_file(
                    file_id=file_id,
                    user=user,
                    target_path=str(target),
                    notes=""
                )
            except Exception as db_error:
                # Compensating action: remove deployed files
                logger.error(f"Database checkout failed for {file_id}, rolling back filesystem changes")
                self._rollback_deployment(deployed_files)
                raise IOError(
                    f"Checkout recording failed: {str(db_error)}. "
                    f"Rolled back {len(deployed_files)} deployed file(s)."
                ) from db_error

            return str(target)

        except (ValueError, IOError):
            # Re-raise known errors
            raise
        except Exception as e:
            # Unexpected error - attempt rollback if files were deployed
            if deployed_files:
                logger.error(f"Unexpected error during checkout: {str(e)}, rolling back deployment")
                self._rollback_deployment(deployed_files)
            raise IOError(f"Checkout failed: {str(e)}")

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

        # For JSON-based components, return original JSON as-is
        if metadata.type in (FileType.PLUGIN, FileType.HOOK, FileType.CONFIG):
            return metadata.frontmatter or ""

        # For script files, concatenate sections in order
        if metadata.type == FileType.SCRIPT:
            return self._recompose_script(sections)

        # Add frontmatter if present (markdown/yaml files)
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

    def _recompose_script(self, sections) -> str:
        """Recompose script content from sections in original order."""
        sorted_sections = sorted(sections, key=lambda s: s.line_start)
        return "".join(section.content for section in sorted_sections)

    def _rollback_deployment(self, deployed_files: Set[Path]) -> None:
        """
        Remove deployed files as compensating action for failed checkout.

        Args:
            deployed_files: Set of file paths to remove
        """
        for file_path in deployed_files:
            try:
                if file_path.exists():
                    file_path.unlink()
                    logger.debug(f"Rolled back file: {file_path}")
            except Exception as e:
                # Log but continue with other rollbacks
                logger.warning(f"Failed to rollback {file_path}: {str(e)}")

        # Also try to remove empty parent directories
        for file_path in deployed_files:
            try:
                parent = file_path.parent
                if parent.exists() and not any(parent.iterdir()):
                    parent.rmdir()
                    logger.debug(f"Removed empty directory: {parent}")
            except Exception:
                pass  # Best effort cleanup

    def _deploy_related_files(self, metadata, target: Path) -> Set[Path]:
        """
        Deploy related files for multi-file components using Supabase metadata.

        Returns set of deployed file paths for rollback tracking.

        This avoids relying on local filesystem state.
        """
        deployed: Set[Path] = set()

        if metadata.type not in (FileType.PLUGIN, FileType.HOOK):
            return deployed

        base_dir = str(Path(metadata.path).parent)
        related_paths: List[str] = []

        if metadata.type == FileType.PLUGIN:
            related_paths = self._find_plugin_related_paths(base_dir, metadata.path)
        elif metadata.type == FileType.HOOK:
            related_paths = self._find_hook_related_paths(base_dir, metadata.frontmatter)

        for related_path in related_paths:
            related = self.store.get_file_by_path(related_path)
            if not related:
                continue
            related_metadata, related_sections = related
            related_content = self._recompose_from_sections(related_metadata, related_sections)

            # Preserve relative path within component directory when possible
            rel_path = Path(related_metadata.path)
            try:
                rel_relative = rel_path.relative_to(Path(base_dir))
            except ValueError:
                rel_relative = rel_path.name

            related_target = target.parent / rel_relative
            related_target.parent.mkdir(parents=True, exist_ok=True)
            related_target.write_text(related_content)
            deployed.add(related_target)

        return deployed

    def _find_plugin_related_paths(self, base_dir: str, primary_path: str) -> List[str]:
        """Find related plugin files in Supabase for a plugin component."""
        related: List[str] = []
        files = self.store.list_files_by_prefix(base_dir)
        for file_data in files:
            storage_path = file_data.get("storage_path", "")
            if storage_path == primary_path:
                continue
            name = Path(storage_path).name
            if name == "hooks.json" or name.endswith(".mcp.json"):
                related.append(storage_path)
        return related

    def _find_hook_related_paths(self, base_dir: str, frontmatter: Optional[str]) -> List[str]:
        """Find related hook script files in Supabase for a hooks.json component."""
        if not frontmatter:
            return []

        try:
            hooks_data = json.loads(frontmatter)
        except json.JSONDecodeError:
            return []

        # Detect plugin-style hook file
        if isinstance(hooks_data, dict) and "hooks" in hooks_data and isinstance(hooks_data.get("hooks"), dict):
            hook_map = hooks_data.get("hooks", {})
        else:
            hook_map = hooks_data if isinstance(hooks_data, dict) else {}

        expected_names = {f"{name}.sh" for name in hook_map.keys()}
        if not expected_names:
            return []

        related: List[str] = []
        files = self.store.list_files_by_prefix(base_dir)
        for file_data in files:
            storage_path = file_data.get("storage_path", "")
            name = Path(storage_path).name
            if name in expected_names:
                related.append(storage_path)
        return related

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
