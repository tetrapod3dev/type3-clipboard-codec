from __future__ import annotations

import hashlib
from typing import Any

from ..models.geometry import BBox3D, GeometryObject, Type3ObjectChain
from ..models.parsed_object import ParsedObject


def _json_safe(value: Any) -> Any:
    if isinstance(value, bytes):
        return value.hex()
    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_safe(v) for v in value]
    if isinstance(value, tuple):
        return [_json_safe(v) for v in value]
    return value


def _bbox_to_dict_mm(bbox: BBox3D | None) -> dict[str, float] | None:
    if bbox is None:
        return None
    return {
        "xmin_mm": bbox.xmin_mm,
        "ymin_mm": bbox.ymin_mm,
        "zmin_mm": bbox.zmin_mm,
        "xmax_mm": bbox.xmax_mm,
        "ymax_mm": bbox.ymax_mm,
        "zmax_mm": bbox.zmax_mm,
        "width_mm": bbox.width_mm,
        "height_mm": bbox.height_mm,
        "depth_mm": bbox.depth_mm,
        "center_x_mm": bbox.center_mm.x,
        "center_y_mm": bbox.center_mm.y,
        "center_z_mm": bbox.center_mm.z,
    }


def _infer_chain_object_type(chain: Type3ObjectChain) -> str:
    count = len(chain.contour_records)
    anchors = len([r for r in chain.contour_records if r.role == "anchor"])
    controls = len([r for r in chain.contour_records if r.role == "control"])

    if count == 4:
        return "rectangle"
    if count == 8:
        if chain.bbox and abs(chain.bbox.width_m - chain.bbox.height_m) < 0.001:
            return "circle"
        if anchors == 4 and controls == 4:
            return "rounded_rectangle"
    if count == 12:
        return "rounded_rectangle"
    if count == 3:
        return "arc"
    if count == 2:
        return "arc"
    return "geometry"


def _chain_to_dict(chain: Type3ObjectChain, index: int, is_text_object: bool = False) -> dict[str, Any]:
    contour_preview = []
    for i, record in enumerate(chain.contour_records[:8]):
        contour_preview.append(
            {
                "index": i + 1,
                "x_mm": record.x_mm,
                "y_mm": record.y_mm,
                "z_mm": record.z_mm,
                "w": record.w,
                "tag_hex": f"0x{record.tag:08X}",
                "role": record.role,
            }
        )

    primary_raw = chain.style.line_color_primary
    secondary_raw = chain.style.line_color_secondary
    selected_raw = chain.style.line_color_selected_raw
    return {
        "index": index,
        "object_type": "text" if is_text_object else _infer_chain_object_type(chain),
        "markers": list(chain.markers),
        "bbox_mm": _bbox_to_dict_mm(chain.bbox),
        "contour_record_count": len(chain.contour_records),
        "anchor_count": len([r for r in chain.contour_records if r.role == "anchor"]),
        "control_count": len([r for r in chain.contour_records if r.role == "control"]),
        "contour_preview": contour_preview,
        "source": {
            "node_class": chain.source_node_class,
            "payload_offset": chain.source_payload_offset,
            "stream_offset": chain.source_stream_offset,
        },
        "style_candidates": {
            "line_color_primary": chain.style.line_color_primary,
            "line_color_primary_raw_hex": (
                f"0x{primary_raw:08X}" if primary_raw is not None else None
            ),
            "line_color_secondary": chain.style.line_color_secondary,
            "line_color_secondary_raw_hex": (
                f"0x{secondary_raw:08X}" if secondary_raw is not None else None
            ),
            "line_color_selected_raw": selected_raw,
            "line_color_selected_raw_hex": (
                f"0x{selected_raw:08X}" if selected_raw is not None else None
            ),
            "line_color_name": chain.style.line_color_name,
            "line_color_hex": f"#{chain.style.line_color_hex}" if chain.style.line_color_hex else None,
            "line_color_confidence": chain.style.line_color_confidence,
            "line_color_source": chain.style.line_color_source,
            "color_candidates": list(chain.style.color_candidates),
            "property_extend_payload_offset": chain.style.property_extend_payload_offset,
            "property_extend_stream_offset": chain.style.property_extend_stream_offset,
            "property_extend_payload_length": chain.style.property_extend_payload_length,
            "fixed_primary_offset": chain.style.fixed_primary_offset,
            "fixed_secondary_offset": chain.style.fixed_secondary_offset,
            "fixed_primary_raw_hex": (
                f"0x{chain.style.fixed_primary_raw:08X}" if chain.style.fixed_primary_raw is not None else None
            ),
            "fixed_secondary_raw_hex": (
                f"0x{chain.style.fixed_secondary_raw:08X}" if chain.style.fixed_secondary_raw is not None else None
            ),
        },
        "text": {
            "text_candidate": chain.text_candidate,
            "source_text_candidate": chain.source_text_candidate,
            "display_text_candidate": chain.display_text_candidate,
            "line_count": chain.line_count,
            "anchor_mm": (
                {
                    "x_mm": chain.text_anchor.x,
                    "y_mm": chain.text_anchor.y,
                    "z_mm": chain.text_anchor.z,
                }
                if chain.text_anchor is not None
                else None
            ),
            "anchor_expected_source": chain.text_anchor_expected_source,
            "anchor_parse_method": chain.text_anchor_parse_method or chain.text_anchor_source,
            "anchor_parse_confidence": chain.text_anchor_parse_confidence or chain.text_anchor_confidence,
            "notes": list(chain.text_notes),
        },
        "unknown_sections": [
            {
                "name": "raw_contour_bytes",
                "size": len(chain.raw_contour_bytes),
                "preview_hex": chain.raw_contour_bytes[:32].hex(),
            }
        ],
    }


