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


def _first_diag(parsed: GeometryObject) -> dict:
    blocks = parsed.candidate_fields.get("contour_header_diagnostics", [])
    assert blocks
    diagnostics = blocks[0].get("diagnostics", [])
    assert diagnostics
    return diagnostics[0]


@pytest.mark.parametrize(
    "sample_name",
    [
        "default_rectangle.txt",
        "default_circle.txt",
        "default_circular_arc.txt",
        "default_rounded_rectangle.txt",
    ],
)
def test_legacy_and_structural_match_on_default_geometry_fixtures(sample_name: str) -> None:
    parsed = _decode(sample_name)
    diag = _first_diag(parsed)
    legacy = diag.get("legacy_selected_candidate")
    structural = diag.get("structural_recommended_candidate")
    assert legacy is not None
    assert structural is not None
    assert legacy["shift"] == structural["shift"]
    assert legacy["kind"] == structural["kind"]
    assert legacy["count"] == structural["count"]
    assert diag.get("selection_mode") == "legacy_count_whitelist"
    assert diag.get("structural_policy_status") == "diagnostic_only"


@pytest.mark.parametrize(
    ("sample_name", "expected_count"),
    [
        ("polyline_5_points.txt", 5),
        ("polygon_5_sides.txt", 5),
        ("polygon_6_sides.txt", 6),
    ],
)
def test_outside_gate_samples_have_structural_recommendation_without_legacy_selection(
    sample_name: str, expected_count: int
) -> None:
    parsed = _decode(sample_name)
    diag = _first_diag(parsed)
    assert diag.get("legacy_selected_candidate") is None
    structural = diag.get("structural_recommended_candidate")
    assert structural is not None
    assert structural["count"] == expected_count
    assert structural["shift"] == 8
    candidates = diag.get("candidates", [])
    assert any(
        c.get("count") == expected_count
        and c.get("structural_valid") is True
        and c.get("legacy_plausible") is False
        for c in candidates
    )


def test_bbox_consistency_is_soft_signal_not_hard_reject() -> None:
    parsed = _decode("polygon_5_sides.txt")
    diag = _first_diag(parsed)
    candidate = next(c for c in diag["candidates"] if c.get("count") == 5 and c.get("shift") == 8)
    assert candidate["structural_valid"] is True
    reasons = candidate.get("structural_failure_reasons") or []
    assert "bbox_inconsistent" not in reasons
    assert candidate.get("bbox_consistency_status") in {"consistent", "mismatch_soft", "unknown_no_bbox"}
