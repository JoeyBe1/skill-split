"""File hashing utilities for verification."""
import hashlib
from pathlib import Path
from typing import Iterable


def compute_file_hash(file_path: str) -> str:
    """Compute SHA256 hash of a file.

    Args:
        file_path: Path to the file to hash

    Returns:
        SHA256 hexdigest string, or empty string if file not found
    """
    path = Path(file_path)

    if not path.exists():
        return ""

    sha256_hash = hashlib.sha256()

    with open(path, "rb") as f:
        # Read and update hash in chunks to handle large files
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)

    return sha256_hash.hexdigest()


def compute_combined_hash(file_path: str, related_paths: Iterable[str]) -> str:
    """
    Compute SHA256 hash of a primary file plus related files.

    Hash order is deterministic: primary file first, then related files
    sorted by path. Each file contributes its path and content.
    """
    path = Path(file_path)
    if not path.exists():
        return ""

    sha256_hash = hashlib.sha256()

    def _update_for_file(p: Path) -> None:
        sha256_hash.update(str(p).encode("utf-8"))
        sha256_hash.update(b"\0")
        with open(p, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        sha256_hash.update(b"\0")

    _update_for_file(path)

    related_list = [Path(p) for p in related_paths if Path(p).exists()]
    for rel_path in sorted(related_list, key=lambda p: str(p)):
        _update_for_file(rel_path)

    return sha256_hash.hexdigest()
