import sys


try:
    from type3_clipboard_codec.utils.hex_text import hex_to_bytes
    from type3_clipboard_codec.utils.bytes_reader import BytesReader
    from type3_clipboard_codec.codec.decoder import Decoder
    from type3_clipboard_codec.models.text_object import TextObject
    
    # 1. Hex 텍스트 변환 테스트
    data = hex_to_bytes("43506172616772617068 00 48656c6c6f5479706533")
    assert b"CParagraph" in data
    print("Hex to Bytes: OK")
    
    # 2. BytesReader 테스트
    reader = BytesReader(data)
    assert reader.read_bytes(10) == b"CParagraph"
    print("BytesReader: OK")
    
    # 3. Decoder & Heuristic Text Parsing 테스트
    decoder = Decoder()
    obj = decoder.decode_bytes(data)
    assert isinstance(obj, TextObject)
    assert obj.text_content == "HelloType3"
    print("Decoder & TextParser: OK")
    
    print("\n[성공] 모든 핵심 기능이 정상 작동합니다.")

except Exception as e:
    print(f"\n[실패] 테스트 중 오류 발생: {e}")
    sys.exit(1)
