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
from type3_clipboard_codec.parsers.type3_chain_parser import Type3ChainParser

TEXT_DIR = REPO_ROOT / "tests" / "samples" / "text"
FIXTURES = [
    "default_text.txt",
    "text_origin_offset.txt",
    "text_group_same_color_two_objects.txt",
    "text_group_mixed_color_two_objects.txt",
    "text_two_objects_mixed_color_not_grouped.txt",
]
MULTI_OBJECT_FIXTURES = [
    "text_group_same_color_two_objects.txt",
    "text_group_mixed_color_two_objects.txt",
    "text_two_objects_mixed_color_not_grouped.txt",
]
TARGET_ANCHORS_MM = [
    (111.111, 222.222, 0.0),
    (211.111, 322.222, 0.0),
]
TOP_LEVEL_HEADER_LEN = 6
LOCAL_WINDOW_RADIUS = 64
KNOWN_MARKERS = [
    b"OBJECTINFOS_CLASSNAME",
    b"OBJETINFOS_CLASSNAME",
    b"CPropertyExtend",
    b"CParagraphe",
    b"CContour",
    b"CCourbe",
    b"CZone",
    b"CObDao",
]
COBDAO_MARKER = b"CObDao"
OBJECTINFOS_MARKER = b"OBJECTINFOS_CLASSNAME"
OBJETINFOS_MARKER = b"OBJETINFOS_CLASSNAME"
COBDAO_ANCHOR_LOCAL_OFFSET = 34


def _read_fixture(name: str) -> bytes:
    return hex_text_to_bytes((TEXT_DIR / name).read_text(encoding="utf-8"))


def _read_nodes(blob: bytes) -> list[Type3Node]:
    return Type3ChainParser()._extract_nodes(blob[TOP_LEVEL_HEADER_LEN:])


def _node_payload_abs_start(node: Type3Node) -> int:
    return node.payload_offset + TOP_LEVEL_HEADER_LEN


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


def _distance_2d(left: dict[str, float] | None, right: dict[str, float] | None) -> float | None:
    if left is None or right is None:
        return None
    return round(math.hypot(float(left["x"]) - float(right["x"]), float(left["y"]) - float(right["y"])), 6)


def _target_point(anchor: tuple[float, float, float]) -> dict[str, float]:
    return {"x": anchor[0], "y": anchor[1], "z": anchor[2]}


def _scan_exact_triples(blob: bytes, anchor: tuple[float, float, float]) -> list[dict[str, Any]]:
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
        hits.append(
            {
                "absolute_offset": off,
                "decoded_anchor_mm": _target_point(anchor),
                "diffs_mm": {"x": round(diffs_mm[0], 9), "y": round(diffs_mm[1], 9), "z": round(diffs_mm[2], 9)},
            }
        )
    return hits


def _classify_hit(hit_abs: int, nodes: list[Type3Node]) -> dict[str, Any]:
    for idx, node in enumerate(nodes):
        payload_start = _node_payload_abs_start(node)
        payload_end = payload_start + len(node.payload)
        if payload_start <= hit_abs < payload_end:
            rel = hit_abs - payload_start
            return {
                "node_index": idx,
                "node_class": node.header.class_name,
                "node_payload_relative_offset": rel,
                "node_payload_offset": node.payload_offset,
                "node_payload_absolute_start": payload_start,
                "node_payload_length": len(node.payload),
                "node": node,
            }
    return {
        "node_index": None,
        "node_class": None,
        "node_payload_relative_offset": None,
        "node_payload_offset": None,
        "node_payload_absolute_start": None,
        "node_payload_length": None,
        "node": None,
    }


def _hex_window(payload: bytes, center: int, radius: int = LOCAL_WINDOW_RADIUS) -> dict[str, Any]:
    start = max(0, center - radius)
    end = min(len(payload), center + 24 + radius)
    return {
        "start": start,
        "end": end,
        "relative_anchor_start": center - start,
        "hex": payload[start:end].hex(" "),
    }


def _hex_window_around_marker(payload: bytes, marker_offset: int) -> dict[str, Any]:
    start = max(0, marker_offset - 64)
    end = min(len(payload), marker_offset + 128)
    return {
        "start": start,
        "end": end,
        "relative_marker_start": marker_offset - start,
        "hex": payload[start:end].hex(" "),
    }


