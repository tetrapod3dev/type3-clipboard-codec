import os

import pytest

from type3_clipboard_codec.adapters.manual_hex_input import ManualHexInput
from type3_clipboard_codec.codec.decoder import Decoder
from type3_clipboard_codec.models.geometry import GeometryObject, Type3ObjectChain
from type3_clipboard_codec.services.inspect_service import InspectService


def _load_geometry(sample_name: str) -> GeometryObject:
    fixture_path = os.path.join(os.path.dirname(__file__), "..", "samples", sample_name)
    with open(fixture_path, "r", encoding="utf-8") as handle:
        hex_data = handle.read()
    parsed = Decoder().decode_bytes(ManualHexInput(hex_data).fetch_data())
    assert isinstance(parsed, GeometryObject)
    return parsed


def _sorted_by_xmin(chains: list[Type3ObjectChain]) -> list[Type3ObjectChain]:
    return sorted(chains, key=lambda chain: chain.bbox.xmin_mm if chain.bbox else float("inf"))


def test_two_rectangle_independent_selection_geometry_and_order():
    parsed = _load_geometry("two_rectangle.txt")

    assert parsed.raw_size > 0
    assert parsed.object_type == "geometry"
    assert parsed.is_grouped is False
    assert parsed.declared_object_count == 2
    assert len(parsed.object_chains) == 2
    assert all(len(chain.contour_records) == 4 for chain in parsed.object_chains)
    assert all(chain.source_stream_offset is not None for chain in parsed.object_chains)
    assert parsed.object_chains == sorted(parsed.object_chains, key=lambda chain: chain.source_stream_offset)

    chains = _sorted_by_xmin(parsed.object_chains)
    first = chains[0]
    second = chains[1]

    assert first.bbox.xmin_mm == pytest.approx(11.111, abs=1e-3)
    assert first.bbox.ymin_mm == pytest.approx(22.222, abs=1e-3)
    assert first.bbox.xmax_mm == pytest.approx(44.444, abs=1e-3)
    assert first.bbox.ymax_mm == pytest.approx(66.666, abs=1e-3)

    assert second.bbox.xmin_mm == pytest.approx(111.111, abs=1e-3)
    assert second.bbox.ymin_mm == pytest.approx(22.222, abs=1e-3)
    assert second.bbox.xmax_mm == pytest.approx(144.444, abs=1e-3)
    assert second.bbox.ymax_mm == pytest.approx(66.666, abs=1e-3)

    delta_x = second.bbox.xmin_mm - first.bbox.xmin_mm
    assert delta_x == pytest.approx(100.0, abs=1e-3)

    assert parsed.aggregate_bbox is not None
    assert parsed.aggregate_bbox.xmin_m == pytest.approx(0.011111, abs=1e-6)
    assert parsed.aggregate_bbox.ymin_m == pytest.approx(0.022222, abs=1e-6)
    assert parsed.aggregate_bbox.zmin_m == pytest.approx(0.0, abs=1e-9)
    assert parsed.aggregate_bbox.xmax_m == pytest.approx(0.144444, abs=1e-6)
    assert parsed.aggregate_bbox.ymax_m == pytest.approx(0.066666, abs=1e-6)
    assert parsed.aggregate_bbox.zmax_m == pytest.approx(0.0, abs=1e-9)


def test_two_rectangle_group_detects_결합_structure_and_preserves_unknown_bytes():
    parsed = _load_geometry("two_rectangle_group.txt")

    assert parsed.raw_size > 0
    assert parsed.object_type == "group"
    assert parsed.is_grouped is True
    assert parsed.group_term_ko == "결합"
    assert parsed.declared_object_count == 1
    assert len(parsed.object_chains) == 2
    assert len(parsed.group_children) == 2
    assert len(parsed.raw_group_bytes) > 0
    assert any("결합" in note for note in parsed.notes)

    chains = _sorted_by_xmin(parsed.object_chains)
    first = chains[0]
    second = chains[1]

    assert len(first.contour_records) == 4
    assert len(second.contour_records) == 4
    assert first.bbox.xmin_mm == pytest.approx(11.111, abs=1e-3)
    assert first.bbox.xmax_mm == pytest.approx(44.444, abs=1e-3)
    assert second.bbox.xmin_mm == pytest.approx(111.111, abs=1e-3)
    assert second.bbox.xmax_mm == pytest.approx(144.444, abs=1e-3)

    group_bbox = parsed.group_bbox or parsed.aggregate_bbox
    assert group_bbox is not None
    assert group_bbox.xmin_m == pytest.approx(0.011111, abs=1e-6)
    assert group_bbox.ymin_m == pytest.approx(0.022222, abs=1e-6)
    assert group_bbox.zmin_m == pytest.approx(0.0, abs=1e-9)
    assert group_bbox.xmax_m == pytest.approx(0.144444, abs=1e-6)
    assert group_bbox.ymax_m == pytest.approx(0.066666, abs=1e-6)
    assert group_bbox.zmax_m == pytest.approx(0.0, abs=1e-9)


def test_preview_summary_for_multi_and_결합_payloads():
    service = InspectService()
    sample_dir = os.path.join(os.path.dirname(__file__), "..", "samples")

    with open(os.path.join(sample_dir, "two_rectangle.txt"), "r", encoding="utf-8") as handle:
        preview_multi = service.inspect(ManualHexInput(handle.read()), verbose=True)
    assert "선언된 객체 수: 2" in preview_multi
    assert "파싱된 child 객체 수: 2" in preview_multi
    assert "객체 구조: independent multi-object selection" in preview_multi
    assert "Aggregate BBox (mm): x(11.111 ~ 144.444), y(22.222 ~ 66.666), z(0.000 ~ 0.000)" in preview_multi
    assert "[객체 #1]" in preview_multi
    assert "[객체 #2]" in preview_multi

    with open(os.path.join(sample_dir, "two_rectangle_group.txt"), "r", encoding="utf-8") as handle:
        preview_group = service.inspect(ManualHexInput(handle.read()), verbose=True)
    assert "선언된 객체 수: 1" in preview_group
    assert "객체 구조: group / combined object (Type3 결합)" in preview_group
    assert "group_term_ko: 결합" in preview_group
    assert "Group child count: 2" in preview_group
    assert "Unknown group metadata bytes:" in preview_group
    assert "[객체 #1]" in preview_group
    assert "[객체 #2]" in preview_group
