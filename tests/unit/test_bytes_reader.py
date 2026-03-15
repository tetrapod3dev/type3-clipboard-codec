from type3_clipboard_codec.utils.bytes_reader import BytesReader
import pytest

def test_reader_read_methods():
    data = b"\x01\x02\x03\x04\x05\x06\x07\x08"
    reader = BytesReader(data)
    
    assert reader.read_u8() == 1
    assert reader.read_u16_le() == 0x0302
    assert reader.read_u32_le() == 0x07060504
    assert reader.remaining() == 1
    assert reader.read_bytes(1) == b"\x08"

def test_reader_peek():
    data = b"\xAA\xBB"
    reader = BytesReader(data)
    
    assert reader.peek_bytes(2) == b"\xAA\xBB"
    assert reader.tell() == 0
    assert reader.read_u8() == 0xAA

def test_reader_eof():
    reader = BytesReader(b"\x01")
    with pytest.raises(EOFError):
        reader.read_bytes(2)