def _nearby_doubles(payload: bytes, center: int, radius: int = LOCAL_WINDOW_RADIUS) -> list[dict[str, Any]]:
    start = max(0, center - radius)
    end = min(len(payload) - 8, center + 24 + radius)
    rows = []
    for off in range(start, end + 1):
        value = struct.unpack("<d", payload[off : off + 8])[0]
        if not math.isfinite(value):
            continue
        value_mm = value * 1000.0
        if abs(value_mm) > 1000000:
            continue
        if abs(value_mm) < 1e-9 or 0.001 <= abs(value_mm) <= 10000:
            rows.append({"offset": off, "double_m": value, "double_mm": round(value_mm, 6)})
    return rows[:80]


def _nearby_ints(payload: bytes, center: int, radius: int = LOCAL_WINDOW_RADIUS) -> list[dict[str, Any]]:
    start = max(0, center - radius)
    end = min(len(payload) - 4, center + 24 + radius)
    rows = []
    for off in range(start, end + 1, 4):
        raw = payload[off : off + 4]
        u32 = struct.unpack("<I", raw)[0]
        i32 = struct.unpack("<i", raw)[0]
        rows.append({"offset": off, "u32le": u32, "i32le": i32, "hex": raw.hex(" ")})
    return rows


def _zero_padding_runs(payload: bytes, center: int, radius: int = LOCAL_WINDOW_RADIUS) -> list[dict[str, int]]:
    start = max(0, center - radius)
    end = min(len(payload), center + 24 + radius)
    rows = []
    cursor = start
    while cursor < end:
        if payload[cursor] != 0:
            cursor += 1
            continue
        run_start = cursor
        while cursor < end and payload[cursor] == 0:
            cursor += 1
        if cursor - run_start >= 4:
            rows.append({"start": run_start, "length": cursor - run_start})
    return rows


def _nearest_marker(payload: bytes, center: int) -> dict[str, Any] | None:
    best = None
    for marker in KNOWN_MARKERS:
        start = 0
        while True:
            pos = payload.find(marker, start)
            if pos < 0:
                break
            dist = abs(center - pos)
            candidate = {"marker": marker.decode("ascii", errors="replace"), "offset": pos, "distance": dist}
            if best is None or candidate["distance"] < best["distance"]:
                best = candidate
            start = pos + 1
    return best


def _marker_positions(payload: bytes, marker: bytes) -> list[int]:
    positions = []
    start = 0
    while True:
        pos = payload.find(marker, start)
        if pos < 0:
            return positions
        positions.append(pos)
        start = pos + 1


def _nearest_objectinfos_before(payload: bytes, marker_offset: int) -> dict[str, Any] | None:
    marker_positions = []
    for marker in (OBJECTINFOS_MARKER, OBJETINFOS_MARKER):
        marker_positions.extend((marker, pos) for pos in _marker_positions(payload, marker) if pos <= marker_offset)
    marker_positions.sort(key=lambda item: item[1])
    positions = marker_positions
    if not positions:
        return None
    marker, pos = positions[-1]
    return {
        "marker": marker.decode("ascii"),
        "offset": pos,
        "distance_before_cobdao": marker_offset - pos,
    }


def _marker_signature(payload: bytes, center: int, radius: int = LOCAL_WINDOW_RADIUS) -> list[dict[str, Any]]:
    rows = []
    start_limit = max(0, center - radius)
    end_limit = min(len(payload), center + 24 + radius)
    for marker in KNOWN_MARKERS:
        start = start_limit
        while True:
            pos = payload.find(marker, start, end_limit)
            if pos < 0:
                break
            rows.append(
                {
                    "marker": marker.decode("ascii", errors="replace"),
                    "offset": pos,
                    "relative_to_hit": pos - center,
                }
            )
            start = pos + 1
    rows.sort(key=lambda row: (row["relative_to_hit"], row["marker"]))
    return rows


