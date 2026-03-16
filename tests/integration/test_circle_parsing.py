import pytest
import os
from type3_clipboard_codec.adapters.manual_hex_input import ManualHexInput
from type3_clipboard_codec.services.inspect_service import InspectService
from type3_clipboard_codec.models.geometry import GeometryObject

def get_sample_path(filename):
    return os.path.join(os.path.dirname(__file__), "..", "samples", filename)

def test_circle_parsing_milestone():
    sample_path = get_sample_path("default_circle.txt")
    with open(sample_path, "r") as f:
        hex_data = f.read()

    service = InspectService()
    adapter = ManualHexInput(hex_data)
    
    # We want to see how it currently behaves
    preview_output = service.inspect(adapter)
    
    print("\n--- Current Preview Output for Circle ---")
    print(preview_output)
    print("------------------------------------------")

    # Expectations for this milestone
    assert "CZone" in preview_output
    assert "CCourbe" in preview_output
    assert "CContour" in preview_output
    assert "CPropertyExtend" in preview_output
    
    # Check if bbox is parsed correctly (in mm)
    # xmin = -22.222, ymin = -11.111, zmin = 0.000
    # xmax = 44.444, ymax = 55.555, zmax = 0.000
    assert "-22.222" in preview_output
    assert "-11.111" in preview_output
    assert "44.444" in preview_output
    assert "55.555" in preview_output
    
    # Size check
    assert "W 66.666 mm" in preview_output
    assert "H 66.666 mm" in preview_output
    assert "D 0.000 mm" in preview_output

    # Circle-specific derived geometry (to be implemented)
    # Center = (11.111, 22.222, 0.000) mm
    # Radius = 33.333 mm
    # Diameter = 66.666 mm
    # Contour records: 8
    
    # These will likely fail initially
    assert "Center = (11.111, 22.222, 0.000) mm" in preview_output
    assert "Radius = 33.333 mm" in preview_output
    assert "Diameter = 66.666 mm" in preview_output
    assert "Contour records: 8" in preview_output
    assert "circle" in preview_output.lower()

    # New checks for ordered records
    assert "곡선 정점/레코드 순서:" in preview_output
    assert "Start / R1" in preview_output
    assert "R8" in preview_output
    assert "w=" in preview_output
    assert "tag=0x" in preview_output