def _iter_geometry_objects(geom: GeometryObject) -> list[dict[str, Any]]:
    if geom.is_grouped:
        child_dicts = [_chain_to_dict(chain, idx + 1, is_text_object=False) for idx, chain in enumerate(geom.group_children)]
        merged_candidates: list[dict[str, Any]] = []
        seen_candidate_keys: set[tuple[Any, ...]] = set()
        for child in child_dicts:
            for candidate in child.get("style_candidates", {}).get("color_candidates", []):
                key = (
                    candidate.get("offset"),
                    candidate.get("raw"),
                    candidate.get("source"),
                    candidate.get("confidence"),
                )
                if key in seen_candidate_keys:
                    continue
                seen_candidate_keys.add(key)
                merged_candidates.append(candidate)
        group_style: dict[str, Any] | None = None
        if merged_candidates:
            merged_candidates.sort(
                key=lambda item: (
                    0 if item.get("confidence") == "confirmed" else (1 if item.get("confidence") == "strong" else 2),
                    0 if item.get("source") == "fixed_offset" else 1,
                )
            )
            top = merged_candidates[0]
            group_style = {
                "line_color_name": top.get("name"),
                "line_color_hex": f"#{top.get('hex_rgb')}" if top.get("hex_rgb") else None,
                "line_color_selected_raw_hex": top.get("raw_hex"),
                "line_color_confidence": top.get("confidence"),
                "line_color_source": top.get("source"),
                "color_candidates": merged_candidates,
                "note": "group child color attribution is provisional.",
            }
        return [
            {
                "index": 1,
                "object_type": "group",
                "is_grouped": True,
                "group_term_ko": geom.group_term_ko,
                "bbox_mm": _bbox_to_dict_mm(geom.group_bbox or geom.aggregate_bbox),
                "child_count": len(geom.group_children),
                "unknown_sections": [
                    {
                        "name": "raw_group_bytes",
                        "size": len(geom.raw_group_bytes),
                        "preview_hex": geom.raw_group_bytes[:32].hex(),
                    }
                ],
                "children": child_dicts,
                "style_candidates": group_style,
                "notes": list(geom.group_notes),
            }
        ]

    return [
        _chain_to_dict(chain, idx + 1, is_text_object=geom.is_text_object)
        for idx, chain in enumerate(geom.object_chains)
    ]


