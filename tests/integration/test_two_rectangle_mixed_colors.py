import pytest

from type3_clipboard_codec.adapters.manual_hex_input import ManualHexInput
from type3_clipboard_codec.codec.decoder import Decoder
from type3_clipboard_codec.models.geometry import GeometryObject
from tests.sample_utils import resolve_sample_path


def _decode_sample(sample_name: str) -> GeometryObject:
    with open(resolve_sample_path(sample_name), "r", encoding="utf-8") as handle:
        raw_hex = handle.read()
    parsed = Decoder().decode_bytes(ManualHexInput(raw_hex).fetch_data())
    assert isinstance(parsed, GeometryObject)
    return parsed


def test_turquoise_and_army_green_rectangles_are_distinguished_per_child():
    parsed = _decode_sample("turquoise_rectangle_and_army_green_rectangle.txt")

    assert parsed.declared_object_count == 2
    assert len(parsed.object_chains) == 2

    by_xmin = sorted(parsed.object_chains, key=lambda chain: chain.bbox.xmin_mm if chain.bbox else 0.0)
    left = by_xmin[0]
    right = by_xmin[1]

    assert left.style.line_color_name == "Turquoise"
    assert left.style.line_color_hex == "64FFCC"
    assert left.style.line_color_confidence in {"confirmed", "strong"}
    assert right.style.line_color_name == "Army Green"
    assert right.style.line_color_hex == "98CC98"
    assert right.style.line_color_confidence in {"confirmed", "strong"}

    assert any(c.get("name") == "Turquoise" for c in left.style.color_candidates)
    assert any(c.get("name") == "Army Green" for c in right.style.color_candidates)
