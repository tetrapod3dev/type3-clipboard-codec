"""Python-source snapshot support only; never a codec or artifact hash API."""

import hashlib
import json
from pathlib import Path

BASELINES = Path(__file__).with_name("source_integrity_baselines.json")


def canonical_source_bytes(raw: bytes) -> bytes:
    """Only CRLF -> LF. No other byte, whitespace or encoding transformation."""
    return raw.replace(b"\r\n", b"\n")


def canonical_source_sha256(path: Path) -> str:
    """Hash a Python source file; reject fixture/binary paths explicitly."""
    path = Path(path)
    if path.suffix != ".py":
        raise ValueError("Canonical source integrity accepts only Python .py sources")
    return hashlib.sha256(canonical_source_bytes(path.read_bytes())).hexdigest()


def source_baseline(group: str) -> dict:
    """Read committed provenance metadata; no Git or working-tree derivation."""
    data = json.loads(BASELINES.read_text(encoding="utf-8"))
    return {data["records"][key]["path"]: data["records"][key] for key in data["groups"][group]}


def source_integrity(root: Path, group: str) -> dict:
    canonical_mismatches = []
    legacy_mismatches = []
    for path, expected in source_baseline(group).items():
        source = root / path
        if canonical_source_sha256(source) != expected["canonical_source_sha256"]:
            canonical_mismatches.append(path)
        if hashlib.sha256(source.read_bytes()).hexdigest() != expected["legacy_raw_sha256"]:
            legacy_mismatches.append(path)
    return {
        "canonical_source_equal": not canonical_mismatches,
        "legacy_raw_source_equal": not legacy_mismatches,
        "canonical_source_mismatches": canonical_mismatches,
        "legacy_raw_source_mismatches": legacy_mismatches,
    }
