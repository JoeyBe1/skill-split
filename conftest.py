"""Pytest configuration and shared fixtures."""

import pytest


@pytest.fixture
def db_path(tmp_path):
    """Create a temporary database file for testing.
    
    This fixture provides a unique database path for each test,
    ensuring tests don't interfere with each other.
    """
    return str(tmp_path / "test.db")
