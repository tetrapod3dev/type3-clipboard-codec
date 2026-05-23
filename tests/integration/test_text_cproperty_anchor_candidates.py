from __future__ import annotations

from pathlib import Path

import pytest

from type3_clipboard_codec import parse_type3_clipboard_bytes_with_parser
from type3_clipboard_codec.inspect.hex_input import hex_text_to_bytes
from type3_clipboard_codec.models.geometry import GeometryObject
from tests.sample_utils import resolve_sample_path


def _decode(sample_name: str) -> GeometryObject:
    raw_hex = resolve_sample_path(sample_name).read_text(encoding="utf-8")
    parsed, _parser_name = parse_type3_clipboard_bytes_with_parser(hex_text_to_bytes(raw_hex))
    assert isinstance(parsed, GeometryObject)
    return parsed


@pytest.mark.parametrize(
    ("sample_name", "expected_count"),
    [
        ("text_group_same_color_two_objects.txt", 1),
        ("text_three_objects_grouped_order_abc.txt", 2),
        ("text_three_objects_not_grouped.txt", 2),
    ],
)
def test_cproperty_anchor_candidates_exist_with_expected_count(sample_name: str, expected_count: int) -> None:
    parsed = _decode(sample_name)
    candidates = parsed.candidate_fields.get("cproperty_anchor_candidates") or []
    assert len(candidates) == expected_count


@pytest.mark.parametrize(
    ("sample_name", "expected_anchors"),
    [
        ("text_group_same_color_two_objects.txt", [(111.111, 222.222), (211.111, 322.222)]),
        ("text_three_objects_grouped_order_abc.txt", [(111.111, 222.222), (211.111, 322.222), (311.111, 422.222)]),
        ("text_three_objects_not_grouped.txt", [(111.111, 222.222), (211.111, 322.222), (311.111, 422.222)]),
    ],
)
def test_active_text_anchor_remains_unchanged(sample_name: str, expected_anchors: list[tuple[float, float]]) -> None:
    parsed = _decode(sample_name)
    observed = sorted((round(chain.text_anchor.x, 3), round(chain.text_anchor.y, 3)) for chain in parsed.object_chains if chain.text_anchor is not None)
    assert observed == sorted((round(x, 3), round(y, 3)) for x, y in expected_anchors)
    for chain in parsed.object_chains:
        assert chain.text_anchor_parse_method in {"baseline_midpoint", "bbox_center_fallback", "direct_field_candidate", "unknown"}


def test_cproperty_anchor_candidate_ownership_and_confidence_are_unresolved_and_provisional() -> None:
    parsed = _decode("text_three_objects_grouped_order_abc.txt")
    candidates = parsed.candidate_fields.get("cproperty_anchor_candidates") or []
    assert candidates
    for candidate in candidates:
        assert candidate["ownership"] == "unresolved"
        assert candidate["matched_chain"] is None
        assert candidate["confidence"] == "provisional"
        assert candidate["source"] == "CPropertyExtend_CObDao_signature_v1"
        assert candidate["anchor_relative_to_cobdao"] == 34
        assert candidate["node_class"] == "CPropertyExtend"
        assert candidate["signature"]["u32le_cobdao_plus_12"] == 131072
        assert candidate["signature"]["u32le_cobdao_plus_56"] == 262144
        assert candidate["signature"]["u32le_cobdao_plus_108"] == 65536
        assert candidate["signature"]["u32le_cobdao_plus_112"] == 262144


def test_no_fixture_filename_branching_in_parser() -> None:
    parser_source = Path("src/type3_clipboard_codec/parsers/type3_chain_parser.py").read_text(encoding="utf-8")
    forbidden_names = [
        "text_group_same_color_two_objects",
        "text_three_objects_grouped_order_abc",
        "text_three_objects_not_grouped",
    ]
    for name in forbidden_names:
        assert name not in parser_source
