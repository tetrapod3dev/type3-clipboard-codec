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


def _all_diags(parsed: GeometryObject) -> list[dict]:
    out: list[dict] = []
    for block in parsed.candidate_fields.get("contour_header_diagnostics", []):
        out.extend(block.get("diagnostics", []))
    return out


@pytest.mark.parametrize(
    "sample_name",
    ["default_rectangle.txt", "default_circle.txt", "default_circular_arc.txt"],
)
def test_refined_recommendation_matches_primary_default_contour_candidates(sample_name: str) -> None:
    parsed = _decode(sample_name)
    diag = _all_diags(parsed)[0]
    legacy = diag.get("legacy_selected_candidate")
    refined = diag.get("refined_recommended_candidate")
    assert legacy is not None
    assert refined is not None
    assert refined["node_class_name"] == "CContour"
    assert legacy["shift"] == refined["shift"]
    assert legacy["kind"] == refined["kind"]
    assert legacy["count"] == refined["count"]
    assert diag.get("recommendation_mode") == "shadow_run_only"
    assert diag.get("structural_policy_status") == "diagnostic_only"


@pytest.mark.parametrize(
    ("sample_name", "expected_count"),
    [
        ("polyline_5_points.txt", 5),
        ("polygon_5_sides.txt", 5),
        ("polygon_6_sides.txt", 6),
    ],
)
def test_refined_recommendation_exists_for_outside_gate_valid_contour_candidates(
    sample_name: str, expected_count: int
) -> None:
    parsed = _decode(sample_name)
    diag = _all_diags(parsed)[0]
    assert diag.get("legacy_selected_candidate") is None
    refined = diag.get("refined_recommended_candidate")
    assert refined is not None
    assert refined["count"] == expected_count
    assert refined["node_class_name"] == "CContour"


@pytest.mark.parametrize(
    "sample_name",
    [
        "two_rectangle.txt",
        "two_circle.txt",
        "turquoise_rectangle_and_army_green_rectangle.txt",
    ],
)
def test_auxiliary_kind3_count1_candidates_do_not_win_refined_recommendation(sample_name: str) -> None:
    parsed = _decode(sample_name)
    found_aux = False
    for diag in _all_diags(parsed):
        for c in diag.get("candidates", []):
            if c.get("kind") == 3 and c.get("count") == 1 and c.get("node_class_name") == "CPropertyExtend":
                found_aux = True
        refined = diag.get("refined_recommended_candidate")
        if refined is not None:
            assert not (refined.get("kind") == 3 and refined.get("count") == 1 and refined.get("node_class_name") == "CPropertyExtend")
    assert found_aux
