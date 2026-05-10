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
        ("polyline_2_points.txt", 2),
        ("polyline_3_points.txt", 3),
        ("polyline_5_points.txt", 5),
    ],
)
def test_polyline_fixtures_are_not_classified_as_arc(sample_name: str, expected_count: int) -> None:
    parsed = _decode(sample_name)
    chain = parsed.object_chains[0]
    assert len(chain.contour_records) == expected_count
    assert chain.shape_type == "polyline_candidate"
    assert chain.shape_type != "circular_arc"
    assert chain.control_record_count == 0
    assert chain.arc_like_control_evidence is False
    assert chain.shape_classification_confidence == "provisional"


def test_default_circular_arc_remains_circular_arc() -> None:
    parsed = _decode("default_circular_arc.txt")
    chain = parsed.object_chains[0]
    assert chain.shape_type == "circular_arc"
    assert chain.control_record_count >= 1
    assert chain.arc_like_control_evidence is True
    assert chain.shape_classification_confidence == "confirmed"

