from __future__ import annotations

import argparse
import json
import struct
from pathlib import Path
from typing import Any

from type3_clipboard_codec import parse_type3_clipboard_bytes_with_parser
from type3_clipboard_codec.inspect.hex_input import hex_text_to_bytes
from type3_clipboard_codec.models.geometry import BBox3D, GeometryObject, Type3Node
from type3_clipboard_codec.parsers.binary.node_scanner import extract_nodes
from type3_clipboard_codec.parsers.common import read_contour_points
from type3_clipboard_codec.utils.bytes_reader import BytesReader


REPO_ROOT = Path(__file__).resolve().parents[1]
SAMPLES_ROOT = REPO_ROOT / "tests" / "samples"
STRIDE = 36

FIXTURES = [
    "polyline_5_points.txt",
    "polygon_5_sides.txt",
    "polygon_6_sides.txt",
    "turquoise_rectangle_and_army_green_rectangle.txt",
    "two_circle.txt",
    "two_rectangle.txt",
    "default_rectangle.txt",
    "default_circle.txt",
    "default_circular_arc.txt",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze contour candidate competition evidence.")
    parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    return parser.parse_args()


def _decode_fixture(path: Path) -> tuple[GeometryObject, bytes, list[Type3Node]]:
    raw_hex = path.read_text(encoding="utf-8")
    payload = hex_text_to_bytes(raw_hex)
    parsed, _ = parse_type3_clipboard_bytes_with_parser(payload)
    if not isinstance(parsed, GeometryObject):
        raise ValueError(f"Fixture did not decode to GeometryObject: {path.name}")
    body = payload[6:] if len(payload) >= 6 else payload
    nodes = extract_nodes(body)
    return parsed, payload, nodes


def _resolve_node_for_diag(diag: dict[str, Any], nodes: list[Type3Node]) -> dict[str, Any]:
    marker_offset = diag.get("marker_offset")
    if marker_offset is None:
        return {"node_class_name": None, "node_index": None, "node_payload_length": None}

    shift8_raw = None
    for cand in diag.get("candidates", []):
        if cand.get("shift") == 8:
            shift8_raw = cand.get("raw_8b_hex")
            break

    for idx, node in enumerate(nodes):
        if node.header.class_name not in {"CContour", "CPropertyExtend"}:
            continue
        if marker_offset + 6 > len(node.payload):
            continue
        if node.payload[marker_offset : marker_offset + 6] != b"CObDao":
            continue
        if shift8_raw is not None:
            hs = marker_offset + 14
            if hs + 8 <= len(node.payload):
                if node.payload[hs : hs + 8].hex() != shift8_raw:
                    continue
        return {
            "node_class_name": node.header.class_name,
            "node_index": idx,
            "node_payload_length": len(node.payload),
            "node_bbox": node.bbox,
            "node_payload": node.payload,
        }
    return {"node_class_name": None, "node_index": None, "node_payload_length": None, "node_payload": None, "node_bbox": None}


def _bbox_from_points(points: list[Any]) -> dict[str, float] | None:
    if not points:
        return None
    xs = [p.x_m for p in points]
    ys = [p.y_m for p in points]
    zs = [p.z_m for p in points]
    return {
        "xmin_mm": round(min(xs) * 1000.0, 3),
        "ymin_mm": round(min(ys) * 1000.0, 3),
        "zmin_mm": round(min(zs) * 1000.0, 3),
        "xmax_mm": round(max(xs) * 1000.0, 3),
        "ymax_mm": round(max(ys) * 1000.0, 3),
        "zmax_mm": round(max(zs) * 1000.0, 3),
    }


def _bbox_relation(candidate_bbox: dict[str, float] | None, node_bbox: BBox3D | None) -> str:
    if candidate_bbox is None or node_bbox is None:
        return "unknown"
    nx0, ny0, nx1, ny1 = node_bbox.xmin_mm, node_bbox.ymin_mm, node_bbox.xmax_mm, node_bbox.ymax_mm
    cx0, cy0, cx1, cy1 = (
        candidate_bbox["xmin_mm"],
        candidate_bbox["ymin_mm"],
        candidate_bbox["xmax_mm"],
        candidate_bbox["ymax_mm"],
    )
    eps = 0.5
    approx_equal = abs(nx0 - cx0) <= eps and abs(ny0 - cy0) <= eps and abs(nx1 - cx1) <= eps and abs(ny1 - cy1) <= eps
    if approx_equal:
        return "approximate_equality"
    contained = cx0 >= nx0 - eps and cy0 >= ny0 - eps and cx1 <= nx1 + eps and cy1 <= ny1 + eps
    if contained:
        return "contained_in_node_bbox"
    overlap = not (cx1 < nx0 or cx0 > nx1 or cy1 < ny0 or cy0 > ny1)
    if overlap:
        return "overlap"
    return "mismatch"


def _candidate_record_evidence(candidate: dict[str, Any], node_payload: bytes | None, node_bbox: BBox3D | None) -> dict[str, Any]:
    out = {
        "record_region_start_offset": None,
        "record_region_end_offset": candidate.get("record_region_end_offset"),
        "decoded_record_count": 0,
        "first_record_summary": None,
        "last_record_summary": None,
        "candidate_record_bbox_mm": None,
        "candidate_bbox_vs_node_bbox": "unknown",
        "role_pattern": [],
        "tag_pattern": [],
        "w_pattern": [],
        "first_last_point_equal": None,
        "geometrically_degenerate": None,
        "near_zero_extent": None,
    }
    if node_payload is None:
        return out
    header_offset = candidate.get("header_offset")
    count = candidate.get("count")
    if header_offset is None or count is None:
        return out
    start = header_offset + 8
    end = start + (int(count) * STRIDE)
    out["record_region_start_offset"] = start
    out["record_region_end_offset"] = end
    if start < 0 or end > len(node_payload):
        return out
    try:
        records = read_contour_points(BytesReader(node_payload[start:]), int(count), stride=STRIDE)
    except Exception:
        return out
    out["decoded_record_count"] = len(records)
    if not records:
        return out
    out["role_pattern"] = [r.role for r in records]
    out["tag_pattern"] = [f"0x{r.tag:08X}" for r in records]
    out["w_pattern"] = [round(r.w, 6) for r in records]
    first = records[0]
    last = records[-1]
    out["first_record_summary"] = {"x_mm": round(first.x_mm, 3), "y_mm": round(first.y_mm, 3), "w": first.w, "tag": f"0x{first.tag:08X}", "role": first.role}
    out["last_record_summary"] = {"x_mm": round(last.x_mm, 3), "y_mm": round(last.y_mm, 3), "w": last.w, "tag": f"0x{last.tag:08X}", "role": last.role}
    out["candidate_record_bbox_mm"] = _bbox_from_points(records)
    out["candidate_bbox_vs_node_bbox"] = _bbox_relation(out["candidate_record_bbox_mm"], node_bbox)
    out["first_last_point_equal"] = abs(first.x_mm - last.x_mm) <= 1e-3 and abs(first.y_mm - last.y_mm) <= 1e-3 and abs(first.z_mm - last.z_mm) <= 1e-3
    bbox = out["candidate_record_bbox_mm"]
    if bbox is not None:
        width = abs(bbox["xmax_mm"] - bbox["xmin_mm"])
        height = abs(bbox["ymax_mm"] - bbox["ymin_mm"])
        out["near_zero_extent"] = width < 1e-3 or height < 1e-3
        out["geometrically_degenerate"] = (width < 1e-3 and height < 1e-3) or len(records) <= 1
    return out


def _analyze_fixture(path: Path) -> dict[str, Any]:
    parsed, _payload, nodes = _decode_fixture(path)
    rows = []
    for block in parsed.candidate_fields.get("contour_header_diagnostics", []):
        chain_index = block.get("chain_index")
        for diag_idx, diag in enumerate(block.get("diagnostics", [])):
            node_ctx = _resolve_node_for_diag(diag, nodes)
            candidates = []
            for order, candidate in enumerate(diag.get("candidates", []), start=1):
                evidence = _candidate_record_evidence(candidate, node_ctx.get("node_payload"), node_ctx.get("node_bbox"))
                candidates.append(
                    {
                        "candidate_order": order,
                        "marker_context": {
                            "fixture": path.name,
                            "chain_index": chain_index,
                            "diagnostic_index": diag_idx,
                            "node_class_name": node_ctx.get("node_class_name"),
                            "node_index": node_ctx.get("node_index"),
                            "node_payload_length": node_ctx.get("node_payload_length"),
                            "marker_offset_relative_to_node_payload": diag.get("marker_offset"),
                            "candidate_shift": candidate.get("shift"),
                            "header_offset": candidate.get("header_offset"),
                            "raw_8b_hex": candidate.get("raw_8b_hex"),
                            "decoded_kind": candidate.get("kind"),
                            "decoded_count": candidate.get("count"),
                        },
                        "existing_validation": {
                            "legacy_plausible": candidate.get("legacy_plausible"),
                            "structural_valid": candidate.get("structural_valid"),
                            "structural_score": candidate.get("structural_score"),
                            "structural_failure_reasons": candidate.get("structural_failure_reasons"),
                            "bbox_consistency_status": candidate.get("bbox_consistency_status"),
                        },
                        "candidate_record_evidence": evidence,
                    }
                )
            rows.append(
                {
                    "fixture": path.name,
                    "chain_index": chain_index,
                    "diagnostic_index": diag_idx,
                    "competition_context": {
                        "legacy_selected_candidate": diag.get("legacy_selected_candidate"),
                        "structural_recommended_candidate": diag.get("structural_recommended_candidate"),
                        "multiple_structural_valid_candidates": len(diag.get("structurally_valid_candidates", [])) > 1,
                        "all_structural_valid_candidates": diag.get("structurally_valid_candidates", []),
                        "selection_mode": diag.get("selection_mode"),
                        "structural_policy_status": diag.get("structural_policy_status"),
                    },
                    "candidates": candidates,
                }
            )
    return {"fixture": path.name, "markers": rows}


def _build_report() -> dict[str, Any]:
    return {
        "policy": "diagnostic only; parser selection unchanged",
        "fixtures": [_analyze_fixture(SAMPLES_ROOT / name) for name in FIXTURES],
    }


def _print_text(report: dict[str, Any]) -> None:
    print("Contour Candidate Competition Analysis")
    print("policy: diagnostic only; parser selection unchanged")
    for fixture in report["fixtures"]:
        print(f"\n[{fixture['fixture']}]")
        for marker in fixture["markers"]:
            comp = marker["competition_context"]
            print(f"- marker#{marker['diagnostic_index']} chain={marker['chain_index']}")
            print(f"  legacy_selected={comp['legacy_selected_candidate']}")
            print(f"  structural_recommended={comp['structural_recommended_candidate']}")
            print(f"  multiple_structural_valid={comp['multiple_structural_valid_candidates']}")
            for cand in marker["candidates"]:
                ctx = cand["marker_context"]
                val = cand["existing_validation"]
                ev = cand["candidate_record_evidence"]
                print(
                    f"    cand#{cand['candidate_order']} shift={ctx['candidate_shift']} kind={ctx['decoded_kind']} count={ctx['decoded_count']} "
                    f"raw={ctx['raw_8b_hex']} legacy={val['legacy_plausible']} structural={val['structural_valid']} score={val['structural_score']}"
                )
                print(
                    f"      bbox_relation={ev['candidate_bbox_vs_node_bbox']} decoded_records={ev['decoded_record_count']} "
                    f"degenerate={ev['geometrically_degenerate']} near_zero={ev['near_zero_extent']}"
                )


def main() -> int:
    args = parse_args()
    report = _build_report()
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        _print_text(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
