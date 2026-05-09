from __future__ import annotations

import pytest

from type3_clipboard_codec.adapters.manual_hex_input import ManualHexInput
from type3_clipboard_codec import parse_type3_clipboard_bytes_with_parser
from type3_clipboard_codec.inspect.hex_input import hex_text_to_bytes
from type3_clipboard_codec.models.geometry import GeometryObject, Type3ObjectChain
from type3_clipboard_codec.services.inspect_service import InspectService
from tests.sample_utils import resolve_sample_path


def _decode_fixture(sample_name: str) -> tuple[GeometryObject, str]:
    sample_path = resolve_sample_path(sample_name)
    raw_hex = sample_path.read_text(encoding="utf-8")
    data = hex_text_to_bytes(raw_hex)
    parsed, parser_name = parse_type3_clipboard_bytes_with_parser(data)
    assert isinstance(parsed, GeometryObject)
    return parsed, parser_name


def _sorted_chains(chains: list[Type3ObjectChain]) -> list[Type3ObjectChain]:
    return sorted(chains, key=lambda c: c.bbox.xmin_mm if c.bbox is not None else float("inf"))


def _preview(sample_name: str) -> str:
    sample_path = resolve_sample_path(sample_name)
    raw_hex = sample_path.read_text(encoding="utf-8")
    return InspectService().inspect(ManualHexInput(raw_hex))


@pytest.mark.parametrize(
    ("sample_name", "expected_type", "expected_count", "expected_bbox"),
    [
        ("default_rectangle.txt", "rectangle", 1, (11.111, 22.222, 44.444, 66.666)),
        ("default_circle.txt", "circle", 1, (-22.222, -11.111, 44.444, 55.555)),
        ("default_circular_arc.txt", "circular_arc", 1, (-22.222, -11.111, 11.111, 22.222)),
        ("default_rounded_rectangle.txt", "rounded_rectangle", 1, (11.111, 22.222, 86.111, 47.222)),
    ],
)
def test_geometry_single_object_snapshot(sample_name, expected_type, expected_count, expected_bbox):
    parsed, parser_name = _decode_fixture(sample_name)
    assert parser_name == "Type3ChainParser"
    assert parsed.raw_size > 0
    assert parsed.object_type == "geometry"
    assert parsed.declared_object_count == 1
    assert len(parsed.object_chains) == expected_count
    assert {"CZone", "CCourbe", "CContour", "CPropertyExtend"}.issubset(set(parsed.markers))
    preview = _preview(sample_name)
    assert f"객체 유형: {expected_type}" in preview

    chain = parsed.object_chains[0]
    assert chain.bbox is not None
    xmin, ymin, xmax, ymax = expected_bbox
    assert chain.bbox.xmin_mm == pytest.approx(xmin, abs=1e-3)
    assert chain.bbox.ymin_mm == pytest.approx(ymin, abs=1e-3)
    assert chain.bbox.xmax_mm == pytest.approx(xmax, abs=1e-3)
    assert chain.bbox.ymax_mm == pytest.approx(ymax, abs=1e-3)
    assert len(chain.contour_records) > 0


def test_two_rectangle_snapshot_count_order_bbox():
    parsed, parser_name = _decode_fixture("two_rectangle.txt")
    assert parser_name == "Type3ChainParser"
    assert parsed.raw_size > 0
    assert parsed.object_type == "geometry"
    assert parsed.declared_object_count == 2
    assert len(parsed.object_chains) == 2
    assert parsed.is_grouped is False

    chains = _sorted_chains(parsed.object_chains)
    assert chains[0].bbox.xmin_mm == pytest.approx(11.111, abs=1e-3)
    assert chains[1].bbox.xmin_mm == pytest.approx(111.111, abs=1e-3)
    assert len(chains[0].contour_records) == 4
    assert len(chains[1].contour_records) == 4


def test_two_rectangle_group_snapshot_group_evidence():
    parsed, parser_name = _decode_fixture("two_rectangle_group.txt")
    assert parser_name == "Type3ChainParser"
    assert parsed.raw_size > 0
    assert parsed.object_type == "group"
    assert parsed.is_grouped is True
    assert parsed.group_term_ko == "결합"
    assert parsed.declared_object_count == 1
    assert len(parsed.object_chains) == 2
    assert len(parsed.group_children) == 2
    assert len(parsed.raw_group_bytes) > 0
    assert any("결합" in note for note in parsed.notes)


