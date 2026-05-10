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
    ("sample_name", "expected_count"),
    [
        ("polyline_5_points.txt", 5),
        ("polygon_5_sides.txt", 5),
        ("polygon_6_sides.txt", 6),
    ],
)
def test_outside_gate_candidates_are_now_actually_selected(sample_name: str, expected_count: int) -> None:
    parsed = _decode(sample_name)
    assert parsed.contour_records
    assert len(parsed.contour_records) == expected_count
    diag = _all_diags(parsed)[0]
    assert diag.get("selection_mode") == "refined_structural_ranking"
    assert diag.get("legacy_selected_candidate") is None
    actual = diag.get("actual_selected_candidate")
    assert actual is not None
    assert actual["count"] == expected_count
    assert actual["node_class_name"] == "CContour"
    assert diag.get("selected_count") == expected_count


@pytest.mark.parametrize(
    "sample_name",
    ["default_rectangle.txt", "default_circle.txt", "default_circular_arc.txt", "default_rounded_rectangle.txt"],
)
def test_default_fixture_winners_are_stable_after_actual_selection_switch(sample_name: str) -> None:
    parsed = _decode(sample_name)
    diag = _all_diags(parsed)[0]
    legacy = diag.get("legacy_selected_candidate")
    actual = diag.get("actual_selected_candidate")
    assert legacy is not None
    assert actual is not None
    assert legacy["shift"] == actual["shift"]
    assert legacy["kind"] == actual["kind"]
    assert legacy["count"] == actual["count"]


@pytest.mark.parametrize(
    "sample_name",
    [
        "two_rectangle.txt",
        "two_circle.txt",
        "turquoise_rectangle_and_army_green_rectangle.txt",
    ],
)
def test_auxiliary_kind3_count1_candidates_do_not_become_actual_winner(sample_name: str) -> None:
    parsed = _decode(sample_name)
    found_aux = False
    for diag in _all_diags(parsed):
        for c in diag.get("candidates", []):
            if c.get("kind") == 3 and c.get("count") == 1 and c.get("node_class_name") == "CPropertyExtend":
                found_aux = True
        actual = diag.get("actual_selected_candidate")
        if actual is not None:
            assert not (
                actual.get("kind") == 3
                and actual.get("count") == 1
                and actual.get("node_class_name") == "CPropertyExtend"
            )
    assert found_aux

