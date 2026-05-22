from __future__ import annotations

import argparse
import hashlib
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
    "text_three_objects_grouped_order_abc.txt",
    "text_three_objects_grouped_order_cba.txt",
    "text_two_objects_mixed_color_not_grouped.txt",
    "text_two_objects_same_color_not_grouped.txt",
    "text_two_objects_not_grouped_selection_reversed.txt",
    "text_three_objects_not_grouped.txt",
]
GROUPED_MULTI_OBJECT_FIXTURES = [
    "text_group_same_color_two_objects.txt",
    "text_group_mixed_color_two_objects.txt",
    "text_three_objects_grouped_order_abc.txt",
    "text_three_objects_grouped_order_cba.txt",
]
NON_GROUPED_MULTI_OBJECT_FIXTURES = [
    "text_two_objects_mixed_color_not_grouped.txt",
    "text_two_objects_same_color_not_grouped.txt",
    "text_two_objects_not_grouped_selection_reversed.txt",
    "text_three_objects_not_grouped.txt",
]
MULTI_OBJECT_FIXTURES = [
    *GROUPED_MULTI_OBJECT_FIXTURES,
    *NON_GROUPED_MULTI_OBJECT_FIXTURES,
]
ORDER_METADATA = {
    "text_group_same_color_two_objects.txt": {
        "grouping_state": "grouped",
        "attempted_selection_order": None,
        "order_control_status": "unknown",
    },
    "text_group_mixed_color_two_objects.txt": {
        "grouping_state": "grouped",
        "attempted_selection_order": None,
        "order_control_status": "unknown",
    },
    "text_three_objects_grouped_order_abc.txt": {
        "grouping_state": "grouped",
        "attempted_selection_order": ["abcdefg", "1234567890", "XYZ"],
        "order_control_status": "attempted",
    },
    "text_three_objects_grouped_order_cba.txt": {
        "grouping_state": "grouped",
        "attempted_selection_order": ["XYZ", "1234567890", "abcdefg"],
        "order_control_status": "attempted",
    },
    "text_two_objects_mixed_color_not_grouped.txt": {
        "grouping_state": "not_grouped",
        "attempted_selection_order": None,
        "order_control_status": "unknown",
    },
    "text_two_objects_same_color_not_grouped.txt": {
        "grouping_state": "not_grouped",
        "attempted_selection_order": None,
        "order_control_status": "unknown",
    },
    "text_two_objects_not_grouped_selection_reversed.txt": {
        "grouping_state": "not_grouped",
        "attempted_selection_order": ["1234567890", "abcdefg"],
        "order_control_status": "attempted",
    },
    "text_three_objects_not_grouped.txt": {
        "grouping_state": "not_grouped",
        "attempted_selection_order": ["abcdefg", "1234567890", "XYZ"],
        "order_control_status": "attempted",
    },
}
TARGET_ANCHORS_MM = [
    (111.111, 222.222, 0.0),
    (211.111, 322.222, 0.0),
    (311.111, 422.222, 0.0),
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
CPARAGRAPHE_ANCHOR_OFFSETS = (158, 166, 174)


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
        "raw_hex": payload[offset : offset + 24].hex(" "),
        "decoded_anchor_mm": {
            "x": round(x * 1000.0, 6),
            "y": round(y * 1000.0, 6),
            "z": round(z * 1000.0, 6),
        },
        "is_finite": True,
    }


def _cparagraphe_direct_anchor(node: Type3Node, chains: list[dict[str, Any]]) -> dict[str, Any] | None:
    offset = CPARAGRAPHE_ANCHOR_OFFSETS[0]
    triple = _decode_triple_at(node.payload, offset)
    if triple is None:
        return None
    point = triple["decoded_anchor_mm"]
    matched = [
        row["chain_index"]
        for row in _chain_matches_for_point(point, chains)
        if row["matched_chain_baseline_anchor"]
    ]
    return {
        "payload_offsets": list(CPARAGRAPHE_ANCHOR_OFFSETS),
        "decoded_anchor_mm": point,
        "matched_chains": matched,
        "raw_hex": triple["raw_hex"],
    }


def _triple_analysis(triple: dict[str, Any] | None, chains: list[dict[str, Any]]) -> dict[str, Any]:
    if triple is None:
        return {
            "raw_hex": None,
            "decoded_double_triple_mm": None,
            "is_finite": False,
            "is_coordinate_like": False,
            "z_approx_zero": False,
            "matches_any_chain_baseline_anchor": False,
            "matches_known_expected_anchor": False,
            "bbox_like_or_unrelated": "unreadable",
        }
    point = triple["decoded_anchor_mm"]
    is_coordinate_like = (
        abs(float(point["x"])) <= 10000.0
        and abs(float(point["y"])) <= 10000.0
        and abs(float(point["z"])) <= 10000.0
    )
    z_approx_zero = abs(float(point["z"])) <= 1e-6
    matches_chain = any(_distance_2d(point, chain["baseline_anchor_mm"]) == 0.0 for chain in chains)
    matches_expected = any(_distance_2d(point, _target_point(anchor)) == 0.0 for anchor in TARGET_ANCHORS_MM)
    bbox_like = any(_distance_2d(point, {"x": chain["bbox"]["center_x"], "y": chain["bbox"]["center_y"], "z": chain["bbox"]["center_z"]}) == 0.0 for chain in chains if chain["bbox"] is not None)
    return {
        "raw_hex": triple["raw_hex"],
        "decoded_double_triple_mm": point,
        "is_finite": bool(triple["is_finite"]),
        "is_coordinate_like": is_coordinate_like,
        "z_approx_zero": z_approx_zero,
        "matches_any_chain_baseline_anchor": matches_chain,
        "matches_known_expected_anchor": matches_expected,
        "bbox_like_or_unrelated": "bbox_center_like" if bbox_like else "unrelated_or_not_bbox_center",
    }


def _window_bytes(window: dict[str, Any]) -> bytes:
    return bytes.fromhex(window["hex"])


def _similarity(left: bytes, right: bytes) -> float:
    if not left or not right:
        return 0.0
    size = min(len(left), len(right))
    equal = sum(1 for i in range(size) if left[i] == right[i])
    return round(equal / size, 6)


