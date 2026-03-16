from ..models.parsed_object import ParsedObject
from ..models.text_object import TextObject
from ..models.geometry import GeometryObject, BBox3D

class PreviewRenderer:
    """
    디코딩된 결과를 CLI에 보기 좋게 출력하는 렌더러.
    """
    def render(self, obj: ParsedObject, verbose: bool = False) -> str:
        """
        모델의 정보를 한국어로 요약하여 문자열로 반환한다.
        """
        lines = []
        lines.append("-" * 50)
        lines.append(f"[객체 정보 요약]")
        
        # 객체 유형 결정 (직사각형/원형/호 특화 표시)
        display_type = obj.object_type
        if isinstance(obj, GeometryObject):
            if len(obj.contour_records) == 4:
                # bbox와 포인트가 일치하는지 간단히 확인하여 'rectangle'로 표시할 수 있음
                display_type = "rectangle"
            elif len(obj.contour_records) == 8:
                # 8개의 포인트와 정사각형에 가까운 BBox면 'circle'로 표시
                if obj.bbox and abs(obj.bbox.width_m - obj.bbox.height_m) < 0.001:
                    display_type = "circle"
            elif len(obj.contour_records) == 2:
                # 2개의 포인트(컨트롤1, 앵커1)를 가진 경우 'circular_arc'로 표시
                # 실제로는 R8, R2 앵커를 포함한 원호 조각
                display_type = "circular_arc"
            
        lines.append(f"- 객체 유형: {display_type}")
        lines.append(f"- 데이터 크기: {obj.raw_size} bytes")
        
        if obj.markers:
            lines.append(f"- 발견된 마커: {', '.join(obj.markers)}")
            
        if isinstance(obj, TextObject):
            lines.append(f"- 텍스트 내용: {obj.text_content}")

        if isinstance(obj, GeometryObject):
            self._render_geometry(obj, lines)
            
        if obj.candidate_fields and verbose:
            lines.append(f"- 추정 필드: {obj.candidate_fields}")
            
        if obj.warnings:
            lines.append(f"[경고 메시지]")
            for w in obj.warnings:
                lines.append(f"  ! {w}")
                
        if obj.notes:
            lines.append(f"[분석 메모]")
            for n in obj.notes:
                lines.append(f"  * {n}")
                
        lines.append("-" * 50)
        return "\n".join(lines)

    def _render_geometry(self, obj: GeometryObject, lines: list[str]) -> None:
        """기하학적 형상 정보를 렌더링한다."""
        if obj.bbox:
            bbox = obj.bbox
            lines.append(f"- BBox (mm): x({bbox.xmin_mm:.3f} ~ {bbox.xmax_mm:.3f}), y({bbox.ymin_mm:.3f} ~ {bbox.ymax_mm:.3f}), z({bbox.zmin_mm:.3f} ~ {bbox.zmax_mm:.3f})")
            lines.append(f"- 크기: W {bbox.width_mm:.3f} mm, H {bbox.height_mm:.3f} mm, D {bbox.depth_mm:.3f} mm")
            
            # 원형 또는 호인 경우 중심, 반지름, 지름 추가 표시
            is_circle = len(obj.contour_records) == 8
            is_arc = len(obj.contour_records) == 2
            
            if is_circle or is_arc:
                c = bbox.center_mm
                lines.append(f"- Center = ({c.x:.3f}, {c.y:.3f}, {c.z:.3f}) mm")
                lines.append(f"- Radius = {bbox.radius_mm:.3f} mm")
                lines.append(f"- Diameter = {bbox.diameter_mm:.3f} mm")

        if obj.contour_records:
            count = len(obj.contour_records)
            lines.append(f"- Contour records: {count}")
            
            if count == 2:
                # Arc specific info
                lines.append(f"- Anchor vertices: 1")
                lines.append(f"- Control vertices: 1")
                # Based on reverse engineering, arc sample is R8 to R2
                # In 2-record arc: R1 (control), R2 (anchor)
                # But semantically it corresponds to R1, R2 from circle? 
                # Wait, User says: "start vertex = R8", "end vertex = R2"
                # If arc sample has 2 records, maybe they are R7, R8? 
                # Let's see how they are labeled.
                start = obj.start_anchor
                end = obj.end_anchor
                if start:
                    lines.append(f"- Arc start = ({start.x_mm:.3f}, {start.y_mm:.3f}, {start.z_mm:.3f}) mm")
                if end:
                    lines.append(f"- Arc end = ({end.x_mm:.3f}, {end.y_mm:.3f}, {end.z_mm:.3f}) mm")

            lines.append(f"- 곡선 정점/레코드 순서:")
            for i, p in enumerate(obj.contour_records):
                label = f"R{i+1}"
                if i == 0:
                    label = f"Start / {label}"
                
                if p.role != "unknown":
                    label = f"{label} / {p.role}"
                
                # tag 값을 16진수로 표시하여 타입 구분 힌트 제공
                info = f"({p.x_mm:.3f}, {p.y_mm:.3f}, {p.z_mm:.3f}) mm, w={p.w:.3f}, tag=0x{p.tag:02X}"
                lines.append(f"  {i+1}. {label:<25} = {info}")
            
            # Regular points display if not circle/arc records (for rectangle etc)
            if count != 8 and count != 2:
                # Already handled by loop above but let's keep consistency for non-role labels
                pass
        elif obj.points:
            lines.append(f"- 정점 수: {len(obj.points)}")
            lines.append(f"- 정점 순서:")
            for i, p in enumerate(obj.points):
                label = f"P{i+1}"
                if i == 0:
                    label = "Start / P1"
                
                # 직사각형인 경우 corner name 추가 (선택사항, 안전한 경우만)
                if len(obj.points) == 4:
                    corner_map = {0: "top-left", 1: "top-right", 2: "bottom-right", 3: "bottom-left"}
                    label += f" / {corner_map[i]:<12}"
                
                lines.append(f"  {i+1}. {label:<15} = ({p.x:.3f}, {p.y:.3f}, {p.z:.3f}) mm")
