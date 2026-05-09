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


@pytest.mark.parametrize(
    ("sample_name", "expected_name", "expected_hex"),
    [
        ("two_rectangle_group_navy_blue.txt", "Navy Blue", "3060CC"),
        ("two_rectangle_group_army_green.txt", "Army Green", "98CC98"),
    ],
)
def test_결합_group_color_candidates_detected(sample_name, expected_name, expected_hex):
    parsed = _decode_sample(sample_name)

    assert parsed.is_grouped is True
    assert parsed.group_term_ko == "결합"
    assert len(parsed.object_chains) == 2

    for chain in parsed.object_chains:
        style = chain.style
        assert style.line_color_name == expected_name
        assert style.line_color_hex == expected_hex
        assert style.line_color_confidence == "confirmed"
        assert style.line_color_source == "fixed_offset"
        assert any(
            c.get("offset") == 526 and c.get("name") == expected_name
            for c in style.color_candidates
        )
        assert any(
            c.get("offset") == 538 and c.get("name") == expected_name
            for c in style.color_candidates
        )
