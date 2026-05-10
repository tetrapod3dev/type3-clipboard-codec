from __future__ import annotations

import pytest

from type3_clipboard_codec import parse_type3_clipboard_bytes_with_parser
from type3_clipboard_codec.inspect.hex_input import hex_text_to_bytes
from type3_clipboard_codec.models.geometry import GeometryObject
from tests.sample_utils import resolve_sample_path


def _decode_fixture(sample_name: str) -> GeometryObject:
    raw_hex = resolve_sample_path(sample_name).read_text(encoding="utf-8")
    parsed, parser_name = parse_type3_clipboard_bytes_with_parser(hex_text_to_bytes(raw_hex))
    assert parser_name == "Type3ChainParser"
    assert isinstance(parsed, GeometryObject)
    return parsed


@pytest.mark.parametrize(
    ("sample_name", "expected_point_count"),
    [
        ("default_rectangle.txt", 4),
        ("default_circle.txt", 8),
        ("default_circular_arc.txt", 3),
        ("default_rounded_rectangle.txt", 12),
    ],
)
def test_geometry_chain_structure_and_contour_invariants(sample_name: str, expected_point_count: int) -> None:
    parsed = _decode_fixture(sample_name)

    assert parsed.object_type == "geometry"
    assert parsed.declared_object_count == 1
    assert len(parsed.object_chains) == 1

    chain = parsed.object_chains[0]
    assert chain.markers[:4] == ["CZone", "CCourbe", "CContour", "CPropertyExtend"]
    assert chain.bbox is not None
    assert len(chain.contour_records) == expected_point_count
    assert len(chain.points) == expected_point_count
    assert chain.source_stream_offset is not None
    assert chain.source_payload_offset is not None


def test_multi_object_and_group_structure_invariants() -> None:
    independent = _decode_fixture("two_rectangle.txt")
    assert independent.object_type == "geometry"
    assert independent.is_grouped is False
    assert independent.declared_object_count == 2
    assert len(independent.object_chains) == 2
    assert all(chain.source_stream_offset is not None for chain in independent.object_chains)
    assert independent.object_chains == sorted(
        independent.object_chains,
        key=lambda chain: chain.source_stream_offset,
    )

    grouped = _decode_fixture("two_rectangle_group.txt")
    assert grouped.object_type == "group"
    assert grouped.is_grouped is True
    assert grouped.group_term_ko == "결합"
    assert grouped.declared_object_count == 1
    assert len(grouped.object_chains) == 2
    assert len(grouped.raw_group_bytes) > 0


def test_rectangle_color_payload_relative_invariants() -> None:
    parsed = _decode_fixture("color_blue_rectangle.txt")
    assert len(parsed.object_chains) == 1
    style = parsed.object_chains[0].style

    assert style.fixed_primary_offset == 0x79
    assert style.fixed_secondary_offset == 0x85
    assert style.line_color_name == "Blue"
    assert style.line_color_hex == "000080"
    assert style.line_color_source == "fixed_offset"
    assert style.line_color_confidence in {"confirmed", "strong"}
