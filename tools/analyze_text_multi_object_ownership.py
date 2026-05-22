from __future__ import annotations

import argparse
import json
import math
import struct
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from type3_clipboard_codec import parse_type3_clipboard_bytes_with_parser
from type3_clipboard_codec.inspect.hex_input import hex_text_to_bytes
from type3_clipboard_codec.models.geometry import BBox3D, GeometryObject, Point, Type3Node
from type3_clipboard_codec.parsers.text.cparagraphe_parser import (
    extract_font_candidates,
    read_paragraphe_slot_record_runs,
    records_to_text_run,
)
from type3_clipboard_codec.parsers.type3_chain_parser import Type3ChainParser

TEXT_DIR = REPO_ROOT / "tests" / "samples" / "text"
FIXTURES = [
    "text_group_same_color_two_objects.txt",
    "text_group_mixed_color_two_objects.txt",
    "text_two_objects_mixed_color_not_grouped.txt",
    "text_two_objects_same_color_not_grouped.txt",
    "text_two_objects_not_grouped_selection_reversed.txt",
    "text_three_objects_not_grouped.txt",
]
COMPARISON_FIXTURES = ["default_text.txt", *FIXTURES]
EXPECTED_ANCHORS_MM = [
    (111.111, 222.222, 0.0),
    (211.111, 322.222, 0.0),
    (311.111, 422.222, 0.0),
]
DIRECT_ANCHOR_OFFSETS = (158, 166, 174)
TOP_LEVEL_HEADER_LEN = 6


def _read_fixture(name: str) -> bytes:
    return hex_text_to_bytes((TEXT_DIR / name).read_text(encoding="utf-8"))


def _point_mm(point: Point | None) -> dict[str, float] | None:
    if point is None:
        return None
    return {"x": round(point.x, 6), "y": round(point.y, 6), "z": round(point.z, 6)}


def _bbox_mm(bbox: BBox3D | None) -> dict[str, float] | None:
    if bbox is None:
        return None
    return {
        "xmin": round(bbox.xmin_mm, 6),
        "ymin": round(bbox.ymin_mm, 6),
        "zmin": round(bbox.zmin_mm, 6),
        "xmax": round(bbox.xmax_mm, 6),
        "ymax": round(bbox.ymax_mm, 6),
        "zmax": round(bbox.zmax_mm, 6),
        "center_x": round(bbox.center_mm.x, 6),
        "center_y": round(bbox.center_mm.y, 6),
        "center_z": round(bbox.center_mm.z, 6),
    }


def _distance_2d(a: dict[str, float] | None, b: dict[str, float] | None) -> float | None:
    if a is None or b is None:
        return None
    return round(math.hypot(float(a["x"]) - float(b["x"]), float(a["y"]) - float(b["y"])), 6)


def _decode_direct_anchor(payload: bytes) -> dict[str, Any] | None:
    x_off, y_off, z_off = DIRECT_ANCHOR_OFFSETS
    if len(payload) < z_off + 8:
        return None
    x_m, y_m, z_m = struct.unpack("<ddd", payload[x_off : z_off + 8])
    if not all(math.isfinite(v) for v in (x_m, y_m, z_m)):
        return None
    return {
        "payload_offsets": {"x": x_off, "y": y_off, "z": z_off},
        "decoded_anchor_mm": {
            "x": round(x_m * 1000.0, 6),
            "y": round(y_m * 1000.0, 6),
            "z": round(z_m * 1000.0, 6),
        },
        "candidate_type": "double64le_contiguous_triple",
    }


def _same_point(a: dict[str, float] | None, b: dict[str, float] | None, tol_mm: float = 1e-6) -> bool:
    if a is None or b is None:
        return False
    return (
        abs(float(a["x"]) - float(b["x"])) <= tol_mm
        and abs(float(a["y"]) - float(b["y"])) <= tol_mm
        and abs(float(a["z"]) - float(b["z"])) <= tol_mm
    )


def _expected_point(anchor: tuple[float, float, float]) -> dict[str, float]:
    return {"x": anchor[0], "y": anchor[1], "z": anchor[2]}


