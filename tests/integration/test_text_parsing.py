import os

from type3_clipboard_codec.adapters.manual_hex_input import ManualHexInput
from type3_clipboard_codec.codec.decoder import Decoder
from type3_clipboard_codec.models.geometry import GeometryObject
from type3_clipboard_codec.services.inspect_service import InspectService


def get_sample_path(filename):
    return os.path.join(os.path.dirname(__file__), "..", "samples", filename)


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
    assert parsed.text_content == "abcdefg"
    assert parsed.raw_data
    assert parsed.raw_text_records

    assert parsed.bbox is not None
    assert abs(parsed.bbox.xmin_mm) < 1.0
    assert abs(parsed.bbox.ymin_mm) < 1.0
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
