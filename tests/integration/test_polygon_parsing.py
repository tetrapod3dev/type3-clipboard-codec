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
        ("polygon_5_sides.txt", 5),
        ("polygon_6_sides.txt", 6),
    ],
)
def test_polygon_fixtures_keep_records_and_are_polygon_candidates(sample_name: str, expected_count: int) -> None:
    parsed = _decode(sample_name)
    chain = parsed.object_chains[0]
    assert len(chain.contour_records) == expected_count
    assert chain.shape_type == "polygon_candidate"
    assert chain.control_record_count == 0
    assert chain.closed_like_evidence is True
    assert chain.shape_classification_confidence == "provisional"

