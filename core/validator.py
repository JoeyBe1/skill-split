"""
Validator for round-trip verification of parsed files.

This module provides the Validator class which verifies that files
can be parsed, stored in the database, and recomposed without data loss.
"""

from __future__ import annotations

from pathlib import Path
from typing import List

from core.database import DatabaseStore
from core.hashing import compute_file_hash
from core.recomposer import Recomposer
from models import ValidationResult


class Validator:
    """
    Verifies round-trip integrity of parsed and stored files.

    Ensures that files can be:
    1. Parsed into sections
    2. Stored in the database
    3. Recomposed back to original form
    4. Verified against original content
    """

    def __init__(self, db: DatabaseStore, recomposer: Recomposer) -> None:
        """
        Initialize the validator with database and recomposer.

        Args:
            db: DatabaseStore instance containing parsed files
            recomposer: Recomposer instance for rebuilding files
        """
        self.db = db
        self.recomposer = recomposer

    def validate_round_trip(self, file_path: str) -> ValidationResult:
        """
        Verify round-trip: original -> DB -> recomposed matches original.

        This validation ensures no data loss occurs during the parse and
        storage process by comparing hashes at each stage.

        Process:
        1. Compute hash of original file
        2. Recompose file from DB
        3. Compute hash of recomposed content
        4. Compare original vs recomposed (primary check)

        Args:
            file_path: Path to the file to validate

        Returns:
            ValidationResult with detailed comparison results.
            When hashes match, is_valid=True and errors list is empty.
            A perfect round-trip is expected.
        """
        result = ValidationResult(is_valid=False)
        errors = []

        # Step 1: Verify original file exists and compute its hash
        original_hash = compute_file_hash(file_path)
        if not original_hash:
            errors.append(f"Original file not found: {file_path}")
            result.errors.extend(errors)
            return result

        result.original_hash = original_hash

        # Step 2: Verify file exists in database
        file_data = self.db.get_file(file_path)
        if file_data is None:
            errors.append(f"File not found in database: {file_path}")
            result.errors.extend(errors)
            return result

        # Step 3: Recompose file from database
        recomposed_content = self.recomposer.recompose(file_path)
        if recomposed_content is None:
            errors.append(f"Failed to recompose file from database: {file_path}")
            result.errors.extend(errors)
            return result

        # Step 4: Compute hash of recomposed content
        recomposed_hash = self._compute_content_hash(recomposed_content)
        result.recomposed_hash = recomposed_hash

        # Step 5: Primary validation: original vs recomposed (full round-trip)
        files_match = original_hash == recomposed_hash
        result.files_match = files_match

        if files_match:
            # Perfect round-trip achieved
            # Set is_valid=True and ensure errors list is empty
            result.is_valid = True
            result.errors.clear()
        else:
            # Round-trip failed - this should not happen with correct parser/recomposer
            errors.append(
                f"Round-trip validation failed: recomposed file does not match original. "
                f"Original: {original_hash}, Recomposed: {recomposed_hash}"
            )
            result.errors.extend(errors)

            # Add diagnostic information to help identify the issue
            self._add_diagnostics(result, file_path, recomposed_content)

        return result

    def _compute_content_hash(self, content: str) -> str:
        """
        Compute SHA256 hash of a string content.

        Args:
            content: String content to hash

        Returns:
            SHA256 hexdigest string
        """
        import hashlib

        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def _add_diagnostics(
        self, result: ValidationResult, file_path: str, recomposed_content: str
    ) -> None:
        """
        Add diagnostic information when validation fails.

        Provides actionable information to identify what went wrong
        during round-trip validation.

        Note: A perfect round-trip is expected. Diagnostics help identify
        parser/recomposer bugs that need to be fixed.

        Args:
            result: ValidationResult to add warnings to
            file_path: Original file path
            recomposed_content: The recomposed content
        """
        original_path = Path(file_path)

        if not original_path.exists():
            result.add_warning("Original file no longer exists for comparison")
            return

        try:
            with open(original_path, "r", encoding="utf-8") as f:
                original_content = f.read()

            # Calculate character-level differences
            original_lines = original_content.splitlines(keepends=True)
            recomposed_lines = recomposed_content.splitlines(keepends=True)

            if len(original_lines) != len(recomposed_lines):
                result.add_warning(
                    f"Line count differs: original={len(original_lines)}, "
                    f"recomposed={len(recomposed_lines)}"
                )

            # Find first differing line
            for i, (orig_line, recomp_line) in enumerate(
                zip(original_lines, recomposed_lines)
            ):
                if orig_line != recomp_line:
                    result.add_warning(
                        f"First difference at line {i + 1}: "
                        f"original={repr(orig_line)}, recomposed={repr(recomp_line)}"
                    )
                    break

        except Exception as e:
            result.add_warning(f"Could not perform diagnostic comparison: {e}")

    def validate_all_files(
        self, file_paths: List[str]
    ) -> dict[str, ValidationResult]:
        """
        Validate round-trip for multiple files.

        Args:
            file_paths: List of file paths to validate

        Returns:
            Dictionary mapping file paths to their validation results
        """
        results = {}

        for file_path in file_paths:
            results[file_path] = self.validate_round_trip(file_path)

        return results

    def get_validation_summary(
        self, results: dict[str, ValidationResult]
    ) -> dict[str, int]:
        """
        Get summary statistics for multiple validation results.

        Args:
            results: Dictionary of validation results

        Returns:
            Dictionary with counts: total, passed, failed, warnings
        """
        summary = {
            "total": len(results),
            "passed": 0,
            "failed": 0,
            "warnings": 0,
        }

        for result in results.values():
            if result.is_valid:
                summary["passed"] += 1
            else:
                summary["failed"] += 1

            if result.warnings:
                summary["warnings"] += 1

        return summary