def _read_nodes(blob: bytes) -> list[Type3Node]:
    return Type3ChainParser()._extract_nodes(blob[TOP_LEVEL_HEADER_LEN:])


def _node_abs_start(node: Type3Node) -> int:
    return node.start_offset + TOP_LEVEL_HEADER_LEN


def _node_payload_abs_start(node: Type3Node) -> int:
    return node.payload_offset + TOP_LEVEL_HEADER_LEN


def _node_abs_end(node: Type3Node) -> int:
    return node.end_offset + TOP_LEVEL_HEADER_LEN


def _text_runs_from_node(node: Type3Node) -> list[dict[str, Any]]:
    if node.header.class_name != "CParagraphe":
        return []
    runs = []
    for records in read_paragraphe_slot_record_runs(node.payload):
        run = records_to_text_run(records)
        if run is not None:
            runs.append({"text": run["text"], "line_count": run["line_count"], "record_count": len(records)})
    return runs


def _style_summary(node: Type3Node) -> dict[str, Any] | None:
    if node.header.class_name != "CPropertyExtend":
        return None
    candidates = []
    for off in (0x79, 0x85, 0x20E, 0x21A):
        if off + 4 <= len(node.payload):
            candidates.append({"payload_offset": off, "u32le": struct.unpack("<I", node.payload[off : off + 4])[0]})
    return {"color_candidate_count": len(candidates), "color_candidates": candidates} if candidates else None


def _node_inventory(blob: bytes, nodes: list[Type3Node]) -> list[dict[str, Any]]:
    rows = []
    for idx, node in enumerate(nodes):
        direct = _decode_direct_anchor(node.payload) if node.header.class_name == "CParagraphe" else None
        fonts = extract_font_candidates(node.payload)
        text_runs = _text_runs_from_node(node)
        rows.append(
            {
                "node_index": idx,
                "class_name": node.header.class_name,
                "absolute_start": _node_abs_start(node),
                "payload_relative_offset": node.start_offset,
                "class_payload_relative_offset": 0,
                "class_payload_absolute_start": _node_payload_abs_start(node),
                "bbox": _bbox_mm(node.bbox),
                "direct_anchor_triple_candidate": direct,
                "text_candidate": text_runs[0]["text"] if text_runs else None,
                "text_run_candidates": text_runs,
                "font_candidate": fonts[0] if fonts else None,
                "style_color_candidate": _style_summary(node),
                "raw_payload_length": len(node.payload),
                "absolute_end": min(_node_abs_end(node), len(blob)),
            }
        )
    return rows


def _nearest_nodes(chain_offset: int | None, nodes: list[Type3Node]) -> dict[str, Any]:
    if chain_offset is None:
        return {"preceding": None, "following": None}
    preceding = None
    following = None
    for idx, node in enumerate(nodes):
        start = node.payload_offset
        row = {"node_index": idx, "class_name": node.header.class_name, "payload_offset": start}
        if start <= chain_offset:
            preceding = row
        elif following is None:
            following = row
    return {"preceding": preceding, "following": following}


def _chain_inventory(parsed: GeometryObject, nodes: list[Type3Node]) -> list[dict[str, Any]]:
    rows = []
    for idx, chain in enumerate(parsed.object_chains):
        associated = []
        chain_node_ids = {id(node) for node in chain.nodes}
        for node_idx, node in enumerate(nodes):
            if id(node) in chain_node_ids:
                associated.append(node_idx)
        source_offsets = {
            "source_payload_offset": chain.source_payload_offset,
            "source_stream_offset": chain.source_stream_offset,
        }
        rows.append(
            {
                "chain_index": idx,
                "shape_or_object_type": chain.shape_type or parsed.object_type,
                "markers": list(chain.markers),
                "class_list": [node.header.class_name for node in chain.nodes],
                "bbox": _bbox_mm(chain.bbox),
                "parser_baseline_midpoint_anchor": _point_mm(chain.text_anchor),
                "anchor_parse_method": chain.text_anchor_parse_method,
                "text_candidate": chain.source_text_candidate or chain.text_candidate,
                "source_payload_offsets": source_offsets,
                "associated_node_indexes": associated,
                "nearest_nodes_by_offset": _nearest_nodes(chain.source_payload_offset, nodes),
                "candidate_ownership_notes": [
                    "Chain is parser-derived geometry/outline evidence.",
                    "Do not equate chain index with CParagraphe ownership without matching evidence.",
                ],
            }
        )
    return rows


