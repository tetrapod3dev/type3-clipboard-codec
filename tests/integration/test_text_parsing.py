from type3_clipboard_codec.adapters.manual_hex_input import ManualHexInput
from type3_clipboard_codec.codec.decoder import Decoder
from type3_clipboard_codec.models.geometry import GeometryObject
from type3_clipboard_codec.services.inspect_service import InspectService
from tests.sample_utils import resolve_sample_path


def get_sample_path(filename):
    return str(resolve_sample_path(filename))


def decode_sample(filename):
    with open(get_sample_path(filename), "r") as f:
        hex_data = f.read()

    return Decoder().decode_bytes(ManualHexInput(hex_data).fetch_data())


def test_default_text_object_first_stage_parsing():
    parsed = decode_sample("default_text.txt")

    assert isinstance(parsed, GeometryObject)
    assert parsed.object_type == "text"
    assert parsed.is_text_object is True
    assert "CParagraphe" in parsed.markers
    assert parsed.font_name == "Arial"
    assert parsed.text_content in {"abcdefg", "1234567890"}
    assert parsed.raw_data
    assert parsed.raw_text_records

    assert parsed.bbox is not None
    # Text anchor is the controlled coordinate; bbox is derived from glyph geometry.
    assert parsed.object_chains
    chain = parsed.object_chains[0]
    assert chain.text_anchor is not None
    assert abs(chain.text_anchor.x - 111.111) < 0.5
    assert abs(chain.text_anchor.y - 222.222) < 0.5
    assert abs(chain.text_anchor.z - 0.0) < 0.1
    assert abs(parsed.bbox.zmin_mm) < 1e-9

    chain_markers = parsed.object_chains[0].markers
    assert "CCourbe" in chain_markers
    assert "CContour" in chain_markers


def test_default_text_preview_includes_text_summary():
    with open(get_sample_path("default_text.txt"), "r") as f:
        hex_data = f.read()

    preview_output = InspectService().inspect(ManualHexInput(hex_data))

    assert "객체 유형: text" in preview_output
    assert "Font: Arial" in preview_output
    assert "Text: abcdefg" in preview_output
    assert "CParagraphe" in preview_output
    assert "provisional" in preview_output


def test_small_caps_fixture_keeps_source_candidate_and_does_not_force_uppercase_equivalence():
    parsed = decode_sample("text_small_caps_mode.txt")
    assert isinstance(parsed, GeometryObject)
    assert parsed.is_text_object is True
    assert parsed.object_chains
    chain = parsed.object_chains[0]
    assert chain.source_text_candidate == "abcdefg"
    # Parser must expose payload evidence and avoid forced case transformation.
    assert chain.display_text_candidate is None


def test_lowercase_mode_fixture_preserves_intentional_uppercase_source_evidence():
    parsed = decode_sample("text_lowercase_mode.txt")
    assert isinstance(parsed, GeometryObject)
    assert parsed.is_text_object is True
    assert parsed.object_chains
    chain = parsed.object_chains[0]
    assert chain.source_text_candidate == "ABCDEFG"
    assert chain.display_text_candidate is None


def test_two_text_objects_same_color_fixture_detects_two_objects_with_order_and_candidates():
    parsed = decode_sample("text_group_same_color_two_objects.txt")
    assert isinstance(parsed, GeometryObject)
    assert parsed.is_text_object is True
    assert len(parsed.object_chains) == 2

    first, second = parsed.object_chains
    assert first.text_anchor is not None
    assert second.text_anchor is not None
    assert first.text_anchor.x < second.text_anchor.x
    assert abs(first.text_anchor.x - 111.111) < 0.5
    assert abs(first.text_anchor.y - 222.222) < 0.5
    assert abs(second.text_anchor.x - 211.111) < 0.5
    assert abs(second.text_anchor.y - 322.222) < 0.5
    assert first.source_text_candidate == "abcdefg"
    assert second.source_text_candidate == "1234567890"
    assert first.style.line_color_name == "Army Green"
    assert second.style.line_color_name == "Army Green"


def test_two_text_objects_mixed_color_fixture_keeps_two_objects_and_text_order():
    parsed = decode_sample("text_group_mixed_color_two_objects.txt")
    assert isinstance(parsed, GeometryObject)
    assert parsed.is_text_object is True
    assert len(parsed.object_chains) == 2

    first, second = parsed.object_chains
    assert first.text_anchor is not None
    assert second.text_anchor is not None
    assert abs(first.text_anchor.x - 111.111) < 0.5
    assert abs(second.text_anchor.x - 211.111) < 0.5
    assert first.source_text_candidate == "abcdefg"
    assert second.source_text_candidate == "1234567890"
    # Mixed-color text fixture currently resolves Navy Blue from payload scan candidates.
    assert first.style.line_color_name == "Navy Blue"
    assert second.style.line_color_name == "Navy Blue"


def test_multiline_order_40_41_42_fixtures_have_multiline_evidence_and_preserve_object_order():
    for sample_name in (
        "text_spacing_fixed.txt",
        "text_spacing_proportional.txt",
        "text_spacing_print_proportional.txt",
    ):
        parsed = decode_sample(sample_name)
        assert isinstance(parsed, GeometryObject)
        assert parsed.is_text_object is True
        assert len(parsed.object_chains) >= 1
        # Conservative evidence check: either explicit newline candidate
        # or at least multiple chains that may represent decomposed lines.
        has_newline = any(
            (chain.source_text_candidate is not None and "\n" in chain.source_text_candidate)
            for chain in parsed.object_chains
        )
        assert has_newline or len(parsed.object_chains) > 1
