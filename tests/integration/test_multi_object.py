import pytest
import os
from type3_clipboard_codec.adapters.manual_hex_input import ManualHexInput
from type3_clipboard_codec.services.inspect_service import InspectService
from type3_clipboard_codec.models.geometry import GeometryObject

from type3_clipboard_codec.codec.decoder import Decoder

def test_parse_two_circle_sample_extracts_two_object_chains():
    # Load two_circle.txt
    fixture_path = os.path.join(os.path.dirname(__file__), "..", "samples", "two_circle.txt")
    with open(fixture_path, "rb") as f:
        binary_data = f.read()
    
    # Try decode with null-tolerance
    hex_data = binary_data.decode('ascii', errors='ignore')
    
    service = InspectService()
    adapter = ManualHexInput(hex_data)
    
    # We need to access the internal parsed object to verify chains
    data = adapter.fetch_data()
    from type3_clipboard_codec.codec.decoder import Decoder
    decoder = Decoder()
    parsed_obj = decoder.decode_bytes(data)
    
    assert isinstance(parsed_obj, GeometryObject)
    assert parsed_obj.declared_object_count == 2
    assert len(parsed_obj.object_chains) == 2

def test_each_object_chain_has_expected_marker_sequence():
    fixture_path = os.path.join(os.path.dirname(__file__), "..", "samples", "two_circle.txt")
    with open(fixture_path, "rb") as f:
        hex_data = f.read().decode('ascii', errors='ignore')
    
    service = InspectService()
    adapter = ManualHexInput(hex_data)
    data = adapter.fetch_data()
    from type3_clipboard_codec.codec.decoder import Decoder
    decoder = Decoder()
    parsed_obj = decoder.decode_bytes(data)
    
    expected_markers = ["CZone", "CCourbe", "CContour", "CPropertyExtend"]
    
    for i, chain in enumerate(parsed_obj.object_chains):
        for marker in expected_markers:
            assert marker in chain.markers, f"Marker {marker} missing in chain {i}"

def test_each_circle_contour_is_parsed_independently():
    fixture_path = os.path.join(os.path.dirname(__file__), "..", "samples", "two_circle.txt")
    with open(fixture_path, "rb") as f:
        hex_data = f.read().decode('ascii', errors='ignore')
    
    service = InspectService()
    adapter = ManualHexInput(hex_data)
    data = adapter.fetch_data()
    from type3_clipboard_codec.codec.decoder import Decoder
    decoder = Decoder()
    parsed_obj = decoder.decode_bytes(data)
    
    obj1 = parsed_obj.object_chains[0]
    obj2 = parsed_obj.object_chains[1]
    
    assert len(obj1.contour_records) == 8
    assert len(obj2.contour_records) == 8
    
    # BBoxes should be different
    assert obj1.bbox.xmin_m != obj2.bbox.xmin_m
    assert obj1.bbox.xmax_m != obj2.bbox.xmax_m

def test_regression_single_fixtures():
    samples = [
        "default_circle.txt",
        "default_rectangle.txt",
        "default_circular_arc.txt",
        "default_rounded_rectangle.txt"
    ]
    
    decoder = Decoder()
    
    for sample in samples:
        fixture_path = os.path.join(os.path.dirname(__file__), "..", "samples", sample)
        with open(fixture_path, "r") as f:
            hex_data = f.read().strip()
        
        adapter = ManualHexInput(hex_data)
        data = adapter.fetch_data()
        parsed_obj = decoder.decode_bytes(data)
        
        assert isinstance(parsed_obj, GeometryObject)
        assert len(parsed_obj.object_chains) == 1, f"Sample {sample} should have exactly 1 chain"
        assert parsed_obj.declared_object_count == 1, f"Sample {sample} should declare 1 object"

def test_preview_output_multi_object():
    fixture_path = os.path.join(os.path.dirname(__file__), "..", "samples", "two_circle.txt")
    with open(fixture_path, "rb") as f:
        hex_data = f.read().decode('ascii', errors='ignore')
    
    service = InspectService()
    adapter = ManualHexInput(hex_data)
    
    preview_output = service.inspect(adapter)
    
    assert "[객체 #1]" in preview_output
    assert "[객체 #2]" in preview_output
    assert "선언된 객체 수: 2" in preview_output
    assert "객체 유형: circle" in preview_output # Should appear inside chains