def to_inspection_dict(
    obj: ParsedObject,
    parser_name: str,
    source: str,
) -> dict[str, Any]:
    data = obj.raw_data
    base: dict[str, Any] = {
        "source": source,
        "raw_size": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "raw_preview_hex": data[:64].hex(),
        "parser": parser_name,
        "object_type": obj.object_type,
        "markers": list(obj.markers),
        "notes": list(obj.notes),
        "warnings": list(obj.warnings),
        "objects": [],
        "unknown_sections": [],
    }

    if isinstance(obj, GeometryObject):
        base["declared_object_count"] = obj.declared_object_count
        base["is_grouped"] = obj.is_grouped
        base["group_term_ko"] = obj.group_term_ko
        base["marker_order"] = obj.candidate_fields.get("nodes") if obj.candidate_fields else None
        base["marker_offsets"] = obj.candidate_fields.get("node_markers_with_offsets") if obj.candidate_fields else None
        base["aggregate_bbox_mm"] = _bbox_to_dict_mm(obj.aggregate_bbox)
        base["bbox_mm"] = _bbox_to_dict_mm(obj.bbox)
        base["text"] = {
            "is_text_object": obj.is_text_object,
            "text_content": obj.text_content,
            "source_text_candidate": obj.source_text_candidate,
            "display_text_candidate": obj.display_text_candidate,
            "font_name": obj.font_name,
            "font_candidates": (
                obj.candidate_fields.get("font_candidates")
                if obj.candidate_fields
                else None
            ),
            "raw_text_record_count": len(obj.raw_text_records),
            "notes": list(obj.text_notes),
        }
        base["candidate_fields"] = _json_safe(dict(obj.candidate_fields))
        base["objects"] = _iter_geometry_objects(obj)
        if len(obj.raw_group_bytes) > 0:
            base["unknown_sections"].append(
                {
                    "name": "raw_group_bytes",
                    "size": len(obj.raw_group_bytes),
                    "preview_hex": obj.raw_group_bytes[:32].hex(),
                }
            )
    else:
        base["bbox_mm"] = None

    return base


def _fmt_bbox_line(name: str, bbox: dict[str, float] | None, indent: str = "") -> list[str]:
    if bbox is None:
        return [f"{indent}{name}: n/a"]
    return [
        f"{indent}{name}:",
        f"{indent}  x: {bbox['xmin_mm']:.3f} ~ {bbox['xmax_mm']:.3f} mm",
        f"{indent}  y: {bbox['ymin_mm']:.3f} ~ {bbox['ymax_mm']:.3f} mm",
        f"{indent}  z: {bbox['zmin_mm']:.3f} ~ {bbox['zmax_mm']:.3f} mm",
        f"{indent}  W: {bbox['width_mm']:.3f} mm",
        f"{indent}  H: {bbox['height_mm']:.3f} mm",
        f"{indent}  D: {bbox['depth_mm']:.3f} mm",
    ]


