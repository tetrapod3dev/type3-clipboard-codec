import pytest

from type3_clipboard_codec.exceptions import InvalidHexError
from type3_clipboard_codec.inspect.hex_input import hex_text_to_bytes, normalize_hex_text


def test_normalize_hex_text_removes_whitespace_and_0x_prefixes():
    assert normalize_hex_text("0x41 42\n0X43") == "414243"


def test_hex_text_to_bytes_valid_payload():
    assert hex_text_to_bytes("0x41 42 43") == b"ABC"


def test_normalize_hex_text_rejects_non_hex_character():
    with pytest.raises(InvalidHexError):
        normalize_hex_text("41GG")


def test_normalize_hex_text_rejects_odd_length():
    with pytest.raises(InvalidHexError):
        normalize_hex_text("123")
