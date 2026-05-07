import os

import pytest

from type3_clipboard_codec.adapters.manual_hex_input import ManualHexInput
from type3_clipboard_codec.codec.decoder import Decoder
from type3_clipboard_codec.models.geometry import GeometryObject
from type3_clipboard_codec.services.inspect_service import InspectService


def get_sample_path(filename):
    return os.path.join(os.path.dirname(__file__), "..", "samples", filename)


def decode_sample(filename):
    with open(get_sample_path(filename), "r") as f:
        hex_data = f.read()

    adapter = ManualHexInput(hex_data)
    return Decoder().decode_bytes(adapter.fetch_data())


@pytest.mark.parametrize(
    ("filename", "expected_raw_value", "expected_name", "expected_hex"),
    [
        ("color_black_rectangle.txt", 0x00000000, "Black", "000000"),
        ("color_blue_rectangle.txt", 0x00008000, "Blue", "000080"),
        ("color_green_rectangle.txt", 0x00000080, "Green", "008000"),
        ("color_cyan_rectangle.txt", 0x00008080, "Cyan", "008080"),
        ("color_light_cyan_rectangle.txt", 0x0000FFFF, "Light Cyan", "00FFFF"),
    ],
)
def test_rectangle_line_color_candidates(filename, expected_raw_value, expected_name, expected_hex):
    parsed = decode_sample(filename)

    assert isinstance(parsed, GeometryObject)
    assert len(parsed.object_chains) == 1

    style = parsed.object_chains[0].style
    assert style.line_color_primary == expected_raw_value
    assert style.line_color_secondary == expected_raw_value
    assert style.line_color_name == expected_name
    assert style.line_color_hex == expected_hex


@pytest.mark.parametrize(
    ("filename", "expected_raw_value", "expected_name", "expected_hex"),
    [
        ("color_black_rectangle.txt", "0x00000000", "Black", "000000"),
        ("color_blue_rectangle.txt", "0x00008000", "Blue", "000080"),
        ("color_green_rectangle.txt", "0x00000080", "Green", "008000"),
        ("color_cyan_rectangle.txt", "0x00008080", "Cyan", "008080"),
        ("color_light_cyan_rectangle.txt", "0x0000FFFF", "Light Cyan", "00FFFF"),
    ],
)
def test_rectangle_preview_includes_color_candidate(filename, expected_raw_value, expected_name, expected_hex):
    with open(get_sample_path(filename), "r") as f:
        hex_data = f.read()

    preview_output = InspectService().inspect(ManualHexInput(hex_data))

    assert f"Line color candidate: {expected_name}" in preview_output
    assert f"#{expected_hex}" in preview_output
    assert f"primary_raw={expected_raw_value}" in preview_output
    assert f"secondary_raw={expected_raw_value}" in preview_output
