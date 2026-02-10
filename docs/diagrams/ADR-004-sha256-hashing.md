# ADR-004: SHA256 Hashing for Integrity Verification

**Status**: Accepted
**Date**: 2025-02-10
**Context**: Phase 01 - Core Parser & Database

## Context

The skill-split system decomposes files into sections and must guarantee:
1. **Byte-perfect round-trip**: Original file content exactly matches recomposed content
2. **Data integrity**: Detect any corruption during storage/retrieval
3. **Verification confidence**: High confidence that parse/recompose is correct

Without cryptographic verification, there's no way to guarantee that the parsing and recomposition process is truly lossless.

## Decision

Use SHA256 cryptographic hashing to verify file integrity and round-trip accuracy.

### Technical Details

- **Hash Computation**: SHA256 of original file content
- **Storage**: Hash stored in files table for verification
- **Verification**: Compare original hash with recomposed hash
- **Multi-file**: Combined hash for components spanning multiple files

### Implementation

```python
import hashlib

def compute_file_hash(file_path: str) -> str:
    """Compute SHA256 hash of file content."""
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            sha256.update(chunk)
    return sha256.hexdigest()

def compute_combined_hash(primary_path: str, related_paths: List[str]) -> str:
    """Compute combined hash for multi-file components."""
    sha256 = hashlib.sha256()

    # Hash files in deterministic order
    paths = sorted([primary_path] + related_paths)
    for path in paths:
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256.update(chunk)

    return sha256.hexdigest()

# Verification
def validate_round_trip(file_path: str) -> ValidationResult:
    # Parse original
    doc = parser.parse(file_path, content, file_type, file_format)
    original_hash = compute_file_hash(file_path)

    # Store and retrieve
    store.store_file(file_path, doc, original_hash)
    metadata, sections = store.get_file(file_path)

    # Recompose
    recomposed = recomposer.recompose(file_path)
    recomposed_hash = hashlib.sha256(recomposed.encode()).hexdigest()

    # Compare
    is_valid = original_hash == recomposed_hash
    return ValidationResult(is_valid, original_hash, recomposed_hash)
```

## Rationale

### Advantages

1. **Strong Verification**: Cryptographic certainty of data integrity
2. **Fast Computation**: SHA256 is efficient even for large files
3. **Collision Resistant**: Practically impossible to have false positives
4. **Multi-file Support**: Can verify integrity across related files
5. **Standard Algorithm**: Built into Python standard library

### Alternatives Considered

1. **MD5 Hashing**
   - Rejected: Collision vulnerabilities
   - Not cryptographically secure
   - Faster but not worth the risk

2. **CRC32 Checksum**
   - Rejected: Not collision-resistant
   - Designed for error detection, not integrity verification
   - Higher false positive rate

3. **No Verification (trust the parser)**
   - Rejected: No way to detect bugs
   - Cannot guarantee byte-perfect round-trip
   - Violates "never lose data" principle

4. **Content Comparison (string equality)**
   - Rejected: Memory intensive for large files
   - No persistent verification
   - Cannot detect corruption over time

## Consequences

### Positive

- Detects any data corruption or parsing bugs
- Confirms byte-perfect round-trip accuracy
- Enables confidence in parse/recompose implementation
- Persistent verification stored in database
- Supports multi-file component verification

### Negative

- Additional compute overhead (~1-5ms per file)
- Larger database records (64 hex characters per file)
- Implementation complexity for multi-file hashing
- Need to recompute on content changes

### Mitigation

- Hash computation is negligible compared to I/O
- Database storage cost is minimal (64 bytes per file)
- Multi-file hashing is well-encapsulated in hashing module
- Hash updates only on content changes

## Usage

```bash
# Verify file round-trip integrity
./skill_split.py verify my-skill.md
# Output:
# File: my-skill.md
# Valid
#
# original_hash:    a1b2c3d4...
# recomposed_hash:  a1b2c3d4...
```

```python
# Programmatic verification
validator = Validator(store, recomposer)
result = validator.validate_round_trip(file_path)

if result.is_valid:
    print("Round-trip successful!")
else:
    print(f"Hash mismatch: {result.original_hash} != {result.recomposed_hash}")
    print(f"Errors: {result.errors}")
```

## Related Decisions

- [ADR-005](./ADR-005-factory-pattern.md): Factory Pattern for Component Handlers

## References

- [SHA256 Wikipedia](https://en.wikipedia.org/wiki/SHA-2)
- [Python hashlib Documentation](https://docs.python.org/3/library/hashlib.html)
- [Hashing Implementation](../../core/hashing.py)
