from type3_clipboard_codec.codec.decoder import Decoder
from type3_clipboard_codec.models.text_object import TextObject

def test_decode_text_object_heuristic():
    decoder = Decoder()
    # "CParagraph" 마커와 텍스트 내용을 포함한 모의 바이너리 데이터
    data = b"SomeHeader\x00CParagraph\x00HelloType3\x00"
    
    obj = decoder.decode_bytes(data)
    
    assert isinstance(obj, TextObject)
    assert obj.object_type == "text"
    assert "CParagraph" in obj.markers
    assert obj.text_content == "HelloType3"

def test_decode_unknown_object():
    decoder = Decoder()
    data = b"\x01\x02\x03\x04\x05"
    
    obj = decoder.decode_bytes(data)
    
    assert obj.object_type == "unknown"
    assert obj.raw_size == 5
