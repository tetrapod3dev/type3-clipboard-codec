from type3_clipboard_codec.adapters.manual_hex_input import ManualHexInput
from type3_clipboard_codec.services.inspect_service import InspectService

def test_full_manual_hex_to_preview_flow():
    # HelloType3 를 Hex로 변환 (마커 포함)
    # CParagraph: 43 50 61 72 61 67 72 61 70 68
    # HelloType3: 48 65 6c 6c 6f 54 79 70 65 33
    hex_data = "43506172616772617068 00 48656c6c6f5479706533"
    
    service = InspectService()
    adapter = ManualHexInput(hex_data)
    
    preview_output = service.inspect(adapter)
    
    assert "text" in preview_output
    assert "CParagraph" in preview_output
    assert "HelloType3" in preview_output
