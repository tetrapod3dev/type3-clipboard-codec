import pytest
import os
from type3_clipboard_codec.adapters.manual_hex_input import ManualHexInput
from type3_clipboard_codec.services.inspect_service import InspectService

def test_arc_parsing_and_preview():
    # Load default_circular_arc.txt
    fixture_path = os.path.join(os.path.dirname(__file__), "..", "samples", "default_circular_arc.txt")
    with open(fixture_path, "r") as f:
        hex_data = f.read().strip()
    
    service = InspectService()
    adapter = ManualHexInput(hex_data)
    
    preview_output = service.inspect(adapter)
    
    print("\n" + preview_output)
    
    # Basic identification
    assert "객체 유형: circular_arc" in preview_output
    assert "Contour records: 2" in preview_output
    
    # Semantic roles
    assert "R1 / anchor" in preview_output
    assert "R2 / control" in preview_output
    
    # Arc specific fields
    assert "Arc start =" in preview_output
    assert "Arc end =" in preview_output
    assert "Anchor vertices: 1" in preview_output
    assert "Control vertices: 1" in preview_output

def test_circle_roles_parsing_and_preview():
    # Load default_circle.txt
    fixture_path = os.path.join(os.path.dirname(__file__), "..", "samples", "default_circle.txt")
    with open(fixture_path, "r") as f:
        hex_data = f.read().strip()
    
    service = InspectService()
    adapter = ManualHexInput(hex_data)
    
    preview_output = service.inspect(adapter)
    
    print("\n" + preview_output)
    
    # Basic identification
    assert "객체 유형: circle" in preview_output
    assert "Contour records: 8" in preview_output
    
    # Alternating roles
    assert "R1 / control" in preview_output
    assert "R2 / anchor" in preview_output
    assert "R3 / control" in preview_output
    assert "R4 / anchor" in preview_output
    assert "R5 / control" in preview_output
    assert "R6 / anchor" in preview_output
    assert "R7 / control" in preview_output
    assert "R8 / anchor" in preview_output
