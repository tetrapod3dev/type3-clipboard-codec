from __future__ import annotations

import pytest

from type3_clipboard_codec import parse_type3_clipboard_bytes_with_parser
from type3_clipboard_codec.inspect.hex_input import hex_text_to_bytes
from type3_clipboard_codec.models.geometry import GeometryObject
from tests.sample_utils import resolve_sample_path


def _decode(sample_name: str) -> GeometryObject:
    raw_hex = resolve_sample_path(sample_name).read_text(encoding="utf-8")
    parsed, parser_name = parse_type3_clipboard_bytes_with_parser(hex_text_to_bytes(raw_hex))
    assert parser_name == "Type3ChainParser"
    assert isinstance(parsed, GeometryObject)
    return parsed


@pytest.mark.parametrize(
    ("sample_name", "expected_count"),
    [
        ("default_rectangle.txt", 4),
        ("default_circle.txt", 8),
        ("default_circular_arc.txt", 3),
        ("default_rounded_rectangle.txt", 12),
    ],
)
def test_contour_header_diagnostics_selected_fields(sample_name: str, expected_count: int) -> None:
    parsed = _decode(sample_name)
    chain = parsed.object_chains[0]
    assert len(chain.contour_records) == expected_count
    assert chain.contour_header_diagnostics

    selected = [d for d in chain.contour_header_diagnostics if d.get("selected_count") is not None]
    assert selected
    first = selected[0]
    assert first["selected_count"] == expected_count
    assert first["selected_shift"] is not None
    assert first["selected_kind"] is not None
    assert isinstance(first["selected_raw_header_hex"], str)
    assert len(first["selected_raw_header_hex"]) == 16
    assert first["confidence"] == "provisional"
    assert first["candidates"]
    assert all(
        isinstance(candidate.get("raw_8b_hex"), str) and len(candidate["raw_8b_hex"]) == 16
        for candidate in first["candidates"]
        if candidate.get("raw_8b_hex") is not None
    )


def test_contour_header_diagnostics_are_payload_relative_not_absolute_rule() -> None:
    parsed = _decode("default_rectangle.txt")
    chain = parsed.object_chains[0]
    diag = chain.contour_header_diagnostics[0]
    assert diag["selected_header_offset"] >= 0
    assert diag["selected_payload_offset"] >= diag["selected_header_offset"]
    assert diag["selection_reason"] in {"first_plausible_shift_with_unique_offset", "no_plausible_candidate"}
    assert all(c["header_offset"] >= 0 for c in diag["candidates"])
    assert all(c["shift"] in diag["candidate_shifts"] for c in diag["candidates"])