def render_inspection_text(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("=" * 60)
    lines.append("TYPE3 Clipboard Hex Inspector")
    lines.append("=" * 60)
    lines.append(f"Input: {payload['source']}")
    lines.append(f"Raw size: {payload['raw_size']} bytes")
    lines.append(f"SHA256: {payload['sha256']}")
    lines.append(f"Parser: {payload['parser']}")
    if payload.get("declared_object_count") is not None:
        lines.append(f"Declared object count: {payload['declared_object_count']}")
    lines.append(f"Top-level object type: {payload['object_type']}")
    markers = payload.get("markers") or []
    lines.append(f"Markers: {', '.join(markers) if markers else 'none'}")
    marker_order = payload.get("marker_order")
    if marker_order:
        lines.append(f"Marker order: {' -> '.join(marker_order)}")
    marker_offsets = payload.get("marker_offsets")
    if marker_offsets:
        lines.append("Marker offsets:")
        for item in marker_offsets:
            lines.append(
                "  "
                f"- {item['class_name']}: start={item['start_offset']}, payload={item['payload_offset']}, end={item['end_offset']}"
            )

    if payload.get("is_grouped"):
        lines.append("Detected structure: grouped / 결합 candidate")
    elif (payload.get("objects") and len(payload["objects"]) > 1):
        lines.append("Detected structure: independent multi-object selection")

    lines.extend(_fmt_bbox_line("Aggregate BBox", payload.get("aggregate_bbox_mm")))

    lines.append("")
    lines.append(f"Parsed objects: {len(payload.get('objects', []))}")
    lines.append("Objects:")

    def append_style_lines(style: dict[str, Any] | None, indent: str) -> None:
        if not style:
            return
        lines.append(f"{indent}Style:")
        if style.get("line_color_name") or style.get("line_color_hex"):
            lines.append(
                f"{indent}  Line color: {style.get('line_color_name')} ({style.get('line_color_hex')})"
            )
        lines.append(f"{indent}  line_color_primary_raw: {style.get('line_color_primary_raw_hex')}")
        lines.append(f"{indent}  line_color_secondary_raw: {style.get('line_color_secondary_raw_hex')}")
        lines.append(f"{indent}  line_color_selected_raw: {style.get('line_color_selected_raw_hex')}")
        lines.append(f"{indent}  line_color_confidence: {style.get('line_color_confidence')}")
        lines.append(f"{indent}  line_color_source: {style.get('line_color_source')}")
        if style.get("note"):
            lines.append(f"{indent}  note: {style.get('note')}")
        color_candidates = style.get("color_candidates") or []
        if color_candidates:
            lines.append(f"{indent}  color_candidates:")
            for candidate in color_candidates[:8]:
                lines.append(
                    f"{indent}    - offset={candidate.get('offset')} raw={candidate.get('raw_hex')} "
                    f"name={candidate.get('name')} hex=#{candidate.get('hex_rgb')} "
                    f"confidence={candidate.get('confidence')} source={candidate.get('source')} "
                    f"encoding={candidate.get('encoding')}"
                )

    for obj in payload.get("objects", []):
        lines.append(f"[Object #{obj['index']}]")
        lines.append(f"  Type: {obj['object_type']}")
        if obj.get("group_term_ko"):
            lines.append(f"  Korean Type3 term: {obj['group_term_ko']}")
        if obj.get("child_count") is not None:
            lines.append(f"  Child count: {obj['child_count']}")
        lines.extend(_fmt_bbox_line("  BBox", obj.get("bbox_mm")))
        bbox = obj.get("bbox_mm")
        if bbox is not None:
            lines.append(
                "  BBox center (calculated): "
                f"X={bbox['center_x_mm']:.3f} mm, Y={bbox['center_y_mm']:.3f} mm, Z={bbox['center_z_mm']:.3f} mm"
            )
        if obj.get("markers"):
            lines.append(f"  Markers: {', '.join(obj['markers'])}")
        if obj.get("contour_record_count") is not None:
            lines.append(f"  Contour records: {obj['contour_record_count']}")
            lines.append(f"  Anchor/Control: {obj['anchor_count']}/{obj['control_count']}")
        text_info = obj.get("text") or {}
        if text_info:
            if text_info.get("text_candidate") is not None:
                lines.append(f"  Text: {text_info.get('text_candidate')}")
            if text_info.get("source_text_candidate") is not None:
                lines.append(f"  Source text candidate: {text_info.get('source_text_candidate')}")
            if text_info.get("display_text_candidate") is not None:
                lines.append(f"  Display text candidate: {text_info.get('display_text_candidate')}")
            if text_info.get("line_count") is not None:
                lines.append(f"  Line count: {text_info.get('line_count')}")
            anchor = text_info.get("anchor_mm")
            if anchor is not None:
                lines.append(
                    "  Text anchor (UI X/Y/Z): "
                    f"X={anchor.get('x_mm'):.3f} mm, Y={anchor.get('y_mm'):.3f} mm, Z={anchor.get('z_mm'):.3f} mm"
                )
            if text_info.get("anchor_expected_source"):
                lines.append(f"  Anchor expected source: {text_info.get('anchor_expected_source')}")
            if text_info.get("anchor_parse_method"):
                lines.append(f"  Anchor parse method: {text_info.get('anchor_parse_method')}")
            if text_info.get("anchor_parse_confidence"):
                lines.append(f"  Anchor parse confidence: {text_info.get('anchor_parse_confidence')}")
            if (
                text_info.get("anchor_expected_source") == "confirmed_from_fixture_setup"
                and text_info.get("anchor_parse_confidence") != "direct_confirmed"
            ):
                lines.append(
                    "  Note: UI anchor value is confirmed by fixture setup, but direct binary offset is not confirmed yet."
                )
            text_notes = text_info.get("notes") or []
            if text_notes:
                lines.append("  Text notes:")
                for note in text_notes:
                    lines.append(f"    * {note}")
            style_for_text = obj.get("style_candidates") or {}
            if style_for_text:
                lines.append(f"  Color candidate: {style_for_text.get('line_color_name')}")
                lines.append(f"  Color confidence: {style_for_text.get('line_color_confidence')}")
                lines.append(f"  Color source: {style_for_text.get('line_color_source')}")
                raw_candidates = style_for_text.get("color_candidates") or []
                if raw_candidates:
                    lines.append("  Raw color candidates:")
                    for candidate in raw_candidates[:8]:
                        lines.append(
                            "    "
                            f"* offset={candidate.get('offset')} raw={candidate.get('raw_hex')} "
                            f"name={candidate.get('name')} hex=#{candidate.get('hex_rgb')} "
                            f"confidence={candidate.get('confidence')} source={candidate.get('source')}"
                        )
        append_style_lines(obj.get("style_candidates"), "  ")
        source = obj.get("source")
        if source:
            lines.append(
                "  Source offsets: "
                f"class={source.get('node_class')}, payload={source.get('payload_offset')}, stream={source.get('stream_offset')}"
            )
        contour_preview = obj.get("contour_preview") or []
        if contour_preview:
            lines.append("  First contour records:")
            for rec in contour_preview[:4]:
                lines.append(
                    "    "
                    f"- R{rec['index']}: ({rec['x_mm']:.3f}, {rec['y_mm']:.3f}, {rec['z_mm']:.3f}) mm, "
                    f"w={rec['w']:.3f}, tag={rec['tag_hex']}, role={rec['role']}"
                )
        unknowns = obj.get("unknown_sections") or []
        if unknowns:
            lines.append("  Unknown/raw sections:")
            for item in unknowns:
                lines.append(f"    - {item['name']}: {item['size']} bytes")

        children = obj.get("children") or []
        for child in children:
            lines.append(f"  [Child #{child['index']}]")
            lines.append(f"    Type: {child['object_type']}")
            lines.extend(_fmt_bbox_line("    BBox", child.get("bbox_mm"), indent=""))
            lines.append(f"    Contour records: {child.get('contour_record_count', 0)}")
            lines.append(f"    Anchor/Control: {child.get('anchor_count', 0)}/{child.get('control_count', 0)}")
            append_style_lines(child.get("style_candidates"), "    ")
            child_unknowns = child.get("unknown_sections") or []
            if child_unknowns:
                lines.append("    Unknown/raw sections:")
                for item in child_unknowns:
                    lines.append(f"      - {item['name']}: {item['size']} bytes")

        for note in obj.get("notes") or []:
            lines.append(f"  Note: {note}")

    text = payload.get("text") or {}
    if text:
        lines.append("")
        lines.append("Text object info:")
        lines.append(f"  is_text_object: {text.get('is_text_object')}")
        lines.append(f"  font_name: {text.get('font_name')}")
        lines.append(f"  font_candidates: {text.get('font_candidates')}")
        lines.append(f"  text_content: {text.get('text_content')}")
        lines.append(f"  source_text_candidate: {text.get('source_text_candidate')}")
        lines.append(f"  display_text_candidate: {text.get('display_text_candidate')}")
        lines.append(f"  raw_text_record_count: {text.get('raw_text_record_count')}")

    warnings = payload.get("warnings") or []
    if warnings:
        lines.append("")
        lines.append("Warnings:")
        for warning in warnings:
            lines.append(f"- {warning}")

    notes = payload.get("notes") or []
    if notes:
        lines.append("")
        lines.append("Notes:")
        for note in notes:
            lines.append(f"- {note}")

    return "\n".join(lines)


def _contiguous_diff_ranges(data_a: bytes, data_b: bytes) -> list[dict[str, int]]:
    limit = min(len(data_a), len(data_b))
    ranges: list[dict[str, int]] = []
    start = -1
    for idx in range(limit):
        if data_a[idx] != data_b[idx]:
            if start < 0:
                start = idx
            continue
        if start >= 0:
            ranges.append({"start": start, "end": idx, "size": idx - start})
            start = -1
    if start >= 0:
        ranges.append({"start": start, "end": limit, "size": limit - start})
    if len(data_a) != len(data_b):
        ranges.append({"start": limit, "end": max(len(data_a), len(data_b)), "size": abs(len(data_a) - len(data_b))})
    return ranges


def build_diff_dict(
    left_label: str,
    left_payload: dict[str, Any],
    left_data: bytes,
    right_label: str,
    right_payload: dict[str, Any],
    right_data: bytes,
) -> dict[str, Any]:
    left_markers = left_payload.get("marker_order") or []
    right_markers = right_payload.get("marker_order") or []

    structural: list[str] = []
    if left_payload.get("declared_object_count") != right_payload.get("declared_object_count"):
        structural.append(
            "declared object count changed; possible wrapper/container difference (including 결합 candidate)."
        )
    if left_payload.get("is_grouped") != right_payload.get("is_grouped"):
        structural.append("group detection state changed between samples.")
    if left_payload.get("candidate_fields", {}).get("structure_kind") != right_payload.get("candidate_fields", {}).get("structure_kind"):
        structural.append("structure_kind candidate changed.")

    return {
        "left": {
            "label": left_label,
            "raw_size": left_payload.get("raw_size"),
            "declared_object_count": left_payload.get("declared_object_count"),
            "marker_order": left_markers,
            "marker_offsets": left_payload.get("marker_offsets"),
            "aggregate_bbox_mm": left_payload.get("aggregate_bbox_mm"),
            "objects_count": len(left_payload.get("objects") or []),
        },
        "right": {
            "label": right_label,
            "raw_size": right_payload.get("raw_size"),
            "declared_object_count": right_payload.get("declared_object_count"),
            "marker_order": right_markers,
            "marker_offsets": right_payload.get("marker_offsets"),
            "aggregate_bbox_mm": right_payload.get("aggregate_bbox_mm"),
            "objects_count": len(right_payload.get("objects") or []),
        },
        "additional_markers_in_right": sorted(set(right_markers) - set(left_markers)),
        "additional_markers_in_left": sorted(set(left_markers) - set(right_markers)),
        "changed_byte_ranges": _contiguous_diff_ranges(left_data, right_data),
        "structural_differences": structural,
    }


def render_diff_text(diff: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("=" * 60)
    lines.append("TYPE3 Clipboard Hex Diff")
    lines.append("=" * 60)
    lines.append(f"Left:  {diff['left']['label']}")
    lines.append(f"Right: {diff['right']['label']}")
    lines.append(f"Left size: {diff['left']['raw_size']} bytes")
    lines.append(f"Right size: {diff['right']['raw_size']} bytes")
    lines.append(f"Left declared object count: {diff['left']['declared_object_count']}")
    lines.append(f"Right declared object count: {diff['right']['declared_object_count']}")
    lines.append(f"Left marker order: {' -> '.join(diff['left']['marker_order'])}")
    lines.append(f"Right marker order: {' -> '.join(diff['right']['marker_order'])}")
    lines.append(f"Additional markers in right: {diff['additional_markers_in_right'] or 'none'}")
    lines.append(f"Additional markers in left: {diff['additional_markers_in_left'] or 'none'}")

    lines.append("Marker offsets (left):")
    for item in diff["left"].get("marker_offsets") or []:
        lines.append(
            "  "
            f"- {item['class_name']}: start={item['start_offset']}, payload={item['payload_offset']}, end={item['end_offset']}"
        )
    lines.append("Marker offsets (right):")
    for item in diff["right"].get("marker_offsets") or []:
        lines.append(
            "  "
            f"- {item['class_name']}: start={item['start_offset']}, payload={item['payload_offset']}, end={item['end_offset']}"
        )

    left_bbox = diff["left"].get("aggregate_bbox_mm")
    right_bbox = diff["right"].get("aggregate_bbox_mm")
    lines.extend(_fmt_bbox_line("Left aggregate bbox", left_bbox))
    lines.extend(_fmt_bbox_line("Right aggregate bbox", right_bbox))

    lines.append("Changed byte ranges:")
    ranges = diff.get("changed_byte_ranges") or []
    lines.append(f"  Total ranges: {len(ranges)}")
    for item in ranges[:40]:
        lines.append(f"  - [{item['start']}:{item['end']}] ({item['size']} bytes)")
    if len(ranges) > 40:
        lines.append(f"  - ... {len(ranges) - 40} additional ranges omitted")

    structural = diff.get("structural_differences") or []
    lines.append("Structural differences:")
    if structural:
        for item in structural:
            lines.append(f"  - {item}")
    else:
        lines.append("  - none detected by current heuristics")

    return "\n".join(lines)


def render_style_debug_text(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("=" * 60)
    lines.append("STYLE DEBUG")
    lines.append("=" * 60)
    lines.append(f"Input: {payload.get('source')}")

    def dump_style_block(label: str, style: dict[str, Any] | None) -> None:
        if not style:
            return
        lines.append(label)
        lines.append(
            "  "
            f"CPropertyExtend payload_offset={style.get('property_extend_payload_offset')} "
            f"stream_offset={style.get('property_extend_stream_offset')} "
            f"payload_length={style.get('property_extend_payload_length')}"
        )
        lines.append(
            "  "
            f"fixed[{style.get('fixed_primary_offset')}]={style.get('fixed_primary_raw_hex')} "
            f"fixed[{style.get('fixed_secondary_offset')}]={style.get('fixed_secondary_raw_hex')}"
        )
        candidates = style.get("color_candidates") or []
        lines.append(f"  palette candidates: {len(candidates)}")
        for candidate in candidates[:16]:
            lines.append(
                "    "
                f"- offset={candidate.get('offset')} raw={candidate.get('raw_hex')} "
                f"name={candidate.get('name')} hex=#{candidate.get('hex_rgb')} "
                f"confidence={candidate.get('confidence')} source={candidate.get('source')} "
                f"encoding={candidate.get('encoding')}"
            )
        lines.append(
            "  "
            f"chosen color: {style.get('line_color_name')} ({style.get('line_color_hex')}) "
            f"raw={style.get('line_color_selected_raw_hex')} "
            f"confidence={style.get('line_color_confidence')} source={style.get('line_color_source')}"
        )

    for obj in payload.get("objects", []):
        dump_style_block(f"[Object #{obj.get('index')}]", obj.get("style_candidates"))
        for child in obj.get("children") or []:
            dump_style_block(f"[Object #{obj.get('index')} / Child #{child.get('index')}]", child.get("style_candidates"))

    if len(lines) <= 4:
        lines.append("No style data available.")
    return "\n".join(lines)
