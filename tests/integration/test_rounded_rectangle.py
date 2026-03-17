import pytest
import os
from type3_clipboard_codec.adapters.manual_hex_input import ManualHexInput
from type3_clipboard_codec.services.inspect_service import InspectService

def test_rounded_rectangle_parsing():
    fixture_path = os.path.join(os.path.dirname(__file__), "..", "samples", "default_rounded_rectangle.txt")
    with open(fixture_path, "r") as f:
        hex_data = f.read().strip()
    
    service = InspectService()
    adapter = ManualHexInput(hex_data)
    preview_output = service.inspect(adapter)
    
    print("\n" + preview_output)
    
    assert "객체 유형: rounded_rectangle" in preview_output
    assert "Contour records: 12" in preview_output
    assert "Anchor vertices: 8" in preview_output
    assert "Control vertices: 4" in preview_output
    
    # Check for sane coordinates (W=75, H=25)
    # x(11.111 ~ 86.111), y(22.222 ~ 47.222)
    assert "W 75.000 mm" in preview_output
    assert "H 25.000 mm" in preview_output
    assert "11.111" in preview_output
    assert "86.111" in preview_output
    assert "22.222" in preview_output
    assert "47.222" in preview_output
