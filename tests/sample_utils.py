from __future__ import annotations

from pathlib import Path


TESTS_ROOT = Path(__file__).resolve().parent
SAMPLES_ROOT = TESTS_ROOT / "samples"
TEXT_SAMPLES_ROOT = SAMPLES_ROOT / "text"


def resolve_sample_path(sample_name: str) -> Path:
    """
    Resolve a sample fixture path.

    Preferred layout:
    - text fixtures under tests/samples/text/
    - non-text fixtures under tests/samples/
    """
    candidate = SAMPLES_ROOT / sample_name
    if candidate.exists():
        return candidate

    text_candidate = TEXT_SAMPLES_ROOT / sample_name
    if text_candidate.exists():
        return text_candidate

    # Compatibility: callers may pass "text/<name>.txt".
    nested_candidate = SAMPLES_ROOT / "text" / sample_name
    if nested_candidate.exists():
        return nested_candidate

    raise FileNotFoundError(f"Sample fixture not found: {sample_name}")