@pytest.mark.parametrize(
    ("sample_name", "expected_name", "expected_hex"),
    [
        ("color_black_rectangle.txt", "Black", "000000"),
        ("color_blue_rectangle.txt", "Blue", "000080"),
        ("color_green_rectangle.txt", "Green", "008000"),
        ("color_cyan_rectangle.txt", "Cyan", "008080"),
        ("color_light_cyan_rectangle.txt", "Light Cyan", "00FFFF"),
    ],
)
def test_geometry_color_fixture_snapshot(sample_name, expected_name, expected_hex):
    parsed, parser_name = _decode_fixture(sample_name)
    assert parser_name == "Type3ChainParser"
    assert len(parsed.object_chains) == 1
    chain = parsed.object_chains[0]
    assert chain.style.line_color_name == expected_name
    assert chain.style.line_color_hex == expected_hex
    assert chain.style.line_color_source == "fixed_offset"
    assert chain.style.line_color_confidence in {"confirmed", "strong"}


def test_text_default_snapshot():
    parsed, parser_name = _decode_fixture("default_text.txt")
    assert parser_name == "Type3ChainParser"
    assert parsed.raw_size > 0
    assert parsed.object_type == "text"
    assert parsed.is_text_object is True
    assert "CParagraphe" in parsed.markers
    assert len(parsed.object_chains) == 1
    assert parsed.font_name == "Arial"
    assert any("provisional" in note.lower() for note in parsed.notes)

    chain = parsed.object_chains[0]
    assert chain.source_text_candidate == "abcdefg"
    assert chain.text_anchor is not None
    assert chain.text_anchor.x == pytest.approx(111.111, abs=0.5)
    assert chain.text_anchor.y == pytest.approx(222.222, abs=0.5)
    assert chain.text_anchor.z == pytest.approx(0.0, abs=0.1)
    assert chain.text_anchor_expected_source == "confirmed_from_fixture_setup"
    assert chain.text_anchor_parse_method in {
        "baseline_midpoint",
        "bbox_center_fallback",
        "direct_field_candidate",
        "unknown",
    }
    assert chain.text_anchor_parse_confidence in {"provisional", "candidate", "fallback", "direct_confirmed"}
    assert chain.line_count == 1
    assert chain.style.line_color_source in {"fixed_offset_text_unverified", "text_candidate_unverified"}
    assert chain.style.line_color_confidence in {"provisional", "unresolved"}


def test_text_group_same_color_two_objects_snapshot():
    parsed, parser_name = _decode_fixture("text_group_same_color_two_objects.txt")
    assert parser_name == "Type3ChainParser"
    assert parsed.object_type == "text"
    assert parsed.is_text_object is True
    assert len(parsed.object_chains) == 2

    first, second = parsed.object_chains
    assert first.source_text_candidate == "abcdefg"
    assert second.source_text_candidate == "1234567890"
    assert first.text_anchor is not None and second.text_anchor is not None
    assert first.text_anchor.x == pytest.approx(111.111, abs=0.5)
    assert first.text_anchor.y == pytest.approx(222.222, abs=0.5)
    assert second.text_anchor.x == pytest.approx(211.111, abs=0.5)
    assert second.text_anchor.y == pytest.approx(322.222, abs=0.5)
    assert first.style.line_color_name == "Army Green"
    assert second.style.line_color_name == "Army Green"
    assert first.style.line_color_confidence in {"provisional", "unresolved"}
    assert second.style.line_color_confidence in {"provisional", "unresolved"}
    assert any("provisional" in note.lower() for note in parsed.notes)


def test_text_multiline_snapshot():
    parsed, parser_name = _decode_fixture("text_multiline_basic.txt")
    assert parser_name == "Type3ChainParser"
    assert parsed.object_type == "text"
    assert parsed.is_text_object is True
    assert len(parsed.object_chains) >= 1
    assert any("provisional" in note.lower() for note in parsed.notes)

    has_newline = any(
        chain.source_text_candidate is not None and "\n" in chain.source_text_candidate
        for chain in parsed.object_chains
    )
    has_multiline_line_count = any((chain.line_count or 0) >= 2 for chain in parsed.object_chains)
    assert has_newline or has_multiline_line_count or len(parsed.object_chains) > 1
