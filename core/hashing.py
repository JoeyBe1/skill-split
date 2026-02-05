"""File hashing utilities for verification."""
import hashlib
from pathlib import Path


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