def _similarity_excluding_local_anchor(left_window: dict[str, Any], right_window: dict[str, Any]) -> float:
    left = bytearray(_window_bytes(left_window))
    right = bytearray(_window_bytes(right_window))
    left_anchor = int(left_window["relative_marker_start"]) + COBDAO_ANCHOR_LOCAL_OFFSET
    right_anchor = int(right_window["relative_marker_start"]) + COBDAO_ANCHOR_LOCAL_OFFSET
    for idx in range(24):
        if 0 <= left_anchor + idx < len(left):
            left[left_anchor + idx] = 0xAA
        if 0 <= right_anchor + idx < len(right):
            right[right_anchor + idx] = 0xAA
    return _similarity(bytes(left), bytes(right))


def _short_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()[:16]


def _u32_signature(section: dict[str, Any]) -> list[int]:
    values = section["decoded_values_from_cobdao"]["u32_i32_candidates"]
    return [int(row["u32le"]) for row in values[:16]]


def _double_signature(section: dict[str, Any]) -> list[Any]:
    values = section["decoded_values_from_cobdao"]["double64_candidates"]
    return [row["double_mm"] for row in values[:12]]


def _zero_signature(section: dict[str, Any]) -> list[tuple[int, int]]:
    marker_offset = int(section["marker_context_hex"]["relative_marker_start"])
    return [
        (int(row["start"]) - marker_offset, int(row["length"]))
        for row in _zero_padding_runs(_window_bytes(section["marker_context_hex"]), section["marker_context_hex"]["relative_marker_start"])
    ]


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
    marker_offsets = _marker_positions(node.payload, COBDAO_MARKER)
    for section_index, marker_offset in enumerate(marker_offsets):
        next_cobdao_offset = marker_offsets[section_index + 1] if section_index + 1 < len(marker_offsets) else None
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
                "section_index": section_index,
                "cobdao_marker_offset": marker_offset,
                "next_cobdao_offset": next_cobdao_offset,
                "section_length_candidate": (
                    next_cobdao_offset - marker_offset if next_cobdao_offset is not None else len(node.payload) - marker_offset
                ),
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
                "cobdao_plus_34_triple_analysis": _triple_analysis(triple, chains),
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
                "section_role_candidate": (
                    "anchor_bearing_candidate"
                    if matching_hits
                    else ("non_anchor_candidate" if triple is not None else "unknown")
                ),
            }
        )
    for section in sections:
        window_bytes = _window_bytes(section["marker_context_hex"])
        section["local_signature"] = {
            "marker_signature": [
                {"marker": marker.decode("ascii", errors="replace"), "relative_to_cobdao": 0}
                for marker in [COBDAO_MARKER]
            ],
            "u32_signature": _u32_signature(section),
            "double_signature": _double_signature(section),
            "zero_padding_signature": _zero_signature(section),
            "local_bytes_hash": _short_hash(window_bytes),
            "local_bytes_excluding_cobdao_plus_34_hash": _short_hash(
                window_bytes[: int(section["marker_context_hex"]["relative_marker_start"]) + COBDAO_ANCHOR_LOCAL_OFFSET]
                + b"<ANCHOR>"
                + window_bytes[
                    int(section["marker_context_hex"]["relative_marker_start"])
                    + COBDAO_ANCHOR_LOCAL_OFFSET
                    + 24 :
                ]
            ),
        }
    anchor_sections = [section for section in sections if section["known_anchor_triple_hit"]]
    if anchor_sections:
        anchor_window = anchor_sections[0]["marker_context_hex"]
        for section in sections:
            section["local_bytes_similarity_to_anchor_bearing_section"] = _similarity(
                _window_bytes(section["marker_context_hex"]),
                _window_bytes(anchor_window),
            )
            section["local_bytes_similarity_to_anchor_bearing_excluding_24_anchor_bytes"] = (
                _similarity_excluding_local_anchor(section["marker_context_hex"], anchor_window)
            )
    else:
        for section in sections:
            section["local_bytes_similarity_to_anchor_bearing_section"] = None
            section["local_bytes_similarity_to_anchor_bearing_excluding_24_anchor_bytes"] = None
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
    cparagraphe_nodes = [(idx, node) for idx, node in enumerate(nodes) if node.header.class_name == "CParagraphe"]
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
        "cparagraphe_direct_anchor_ownership": [
            {
                "node_index": idx,
                "payload_length": len(node.payload),
                "source_offset": node.start_offset,
                "payload_relative_offset": node.payload_offset,
                "direct_anchor": _cparagraphe_direct_anchor(node, chains),
            }
            for idx, node in cparagraphe_nodes
        ],
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


def _fixture_hits(fixture: dict[str, Any]) -> list[dict[str, Any]]:
    hits = []
    for node in fixture["cproperty_nodes"]:
        hits.extend(node["anchor_triple_hits_inside_node"])
    return hits


def _anchor_sections(fixture: dict[str, Any]) -> list[dict[str, Any]]:
    sections = []
    for node in fixture["cproperty_nodes"]:
        sections.extend(section for section in node["cobdao_sections"] if section["known_anchor_triple_hit"])
    return sections


def _compact_section(section: dict[str, Any]) -> dict[str, Any]:
    return {
        "section_index": section["section_index"],
        "cobdao_marker_offset": section["cobdao_marker_offset"],
        "section_length_candidate": section["section_length_candidate"],
        "section_role_candidate": section["section_role_candidate"],
        "decoded": section["cobdao_plus_34_triple_analysis"]["decoded_double_triple_mm"],
        "coordinate_like": section["cobdao_plus_34_triple_analysis"]["is_coordinate_like"],
    }


