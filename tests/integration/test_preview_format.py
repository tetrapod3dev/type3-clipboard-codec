import os
import pytest
from type3_clipboard_codec.adapters.manual_hex_input import ManualHexInput
from type3_clipboard_codec.services.inspect_service import InspectService

def test_rectangle_preview_format():
    """
    default_rectangle.txt 피스처를 사용하여 미리보기 출력 형식을 검증한다.
    """
    # 피스처 경로 설정
    fixture_path = os.path.join(os.path.dirname(__file__), "..", "samples", "default_rectangle.txt")
    
    with open(fixture_path, "r") as f:
        hex_data = f.read()
        
    service = InspectService()
    adapter = ManualHexInput(hex_data)
    
    # 기본 모드에서 분석 (verbose=False)
    preview_output = service.inspect(adapter, verbose=False)
    
    # 1. 마커 확인
    assert "CZone" in preview_output
    assert "CCourbe" in preview_output
    assert "CContour" in preview_output
    assert "CPropertyExtend" in preview_output
    
    # 2. BBox 및 크기 형식 확인
    # x(11.111 ~ 44.444), y(22.222 ~ 66.666), z(0.000 ~ 0.000)
    assert "BBox (mm): x(11.111 ~ 44.444), y(22.222 ~ 66.666), z(0.000 ~ 0.000)" in preview_output
    assert "W 33.333 mm, H 44.444 mm, D 0.000 mm" in preview_output
    
    # 3. 정점 정보 확인
    assert "Contour records: 4" in preview_output
    assert "곡선 정점/레코드 순서:" in preview_output
    assert "Start / R1 / anchor" in preview_output
    
    # 좌표 확인 (11.111, 66.666, 0.000) 등
    assert "(11.111, 66.666, 0.000) mm" in preview_output # top-left
    assert "(44.444, 66.666, 0.000) mm" in preview_output # top-right
    assert "(44.444, 22.222, 0.000) mm" in preview_output # bottom-right
    assert "(11.111, 22.222, 0.000) mm" in preview_output # bottom-left
    
    # 4. 기본 모드에서 추정 필드(raw dump)가 숨겨져 있는지 확인
    assert "추정 필드" not in preview_output
    assert "nodes" not in preview_output

def test_verbose_preview_format():
    """
    Verbose 모드에서 추정 필드가 표시되는지 확인한다.
    """
    fixture_path = os.path.join(os.path.dirname(__file__), "..", "samples", "default_rectangle.txt")
    with open(fixture_path, "r") as f:
        hex_data = f.read()
        
    service = InspectService()
    adapter = ManualHexInput(hex_data)
    
    preview_output = service.inspect(adapter, verbose=True)
    
    # Verbose 모드에서는 추정 필드가 나타나야 함
    assert "추정 필드" in preview_output
    assert "nodes" in preview_output
