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
        
        lines.append(f"- 객체 유형: {obj.object_type}")
        lines.append(f"- 데이터 크기: {obj.raw_size} bytes")
        
        if isinstance(obj, GeometryObject) and obj.declared_object_count is not None:
             lines.append(f"- 선언된 객체 수: {obj.declared_object_count}")

        if obj.markers:
            lines.append(f"- 발견된 마커: {', '.join(obj.markers)}")
            
        if isinstance(obj, TextObject):
            lines.append(f"- 텍스트 내용: {obj.text_content}")

        if isinstance(obj, GeometryObject):
            if obj.object_chains:
                for i, chain in enumerate(obj.object_chains):
                    lines.append(f"\n[객체 #{i+1}]")
                    self._render_chain(chain, lines)
            else:
                # Fallback for old/empty objects
                self._render_geometry(obj, lines, obj.object_type)
            
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

    def _render_chain(self, chain: "Type3ObjectChain", lines: list[str]) -> None:
        """단일 객체 체인 정보를 렌더링한다."""
        # 객체 유형 추정
        display_type = "geometry"
        count = len(chain.contour_records)
        anchors = len([r for r in chain.contour_records if r.role == "anchor"])
        controls = len([r for r in chain.contour_records if r.role == "control"])

        if count == 4:
            display_type = "rectangle"
        elif count == 8:
            if chain.bbox and abs(chain.bbox.width_m - chain.bbox.height_m) < 0.001:
                display_type = "circle"
            elif anchors == 4 and controls == 4:
                display_type = "rounded_rectangle"
        elif count == 12:
            display_type = "rounded_rectangle"
        elif count == 3:
            display_type = "circular_arc"
        elif count == 2:
            display_type = "circular_arc (incomplete)"

        lines.append(f"  - 객체 유형: {display_type}")
        lines.append(f"  - 마커: {', '.join(chain.markers)}")

        if chain.bbox:
            bbox = chain.bbox
            lines.append(f"  - BBox (mm): x({bbox.xmin_mm:.3f} ~ {bbox.xmax_mm:.3f}), y({bbox.ymin_mm:.3f} ~ {bbox.ymax_mm:.3f}), z({bbox.zmin_mm:.3f} ~ {bbox.zmax_mm:.3f})")
            lines.append(f"  - 크기: W {bbox.width_mm:.3f} mm, H {bbox.height_mm:.3f} mm, D {bbox.depth_mm:.3f} mm")
            
            if display_type in ["circle", "circular_arc", "circular_arc (incomplete)"]:
                c = bbox.center_mm
                lines.append(f"  - Center = ({c.x:.3f}, {c.y:.3f}, {c.z:.3f}) mm")
                lines.append(f"  - Radius = {bbox.radius_mm:.3f} mm")
                lines.append(f"  - Diameter = {bbox.diameter_mm:.3f} mm")

        if chain.contour_records:
            lines.append(f"  - Contour records: {count}")
            if count in [2, 3]:
                # Arc specific
                arc_anchors = [r for r in chain.contour_records if r.role == "anchor"]
                if len(arc_anchors) >= 1:
                    start = arc_anchors[0]
                    lines.append(f"  - Arc start = ({start.x_mm:.3f}, {start.y_mm:.3f}, {start.z_mm:.3f}) mm")
                if len(arc_anchors) >= 2:
                    end = arc_anchors[-1]
                    lines.append(f"  - Arc end = ({end.x_mm:.3f}, {end.y_mm:.3f}, {end.z_mm:.3f}) mm")

            if count in [2, 3] or display_type == "rounded_rectangle":
                 lines.append(f"  - Anchor vertices: {anchors}")
                 lines.append(f"  - Control vertices: {controls}")

            lines.append(f"  - 곡선 정점/레코드 순서:")
            for i, p in enumerate(chain.contour_records):
                label = f"R{i+1}"
                if i == 0:
                    label = f"Start / {label}"
                if p.role != "unknown":
                    label = f"{label} / {p.role}"
                info = f"({p.x_mm:.3f}, {p.y_mm:.3f}, {p.z_mm:.3f}) mm, w={p.w:.3f}, tag=0x{p.tag:02X}"
                lines.append(f"    {i+1}. {label:<25} = {info}")
        elif chain.points:
            lines.append(f"  - 정점 수: {len(chain.points)}")

    def _render_geometry(self, obj: GeometryObject, lines: list[str], display_type: str) -> None:
        """기하학적 형상 정보를 렌더링한다."""
        if obj.bbox:
            bbox = obj.bbox
            lines.append(f"- BBox (mm): x({bbox.xmin_mm:.3f} ~ {bbox.xmax_mm:.3f}), y({bbox.ymin_mm:.3f} ~ {bbox.ymax_mm:.3f}), z({bbox.zmin_mm:.3f} ~ {bbox.zmax_mm:.3f})")
            lines.append(f"- 크기: W {bbox.width_mm:.3f} mm, H {bbox.height_mm:.3f} mm, D {bbox.depth_mm:.3f} mm")
            
            is_circle = display_type == "circle"
            is_arc = display_type in ["circular_arc", "circular_arc (incomplete)"]
            
            if is_circle or is_arc:
                # 반지름과 지름은 BBox 기반이므로 호에서도 어느 정도 유효 (전체 원의 BBox라고 가정할 때)
                c = bbox.center_mm
                lines.append(f"- Center = ({c.x:.3f}, {c.y:.3f}, {c.z:.3f}) mm")
                lines.append(f"- Radius = {bbox.radius_mm:.3f} mm")
                lines.append(f"- Diameter = {bbox.diameter_mm:.3f} mm")

        if obj.contour_records:
            count = len(obj.contour_records)
            lines.append(f"- Contour records: {count}")
            
            if count in [2, 3]:
                # Arc specific info
                start = obj.start_anchor
                end = obj.end_anchor
                if start:
                    lines.append(f"- Arc start = ({start.x_mm:.3f}, {start.y_mm:.3f}, {start.z_mm:.3f}) mm")
                if end:
                    lines.append(f"- Arc end = ({end.x_mm:.3f}, {end.y_mm:.3f}, {end.z_mm:.3f}) mm")
            
            if count in [2, 3] or display_type == "rounded_rectangle":
                 lines.append(f"- Anchor vertices: {len(obj.anchor_records)}")
                 lines.append(f"- Control vertices: {len(obj.control_records)}")

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
            if count not in [8, 2, 3]:
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