def _compare_grouped_non_grouped(fixtures: list[dict[str, Any]]) -> dict[str, Any]:
    grouped = [fx for fx in fixtures if fx["fixture"] in GROUPED_MULTI_OBJECT_FIXTURES]
    nongrouped_fixtures = [fx for fx in fixtures if fx["fixture"] in NON_GROUPED_MULTI_OBJECT_FIXTURES]
    grouped_hits = []
    for fx in grouped:
        grouped_hits.extend(_fixture_hits(fx))
    nongrouped_hits = []
    for fx in nongrouped_fixtures:
        nongrouped_hits.extend(_fixture_hits(fx))

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
    for fx in nongrouped_fixtures:
        for node in fx["cproperty_nodes"]:
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
    grouped_baseline_offset = grouped_offsets[0] if grouped_offsets else None
    grouped_baseline_cobdao_offset = grouped_cobdao_offsets[0] if grouped_cobdao_offsets else None
    non_grouped_by_fixture = []
    for fx in nongrouped_fixtures:
        sections = _first_cproperty_sections(fx)
        anchor_sections = [section for section in sections if section["known_anchor_triple_hit"]]
        inserted_sections = [
            section
            for section in sections
            if not section["known_anchor_triple_hit"] and section["section_length_candidate"] == 148
        ]
        inserted = inserted_sections[0] if inserted_sections else None
        fixture_hits = _fixture_hits(fx)
        anchor = anchor_sections[0] if anchor_sections else None
        hit = anchor["anchor_hits"][0] if anchor is not None and anchor["anchor_hits"] else None
        non_grouped_by_fixture.append(
            {
                "fixture": fx["fixture"],
                "parser_chain_count": len(fx["chain_inventory"]),
                "cobdao_section_count": len(sections),
                "anchor_bearing_section_indexes": [section["section_index"] for section in anchor_sections],
                "anchor_bearing_cobdao_offsets": [section["cobdao_marker_offset"] for section in anchor_sections],
                "anchor_hit_offsets": [row["cproperty_payload_relative_offset"] for row in fixture_hits],
                "hit_relative_to_cobdao": [section["hit_relative_to_cobdao"] for section in anchor_sections],
                "inserted_148_section_count": len(inserted_sections),
                "inserted_148_section_candidates": [_compact_section(section) for section in inserted_sections],
                "inserted_section_candidate": (
                    _compact_section(inserted)
                    if inserted is not None
                    else None
                ),
                "offset_delta_from_grouped": (
                    hit["cproperty_payload_relative_offset"] - grouped_baseline_offset
                    if hit is not None and grouped_baseline_offset is not None
                    else None
                ),
                "cobdao_offset_delta_from_grouped": (
                    anchor["cobdao_marker_offset"] - grouped_baseline_cobdao_offset
                    if anchor is not None and grouped_baseline_cobdao_offset is not None
                    else None
                ),
            }
        )
    grouped_to_nongrouped_delta = (
        non_grouped_by_fixture[0]["offset_delta_from_grouped"] if non_grouped_by_fixture else None
    )
    nongrouped_cobdao_delta = (
        non_grouped_by_fixture[0]["cobdao_offset_delta_from_grouped"] if non_grouped_by_fixture else None
    )
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
        "non_grouped_by_fixture": non_grouped_by_fixture,
        "cobdao_section_counts_identical": (
            len(set([*grouped_section_counts, *nongrouped_section_counts])) == 1
            if [*grouped_section_counts, *nongrouped_section_counts]
            else False
        ),
        "grouped_offsets_identical": len(set(grouped_offsets)) == 1 if grouped_offsets else False,
        "grouped_local_structure_identical_excluding_anchor_bytes": same_grouped_local_structure,
        "grouped_marker_signature_identical": same_grouped_marker_signature,
        "offset_delta_non_grouped_minus_grouped": grouped_to_nongrouped_delta,
        "cobdao_offset_delta_non_grouped_minus_grouped": nongrouped_cobdao_delta,
        "delta_explanation_candidate": (
            "two-object non-grouped CPropertyExtend anchor contexts are shifted by 148 bytes from grouped fixtures; three-object scaling adds more CObDao sections and more CPropertyExtend anchor hits"
            if non_grouped_by_fixture
            and all(
                row["offset_delta_from_grouped"] == 148
                for row in non_grouped_by_fixture
                if row["parser_chain_count"] == 2
            )
            and all(
                row["cobdao_section_count"] == 6
                for row in non_grouped_by_fixture
                if row["parser_chain_count"] == 2
            )
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


def _all_cobdao_sections(fixtures: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for fx in fixtures:
        for node in fx["cproperty_nodes"]:
            for section in node["cobdao_sections"]:
                rows.append(
                    {
                        "fixture": fx["fixture"],
                        "cproperty_node_index": node["cproperty_node_index"],
                        **section,
                    }
                )
    return rows


def _feature_counts(sections: list[dict[str, Any]], feature: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for section in sections:
        value = section["cobdao_plus_34_triple_analysis"].get(feature)
        key = str(value)
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


def _anchor_bearing_aggregate(fixtures: list[dict[str, Any]]) -> dict[str, Any]:
    sections = _all_cobdao_sections([fx for fx in fixtures if fx["fixture"] in MULTI_OBJECT_FIXTURES])
    anchor = [section for section in sections if section["known_anchor_triple_hit"]]
    non_anchor = [section for section in sections if not section["known_anchor_triple_hit"]]
    anchor_indexes = sorted({section["section_index"] for section in anchor})
    non_anchor_indexes = sorted({section["section_index"] for section in non_anchor})
    coordinate_like_non_anchor = [
        {
            "fixture": section["fixture"],
            "section_index": section["section_index"],
            "cobdao_marker_offset": section["cobdao_marker_offset"],
            "decoded": section["cobdao_plus_34_triple_analysis"]["decoded_double_triple_mm"],
        }
        for section in non_anchor
        if section["cobdao_plus_34_triple_analysis"]["is_coordinate_like"]
    ]
    ambiguous = [
        section
        for section in non_anchor
        if section["cobdao_plus_34_triple_analysis"]["is_coordinate_like"]
        and section["cobdao_plus_34_triple_analysis"]["z_approx_zero"]
    ]
    return {
        "section_count": len(sections),
        "anchor_bearing_count": len(anchor),
        "non_anchor_count": len(non_anchor),
        "anchor_bearing_section_indexes": anchor_indexes,
        "non_anchor_section_indexes": non_anchor_indexes,
        "anchor_bearing_coordinate_like_counts": _feature_counts(anchor, "is_coordinate_like"),
        "non_anchor_coordinate_like_counts": _feature_counts(non_anchor, "is_coordinate_like"),
        "anchor_bearing_z_approx_zero_counts": _feature_counts(anchor, "z_approx_zero"),
        "non_anchor_z_approx_zero_counts": _feature_counts(non_anchor, "z_approx_zero"),
        "anchor_bearing_matches_chain_counts": _feature_counts(anchor, "matches_any_chain_baseline_anchor"),
        "non_anchor_matches_chain_counts": _feature_counts(non_anchor, "matches_any_chain_baseline_anchor"),
        "coordinate_like_non_anchor_sections": coordinate_like_non_anchor,
        "ambiguous_non_anchor_sections": [
            {
                "fixture": section["fixture"],
                "section_index": section["section_index"],
                "cobdao_marker_offset": section["cobdao_marker_offset"],
                "decoded": section["cobdao_plus_34_triple_analysis"]["decoded_double_triple_mm"],
            }
            for section in ambiguous
        ],
        "features_that_distinguish_anchor_bearing_sections": [
            "matches known expected anchor and parsed chain baseline anchor in current analyzer evidence",
            "z_approx_zero is true for current anchor-bearing sections",
        ],
        "features_that_do_not_distinguish_anchor_bearing_sections": [
            "CObDao + 34 can be decoded as finite double triple in all current CObDao sections",
            "coordinate-like values also appear in some non-anchor sections",
            "OBJETINFOS_CLASSNAME -> CObDao distance is repeated and not unique to anchor-bearing sections",
            "section index is not stable across grouped and non-grouped fixtures",
        ],
        "false_positive_risk": (
            "High if selecting by coordinate-like triple alone; non-anchor sections can decode to coordinate-like "
            "finite triples. Baseline-anchor equality is analyzer evidence only and must not become parser selection."
        ),
    }


def _first_cproperty_sections(fixture: dict[str, Any]) -> list[dict[str, Any]]:
    return fixture["cproperty_nodes"][0]["cobdao_sections"] if fixture["cproperty_nodes"] else []


def _section_similarity_row(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    return {
        "left_section_index": left["section_index"],
        "right_section_index": right["section_index"],
        "left_cobdao_offset": left["cobdao_marker_offset"],
        "right_cobdao_offset": right["cobdao_marker_offset"],
        "left_role": left["section_role_candidate"],
        "right_role": right["section_role_candidate"],
        "same_role": left["section_role_candidate"] == right["section_role_candidate"],
        "same_length_candidate": left["section_length_candidate"] == right["section_length_candidate"],
        "same_u32_signature": left["local_signature"]["u32_signature"] == right["local_signature"]["u32_signature"],
        "same_zero_padding_signature": left["local_signature"]["zero_padding_signature"]
        == right["local_signature"]["zero_padding_signature"],
        "local_bytes_similarity": _similarity(
            _window_bytes(left["marker_context_hex"]),
            _window_bytes(right["marker_context_hex"]),
        ),
        "local_bytes_similarity_excluding_24_anchor_bytes": _similarity_excluding_local_anchor(
            left["marker_context_hex"],
            right["marker_context_hex"],
        ),
    }


def _section_alignment_analysis(fixtures: list[dict[str, Any]]) -> dict[str, Any]:
    by_name = {fixture["fixture"]: fixture for fixture in fixtures}
    same = by_name["text_group_same_color_two_objects.txt"]
    mixed = by_name["text_group_mixed_color_two_objects.txt"]
    same_sections = _first_cproperty_sections(same)
    mixed_sections = _first_cproperty_sections(mixed)

    grouped_pairs = [
        _section_similarity_row(left, right)
        for left, right in zip(same_sections, mixed_sections)
    ]
    grouped_anchor = next((section for section in same_sections if section["known_anchor_triple_hit"]), None)
    non_grouped_alignments = []
    for fixture_name in NON_GROUPED_MULTI_OBJECT_FIXTURES:
        nongrouped = by_name[fixture_name]
        nongrouped_sections = _first_cproperty_sections(nongrouped)
        grouped_to_nongrouped_direct = [
            _section_similarity_row(left, right)
            for left, right in zip(same_sections, nongrouped_sections)
        ]
        shifted_pairs = []
        for grouped_idx, nongrouped_idx in ((0, 0), (1, 2), (2, 3), (3, 4), (4, 5)):
            if grouped_idx < len(same_sections) and nongrouped_idx < len(nongrouped_sections):
                shifted_pairs.append(_section_similarity_row(same_sections[grouped_idx], nongrouped_sections[nongrouped_idx]))

        inserted_sections = [
            section
            for section in nongrouped_sections
            if not section["known_anchor_triple_hit"] and section["section_length_candidate"] == 148
        ]
        extra = inserted_sections[0] if inserted_sections else None
        nongrouped_anchor = next((section for section in nongrouped_sections if section["known_anchor_triple_hit"]), None)
        non_grouped_alignments.append(
            {
                "grouped_fixture": same["fixture"],
                "non_grouped_fixture": nongrouped["fixture"],
                "grouped_section_count": len(same_sections),
                "non_grouped_section_count": len(nongrouped_sections),
                "section_count_delta": len(nongrouped_sections) - len(same_sections),
                "direct_index_alignment": grouped_to_nongrouped_direct,
                "shifted_alignment_candidate": shifted_pairs,
                "inserted_section_candidate": (
                    {
                        "section_index": extra["section_index"],
                        "cobdao_marker_offset": extra["cobdao_marker_offset"],
                        "section_length_candidate": extra["section_length_candidate"],
                        "cobdao_plus_34_triple_analysis": extra["cobdao_plus_34_triple_analysis"],
                        "section_role_candidate": extra["section_role_candidate"],
                        "matched_chains": extra["matched_chains"],
                        "local_signature": extra["local_signature"],
                    }
                    if extra is not None
                    else None
                ),
                "inserted_148_section_count": len(inserted_sections),
                "inserted_148_section_candidates": [_compact_section(section) for section in inserted_sections],
                "anchor_bearing_shift": (
                    {
                        "grouped_anchor_cobdao_offset": grouped_anchor["cobdao_marker_offset"],
                        "non_grouped_anchor_cobdao_offset": nongrouped_anchor["cobdao_marker_offset"],
                        "cobdao_offset_delta": nongrouped_anchor["cobdao_marker_offset"] - grouped_anchor["cobdao_marker_offset"],
                        "grouped_anchor_hit_offset": grouped_anchor["anchor_hits"][0]["cproperty_payload_relative_offset"],
                        "non_grouped_anchor_hit_offset": nongrouped_anchor["anchor_hits"][0]["cproperty_payload_relative_offset"],
                        "anchor_hit_offset_delta": nongrouped_anchor["anchor_hits"][0]["cproperty_payload_relative_offset"]
                        - grouped_anchor["anchor_hits"][0]["cproperty_payload_relative_offset"],
                    }
                    if grouped_anchor is not None and nongrouped_anchor is not None
                    else None
                ),
                "insertion_explanation_candidate": (
                    "non-grouped section index 1 is a 148-byte inserted section candidate before the anchor-bearing section"
                    if extra is not None and extra["section_length_candidate"] == 148
                    else "unresolved"
                ),
            }
        )
    return {
        "grouped_same_vs_grouped_mixed": {
            "left_fixture": same["fixture"],
            "right_fixture": mixed["fixture"],
            "left_section_count": len(same_sections),
            "right_section_count": len(mixed_sections),
            "section_count_equal": len(same_sections) == len(mixed_sections),
            "index_alignment": grouped_pairs,
            "anchor_bearing_section_index_equal": (
                [section["section_index"] for section in same_sections if section["known_anchor_triple_hit"]]
                == [section["section_index"] for section in mixed_sections if section["known_anchor_triple_hit"]]
            ),
        },
        "grouped_vs_non_grouped": non_grouped_alignments[0],
        "grouped_vs_non_grouped_all": non_grouped_alignments,
    }


def _selector_candidate_evaluation() -> list[dict[str, Any]]:
    return [
        {
            "selector_candidate": "section_index",
            "works_for_grouped": True,
            "works_for_non_grouped": False,
            "false_positive_risk": "high",
            "parser_safe": False,
            "reason": "grouped anchor-bearing section index is 1, non-grouped is 2",
        },
        {
            "selector_candidate": "section_order_after_inserted_section_correction",
            "works_for_grouped": True,
            "works_for_non_grouped": "provisional",
            "false_positive_risk": "medium",
            "parser_safe": False,
            "reason": "requires detecting inserted section semantics, which is not established",
        },
        {
            "selector_candidate": "CObDao_plus_34_coordinate_like",
            "works_for_grouped": True,
            "works_for_non_grouped": True,
            "false_positive_risk": "high",
            "parser_safe": False,
            "reason": "non-anchor sections can decode coordinate-like triples, especially zero triples",
        },
        {
            "selector_candidate": "chain_source_offset_proximity",
            "works_for_grouped": "unclear",
            "works_for_non_grouped": "unclear",
            "false_positive_risk": "unknown",
            "parser_safe": False,
            "reason": "current source offsets are parser diagnostics and do not define a stable local section rule",
        },
        {
            "selector_candidate": "local_u32_i32_signature",
            "works_for_grouped": "provisional",
            "works_for_non_grouped": "provisional",
            "false_positive_risk": "unknown",
            "parser_safe": False,
            "reason": "signatures are reported but not yet reduced to a stable semantic discriminator",
        },
        {
            "selector_candidate": "OBJETINFOS_CObDao_marker_signature",
            "works_for_grouped": True,
            "works_for_non_grouped": True,
            "false_positive_risk": "high",
            "parser_safe": False,
            "reason": "marker signature appears in non-anchor sections too",
        },
        {
            "selector_candidate": "section_alignment",
            "works_for_grouped": True,
            "works_for_non_grouped": "provisional",
            "false_positive_risk": "medium",
            "parser_safe": False,
            "reason": "alignment supports inserted-section hypothesis but not a baseline-independent selector",
        },
    ]


def _chain_order_labels(fixture: dict[str, Any]) -> list[str | None]:
    return [chain["text_candidate"] for chain in fixture["chain_inventory"]]


def _flatten_matched_chains(sections: list[dict[str, Any]]) -> list[int]:
    owners: list[int] = []
    for section in sections:
        for chain_index in section["matched_chains"]:
            if chain_index not in owners:
                owners.append(chain_index)
    return owners


def _chain_indexes_to_labels(fixture: dict[str, Any], indexes: list[int]) -> list[str | None]:
    by_index = {chain["chain_index"]: chain["text_candidate"] for chain in fixture["chain_inventory"]}
    return [by_index.get(index) for index in indexes]


def _cparagraphe_owner_indexes(fixture: dict[str, Any]) -> list[int]:
    owners: list[int] = []
    for row in fixture["cparagraphe_direct_anchor_ownership"]:
        direct = row["direct_anchor"]
        if direct is None:
            continue
        for chain_index in direct["matched_chains"]:
            if chain_index not in owners:
                owners.append(chain_index)
    return owners


def _anchor_storage_scaling_summary(fixtures: list[dict[str, Any]]) -> dict[str, Any]:
    rows = []
    for fixture in fixtures:
        if fixture["fixture"] not in MULTI_OBJECT_FIXTURES:
            continue
        chain_count = len(fixture["chain_inventory"])
        cparagraphe_owners = _cparagraphe_owner_indexes(fixture)
        cproperty_owners = _flatten_matched_chains(_anchor_sections(fixture))
        pattern_holds = (
            len(fixture["cparagraphe_direct_anchor_ownership"]) == 1
            and len(cparagraphe_owners) == 1
            and len(cproperty_owners) == max(0, chain_count - 1)
        )
        rows.append(
            {
                "fixture": fixture["fixture"],
                "parsed_chain_count": chain_count,
                "cparagraphe_count": len(fixture["cparagraphe_direct_anchor_ownership"]),
                "cparagraphe_anchor_owner_count": len(cparagraphe_owners),
                "cpropertyextend_anchor_hit_count": len(_anchor_sections(fixture)),
                "pattern_1_plus_n_minus_1_holds": pattern_holds,
                "cparagraphe_owner_chain_indexes": cparagraphe_owners,
                "cparagraphe_owner_texts": _chain_indexes_to_labels(fixture, cparagraphe_owners),
                "cpropertyextend_owner_chain_indexes": cproperty_owners,
                "cpropertyextend_owner_texts": _chain_indexes_to_labels(fixture, cproperty_owners),
            }
        )
    return {
        "status": "observed",
        "model": "For N parsed text chains, one anchor is stored in CParagraphe and N-1 anchors are stored in CPropertyExtend CObDao-local sections.",
        "rows": rows,
        "all_current_multi_object_fixtures_hold": all(row["pattern_1_plus_n_minus_1_holds"] for row in rows),
        "parser_promotion_status": "analyzer_only",
    }


def _grouped_not_grouped_section_scaling_summary(fixtures: list[dict[str, Any]]) -> dict[str, Any]:
    rows = []
    by_object_count: dict[int, dict[str, list[dict[str, Any]]]] = {}
    for fixture in fixtures:
        if fixture["fixture"] not in MULTI_OBJECT_FIXTURES:
            continue
        metadata = ORDER_METADATA.get(fixture["fixture"], {})
        grouping = metadata.get("grouping_state", "unknown")
        object_count = len(fixture["chain_inventory"])
        row = {
            "fixture": fixture["fixture"],
            "object_count": object_count,
            "grouping_state": grouping,
            "cobdao_section_count": len(_first_cproperty_sections(fixture)),
        }
        rows.append(row)
        by_object_count.setdefault(object_count, {}).setdefault(str(grouping), []).append(row)

    comparisons = []
    for object_count, grouped_rows in sorted(by_object_count.items()):
        grouped_counts = sorted({row["cobdao_section_count"] for row in grouped_rows.get("grouped", [])})
        not_grouped_counts = sorted({row["cobdao_section_count"] for row in grouped_rows.get("not_grouped", [])})
        delta = None
        delta_matches = None
        if len(grouped_counts) == 1 and len(not_grouped_counts) == 1:
            delta = not_grouped_counts[0] - grouped_counts[0]
            delta_matches = delta == object_count - 1
        comparisons.append(
            {
                "object_count": object_count,
                "grouped_section_counts": grouped_counts,
                "not_grouped_section_counts": not_grouped_counts,
                "not_grouped_minus_grouped_delta": delta,
                "candidate_not_grouped_delta_object_count_minus_1": object_count - 1,
                "delta_matches_candidate": delta_matches,
                "confidence": "provisional",
            }
        )
    return {
        "status": "observed_provisional",
        "rows": rows,
        "comparisons_by_object_count": comparisons,
        "candidate_formula": "not_grouped_delta = object_count - 1",
        "candidate_formula_holds_for_comparable_counts": all(
            row["delta_matches_candidate"] is True
            for row in comparisons
            if row["not_grouped_minus_grouped_delta"] is not None
        ),
        "confidence": "provisional",
    }


def _selection_order_primary_owner_summary(fixtures: list[dict[str, Any]]) -> dict[str, Any]:
    rows = []
    known_order_rows = []
    for fixture in fixtures:
        if fixture["fixture"] not in MULTI_OBJECT_FIXTURES:
            continue
        metadata = ORDER_METADATA.get(fixture["fixture"], {})
        attempted_order = metadata.get("attempted_selection_order")
        cparagraphe_owners = _cparagraphe_owner_indexes(fixture)
        cproperty_owners = _flatten_matched_chains(_anchor_sections(fixture))
        owner_texts = _chain_indexes_to_labels(fixture, cparagraphe_owners)
        maps_to_first = None
        maps_to_last = None
        if attempted_order and owner_texts:
            maps_to_first = owner_texts[0] == attempted_order[0]
            maps_to_last = owner_texts[0] == attempted_order[-1]
            known_order_rows.append((maps_to_first, maps_to_last))
        rows.append(
            {
                "fixture": fixture["fixture"],
                "grouping_state": metadata.get("grouping_state", "unknown"),
                "attempted_selection_order": attempted_order,
                "order_control_status": metadata.get("order_control_status", "unknown"),
                "parser_chain_order": _chain_order_labels(fixture),
                "cparagraphe_owner_chain_indexes": cparagraphe_owners,
                "cparagraphe_owner_texts": owner_texts,
                "cpropertyextend_owner_chain_indexes": cproperty_owners,
                "cpropertyextend_owner_texts": _chain_indexes_to_labels(fixture, cproperty_owners),
                "attempted_order_first_maps_to_cparagraphe_owner": maps_to_first,
                "attempted_order_last_maps_to_cparagraphe_owner": maps_to_last,
                "actual_stored_order": "unresolved",
                "primary_object_hypothesis_status": "provisional",
            }
        )
    return {
        "status": "observed_provisional",
        "rows": rows,
        "parser_chain_order_can_remain_stable_while_cparagraphe_owner_changes": True,
        "grouped_order_effect_observed": True,
        "actual_stored_order_status": "unresolved",
        "primary_object_hypothesis_status": "provisional",
    }


def _answers(fixtures: list[dict[str, Any]], comparison: dict[str, Any], alignment: dict[str, Any]) -> dict[str, Any]:
    by_name = {fixture["fixture"]: fixture for fixture in fixtures}
    grouped_counts = [
        len(_first_cproperty_sections(by_name[name]))
        for name in GROUPED_MULTI_OBJECT_FIXTURES
        if name in by_name
    ]
    nongrouped_counts = [
        len(_first_cproperty_sections(by_name[name]))
        for name in NON_GROUPED_MULTI_OBJECT_FIXTURES
        if name in by_name
    ]
    cparagraphe_ownership = {
        name: (
            by_name[name]["cparagraphe_direct_anchor_ownership"][0]["direct_anchor"]["matched_chains"]
            if by_name[name]["cparagraphe_direct_anchor_ownership"]
            and by_name[name]["cparagraphe_direct_anchor_ownership"][0]["direct_anchor"] is not None
            else []
        )
        for name in MULTI_OBJECT_FIXTURES
        if name in by_name
    }
    cproperty_ownership = {
        name: [
            section["matched_chains"]
            for section in _anchor_sections(by_name[name])
        ]
        for name in MULTI_OBJECT_FIXTURES
        if name in by_name
    }
    two_object_non_grouped_shifted = all(
        row["section_count_delta"] == 1
        and row["inserted_section_candidate"] is not None
        and row["inserted_section_candidate"]["section_length_candidate"] == 148
        and row["anchor_bearing_shift"] is not None
        and row["anchor_bearing_shift"]["cobdao_offset_delta"] == 148
        for row in alignment["grouped_vs_non_grouped_all"]
        if row["non_grouped_section_count"] == 6
    )
    scaling_rows = []
    for name in MULTI_OBJECT_FIXTURES:
        if name not in by_name:
            continue
        fx = by_name[name]
        sections = _first_cproperty_sections(fx)
        anchor_sections = _anchor_sections(fx)
        inserted_sections = [
            section
            for section in sections
            if not section["known_anchor_triple_hit"] and section["section_length_candidate"] == 148
        ]
        scaling_rows.append(
            {
                "fixture": name,
                "parser_chain_count": len(fx["chain_inventory"]),
                "cparagraphe_count": len(fx["cparagraphe_direct_anchor_ownership"]),
                "cobdao_section_count": len(sections),
                "inserted_148_section_count": len(inserted_sections),
                "cproperty_anchor_hit_count": len(anchor_sections),
                "section_count_equals_4_plus_object_count": len(sections) == 4 + len(fx["chain_inventory"]),
                "anchor_storage_matches_one_cparagraphe_plus_n_minus_1_cproperty": (
                    len(fx["cparagraphe_direct_anchor_ownership"]) == 1
                    and len(anchor_sections) == max(0, len(fx["chain_inventory"]) - 1)
                ),
            }
        )
    three = by_name.get("text_three_objects_not_grouped.txt")
    three_sections = _first_cproperty_sections(three) if three is not None else []
    three_anchor_sections = _anchor_sections(three) if three is not None else []
    three_inserted = [
        section
        for section in three_sections
        if not section["known_anchor_triple_hit"] and section["section_length_candidate"] == 148
    ]
    all_anchor_storage_matches = all(
        row["anchor_storage_matches_one_cparagraphe_plus_n_minus_1_cproperty"]
        for row in scaling_rows
    )
    section_count_four_plus_n_rows = [
        row for row in scaling_rows if row["section_count_equals_4_plus_object_count"]
    ]
    two_object_non_grouped_counts = [
        len(_first_cproperty_sections(by_name[name]))
        for name in NON_GROUPED_MULTI_OBJECT_FIXTURES
        if name in by_name and len(by_name[name]["chain_inventory"]) == 2
    ]
    two_object_grouped_counts = [
        len(_first_cproperty_sections(by_name[name]))
        for name in GROUPED_MULTI_OBJECT_FIXTURES
        if name in by_name and len(by_name[name]["chain_inventory"]) == 2
    ]
    not_grouped_structure_conclusion = (
        "Observed in all 2-object not-grouped fixtures and the 3-object not-grouped fixture; "
        "current evidence points to not-grouped/multi-independent-object structure rather than mixed color. "
        "The 3-object fixture does not follow simple section_count = 4 + object_count scaling."
        if two_object_non_grouped_shifted
        and set(two_object_non_grouped_counts) == {6}
        and set(two_object_grouped_counts) == {5}
        and three is not None
        else "unresolved"
    )
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
        "same_color_not_grouped_cobdao_section_count_is_6": (
            len(_first_cproperty_sections(by_name["text_two_objects_same_color_not_grouped.txt"])) == 6
            if "text_two_objects_same_color_not_grouped.txt" in by_name
            else None
        ),
        "inserted_section_cause_current_conclusion": not_grouped_structure_conclusion,
        "selection_reversed_section_position_same": (
            len(_first_cproperty_sections(by_name["text_two_objects_not_grouped_selection_reversed.txt"])) == 6
            and bool(_anchor_sections(by_name["text_two_objects_not_grouped_selection_reversed.txt"]))
            and _anchor_sections(by_name["text_two_objects_not_grouped_selection_reversed.txt"])[0]["section_index"] == 2
            if "text_two_objects_not_grouped_selection_reversed.txt" in by_name
            else None
        ),
        "cparagraphe_direct_anchor_ownership_by_fixture": cparagraphe_ownership,
        "cproperty_anchor_ownership_by_fixture": cproperty_ownership,
        "selection_order_ownership_effect": (
            "Attempted reversed selection fixture keeps 6 CObDao sections and inserted section index 1, but "
            "CParagraphe/CPropertyExtend anchor ownership swaps back to grouped-like chain pairing; stored order remains unresolved."
        ),
        "object_count_scaling": scaling_rows,
        "section_count_scaling_conclusion": (
            "section_count = 4 + object_count fits the current 2-object fixtures but fails for text_three_objects_not_grouped; "
            f"3-object not-grouped has {len(three_sections) if three is not None else None} CObDao sections."
            if three is not None and len(section_count_four_plus_n_rows) != len(scaling_rows)
            else "unresolved"
        ),
        "anchor_storage_scaling_conclusion": (
            "Current fixtures support one CParagraphe direct anchor plus N-1 CPropertyExtend anchor hits for N parsed text chains."
            if all_anchor_storage_matches
            else "unresolved"
        ),
        "text_three_objects_not_grouped_summary": (
            {
                "parser_chain_count": len(three["chain_inventory"]),
                "cparagraphe_count": len(three["cparagraphe_direct_anchor_ownership"]),
                "cobdao_section_count": len(three_sections),
                "inserted_148_section_count": len(three_inserted),
                "cproperty_anchor_hit_count": len(three_anchor_sections),
                "cparagraphe_direct_anchor_ownership": cparagraphe_ownership.get("text_three_objects_not_grouped.txt"),
                "cproperty_anchor_ownership": cproperty_ownership.get("text_three_objects_not_grouped.txt"),
            }
            if three is not None
            else None
        ),
        "minimum_parser_rule_needed": [
            "class-relative section boundary for CPropertyExtend anchor records",
            "chain ownership rule connecting CPropertyExtend local record to parser chain without filename assumptions",
            "grouped/non-grouped shift explanation that is stable across more fixtures",
            "anchor-bearing CObDao section selection rule that does not depend on parser baseline_midpoint",
        ],
        "parser_readiness": "not_ready_analyzer_only",
    }


def build_report() -> dict[str, Any]:
    fixture_reports = [_fixture_report(name) for name in FIXTURES]
    comparison = _compare_grouped_non_grouped(fixture_reports)
    aggregate = _anchor_bearing_aggregate(fixture_reports)
    alignment = _section_alignment_analysis(fixture_reports)
    anchor_storage_summary = _anchor_storage_scaling_summary(fixture_reports)
    section_scaling_summary = _grouped_not_grouped_section_scaling_summary(fixture_reports)
    selection_order_summary = _selection_order_primary_owner_summary(fixture_reports)
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
        "anchor_bearing_vs_non_anchor_aggregate": aggregate,
        "section_alignment_analysis": alignment,
        "selector_candidate_evaluation": _selector_candidate_evaluation(),
        "anchor_storage_scaling_summary": anchor_storage_summary,
        "grouped_not_grouped_section_scaling_summary": section_scaling_summary,
        "selection_order_primary_owner_summary": selection_order_summary,
        "answers": _answers(fixture_reports, comparison, alignment),
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
        for row in fx["cparagraphe_direct_anchor_ownership"]:
            direct = row["direct_anchor"]
            if direct is None:
                print(f"  CParagraphe node={row['node_index']} direct_anchor=None")
            else:
                print(
                    f"  CParagraphe node={row['node_index']} direct_anchor={direct['decoded_anchor_mm']} "
                    f"matched_chains={direct['matched_chains']}"
                )
        for node in fx["cproperty_nodes"]:
            print(
                f"  CPropertyExtend node={node['cproperty_node_index']} "
                f"payload_len={node['payload_length']} payload_rel={node['payload_relative_offset']}"
            )
            print("  [CObDao section scan]")
            for section in node["cobdao_sections"]:
                triple = section["cobdao_plus_34_triple_analysis"]
                print(
                    f"    section={section['section_index']} cobdao_offset={section['cobdao_marker_offset']} "
                    f"next_cobdao={section['next_cobdao_offset']} len_candidate={section['section_length_candidate']} "
                    f"known_anchor={str(section['known_anchor_triple_hit']).lower()} "
                    f"role={section['section_role_candidate']} "
                    f"hit_relative_to_cobdao={section['hit_relative_to_cobdao']} "
                    f"coordinate_like={str(triple['is_coordinate_like']).lower()} "
                    f"z_approx_zero={str(triple['z_approx_zero']).lower()} "
                    f"matches_chain={str(triple['matches_any_chain_baseline_anchor']).lower()} "
                    f"matched_chains={section['matched_chains']} decoded={triple['decoded_double_triple_mm']}"
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
    print("[Anchor-bearing vs Non-anchor Aggregate]")
    print(json.dumps(report["anchor_bearing_vs_non_anchor_aggregate"], ensure_ascii=False, indent=2))
    print("[Section Alignment Analysis]")
    print(json.dumps(report["section_alignment_analysis"], ensure_ascii=False, indent=2))
    print("[Selector Candidate Evaluation]")
    print(json.dumps(report["selector_candidate_evaluation"], ensure_ascii=False, indent=2))
    print("[Anchor Storage Scaling Summary]")
    print(json.dumps(report["anchor_storage_scaling_summary"], ensure_ascii=False, indent=2))
    print("[Grouped vs Not-grouped Section Scaling Summary]")
    print(json.dumps(report["grouped_not_grouped_section_scaling_summary"], ensure_ascii=False, indent=2))
    print("[Selection Order / Primary Owner Summary]")
    print(json.dumps(report["selection_order_primary_owner_summary"], ensure_ascii=False, indent=2))
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
    print()
    print("## Anchor-bearing vs Non-anchor Aggregate")
    print()
    agg = report["anchor_bearing_vs_non_anchor_aggregate"]
    print(f"- anchor-bearing sections: `{agg['anchor_bearing_count']}`")
    print(f"- non-anchor sections: `{agg['non_anchor_count']}`")
    print(f"- false positive risk: {agg['false_positive_risk']}")
    print()
    print("## Section Alignment")
    print()
    for alignment in report["section_alignment_analysis"]["grouped_vs_non_grouped_all"]:
        print(f"### `{alignment['non_grouped_fixture']}`")
        print()
        print(f"- section count delta: `{alignment['section_count_delta']}`")
        print(f"- inserted section candidate: `{alignment['inserted_section_candidate']}`")
        print()
    print()
    print("## Selector Candidates")
    print()
    print("| selector | grouped | non-grouped | parser-safe | reason |")
    print("|---|---|---|---|---|")
    for row in report["selector_candidate_evaluation"]:
        print(
            f"| {row['selector_candidate']} | {row['works_for_grouped']} | {row['works_for_non_grouped']} | "
            f"{row['parser_safe']} | {row['reason']} |"
        )
    print()
    print("## Anchor Storage Scaling Summary")
    print()
    print("| fixture | chains | CParagraphe owners | CPropertyExtend owners | pattern holds |")
    print("|---|---:|---|---|---|")
    for row in report["anchor_storage_scaling_summary"]["rows"]:
        print(
            f"| {row['fixture']} | {row['parsed_chain_count']} | {row['cparagraphe_owner_chain_indexes']} | "
            f"{row['cpropertyextend_owner_chain_indexes']} | {row['pattern_1_plus_n_minus_1_holds']} |"
        )
    print()
    print("## Grouped vs Not-grouped Section Scaling Summary")
    print()
    print("| object count | grouped sections | not-grouped sections | delta | candidate holds |")
    print("|---:|---|---|---:|---|")
    for row in report["grouped_not_grouped_section_scaling_summary"]["comparisons_by_object_count"]:
        print(
            f"| {row['object_count']} | {row['grouped_section_counts']} | {row['not_grouped_section_counts']} | "
            f"{row['not_grouped_minus_grouped_delta']} | {row['delta_matches_candidate']} |"
        )
    print()
    print("## Selection Order / Primary Owner Summary")
    print()
    print("| fixture | attempted order | chain order | CParagraphe owner | first maps | last maps |")
    print("|---|---|---|---|---|---|")
    for row in report["selection_order_primary_owner_summary"]["rows"]:
        print(
            f"| {row['fixture']} | {row['attempted_selection_order']} | {row['parser_chain_order']} | "
            f"{row['cparagraphe_owner_texts']} | {row['attempted_order_first_maps_to_cparagraphe_owner']} | "
            f"{row['attempted_order_last_maps_to_cparagraphe_owner']} |"
        )


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
