from type3_clipboard_codec.adapters.manual_hex_input import ManualHexInput
from type3_clipboard_codec.codec.decoder import Decoder
from type3_clipboard_codec.models.geometry import GeometryObject
from tests.sample_utils import resolve_sample_path


def _decode(name: str) -> GeometryObject:
    hex_data = resolve_sample_path(name).read_text(encoding="utf-8")
    parsed = Decoder().decode_bytes(ManualHexInput(hex_data).fetch_data())
    assert isinstance(parsed, GeometryObject)
    return parsed


def test_single_text_color_fixtures_are_text_objects():
    for sample in ("text_color_army_green.txt", "text_color_navy_blue.txt"):
        parsed = _decode(sample)
        assert parsed.is_text_object is True
        assert parsed.object_chains
        style = parsed.object_chains[0].style
        # Text color fixed offsets are not confirmed yet.
        assert style.line_color_source != "fixed_offset"
        assert style.line_color_confidence in {"provisional", "unresolved", "weak", "candidate", None}


def test_mixed_color_two_object_fixture_keeps_ownership_provisional():
    parsed = _decode("text_group_mixed_color_two_objects.txt")
    assert parsed.is_text_object is True
    assert len(parsed.object_chains) == 2
    # Do not force strict ownership until mapping is validated.
    confidences = [c.style.line_color_confidence for c in parsed.object_chains]
    assert all(conf in {"provisional", "unresolved", None} for conf in confidences)
