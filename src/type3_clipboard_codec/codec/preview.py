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
        if isinstance(obj, GeometryObject):
            lines.append(f"- 파싱된 child 객체 수: {len(obj.object_chains)}")

        if obj.markers:
            lines.append(f"- 발견된 마커: {', '.join(obj.markers)}")
        if isinstance(obj, GeometryObject):
            marker_chain = obj.candidate_fields.get("nodes") if obj.candidate_fields else None
            if marker_chain:
                lines.append(f"- Class marker chain: {' -> '.join(marker_chain)}")
            if obj.aggregate_bbox:
                ab = obj.aggregate_bbox
                lines.append(
                    f"- Aggregate BBox (mm): x({ab.xmin_mm:.3f} ~ {ab.xmax_mm:.3f}), y({ab.ymin_mm:.3f} ~ {ab.ymax_mm:.3f}), z({ab.zmin_mm:.3f} ~ {ab.zmax_mm:.3f})"
                )
            if obj.is_grouped:
                lines.append("- 객체 구조: group / combined object (Type3 결합)")
                if obj.group_term_ko:
                    lines.append(f"- group_term_ko: {obj.group_term_ko}")
                if obj.group_bbox:
                    gb = obj.group_bbox
                    lines.append(
                        f"- Group BBox (mm): x({gb.xmin_mm:.3f} ~ {gb.xmax_mm:.3f}), y({gb.ymin_mm:.3f} ~ {gb.ymax_mm:.3f}), z({gb.zmin_mm:.3f} ~ {gb.zmax_mm:.3f})"
                    )
                lines.append(f"- Group child count: {len(obj.group_children)}")
                lines.append(f"- Unknown group metadata bytes: {len(obj.raw_group_bytes)}")
            elif len(obj.object_chains) > 1:
                lines.append("- 객체 구조: independent multi-object selection")
            
        if isinstance(obj, TextObject):
            lines.append(f"- 텍스트 내용: {obj.text_content}")
        elif isinstance(obj, GeometryObject) and obj.is_text_object:
            lines.append("- 텍스트 객체: provisional")
            if obj.font_name:
                lines.append(f"- Font: {obj.font_name}")
            if obj.text_content:
                lines.append(f"- Text: {obj.text_content}")
            if obj.bbox:
                bbox = obj.bbox
                lines.append(f"- BBox (mm): x({bbox.xmin_mm:.3f} ~ {bbox.xmax_mm:.3f}), y({bbox.ymin_mm:.3f} ~ {bbox.ymax_mm:.3f}), z({bbox.zmin_mm:.3f} ~ {bbox.zmax_mm:.3f})")

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
        display_type = chain.shape_type or "geometry"
        count = len(chain.contour_records)
        anchors = len([r for r in chain.contour_records if r.role == "anchor"])
        controls = len([r for r in chain.contour_records if r.role == "control"])

        lines.append(f"  - 객체 유형: {display_type}")
        if chain.shape_classification_reason:
            lines.append(
                f"  - Shape classification: {chain.shape_classification_reason} "
                f"(confidence={chain.shape_classification_confidence})"
            )
        lines.append(f"  - 마커: {', '.join(chain.markers)}")
        if chain.source_node_class is not None:
            lines.append(
                f"  - Source: {chain.source_node_class} payload_offset={chain.source_payload_offset} stream_offset={chain.source_stream_offset}"
            )
            lines.append(f"  - Raw contour bytes: {len(chain.raw_contour_bytes)}")

        if chain.bbox:
            bbox = chain.bbox
            lines.append(f"  - BBox (mm): x({bbox.xmin_mm:.3f} ~ {bbox.xmax_mm:.3f}), y({bbox.ymin_mm:.3f} ~ {bbox.ymax_mm:.3f}), z({bbox.zmin_mm:.3f} ~ {bbox.zmax_mm:.3f})")
            lines.append(f"  - 크기: W {bbox.width_mm:.3f} mm, H {bbox.height_mm:.3f} mm, D {bbox.depth_mm:.3f} mm")
            
            if display_type in ["circle", "circular_arc"]:
                c = bbox.center_mm
                lines.append(f"  - Center = ({c.x:.3f}, {c.y:.3f}, {c.z:.3f}) mm")
                lines.append(f"  - Radius = {bbox.radius_mm:.3f} mm")
                lines.append(f"  - Diameter = {bbox.diameter_mm:.3f} mm")

        if chain.style.line_color_primary is not None or chain.style.line_color_secondary is not None:
            color_name = chain.style.line_color_name or "unknown"
            color_hex = f"#{chain.style.line_color_hex}" if chain.style.line_color_hex else "#??????"
            primary = self._format_optional_u32(chain.style.line_color_primary)
            secondary = self._format_optional_u32(chain.style.line_color_secondary)
            lines.append(f"  - Line color candidate: {color_name} ({color_hex}, primary_raw={primary}, secondary_raw={secondary})")

        if chain.contour_records:
            lines.append(f"  - Contour records: {count}")
            if display_type == "circular_arc":
                # Arc specific
                arc_anchors = [r for r in chain.contour_records if r.role == "anchor"]
                if len(arc_anchors) >= 1:
                    start = arc_anchors[0]
                    lines.append(f"  - Arc start = ({start.x_mm:.3f}, {start.y_mm:.3f}, {start.z_mm:.3f}) mm")
                if len(arc_anchors) >= 2:
                    end = arc_anchors[-1]
                    lines.append(f"  - Arc end = ({end.x_mm:.3f}, {end.y_mm:.3f}, {end.z_mm:.3f}) mm")

            if display_type in {"circular_arc", "rounded_rectangle"}:
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

    def _format_optional_u32(self, value: int | None) -> str:
        if value is None:
            return "n/a"
        return f"0x{value:08X}"

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