def _local_record_start_candidates(payload: bytes, center: int) -> list[dict[str, Any]]:
    candidates = set()
    for back in (0, 4, 8, 16, 24, 32, 40, 48, 64, 80, 96, 128, 148, 204):
        pos = center - back
        if 0 <= pos < len(payload):
            candidates.add(pos)
    for pos in range(max(0, center - 96), center + 1):
        if pos + 4 <= len(payload) and payload[pos : pos + 4] in {b"\x05\x00\x00\x00", b"\x01\x00\x00\x00"}:
            candidates.add(pos)
    rows = []
    for pos in sorted(candidates):
        prefix = payload[pos : min(len(payload), pos + 16)]
        rows.append(
            {
                "offset": pos,
                "distance_before_hit": center - pos,
                "prefix_hex": prefix.hex(" "),
                "u32le_at_start": struct.unpack("<I", payload[pos : pos + 4])[0] if pos + 4 <= len(payload) else None,
            }
        )
    return rows


def _decode_triple_at(payload: bytes, offset: int) -> dict[str, Any] | None:
    if offset < 0 or offset + 24 > len(payload):
        return None
    x, y, z = struct.unpack("<ddd", payload[offset : offset + 24])
    if not all(math.isfinite(v) for v in (x, y, z)):
        return None
    return {
        "offset": offset,
        "decoded_anchor_mm": {
            "x": round(x * 1000.0, 6),
            "y": round(y * 1000.0, 6),
            "z": round(z * 1000.0, 6),
        },
    }


def _chain_rows(parsed: GeometryObject) -> list[dict[str, Any]]:
    rows = []
    for idx, chain in enumerate(parsed.object_chains):
        anchor = _point_mm(chain.text_anchor)
        rows.append(
            {
                "chain_index": idx,
                "baseline_anchor_mm": anchor,
                "bbox": _bbox_mm(chain.bbox),
                "text_candidate": chain.source_text_candidate or chain.text_candidate,
                "source_payload_offset": chain.source_payload_offset,
                "source_stream_offset": chain.source_stream_offset,
                "source_node_class": chain.source_node_class,
            }
        )
    return rows


def _chain_context(hit_rel: int, node: Type3Node, target: dict[str, float], chains: list[dict[str, Any]]) -> list[dict[str, Any]]:
    hit_stream_offset = node.payload_offset + hit_rel
    rows = []
    for chain in chains:
        stream = chain["source_stream_offset"]
        source_delta = None if stream is None else hit_stream_offset - stream
        rows.append(
            {
                "chain_index": chain["chain_index"],
                "matched_chain_baseline_anchor": _distance_2d(target, chain["baseline_anchor_mm"]) == 0.0,
                "anchor_distance_mm": _distance_2d(target, chain["baseline_anchor_mm"]),
                "bbox_center_distance_mm": _distance_2d(
                    target,
                    {
                        "x": chain["bbox"]["center_x"],
                        "y": chain["bbox"]["center_y"],
                        "z": chain["bbox"]["center_z"],
                    }
                    if chain["bbox"] is not None
                    else None,
                ),
                "source_payload_offset": chain["source_payload_offset"],
                "source_stream_offset": stream,
                "hit_stream_offset": hit_stream_offset,
                "hit_minus_chain_source_stream_offset": source_delta,
                "text_candidate": chain["text_candidate"],
            }
        )
    rows.sort(key=lambda row: (float("inf") if row["anchor_distance_mm"] is None else row["anchor_distance_mm"]))
    return rows


