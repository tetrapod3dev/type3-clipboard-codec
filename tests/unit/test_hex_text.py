from type3_clipboard_codec.utils.hex_text import hex_to_bytes, normalize_hex_text
from type3_clipboard_codec.exceptions import InvalidHexError
import pytest

def test_normalize_hex_text():
    assert normalize_hex_text("0x12 34\n56") == "123456"
    assert normalize_hex_text("12:34:56") == "123456"
    assert normalize_hex_text("12,34,56") == "123456"

def test_hex_to_bytes_valid():
    assert hex_to_bytes("414243") == b"ABC"
    assert hex_to_bytes("0x41 42") == b"AB"

def test_hex_to_bytes_invalid_length():
    with pytest.raises(InvalidHexError):
        hex_to_bytes("123")

def test_hex_to_bytes_invalid_chars():
    with pytest.raises(InvalidHexError):
        hex_to_bytes("ZZ")
