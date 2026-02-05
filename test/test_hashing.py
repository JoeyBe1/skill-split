"""Unit tests for hashing module."""
import hashlib
import tempfile
from pathlib import Path

import pytest

from core.hashing import compute_file_hash


def test_valid_file_hashing():
    """Test that a valid file produces a consistent SHA256 hash."""
    with tempfile.NamedTemporaryFile(mode='wb', delete=False) as tmp:
        content = b"Hello, World!"
        tmp.write(content)
        tmp_path = tmp.name

    try:
        result = compute_file_hash(tmp_path)

        # Compute expected hash directly
        expected = hashlib.sha256(content).hexdigest()

        assert result == expected
        assert len(result) == 64  # SHA256 produces 64 hex characters
        assert isinstance(result, str)
    finally:
        Path(tmp_path).unlink()


def test_nonexistent_file_returns_empty_string():
    """Test that a non-existent file returns an empty string."""
    result = compute_file_hash("/path/that/does/not/exist.txt")
    assert result == ""


def test_same_content_produces_same_hash():
    """Test that identical content produces the same hash."""
    content = b"Test content for hashing"

    with tempfile.NamedTemporaryFile(mode='wb', delete=False) as tmp1:
        tmp1.write(content)
        tmp1_path = tmp1.name

    with tempfile.NamedTemporaryFile(mode='wb', delete=False) as tmp2:
        tmp2.write(content)
        tmp2_path = tmp2.name

    try:
        hash1 = compute_file_hash(tmp1_path)
        hash2 = compute_file_hash(tmp2_path)

        assert hash1 == hash2
    finally:
        Path(tmp1_path).unlink()
        Path(tmp2_path).unlink()


def test_different_content_produces_different_hash():
    """Test that different content produces different hashes."""
    with tempfile.NamedTemporaryFile(mode='wb', delete=False) as tmp1:
        tmp1.write(b"Content A")
        tmp1_path = tmp1.name

    with tempfile.NamedTemporaryFile(mode='wb', delete=False) as tmp2:
        tmp2.write(b"Content B")
        tmp2_path = tmp2.name

    try:
        hash1 = compute_file_hash(tmp1_path)
        hash2 = compute_file_hash(tmp2_path)

        assert hash1 != hash2
    finally:
        Path(tmp1_path).unlink()
        Path(tmp2_path).unlink()


def test_large_file_chunked_reading():
    """Test that large files are read in chunks correctly."""
    # Create content larger than the 4096 byte chunk size
    content = b"x" * 10000

    with tempfile.NamedTemporaryFile(mode='wb', delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        result = compute_file_hash(tmp_path)
        expected = hashlib.sha256(content).hexdigest()

        assert result == expected
    finally:
        Path(tmp_path).unlink()