def _chain_matches_for_point(point: dict[str, float] | None, chains: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if point is None:
        return []
    rows = []
    for chain in chains:
        rows.append(
            {
                "chain_index": chain["chain_index"],
                "matched_chain_baseline_anchor": _distance_2d(point, chain["baseline_anchor_mm"]) == 0.0,
                "anchor_distance_mm": _distance_2d(point, chain["baseline_anchor_mm"]),
                "bbox_center_distance_mm": _distance_2d(
                    point,
                    {
                        "x": chain["bbox"]["center_x"],
                        "y": chain["bbox"]["center_y"],
                        "z": chain["bbox"]["center_z"],
                    }
                    if chain["bbox"] is not None
                    else None,
                ),
                "source_payload_offset": chain["source_payload_offset"],
                "source_stream_offset": chain["source_stream_offset"],
                "text_candidate": chain["text_candidate"],
            }
        )
    rows.sort(key=lambda row: (float("inf") if row["anchor_distance_mm"] is None else row["anchor_distance_mm"]))
    return rows


def _color_candidates(node: Type3Node) -> list[dict[str, Any]]:
    rows = []
    for off in (0x79, 0x85, 0x20E, 0x21A):
        if off + 4 <= len(node.payload):
            rows.append({"payload_offset": off, "u32le": struct.unpack("<I", node.payload[off : off + 4])[0]})
    return rows


def _cobdao_sections(node: Type3Node, anchor_hits: list[dict[str, Any]], chains: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sections = []
    for marker_offset in _marker_positions(node.payload, COBDAO_MARKER):
        triple = _decode_triple_at(node.payload, marker_offset + COBDAO_ANCHOR_LOCAL_OFFSET)
        matching_hits = [
            hit
            for hit in anchor_hits
            if hit["node_class"] == "CPropertyExtend"
            and hit["cproperty_payload_relative_offset"] is not None
            and int(hit["cproperty_payload_relative_offset"]) - marker_offset == COBDAO_ANCHOR_LOCAL_OFFSET
        ]
        matched_chains = []
        if triple is not None:
            matched_chains = _chain_matches_for_point(triple["decoded_anchor_mm"], chains)
        sections.append(
            {
                "cobdao_marker_offset": marker_offset,
                "marker_text": COBDAO_MARKER.decode("ascii"),
                "marker_context_hex": _hex_window_around_marker(node.payload, marker_offset),
                "local_section_start_candidate": (
                    _nearest_objectinfos_before(node.payload, marker_offset) or {"offset": marker_offset}
                ),
                "nearby_objectinfos_marker": _nearest_objectinfos_before(node.payload, marker_offset),
                "decoded_values_from_cobdao": {
                    "double64_candidates": _nearby_doubles(node.payload, marker_offset, radius=48),
                    "u32_i32_candidates": _nearby_ints(node.payload, marker_offset, radius=48),
                },
                "local_triple_at_cobdao_plus_34": triple,
                "known_anchor_triple_hit": bool(matching_hits),
                "anchor_hits": matching_hits,
                "hit_relative_to_cobdao": (
                    int(matching_hits[0]["cproperty_payload_relative_offset"]) - marker_offset
                    if matching_hits
                    else None
                ),
                "matched_chains": [
                    row["chain_index"] for row in matched_chains if row["matched_chain_baseline_anchor"]
                ],
                "chain_match_candidates": matched_chains,
            }
        )
    return sections


def _anchor_hit_context(
    *,
    fixture: str,
    target_anchor: tuple[float, float, float],
    hit: dict[str, Any],
    nodes: list[Type3Node],
    chains: list[dict[str, Any]],
) -> dict[str, Any]:
    cls = _classify_hit(hit["absolute_offset"], nodes)
    node = cls["node"]
    if node is None:
        return {**hit, "fixture": fixture, "node_class": None}
    rel = int(cls["node_payload_relative_offset"])
    target = _target_point(target_anchor)
    return {
        "fixture": fixture,
        "target_anchor_mm": target,
        "absolute_offset": hit["absolute_offset"],
        "node_index": cls["node_index"],
        "node_class": cls["node_class"],
        "cproperty_payload_relative_offset": rel if cls["node_class"] == "CPropertyExtend" else None,
        "node_payload_relative_offset": rel,
        "local_context_hex": _hex_window(node.payload, rel),
        "nearby_decoded_doubles": _nearby_doubles(node.payload, rel),
        "nearby_u32_i32_values": _nearby_ints(node.payload, rel),
        "nearby_zero_padding_patterns": _zero_padding_runs(node.payload, rel),
        "nearest_known_class_marker": _nearest_marker(node.payload, rel),
        "local_marker_signature": _marker_signature(node.payload, rel),
        "possible_local_record_start_candidates": _local_record_start_candidates(node.payload, rel),
        "chain_match_candidates": _chain_context(rel, node, target, chains),
    }


def _fixture_report(name: str) -> dict[str, Any]:
    blob = _read_fixture(name)
    parsed, parser_name = parse_type3_clipboard_bytes_with_parser(blob)
    if not isinstance(parsed, GeometryObject):
        raise TypeError(f"{name} did not parse as GeometryObject")
    nodes = _read_nodes(blob)
    chains = _chain_rows(parsed)
    cprop_nodes = [(idx, node) for idx, node in enumerate(nodes) if node.header.class_name == "CPropertyExtend"]
    all_hit_contexts = []
    for target in TARGET_ANCHORS_MM:
        for hit in _scan_exact_triples(blob, target):
            all_hit_contexts.append(
                _anchor_hit_context(fixture=name, target_anchor=target, hit=hit, nodes=nodes, chains=chains)
            )
    cprop_summaries = []
    for idx, node in cprop_nodes:
        hits = [hit for hit in all_hit_contexts if hit["node_index"] == idx and hit["node_class"] == "CPropertyExtend"]
        cprop_summaries.append(
            {
                "fixture": name,
                "cproperty_node_index": idx,
                "payload_length": len(node.payload),
                "source_offset": node.start_offset,
                "payload_relative_offset": node.payload_offset,
                "known_color_candidates": _color_candidates(node),
                "anchor_triple_hits_inside_node": hits,
                "cobdao_sections": _cobdao_sections(node, hits, chains),
            }
        )
    return {
        "fixture": name,
        "parser_name": parser_name,
        "raw_size": len(blob),
        "chain_inventory": chains,
        "cproperty_nodes": cprop_summaries,
        "all_anchor_hits": all_hit_contexts,
    }


def _bytes_without_anchor(window: dict[str, Any]) -> str:
    data = bytes.fromhex(window["hex"])
    anchor_start = int(window["relative_anchor_start"])
    stripped = data[:anchor_start] + b"<ANCHOR>" + data[anchor_start + 24 :]
    return stripped.hex(" ")


def _marker_signature_key(hit: dict[str, Any]) -> list[tuple[str, int]]:
    return [(row["marker"], row["relative_to_hit"]) for row in hit["local_marker_signature"]]


def _compare_grouped_non_grouped(fixtures: list[dict[str, Any]]) -> dict[str, Any]:
    grouped = [
        fx
        for fx in fixtures
        if fx["fixture"] in {"text_group_same_color_two_objects.txt", "text_group_mixed_color_two_objects.txt"}
    ]
    nongrouped = next((fx for fx in fixtures if fx["fixture"] == "text_two_objects_mixed_color_not_grouped.txt"), None)
    grouped_hits = []
    for fx in grouped:
        for node in fx["cproperty_nodes"]:
            grouped_hits.extend(node["anchor_triple_hits_inside_node"])
    nongrouped_hits = []
    if nongrouped is not None:
        for node in nongrouped["cproperty_nodes"]:
            nongrouped_hits.extend(node["anchor_triple_hits_inside_node"])

    grouped_offsets = [hit["cproperty_payload_relative_offset"] for hit in grouped_hits]
    nongrouped_offsets = [hit["cproperty_payload_relative_offset"] for hit in nongrouped_hits]
    grouped_cobdao_offsets = []
    nongrouped_cobdao_offsets = []
    grouped_hit_relative_to_cobdao = []
    nongrouped_hit_relative_to_cobdao = []
    grouped_section_counts = []
    nongrouped_section_counts = []
    for fx in grouped:
        for node in fx["cproperty_nodes"]:
            grouped_section_counts.append(len(node["cobdao_sections"]))
            for section in node["cobdao_sections"]:
                if section["known_anchor_triple_hit"]:
                    grouped_cobdao_offsets.append(section["cobdao_marker_offset"])
                    grouped_hit_relative_to_cobdao.append(section["hit_relative_to_cobdao"])
    if nongrouped is not None:
        for node in nongrouped["cproperty_nodes"]:
            nongrouped_section_counts.append(len(node["cobdao_sections"]))
            for section in node["cobdao_sections"]:
                if section["known_anchor_triple_hit"]:
                    nongrouped_cobdao_offsets.append(section["cobdao_marker_offset"])
                    nongrouped_hit_relative_to_cobdao.append(section["hit_relative_to_cobdao"])
    same_grouped_local_structure = False
    if len(grouped_hits) >= 2:
        same_grouped_local_structure = (
            _bytes_without_anchor(grouped_hits[0]["local_context_hex"])
            == _bytes_without_anchor(grouped_hits[1]["local_context_hex"])
        )
    same_grouped_marker_signature = False
    if len(grouped_hits) >= 2:
        same_grouped_marker_signature = _marker_signature_key(grouped_hits[0]) == _marker_signature_key(grouped_hits[1])
    grouped_to_nongrouped_delta = None
    if grouped_offsets and nongrouped_offsets:
        grouped_to_nongrouped_delta = nongrouped_offsets[0] - grouped_offsets[0]
    return {
        "grouped_cproperty_anchor_offsets": grouped_offsets,
        "non_grouped_cproperty_anchor_offsets": nongrouped_offsets,
        "grouped_cobdao_anchor_section_offsets": grouped_cobdao_offsets,
        "non_grouped_cobdao_anchor_section_offsets": nongrouped_cobdao_offsets,
        "grouped_hit_relative_to_cobdao": grouped_hit_relative_to_cobdao,
        "non_grouped_hit_relative_to_cobdao": nongrouped_hit_relative_to_cobdao,
        "all_anchor_hits_relative_to_cobdao_are_34": all(
            rel == COBDAO_ANCHOR_LOCAL_OFFSET
            for rel in [*grouped_hit_relative_to_cobdao, *nongrouped_hit_relative_to_cobdao]
        ),
        "grouped_cobdao_section_counts": grouped_section_counts,
        "non_grouped_cobdao_section_counts": nongrouped_section_counts,
        "cobdao_section_counts_identical": (
            len(set([*grouped_section_counts, *nongrouped_section_counts])) == 1
            if [*grouped_section_counts, *nongrouped_section_counts]
            else False
        ),
        "grouped_offsets_identical": len(set(grouped_offsets)) == 1 if grouped_offsets else False,
        "grouped_local_structure_identical_excluding_anchor_bytes": same_grouped_local_structure,
        "grouped_marker_signature_identical": same_grouped_marker_signature,
        "offset_delta_non_grouped_minus_grouped": grouped_to_nongrouped_delta,
        "cobdao_offset_delta_non_grouped_minus_grouped": (
            nongrouped_cobdao_offsets[0] - grouped_cobdao_offsets[0]
            if grouped_cobdao_offsets and nongrouped_cobdao_offsets
            else None
        ),
        "delta_explanation_candidate": (
            "non-grouped CPropertyExtend anchor context is shifted by 148 bytes from grouped fixtures"
            if grouped_to_nongrouped_delta == 148
            else "unresolved"
        ),
        "same_local_structure_grouped_vs_non_grouped_excluding_anchor_bytes": (
            _bytes_without_anchor(grouped_hits[0]["local_context_hex"])
            == _bytes_without_anchor(nongrouped_hits[0]["local_context_hex"])
            if grouped_hits and nongrouped_hits
            else False
        ),
        "same_marker_signature_grouped_vs_non_grouped": (
            _marker_signature_key(grouped_hits[0]) == _marker_signature_key(nongrouped_hits[0])
            if grouped_hits and nongrouped_hits
            else False
        ),
        "parser_promotion_status": "analyzer_only",
    }


def _answers(fixtures: list[dict[str, Any]], comparison: dict[str, Any]) -> dict[str, Any]:
    return {
        "anchor_triple_at_cobdao_plus_34_for_target_fixtures": comparison[
            "all_anchor_hits_relative_to_cobdao_are_34"
        ],
        "cobdao_sections_multiple": not comparison["cobdao_section_counts_identical"]
        or (comparison["grouped_cobdao_section_counts"][:1] != [1]),
        "same_local_structure_for_grouped_472": comparison["grouped_local_structure_identical_excluding_anchor_bytes"],
        "same_marker_signature_for_grouped_472": comparison["grouped_marker_signature_identical"],
        "non_grouped_620_shift_candidate": comparison["delta_explanation_candidate"],
        "cobdao_section_shift_candidate": (
            "anchor-bearing CObDao section is shifted by 148 bytes in non-grouped fixture"
            if comparison["cobdao_offset_delta_non_grouped_minus_grouped"] == 148
            else "unresolved"
        ),
        "objectinfos_cobdao_relationship": "Observed OBJETINFOS_CLASSNAME appears immediately before the CObDao marker in the local section; CObDao is 24 bytes after OBJETINFOS_CLASSNAME in current target sections",
        "record_boundary_status": "candidate_only",
        "chain_connection_basis": "anchor equality and bbox proximity identify the matching chain; hit/source stream deltas are diagnostics only",
        "minimum_parser_rule_needed": [
            "class-relative section boundary for CPropertyExtend anchor records",
            "chain ownership rule connecting CPropertyExtend local record to parser chain without filename assumptions",
            "grouped/non-grouped shift explanation that is stable across more fixtures",
        ],
        "parser_readiness": "not_ready_analyzer_only",
    }


def build_report() -> dict[str, Any]:
    fixture_reports = [_fixture_report(name) for name in FIXTURES]
    comparison = _compare_grouped_non_grouped(fixture_reports)
    return {
        "policy": {
            "scope": "CPropertyExtend anchor context structure/evidence audit only",
            "parser_behavior": "not_modified",
            "cproperty_anchor_promotion": "not_applied",
            "absolute_offsets": "diagnostic_only",
            "active_anchor_fallback": "baseline_midpoint remains active",
        },
        "fixtures": fixture_reports,
        "grouped_vs_non_grouped_comparison": comparison,
        "answers": _answers(fixture_reports, comparison),
    }


def _print_text(report: dict[str, Any]) -> None:
    print("Text CPropertyExtend Anchor Context Analysis")
    print(f"policy.scope: {report['policy']['scope']}")
    print(f"policy.parser_behavior: {report['policy']['parser_behavior']}")
    print()
    for fx in report["fixtures"]:
        if fx["fixture"] not in MULTI_OBJECT_FIXTURES:
            continue
        print(f"Fixture: {fx['fixture']}")
        for node in fx["cproperty_nodes"]:
            print(
                f"  CPropertyExtend node={node['cproperty_node_index']} "
                f"payload_len={node['payload_length']} payload_rel={node['payload_relative_offset']}"
            )
            print("  [CObDao section scan]")
            for section in node["cobdao_sections"]:
                print(
                    f"    cobdao_offset={section['cobdao_marker_offset']} "
                    f"known_anchor={str(section['known_anchor_triple_hit']).lower()} "
                    f"hit_relative_to_cobdao={section['hit_relative_to_cobdao']} "
                    f"matched_chains={section['matched_chains']}"
                )
            for hit in node["anchor_triple_hits_inside_node"]:
                print(
                    f"    anchor={hit['target_anchor_mm']} cproperty_offset={hit['cproperty_payload_relative_offset']} "
                    f"nearest_marker={hit['nearest_known_class_marker']} "
                    f"matched_chains={[c['chain_index'] for c in hit['chain_match_candidates'] if c['matched_chain_baseline_anchor']]}"
                )
                print(f"    local_context_hex={hit['local_context_hex']['hex']}")
        print()
    print("[Grouped vs Non-grouped]")
    print(json.dumps(report["grouped_vs_non_grouped_comparison"], ensure_ascii=False, indent=2))
    print("[Answers]")
    print(json.dumps(report["answers"], ensure_ascii=False, indent=2))


def _print_markdown(report: dict[str, Any]) -> None:
    print("# Text CPropertyExtend Anchor Context Analysis")
    print()
    print("| fixture | CPropertyExtend node | CObDao offset | target anchor mm | payload offset | hit rel to CObDao | matched chains |")
    print("|---|---:|---:|---|---:|---:|---|")
    for fx in report["fixtures"]:
        if fx["fixture"] not in MULTI_OBJECT_FIXTURES:
            continue
        for node in fx["cproperty_nodes"]:
            for section in node["cobdao_sections"]:
                if not section["known_anchor_triple_hit"]:
                    continue
                hit = section["anchor_hits"][0]
                print(
                    f"| {fx['fixture']} | {node['cproperty_node_index']} | {section['cobdao_marker_offset']} | "
                    f"{hit['target_anchor_mm']} | {hit['cproperty_payload_relative_offset']} | "
                    f"{section['hit_relative_to_cobdao']} | {section['matched_chains']} |"
                )
    print()
    print("## Grouped vs Non-grouped")
    print()
    comp = report["grouped_vs_non_grouped_comparison"]
    print(f"- grouped offsets: `{comp['grouped_cproperty_anchor_offsets']}`")
    print(f"- non-grouped offsets: `{comp['non_grouped_cproperty_anchor_offsets']}`")
    print(f"- delta: `{comp['offset_delta_non_grouped_minus_grouped']}`")
    print(f"- status: `{comp['parser_promotion_status']}`")


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit CPropertyExtend anchor triple local context.")
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
