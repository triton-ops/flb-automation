"""checksum.py — parse sha256sum-format manifests and hash local files, for FLR
content-integrity verification.

test-data/test-data.md's "Checksum manifests" section documents per-host manifests under
test-data/manifests/ as "the verification oracle for FLR" — this module is what actually reads
them and compares against a file recovered via FileLevelRecoveryPage.download_selected().
"""
from __future__ import annotations

import hashlib
from pathlib import Path


def load_manifest(manifest_path: str | Path) -> dict[str, str]:
    """Parse a `sha256sum`-format manifest (one '<hex-digest>  ./relative/path' line per file)
    into {basename: lowercase hex digest}. Every manifest in this repo is a flat,
    single-directory fileset (see test-data/test-data.md), so the basename alone is a safe,
    unambiguous key."""
    manifest: dict[str, str] = {}
    for line in Path(manifest_path).read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        digest, path = line.split(None, 1)
        manifest[Path(path).name] = digest.lower()
    return manifest


def sha256_of(path: str | Path) -> str:
    """Hex digest of a local file's contents, chunked to handle large files without loading
    them fully into memory."""
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_of_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