def _bbox_proximity(direct: dict[str, float] | None, chain_row: dict[str, Any]) -> float | None:
    bbox = chain_row.get("bbox")
    if bbox is None or direct is None:
        return None
    return _distance_2d(direct, {"x": bbox["center_x"], "y": bbox["center_y"], "z": bbox["center_z"]})


def _ownership_analysis(node_rows: list[dict[str, Any]], chain_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    cpar_nodes = [row for row in node_rows if row["class_name"] == "CParagraphe"]
    for node in cpar_nodes:
        direct = node.get("direct_anchor_triple_candidate")
        direct_mm = direct.get("decoded_anchor_mm") if direct else None
        exact_matches = [
            chain["chain_index"]
            for chain in chain_rows
            if _same_point(direct_mm, chain.get("parser_baseline_midpoint_anchor"))
        ]
        prox = [
            {
                "chain_index": chain["chain_index"],
                "anchor_distance_mm": _distance_2d(direct_mm, chain.get("parser_baseline_midpoint_anchor")),
                "bbox_center_distance_mm": _bbox_proximity(direct_mm, chain),
            }
            for chain in chain_rows
        ]
        prox.sort(key=lambda r: (float("inf") if r["anchor_distance_mm"] is None else r["anchor_distance_mm"]))
        nearest = prox[0]["chain_index"] if prox else None
        confidence = "strong_for_one_chain_unresolved_for_other_chains" if exact_matches else "unresolved"
        rows.append(
            {
                "node_index": node["node_index"],
                "direct_anchor_offsets": {"x": 158, "y": 166, "z": 174},
                "decoded_direct_anchor_mm": direct_mm,
                "text_run_candidates": node.get("text_run_candidates", []),
                "nearest_chain_by_offset": node.get("nearest_chain_by_offset"),
                "exact_anchor_match_chains": exact_matches,
                "bbox_overlap_or_proximity": prox,
                "ownership_confidence": confidence,
                "notes": [
                    "Direct triple links best to chains whose parser baseline_midpoint anchor is exactly equal.",
                    "Text run ownership remains separate from anchor ownership.",
                    "Single CParagraphe cannot currently explain every parsed chain as a per-chain direct field.",
                ],
                "nearest_chain_by_anchor_distance": nearest,
            }
        )
    return rows


def _classify_offset(offset: int, nodes: list[Type3Node]) -> dict[str, Any]:
    for idx, node in enumerate(nodes):
        payload_start = _node_payload_abs_start(node)
        payload_end = payload_start + len(node.payload)
        if payload_start <= offset < payload_end:
            return {
                "node_index": idx,
                "node_class": node.header.class_name,
                "class_payload_relative_offset": offset - payload_start,
                "inside_cparagraphe": node.header.class_name == "CParagraphe",
                "inside_text_related_or_geometry_node": node.header.class_name
                in {"CParagraphe", "CPropertyExtend", "CContour", "CCourbe", "CZone"},
            }
    return {
        "node_index": None,
        "node_class": None,
        "class_payload_relative_offset": None,
        "inside_cparagraphe": False,
        "inside_text_related_or_geometry_node": False,
    }


def _scan_anchor_triple(blob: bytes, nodes: list[Type3Node], chain_rows: list[dict[str, Any]], anchor: tuple[float, float, float]) -> dict[str, Any]:
    target_m = tuple(v / 1000.0 for v in anchor)
    hits = []
    for off in range(0, len(blob) - 24 + 1):
        x, y, z = struct.unpack("<ddd", blob[off : off + 24])
        if not all(math.isfinite(v) for v in (x, y, z)):
            continue
        diffs_mm = (
            abs(x - target_m[0]) * 1000.0,
            abs(y - target_m[1]) * 1000.0,
            abs(z - target_m[2]) * 1000.0,
        )
        if any(diff > 1e-6 for diff in diffs_mm):
            continue
        node_context = _classify_offset(off, nodes)
        chain_distances = [
            {
                "chain_index": chain["chain_index"],
                "anchor_distance_mm": _distance_2d(_expected_point(anchor), chain.get("parser_baseline_midpoint_anchor")),
                "source_payload_offset": chain["source_payload_offsets"]["source_payload_offset"],
            }
            for chain in chain_rows
        ]
        chain_distances.sort(key=lambda r: (float("inf") if r["anchor_distance_mm"] is None else r["anchor_distance_mm"]))
        hits.append(
            {
                "absolute_offset": off,
                "diffs_mm": {"x": round(diffs_mm[0], 9), "y": round(diffs_mm[1], 9), "z": round(diffs_mm[2], 9)},
                **node_context,
                "chain_relative_context": chain_distances[:3],
            }
        )
    return {
        "target_anchor_mm": _expected_point(anchor),
        "hit_count": len(hits),
        "hits": hits,
        "status": "found" if hits else "not found as exact contiguous triple",
    }


def _fixture_report(name: str) -> dict[str, Any]:
    blob = _read_fixture(name)
    parsed, parser_name = parse_type3_clipboard_bytes_with_parser(blob)
    if not isinstance(parsed, GeometryObject):
        raise TypeError(f"{name} did not parse as GeometryObject")
    nodes = _read_nodes(blob)
    node_rows = _node_inventory(blob, nodes)
    chain_rows = _chain_inventory(parsed, nodes)
    cpar_count = sum(1 for row in node_rows if row["class_name"] == "CParagraphe")
    scan_rows = [_scan_anchor_triple(blob, nodes, chain_rows, anchor) for anchor in EXPECTED_ANCHORS_MM]
    return {
        "fixture": name,
        "parser_name": parser_name,
        "raw_size": len(blob),
        "parser_chain_count": len(chain_rows),
        "cparagraphe_count": cpar_count,
        "node_inventory": node_rows,
        "chain_inventory": chain_rows,
        "cparagraphe_ownership_analysis": _ownership_analysis(node_rows, chain_rows),
        "whole_payload_anchor_scan": scan_rows,
        "summary": _fixture_summary(name, cpar_count, chain_rows, scan_rows),
    }


def _fixture_summary(name: str, cpar_count: int, chain_rows: list[dict[str, Any]], scan_rows: list[dict[str, Any]]) -> dict[str, Any]:
    direct_hits = {
        f"{scan['target_anchor_mm']['x']},{scan['target_anchor_mm']['y']},{scan['target_anchor_mm']['z']}": scan["status"]
        for scan in scan_rows
    }
    return {
        "fixture": name,
        "cparagraphe_count": cpar_count,
        "chain_count": len(chain_rows),
        "direct_triple_scan_status": direct_hits,
        "ownership_status": "chain_count_exceeds_cparagraphe_count" if len(chain_rows) != cpar_count else "count_aligned",
    }


def build_report() -> dict[str, Any]:
    reports = [_fixture_report(name) for name in COMPARISON_FIXTURES]
    multi = [row for row in reports if row["fixture"] in FIXTURES]
    return {
        "policy": {
            "scope": "structure/evidence audit only",
            "parser_behavior": "not_modified",
            "direct_anchor_promotion": "not_applied",
            "absolute_offsets": "diagnostic_only",
            "active_anchor_fallback": "baseline_midpoint remains active",
        },
        "fixtures": reports,
        "multi_object_fixtures": multi,
        "answers": _answers(multi),
    }


def _answers(multi: list[dict[str, Any]]) -> dict[str, Any]:
    unmatched_status = {}
    for fx in multi:
        statuses = []
        for scan in fx["whole_payload_anchor_scan"]:
            statuses.append({"target_anchor_mm": scan["target_anchor_mm"], "status": scan["status"], "hit_count": scan["hit_count"]})
        unmatched_status[fx["fixture"]] = statuses
    return {
        "cparagraphe_always_one_in_multi_object_fixtures": all(fx["cparagraphe_count"] == 1 for fx in multi),
        "best_current_connection_basis": "exact equality between CParagraphe direct triple and parser baseline_midpoint anchor for one chain; chain/source offset and bbox proximity are supporting diagnostics only",
        "unmatched_chain_anchor_presence": unmatched_status,
        "parser_readiness": "not_ready",
        "why_not_ready": [
            "chain count and CParagraphe count diverge in multi-object fixtures",
            "the unmatched chain anchor triple is outside CParagraphe in current multi-object fixtures",
            "text-run ownership and anchor ownership are not yet structurally separable for all chains",
        ],
    }


def _print_text(report: dict[str, Any]) -> None:
    print("Text Multi-object Ownership Analysis")
    print(f"policy.scope: {report['policy']['scope']}")
    print(f"policy.parser_behavior: {report['policy']['parser_behavior']}")
    print(f"policy.active_anchor_fallback: {report['policy']['active_anchor_fallback']}")
    print()
    for fx in report["multi_object_fixtures"]:
        print(f"Fixture: {fx['fixture']}")
        print(f"  parser_chains={fx['parser_chain_count']} cparagraphe_count={fx['cparagraphe_count']}")
        print("  [Node inventory]")
        for node in fx["node_inventory"]:
            direct = node["direct_anchor_triple_candidate"]
            print(
                f"    node={node['node_index']} class={node['class_name']} "
                f"payload_rel={node['payload_relative_offset']} payload_len={node['raw_payload_length']} "
                f"text={node['text_candidate']} direct={direct['decoded_anchor_mm'] if direct else None}"
            )
        print("  [Chain inventory]")
        for chain in fx["chain_inventory"]:
            print(
                f"    chain={chain['chain_index']} type={chain['shape_or_object_type']} "
                f"anchor={chain['parser_baseline_midpoint_anchor']} text={chain['text_candidate']} "
                f"source_offsets={chain['source_payload_offsets']} nodes={chain['associated_node_indexes']}"
            )
        print("  [CParagraphe ownership analysis]")
        for row in fx["cparagraphe_ownership_analysis"]:
            print(
                f"    cpar_node={row['node_index']} direct={row['decoded_direct_anchor_mm']} "
                f"exact_anchor_match_chains={row['exact_anchor_match_chains']} "
                f"confidence={row['ownership_confidence']}"
            )
        print("  [Whole-payload anchor scan]")
        for scan in fx["whole_payload_anchor_scan"]:
            print(
                f"    target={scan['target_anchor_mm']} hit_count={scan['hit_count']} status={scan['status']}"
            )
        print()
    print("[Answers]")
    print(json.dumps(report["answers"], ensure_ascii=False, indent=2))


def _print_markdown(report: dict[str, Any]) -> None:
    print("# Text Multi-object Ownership Analysis")
    print()
    print("| fixture | parser chains | CParagraphe count | ownership status |")
    print("|---|---:|---:|---|")
    for fx in report["multi_object_fixtures"]:
        print(
            f"| {fx['fixture']} | {fx['parser_chain_count']} | {fx['cparagraphe_count']} | "
            f"{fx['summary']['ownership_status']} |"
        )
    print()
    print("## Whole-payload Anchor Scan")
    print()
    print("| fixture | target anchor mm | hit count | status |")
    print("|---|---|---:|---|")
    for fx in report["multi_object_fixtures"]:
        for scan in fx["whole_payload_anchor_scan"]:
            print(f"| {fx['fixture']} | {scan['target_anchor_mm']} | {scan['hit_count']} | {scan['status']} |")


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit multi-object text chain/node ownership evidence.")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--markdown", action="store_true")
    args = parser.parse_args()

    report = build_report()
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    elif args.markdown:
        _print_markdown(report)
    else:
        _print_text(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
