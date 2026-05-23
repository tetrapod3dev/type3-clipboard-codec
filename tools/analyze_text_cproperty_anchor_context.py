from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
import sys
import time
from dataclasses import dataclass, field
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
    "text_three_objects_grouped_order_abc_content_variation.txt",
    "text_three_objects_grouped_order_abc_height_30mm.txt",
    "text_three_objects_grouped_order_abc_font_arial_bold.txt",
    "text_three_objects_grouped_order_abc_mixed_color.txt",
    "text_three_objects_grouped_order_cba.txt",
    "text_two_objects_mixed_color_not_grouped.txt",
    "text_two_objects_same_color_not_grouped.txt",
    "text_two_objects_not_grouped_selection_reversed.txt",
    "text_three_objects_not_grouped.txt",
    "text_three_objects_not_grouped_mixed_color.txt",
]
GROUPED_MULTI_OBJECT_FIXTURES = [
    "text_group_same_color_two_objects.txt",
    "text_group_mixed_color_two_objects.txt",
    "text_three_objects_grouped_order_abc.txt",
    "text_three_objects_grouped_order_abc_content_variation.txt",
    "text_three_objects_grouped_order_abc_height_30mm.txt",
    "text_three_objects_grouped_order_abc_font_arial_bold.txt",
    "text_three_objects_grouped_order_abc_mixed_color.txt",
    "text_three_objects_grouped_order_cba.txt",
]
NON_GROUPED_MULTI_OBJECT_FIXTURES = [
    "text_two_objects_mixed_color_not_grouped.txt",
    "text_two_objects_same_color_not_grouped.txt",
    "text_two_objects_not_grouped_selection_reversed.txt",
    "text_three_objects_not_grouped.txt",
    "text_three_objects_not_grouped_mixed_color.txt",
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
    "text_three_objects_grouped_order_abc_content_variation.txt": {
        "grouping_state": "grouped",
        "attempted_selection_order": ["HELLO", "9876543210", "Type3"],
        "order_control_status": "attempted",
    },
    "text_three_objects_grouped_order_abc_height_30mm.txt": {
        "grouping_state": "grouped",
        "attempted_selection_order": ["abcdefg", "1234567890", "XYZ"],
        "order_control_status": "attempted",
    },
    "text_three_objects_grouped_order_abc_font_arial_bold.txt": {
        "grouping_state": "grouped",
        "attempted_selection_order": ["abcdefg", "1234567890", "XYZ"],
        "order_control_status": "attempted",
    },
    "text_three_objects_grouped_order_abc_mixed_color.txt": {
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
    "text_three_objects_not_grouped_mixed_color.txt": {
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
MAX_FIXTURES = 100
MAX_CPROPERTY_NODES_PER_FIXTURE = 20
MAX_COBDAO_SECTIONS_PER_NODE = 200
MAX_TOTAL_COBDAO_SECTIONS = 5000
MAX_SECTION_COMPARISONS = 50000
MAX_NEAR_MISS_ROWS = 200
MAX_SIGNATURE_ROWS = 200
MAX_FIELD_DIFF_ROWS = 500
MAX_LOCAL_HEX_BYTES = 128
MAX_DECODED_VALUES_PER_SECTION = 128
MAX_MARKER_SCAN_ITERATIONS = 10000
MAX_RUNTIME_SECONDS = 30
DEFAULT_SAFE_MAX_FIXTURES = 3
DEFAULT_SAFE_MAX_RUNTIME_SECONDS = 8
DEFAULT_SAFE_MAX_OUTPUT_ROWS = 40
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


@dataclass
class AnalysisLimits:
    max_fixtures: int = MAX_FIXTURES
    max_cproperty_nodes_per_fixture: int = MAX_CPROPERTY_NODES_PER_FIXTURE
    max_cobdao_sections_per_node: int = MAX_COBDAO_SECTIONS_PER_NODE
    max_total_cobdao_sections: int = MAX_TOTAL_COBDAO_SECTIONS
    max_section_comparisons: int = MAX_SECTION_COMPARISONS
    max_near_miss_rows: int = MAX_NEAR_MISS_ROWS
    max_signature_rows: int = MAX_SIGNATURE_ROWS
    max_field_diff_rows: int = MAX_FIELD_DIFF_ROWS
    max_local_hex_bytes: int = MAX_LOCAL_HEX_BYTES
    max_decoded_values_per_section: int = MAX_DECODED_VALUES_PER_SECTION
    max_marker_scan_iterations: int = MAX_MARKER_SCAN_ITERATIONS
    max_runtime_seconds: int = MAX_RUNTIME_SECONDS
    max_output_rows: int = MAX_FIELD_DIFF_ROWS

    def as_dict(self) -> dict[str, int]:
        return {
            "max_runtime_seconds": self.max_runtime_seconds,
            "max_fixtures": self.max_fixtures,
            "max_cproperty_nodes_per_fixture": self.max_cproperty_nodes_per_fixture,
            "max_cobdao_sections_per_node": self.max_cobdao_sections_per_node,
            "max_total_cobdao_sections": self.max_total_cobdao_sections,
            "max_section_comparisons": self.max_section_comparisons,
            "max_near_miss_rows": self.max_near_miss_rows,
            "max_signature_rows": self.max_signature_rows,
            "max_field_diff_rows": self.max_field_diff_rows,
            "max_local_hex_bytes": self.max_local_hex_bytes,
            "max_decoded_values_per_section": self.max_decoded_values_per_section,
            "max_marker_scan_iterations": self.max_marker_scan_iterations,
            "max_output_rows": self.max_output_rows,
        }


@dataclass
class AnalysisContext:
    limits: AnalysisLimits = field(default_factory=AnalysisLimits)
    start_time: float = field(default_factory=time.monotonic)
    warnings: list[str] = field(default_factory=list)
    truncated: bool = False
    total_cobdao_sections: int = 0
    section_comparisons: int = 0

    @property
    def deadline(self) -> float:
        return self.start_time + self.limits.max_runtime_seconds

    def warn(self, message: str) -> None:
        if message not in self.warnings:
            self.warnings.append(message)

    def truncate(self, message: str) -> None:
        self.truncated = True
        self.warn(message)

    def check_deadline(self, stage: str) -> bool:
        if time.monotonic() > self.deadline:
            self.truncate(f"runtime limit reached at {stage}")
            return False
        return True

    def consume_cobdao_section(self, stage: str) -> bool:
        if self.total_cobdao_sections >= self.limits.max_total_cobdao_sections:
            self.truncate(
                f"total CObDao section limit reached at {stage}: {self.limits.max_total_cobdao_sections}"
            )
            return False
        self.total_cobdao_sections += 1
        return True

    def consume_comparison(self, stage: str, count: int = 1) -> bool:
        if self.section_comparisons + count > self.limits.max_section_comparisons:
            self.truncate(
                f"section comparison truncated at {self.limits.max_section_comparisons} comparisons during {stage}"
            )
            return False
        self.section_comparisons += count
        return True


_ACTIVE_CONTEXT: AnalysisContext | None = None


def _context() -> AnalysisContext:
    global _ACTIVE_CONTEXT
    if _ACTIVE_CONTEXT is None:
        _ACTIVE_CONTEXT = AnalysisContext()
    return _ACTIVE_CONTEXT


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
    ctx = _context()
    if center < 0 or center > len(payload):
        ctx.truncate(f"local hex window skipped for invalid center offset {center}")
        center = max(0, min(center, len(payload)))
    radius = min(radius, max(0, (ctx.limits.max_local_hex_bytes - 24) // 2))
    start = max(0, center - radius)
    end = min(len(payload), start + ctx.limits.max_local_hex_bytes, center + 24 + radius)
    return {
        "start": start,
        "end": end,
        "relative_anchor_start": center - start,
        "hex": payload[start:end].hex(" "),
    }


def _hex_window_around_marker(payload: bytes, marker_offset: int) -> dict[str, Any]:
    start = max(0, marker_offset - 64)
    end = min(len(payload), marker_offset + 160)
    return {
        "start": start,
        "end": end,
        "relative_marker_start": marker_offset - start,
        "hex": payload[start:end].hex(" "),
    }


def _nearby_doubles(payload: bytes, center: int, radius: int = LOCAL_WINDOW_RADIUS) -> list[dict[str, Any]]:
    ctx = _context()
    if center < 0 or center > len(payload):
        ctx.truncate(f"double decode skipped for invalid center offset {center}")
        return []
    start = max(0, center - radius)
    end = min(len(payload) - 8, center + 24 + radius)
    rows = []
    for off in range(start, end + 1):
        if len(rows) >= ctx.limits.max_decoded_values_per_section:
            ctx.truncate(f"double decode truncated at {ctx.limits.max_decoded_values_per_section} rows")
            break
        value = struct.unpack("<d", payload[off : off + 8])[0]
        if not math.isfinite(value):
            continue
        value_mm = value * 1000.0
        if abs(value_mm) > 1000000:
            continue
        if abs(value_mm) < 1e-9 or 0.001 <= abs(value_mm) <= 10000:
            rows.append({"offset": off, "double_m": value, "double_mm": round(value_mm, 6)})
    return rows[: min(80, ctx.limits.max_decoded_values_per_section)]


def _nearby_ints(payload: bytes, center: int, radius: int = LOCAL_WINDOW_RADIUS) -> list[dict[str, Any]]:
    ctx = _context()
    if center < 0 or center > len(payload):
        ctx.truncate(f"integer decode skipped for invalid center offset {center}")
        return []
    start = max(0, center - radius)
    end = min(len(payload) - 4, center + 24 + radius)
    rows = []
    for off in range(start, end + 1, 4):
        if len(rows) >= ctx.limits.max_decoded_values_per_section:
            ctx.truncate(f"integer decode truncated at {ctx.limits.max_decoded_values_per_section} rows")
            break
        raw = payload[off : off + 4]
        u32 = struct.unpack("<I", raw)[0]
        i32 = struct.unpack("<i", raw)[0]
        rows.append({"offset": off, "u32le": u32, "i32le": i32, "hex": raw.hex(" ")})
    return rows


def _zero_padding_runs(payload: bytes, center: int, radius: int = LOCAL_WINDOW_RADIUS) -> list[dict[str, int]]:
    ctx = _context()
    if center < 0 or center > len(payload):
        ctx.truncate(f"zero padding scan skipped for invalid center offset {center}")
        return []
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
    ctx = _context()
    best = None
    for marker in KNOWN_MARKERS:
        start = 0
        visited: set[int] = set()
        iterations = 0
        while True:
            if iterations >= ctx.limits.max_marker_scan_iterations:
                ctx.truncate(f"marker scan truncated by iteration limit in nearest_marker for {marker!r}")
                break
            if not ctx.check_deadline("nearest_marker"):
                break
            pos = payload.find(marker, start)
            if pos < 0:
                break
            if pos in visited:
                ctx.truncate(f"marker scan repeated offset {pos} in nearest_marker; breaking")
                break
            visited.add(pos)
            dist = abs(center - pos)
            candidate = {"marker": marker.decode("ascii", errors="replace"), "offset": pos, "distance": dist}
            if best is None or candidate["distance"] < best["distance"]:
                best = candidate
            start = pos + 1
            iterations += 1
    return best


def _marker_positions(payload: bytes, marker: bytes) -> list[int]:
    ctx = _context()
    positions = []
    start = 0
    visited: set[int] = set()
    iterations = 0
    while True:
        if iterations >= ctx.limits.max_marker_scan_iterations:
            ctx.truncate(f"marker scan truncated by iteration limit for {marker!r}")
            return positions
        if not ctx.check_deadline("marker_positions"):
            return positions
        pos = payload.find(marker, start)
        if pos < 0:
            return positions
        if pos in visited:
            ctx.truncate(f"marker scan repeated offset {pos} for {marker!r}; breaking")
            return positions
        visited.add(pos)
        positions.append(pos)
        start = pos + 1
        iterations += 1


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
    ctx = _context()
    rows = []
    start_limit = max(0, center - radius)
    end_limit = min(len(payload), center + 24 + radius)
    for marker in KNOWN_MARKERS:
        start = start_limit
        visited: set[int] = set()
        iterations = 0
        while True:
            if iterations >= ctx.limits.max_marker_scan_iterations:
                ctx.truncate(f"marker signature scan truncated by iteration limit for {marker!r}")
                break
            if not ctx.check_deadline("marker_signature"):
                break
            pos = payload.find(marker, start, end_limit)
            if pos < 0:
                break
            if pos in visited:
                ctx.truncate(f"marker signature repeated offset {pos}; breaking")
                break
            visited.add(pos)
            rows.append(
                {
                    "marker": marker.decode("ascii", errors="replace"),
                    "offset": pos,
                    "relative_to_hit": pos - center,
                }
            )
            start = pos + 1
            iterations += 1
    rows.sort(key=lambda row: (row["relative_to_hit"], row["marker"]))
    if len(rows) > ctx.limits.max_signature_rows:
        ctx.truncate(f"marker signature rows truncated at {ctx.limits.max_signature_rows}")
        return rows[: ctx.limits.max_signature_rows]
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
    ctx = _context()
    sections = []
    marker_offsets = _marker_positions(node.payload, COBDAO_MARKER)
    for section_index, marker_offset in enumerate(marker_offsets):
        if section_index >= ctx.limits.max_cobdao_sections_per_node:
            ctx.truncate(
                f"CObDao section scan truncated at {ctx.limits.max_cobdao_sections_per_node} sections for one node"
            )
            break
        if not ctx.consume_cobdao_section("cobdao_sections"):
            break
        if not ctx.check_deadline("cobdao_sections"):
            break
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
        if not ctx.check_deadline("cobdao_section_signatures"):
            break
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
            if not ctx.consume_comparison("local_bytes_similarity"):
                break
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
    for index, section in enumerate(sections):
        previous_section = sections[index - 1] if index > 0 else None
        next_section = sections[index + 1] if index + 1 < len(sections) else None
        section["neighbor_relation"] = {
            "previous_section_index": previous_section["section_index"] if previous_section else None,
            "previous_section_role_candidate": previous_section["section_role_candidate"] if previous_section else None,
            "previous_section_length_candidate": previous_section["section_length_candidate"] if previous_section else None,
            "distance_from_previous_cobdao": (
                section["cobdao_marker_offset"] - previous_section["cobdao_marker_offset"] if previous_section else None
            ),
            "next_section_index": next_section["section_index"] if next_section else None,
            "next_section_role_candidate": next_section["section_role_candidate"] if next_section else None,
            "next_section_length_candidate": next_section["section_length_candidate"] if next_section else None,
            "distance_to_next_cobdao": (
                next_section["cobdao_marker_offset"] - section["cobdao_marker_offset"] if next_section else None
            ),
        }
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
    ctx = _context()
    if not ctx.check_deadline(f"fixture {name}"):
        return {
            "fixture": name,
            "parser_name": None,
            "raw_size": None,
            "chain_inventory": [],
            "cparagraphe_direct_anchor_ownership": [],
            "cproperty_nodes": [],
            "all_anchor_hits": [],
            "truncated": True,
        }
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
        if not ctx.check_deadline(f"scan_exact_triples {name}"):
            break
        for hit in _scan_exact_triples(blob, target):
            all_hit_contexts.append(
                _anchor_hit_context(fixture=name, target_anchor=target, hit=hit, nodes=nodes, chains=chains)
            )
    cprop_summaries = []
    for cprop_count, (idx, node) in enumerate(cprop_nodes):
        if cprop_count >= ctx.limits.max_cproperty_nodes_per_fixture:
            ctx.truncate(
                f"CPropertyExtend node scan truncated at {ctx.limits.max_cproperty_nodes_per_fixture} nodes for {name}"
            )
            break
        if not ctx.check_deadline(f"cproperty nodes {name}"):
            break
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
    if not _context().consume_comparison("section_similarity"):
        return {
            "left_section_index": left["section_index"],
            "right_section_index": right["section_index"],
            "left_cobdao_offset": left["cobdao_marker_offset"],
            "right_cobdao_offset": right["cobdao_marker_offset"],
            "truncated": True,
        }
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


def _section_feature_value(section: dict[str, Any], feature: dict[str, Any]) -> Any:
    kind = feature["kind"]
    offset = feature.get("offset")
    marker_offset = int(section["marker_context_hex"]["relative_marker_start"])
    data = _window_bytes(section["marker_context_hex"])
    if kind == "u32le":
        start = marker_offset + int(offset)
        if start < 0 or start + 4 > len(data):
            return None
        return struct.unpack("<I", data[start : start + 4])[0]
    if kind == "i32le":
        start = marker_offset + int(offset)
        if start < 0 or start + 4 > len(data):
            return None
        return struct.unpack("<i", data[start : start + 4])[0]
    if kind == "double64le":
        start = marker_offset + int(offset)
        if start < 0 or start + 8 > len(data):
            return None
        value = struct.unpack("<d", data[start : start + 8])[0]
        if not math.isfinite(value):
            return "non_finite"
        return round(value * 1000.0, 6)
    if kind == "bytes4":
        start = marker_offset + int(offset)
        if start < 0 or start + 4 > len(data):
            return None
        return data[start : start + 4].hex(" ")
    if kind == "section_length_candidate":
        return section["section_length_candidate"]
    if kind == "objectinfos_distance":
        marker = section["nearby_objectinfos_marker"]
        return marker["distance_before_cobdao"] if marker else None
    if kind == "previous_section_role":
        return section["neighbor_relation"]["previous_section_role_candidate"]
    if kind == "next_section_role":
        return section["neighbor_relation"]["next_section_role_candidate"]
    if kind == "previous_section_length":
        return section["neighbor_relation"]["previous_section_length_candidate"]
    if kind == "next_section_length":
        return section["neighbor_relation"]["next_section_length_candidate"]
    if kind == "distance_from_previous_cobdao":
        return section["neighbor_relation"]["distance_from_previous_cobdao"]
    if kind == "distance_to_next_cobdao":
        return section["neighbor_relation"]["distance_to_next_cobdao"]
    if kind == "coordinate_like_at_plus_34":
        return section["cobdao_plus_34_triple_analysis"]["is_coordinate_like"]
    if kind == "z_approx_zero_at_plus_34":
        return section["cobdao_plus_34_triple_analysis"]["z_approx_zero"]
    return None


def _value_counts(values: list[Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        key = str(value)
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


def _field_difference_row(feature: dict[str, Any], anchor: list[dict[str, Any]], non_anchor: list[dict[str, Any]]) -> dict[str, Any]:
    anchor_values = [_section_feature_value(section, feature) for section in anchor]
    non_anchor_values = [_section_feature_value(section, feature) for section in non_anchor]
    anchor_set = set(anchor_values)
    non_anchor_set = set(non_anchor_values)
    false_positive_count = sum(1 for value in non_anchor_values if value in anchor_set)
    false_negative_count = 0
    if len(anchor_set) == 1:
        anchor_value = next(iter(anchor_set))
        false_negative_count = sum(1 for value in anchor_values if value != anchor_value)
    disjoint = anchor_set.isdisjoint(non_anchor_set)
    stable_anchor = len(anchor_set) == 1
    if stable_anchor and disjoint:
        usefulness = "strong_current_fixture_separator"
    elif disjoint:
        usefulness = "separates_current_fixture_sets_but_anchor_values_vary"
    elif false_positive_count < len(non_anchor_values):
        usefulness = "partial_separator"
    else:
        usefulness = "not_useful"
    return {
        "feature": feature["name"],
        "local_offset_relative_to_cobdao": feature.get("offset"),
        "decoded_type": feature["kind"],
        "anchor_bearing_value_distribution": _value_counts(anchor_values),
        "non_anchor_value_distribution": _value_counts(non_anchor_values),
        "anchor_unique_value_count": len(anchor_set),
        "non_anchor_unique_value_count": len(non_anchor_set),
        "separation_score": round(1.0 - (false_positive_count / len(non_anchor_values) if non_anchor_values else 0.0), 6),
        "false_positive_count": false_positive_count,
        "false_negative_count": false_negative_count,
        "candidate_usefulness": usefulness,
        "notes": "analyzer label uses known anchor/baseline evidence; this row is not a parser rule",
    }


def _field_features() -> list[dict[str, Any]]:
    features: list[dict[str, Any]] = []
    for offset in range(0, 129, 4):
        features.append({"name": f"u32le@CObDao+{offset}", "kind": "u32le", "offset": offset})
        features.append({"name": f"i32le@CObDao+{offset}", "kind": "i32le", "offset": offset})
        features.append({"name": f"bytes4@CObDao+{offset}", "kind": "bytes4", "offset": offset})
    for offset in range(0, 129, 8):
        features.append({"name": f"double64le_mm@CObDao+{offset}", "kind": "double64le", "offset": offset})
    features.extend(
        [
            {"name": "section_length_candidate", "kind": "section_length_candidate"},
            {"name": "OBJETINFOS_to_CObDao_distance", "kind": "objectinfos_distance"},
            {"name": "previous_section_role_candidate", "kind": "previous_section_role"},
            {"name": "next_section_role_candidate", "kind": "next_section_role"},
            {"name": "previous_section_length_candidate", "kind": "previous_section_length"},
            {"name": "next_section_length_candidate", "kind": "next_section_length"},
            {"name": "distance_from_previous_cobdao", "kind": "distance_from_previous_cobdao"},
            {"name": "distance_to_next_cobdao", "kind": "distance_to_next_cobdao"},
            {"name": "coordinate_like_at_CObDao+34", "kind": "coordinate_like_at_plus_34"},
            {"name": "z_approx_zero_at_CObDao+34", "kind": "z_approx_zero_at_plus_34"},
        ]
    )
    return features


def _anchor_vs_non_anchor_field_difference_summary(fixtures: list[dict[str, Any]]) -> dict[str, Any]:
    sections = _all_cobdao_sections([fx for fx in fixtures if fx["fixture"] in MULTI_OBJECT_FIXTURES])
    anchor = [section for section in sections if section["known_anchor_triple_hit"]]
    non_anchor = [section for section in sections if not section["known_anchor_triple_hit"]]
    rows = [_field_difference_row(feature, anchor, non_anchor) for feature in _field_features()]
    rows.sort(
        key=lambda row: (
            -float(row["separation_score"]),
            row["false_positive_count"],
            row["anchor_unique_value_count"],
            row["feature"],
        )
    )
    return {
        "status": "evidence_only",
        "label_definition": "anchor_bearing_candidate means CObDao+34 matches a known chain baseline anchor in analyzer evidence",
        "section_counts": {
            "anchor_bearing": len(anchor),
            "non_anchor": len(non_anchor),
            "total": len(sections),
        },
        "rows": rows,
        "top_current_separators": [
            row
            for row in rows
            if row["candidate_usefulness"] in {"strong_current_fixture_separator", "separates_current_fixture_sets_but_anchor_values_vary"}
        ][:20],
    }


def _stable_anchor_bearing_signature_candidates(field_summary: dict[str, Any]) -> list[dict[str, Any]]:
    candidates = []
    for row in field_summary["top_current_separators"][:12]:
        candidates.append(
            {
                "candidate": row["feature"],
                "works_on_anchor_bearing_sections": field_summary["section_counts"]["anchor_bearing"] - row["false_negative_count"],
                "anchor_bearing_section_count": field_summary["section_counts"]["anchor_bearing"],
                "false_positives": row["false_positive_count"],
                "false_negatives": row["false_negative_count"],
                "parser_safe_candidate": False,
                "reason": (
                    "separates the current labeled fixture set, but the field has no confirmed semantic meaning yet"
                    if row["false_positive_count"] == 0
                    else "partial current separator only"
                ),
            }
        )
    if not candidates:
        candidates.append(
            {
                "candidate": "none",
                "works_on_anchor_bearing_sections": 0,
                "anchor_bearing_section_count": field_summary["section_counts"]["anchor_bearing"],
                "false_positives": None,
                "false_negatives": None,
                "parser_safe_candidate": False,
                "reason": "no local field currently separates anchor-bearing from non-anchor sections without analyzer labels",
            }
        )
    return candidates


def _rejected_selector_candidates(field_summary: dict[str, Any]) -> list[dict[str, Any]]:
    coordinate_row = next(
        row for row in field_summary["rows"] if row["feature"] == "coordinate_like_at_CObDao+34"
    )
    return [
        {
            "selector": "coordinate-like at CObDao + 34",
            "rejected_for_parser": True,
            "reason": f"false positives in non-anchor sections: {coordinate_row['false_positive_count']}",
        },
        {
            "selector": "section index",
            "rejected_for_parser": True,
            "reason": "anchor-bearing indexes vary across grouped/not-grouped and 2-object/3-object fixtures",
        },
        {
            "selector": "CPropertyExtend absolute/payload offset",
            "rejected_for_parser": True,
            "reason": "payload offsets shift by grouping/object-count structure and are diagnostic only",
        },
        {
            "selector": "baseline equality",
            "rejected_for_parser": True,
            "reason": "baseline equality is the analyzer label/evidence source and would be circular as a parser selector",
        },
        {
            "selector": "fixture filename",
            "rejected_for_parser": True,
            "reason": "fixture names are test metadata and cannot define parser behavior",
        },
        {
            "selector": "attempted selection order alone",
            "rejected_for_parser": True,
            "reason": "attempted UI order is not encoded as a confirmed payload field and actual stored order remains unresolved",
        },
    ]


SIGNATURE_COMPONENTS = [
    {
        "component": "node_class_CPropertyExtend",
        "condition": "node class == CPropertyExtend",
        "kind": "section_field",
    },
    {
        "component": "OBJETINFOS_at_CObDao_minus_24",
        "condition": "nearby OBJETINFOS_CLASSNAME distance_before_cobdao == 24",
        "kind": "section_field",
    },
    {
        "component": "CObDao_marker",
        "condition": "CObDao marker exists",
        "kind": "section_field",
    },
    {
        "component": "u32le_CObDao_plus_12",
        "condition": "u32le@CObDao+12 == 131072",
        "kind": "u32le",
        "offset": 12,
        "expected": 131072,
    },
    {
        "component": "u32le_CObDao_plus_56",
        "condition": "u32le@CObDao+56 == 262144",
        "kind": "u32le",
        "offset": 56,
        "expected": 262144,
    },
    {
        "component": "u32le_CObDao_plus_108",
        "condition": "u32le@CObDao+108 == 65536",
        "kind": "u32le",
        "offset": 108,
        "expected": 65536,
    },
    {
        "component": "u32le_CObDao_plus_112",
        "condition": "u32le@CObDao+112 == 262144",
        "kind": "u32le",
        "offset": 112,
        "expected": 262144,
    },
    {
        "component": "finite_double_triple_at_CObDao_plus_34",
        "condition": "CObDao+34 decodes as finite double64 triple",
        "kind": "triple_finite",
    },
    {
        "component": "z_near_zero_at_CObDao_plus_34",
        "condition": "decoded CObDao+34 triple z is near 0",
        "kind": "triple_z_near_zero",
    },
    {
        "component": "coordinate_like_at_CObDao_plus_34",
        "condition": "decoded CObDao+34 triple is coordinate-like",
        "kind": "triple_coordinate_like",
    },
]


def _signature_component_passes(section: dict[str, Any], component: dict[str, Any]) -> bool:
    kind = component["kind"]
    if kind == "section_field":
        if component["component"] == "node_class_CPropertyExtend":
            return True
        if component["component"] == "OBJETINFOS_at_CObDao_minus_24":
            marker = section["nearby_objectinfos_marker"]
            return bool(marker and marker["distance_before_cobdao"] == 24)
        if component["component"] == "CObDao_marker":
            return section["marker_text"] == "CObDao"
    if kind == "u32le":
        value = _section_feature_value(
            section,
            {"name": component["component"], "kind": "u32le", "offset": component["offset"]},
        )
        return value == component["expected"]
    if kind == "triple_finite":
        triple = section["local_triple_at_cobdao_plus_34"]
        return bool(triple and triple["is_finite"])
    if kind == "triple_z_near_zero":
        return section["cobdao_plus_34_triple_analysis"]["z_approx_zero"] is True
    if kind == "triple_coordinate_like":
        return section["cobdao_plus_34_triple_analysis"]["is_coordinate_like"] is True
    return False


def _section_matches_local_record_signature(section: dict[str, Any]) -> bool:
    return all(_signature_component_passes(section, component) for component in SIGNATURE_COMPONENTS)


def _local_record_signature_summary(fixtures: list[dict[str, Any]]) -> dict[str, Any]:
    sections = _all_cobdao_sections([fx for fx in fixtures if fx["fixture"] in MULTI_OBJECT_FIXTURES])
    anchor = [section for section in sections if section["known_anchor_triple_hit"]]
    non_anchor = [section for section in sections if not section["known_anchor_triple_hit"]]
    matched = [section for section in sections if _section_matches_local_record_signature(section)]
    matched_anchor = [section for section in matched if section["known_anchor_triple_hit"]]
    matched_non_anchor = [section for section in matched if not section["known_anchor_triple_hit"]]
    false_negative = [section for section in anchor if not _section_matches_local_record_signature(section)]
    fixtures_covered = sorted({section["fixture"] for section in matched_anchor})
    expected_anchor_fixtures = sorted({section["fixture"] for section in anchor})
    return {
        "signature_name": "CPropertyExtend_CObDao_anchor_record_candidate_v1",
        "status": "strong_observed_signature_candidate",
        "definition": [component["condition"] for component in SIGNATURE_COMPONENTS],
        "matched_section_count": len(matched),
        "anchor_bearing_matched_count": len(matched_anchor),
        "non_anchor_matched_count": len(matched_non_anchor),
        "false_positive_count": len(matched_non_anchor),
        "false_negative_count": len(false_negative),
        "coverage": {
            "anchor_bearing_total": len(anchor),
            "non_anchor_total": len(non_anchor),
            "anchor_bearing_coverage_ratio": round(len(matched_anchor) / len(anchor), 6) if anchor else None,
        },
        "fixtures_covered": fixtures_covered,
        "failed_fixtures": sorted(set(expected_anchor_fixtures) - set(fixtures_covered)),
        "parser_safe_candidate": "provisional_false",
        "reason": (
            "FP/FN are zero in the current labeled fixture set, but components were discovered with analyzer labels "
            "and the local record field semantics are not confirmed."
        ),
    }


def _signature_components_summary(fixtures: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sections = _all_cobdao_sections([fx for fx in fixtures if fx["fixture"] in MULTI_OBJECT_FIXTURES])
    anchor = [section for section in sections if section["known_anchor_triple_hit"]]
    non_anchor = [section for section in sections if not section["known_anchor_triple_hit"]]
    rows = []
    for component in SIGNATURE_COMPONENTS:
        anchor_pass = [section for section in anchor if _signature_component_passes(section, component)]
        non_anchor_pass = [section for section in non_anchor if _signature_component_passes(section, component)]
        false_negative_count = len(anchor) - len(anchor_pass)
        false_positive_count = len(non_anchor_pass)
        usefulness = (
            "strong_separator"
            if false_positive_count == 0 and false_negative_count == 0
            else "supporting_context"
            if false_negative_count == 0
            else "not_stable"
        )
        rows.append(
            {
                "component": component["component"],
                "condition": component["condition"],
                "anchor_bearing_pass_count": len(anchor_pass),
                "non_anchor_pass_count": len(non_anchor_pass),
                "false_positive_count": false_positive_count,
                "false_negative_count": false_negative_count,
                "usefulness": usefulness,
            }
        )
    return rows


LOCAL_RECORD_LAYOUT_FIELDS = [
    {
        "local_offset": -24,
        "byte_range": "CObDao-24..CObDao-5",
        "decoded_type": "ascii",
        "candidate_role": "section_header_field",
        "note": "OBJETINFOS_CLASSNAME marker immediately precedes current CObDao local sections.",
    },
    {
        "local_offset": 0,
        "byte_range": "CObDao+0..CObDao+5",
        "decoded_type": "ascii",
        "candidate_role": "section_header_field",
        "note": "CObDao marker.",
    },
    {
        "local_offset": 12,
        "byte_range": "CObDao+12..CObDao+15",
        "decoded_type": "u32le",
        "candidate_role": "record_type_or_subtype",
        "note": "Stable current separator; semantic meaning unknown.",
    },
    {
        "local_offset": 16,
        "byte_range": "CObDao+16..CObDao+29",
        "decoded_type": "bytes14",
        "candidate_role": "padding_or_reserved",
        "note": "Observed stable zero-filled gap before the anchor payload in current anchor-bearing sections.",
    },
    {
        "local_offset": 30,
        "byte_range": "CObDao+30..CObDao+33",
        "decoded_type": "bytes4",
        "candidate_role": "neighboring_metadata",
        "note": "Varies with observed color/style context; not part of the anchor coordinate triple.",
    },
    {
        "local_offset": 34,
        "byte_range": "CObDao+34..CObDao+57",
        "decoded_type": "double64le[3]",
        "candidate_role": "anchor_x/y/z_payload",
        "note": "Contiguous finite coordinate-like triple in anchor-bearing sections.",
    },
    {
        "local_offset": 58,
        "byte_range": "CObDao+58..CObDao+107",
        "decoded_type": "bytes50",
        "candidate_role": "neighboring_metadata",
        "note": "Mostly stable trailing local bytes after the anchor payload; internal field boundaries remain unknown.",
    },
    {
        "local_offset": 56,
        "byte_range": "CObDao+56..CObDao+59",
        "decoded_type": "u32le",
        "candidate_role": "unknown_flag",
        "note": "Overlaps the last two bytes of the z double at +50..+57; may not be an independent field.",
    },
    {
        "local_offset": 108,
        "byte_range": "CObDao+108..CObDao+111",
        "decoded_type": "u32le",
        "candidate_role": "unknown_flag",
        "note": "Stable current separator after the anchor payload region.",
    },
    {
        "local_offset": 112,
        "byte_range": "CObDao+112..CObDao+115",
        "decoded_type": "u32le",
        "candidate_role": "unknown_flag",
        "note": "Stable current separator after the anchor payload region.",
    },
]


def _section_raw_bytes(section: dict[str, Any], local_offset: int, size: int) -> bytes | None:
    marker_offset = int(section["marker_context_hex"]["relative_marker_start"])
    data = _window_bytes(section["marker_context_hex"])
    start = marker_offset + local_offset
    if start < 0 or start + size > len(data):
        return None
    return data[start : start + size]


def _decode_layout_value(section: dict[str, Any], field: dict[str, Any]) -> Any:
    offset = int(field["local_offset"])
    decoded_type = field["decoded_type"]
    if decoded_type == "ascii":
        size = 20 if offset == -24 else 6
        raw = _section_raw_bytes(section, offset, size)
        return None if raw is None else raw.decode("ascii", errors="replace")
    if decoded_type == "u32le":
        return _section_feature_value(section, {"kind": "u32le", "offset": offset})
    if decoded_type == "double64le[3]":
        triple = section["local_triple_at_cobdao_plus_34"]
        return None if triple is None else triple["decoded_anchor_mm"]
    if decoded_type.startswith("bytes"):
        size = int(decoded_type.removeprefix("bytes"))
        raw = _section_raw_bytes(section, offset, size)
        return None if raw is None else raw.hex(" ")
    return None


def _summarize_stability(values: list[Any]) -> str:
    if not values:
        return "unknown"
    if len({json.dumps(value, sort_keys=True) for value in values}) == 1:
        return "stable"
    return "variable"


def _local_record_chunks(section: dict[str, Any], start_offset: int = -24, end_offset: int = 129) -> list[dict[str, Any]]:
    chunks = []
    marker_offset = int(section["marker_context_hex"]["relative_marker_start"])
    data = _window_bytes(section["marker_context_hex"])
    for local_start in range(start_offset, end_offset, 16):
        local_end = min(local_start + 16, end_offset)
        start = marker_offset + local_start
        end = marker_offset + local_end
        if start < 0 or end > len(data):
            continue
        chunks.append(
            {
                "local_range": f"{local_start:+d}..{local_end - 1:+d}",
                "hex": data[start:end].hex(" "),
            }
        )
    return chunks


def _aligned_local_u32_i32_fields(section: dict[str, Any], start_offset: int = -24, end_offset: int = 128) -> list[dict[str, Any]]:
    rows = []
    for local_offset in range(start_offset, end_offset + 1, 4):
        raw = _section_raw_bytes(section, local_offset, 4)
        if raw is None:
            continue
        rows.append(
            {
                "local_offset_from_cobdao": local_offset,
                "u32le": struct.unpack("<I", raw)[0],
                "i32le": struct.unpack("<i", raw)[0],
                "hex": raw.hex(" "),
            }
        )
    return rows


def _aligned_local_double_fields(section: dict[str, Any], start_offset: int = -24, end_offset: int = 128) -> list[dict[str, Any]]:
    rows = []
    for local_offset in range(start_offset, end_offset + 1, 8):
        raw = _section_raw_bytes(section, local_offset, 8)
        if raw is None:
            continue
        value = struct.unpack("<d", raw)[0]
        if not math.isfinite(value):
            decoded: float | str = "non_finite"
        else:
            decoded = round(value * 1000.0, 6)
        rows.append(
            {
                "local_offset_from_cobdao": local_offset,
                "double_mm": decoded,
                "hex": raw.hex(" "),
            }
        )
    return rows


def _range_dict(start: int, end: int) -> dict[str, Any]:
    return {
        "local_range": f"{start:+d}..{end:+d}",
        "start_offset_from_cobdao": start,
        "end_offset_from_cobdao": end,
        "length": end - start + 1,
    }


def _byte_stability_ranges(sections: list[dict[str, Any]], start_offset: int, end_offset: int) -> dict[str, Any]:
    stable_offsets = []
    variable_offsets = []
    missing_offsets = []
    for local_offset in range(start_offset, end_offset + 1):
        values = [_section_raw_bytes(section, local_offset, 1) for section in sections]
        if any(value is None for value in values):
            missing_offsets.append(local_offset)
        elif len(set(values)) == 1:
            stable_offsets.append(local_offset)
        else:
            variable_offsets.append(local_offset)

    def collapse(offsets: list[int]) -> list[dict[str, Any]]:
        if not offsets:
            return []
        ranges = []
        range_start = offsets[0]
        previous = offsets[0]
        for offset in offsets[1:]:
            if offset == previous + 1:
                previous = offset
                continue
            ranges.append(_range_dict(range_start, previous))
            range_start = previous = offset
        ranges.append(_range_dict(range_start, previous))
        return ranges

    return {
        "window": f"CObDao{start_offset:+d}..CObDao{end_offset:+d}",
        "stable_byte_count": len(stable_offsets),
        "variable_byte_count": len(variable_offsets),
        "missing_byte_count": len(missing_offsets),
        "stable_byte_ranges": collapse(stable_offsets),
        "variable_byte_ranges": collapse(variable_offsets),
        "missing_byte_ranges": collapse(missing_offsets),
    }


def _compact_neighbor_section(section: dict[str, Any] | None) -> dict[str, Any] | None:
    if section is None:
        return None
    return {
        "section_index": section["section_index"],
        "cobdao_marker_offset": section["cobdao_marker_offset"],
        "section_length_candidate": section["section_length_candidate"],
        "section_role_candidate": section["section_role_candidate"],
        "signature_matched": _section_matches_local_record_signature(section),
        "coordinate_like_at_CObDao_plus_34": section["cobdao_plus_34_triple_analysis"]["is_coordinate_like"],
        "strong_separator_fields_matched": sorted(
            {
                "u32le_CObDao_plus_12",
                "u32le_CObDao_plus_56",
                "u32le_CObDao_plus_108",
                "u32le_CObDao_plus_112",
            }.intersection(_signature_match_detail(section)["matched_components"])
        ),
    }


def _previous_next_sections(section: dict[str, Any], sections: list[dict[str, Any]]) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    index = int(section["section_index"])
    previous_section = sections[index - 1] if index > 0 else None
    next_section = sections[index + 1] if index + 1 < len(sections) else None
    return previous_section, next_section


def _grouped_not_grouped_local_record_comparison(fixtures: list[dict[str, Any]]) -> dict[str, Any]:
    by_name = {fixture["fixture"]: fixture for fixture in fixtures}
    grouped = by_name.get("text_group_same_color_two_objects.txt")
    not_grouped = by_name.get("text_two_objects_same_color_not_grouped.txt")
    if grouped is None or not_grouped is None:
        return {"status": "unavailable"}
    grouped_sections = _first_cproperty_sections(grouped)
    not_grouped_sections = _first_cproperty_sections(not_grouped)
    same_index_pairs = []
    for index in range(min(len(grouped_sections), len(not_grouped_sections))):
        same_index_pairs.append(_section_similarity_row(grouped_sections[index], not_grouped_sections[index]))
    grouped_anchor = next((section for section in grouped_sections if section["known_anchor_triple_hit"]), None)
    not_grouped_anchor = next((section for section in not_grouped_sections if section["known_anchor_triple_hit"]), None)
    return {
        "status": "observed_provisional",
        "grouped_fixture": grouped["fixture"],
        "not_grouped_fixture": not_grouped["fixture"],
        "same_section_index_pairs": same_index_pairs,
        "anchor_to_anchor_shifted_pair": (
            _section_similarity_row(grouped_anchor, not_grouped_anchor)
            if grouped_anchor is not None and not_grouped_anchor is not None
            else None
        ),
        "interpretation": (
            "The anchor-bearing local record remains similar when compared anchor-to-anchor after the not-grouped "
            "inserted-section shift; same-index comparison is weaker because section indexes move."
        ),
    }


def _anchor_record_layout_candidate(fixtures: list[dict[str, Any]]) -> dict[str, Any]:
    sections = _all_cobdao_sections([fx for fx in fixtures if fx["fixture"] in MULTI_OBJECT_FIXTURES])
    anchor = [section for section in sections if section["known_anchor_triple_hit"]]
    non_anchor = [section for section in sections if not section["known_anchor_triple_hit"]]
    sections_by_fixture = {
        fixture["fixture"]: _first_cproperty_sections(fixture)
        for fixture in fixtures
        if fixture["fixture"] in MULTI_OBJECT_FIXTURES
    }
    rows = []
    for field in LOCAL_RECORD_LAYOUT_FIELDS:
        anchor_values = [_decode_layout_value(section, field) for section in anchor]
        non_anchor_values = [_decode_layout_value(section, field) for section in non_anchor]
        rows.append(
            {
                "local_offset_from_cobdao": field["local_offset"],
                "byte_range": field["byte_range"],
                "decoded_type": field["decoded_type"],
                "decoded_value_in_anchor_bearing_sections": _value_counts(anchor_values),
                "stability_across_anchor_bearing_sections": _summarize_stability(anchor_values),
                "value_distribution_in_non_anchor_sections": _value_counts(non_anchor_values),
                "candidate_role": field["candidate_role"],
                "interpretation_note": field["note"],
            }
        )
    return {
        "status": "observed_provisional",
        "window_definition": "CObDao-24 through CObDao+128; wider CObDao-64 through CObDao+128 retained in section marker_context_hex.",
        "anchor_bearing_section_count": len(anchor),
        "non_anchor_section_count": len(non_anchor),
        "layout_rows": rows,
        "sample_anchor_local_record_windows": [
            {
                "fixture": section["fixture"],
                "section_index": section["section_index"],
                "cobdao_marker_offset": section["cobdao_marker_offset"],
                "matched_chains": section["matched_chains"],
                "grouped_chunks": _local_record_chunks(section),
                "wide_context_chunks": _local_record_chunks(section, start_offset=-64, end_offset=160),
                "aligned_u32_i32_fields": _aligned_local_u32_i32_fields(section),
                "aligned_double_fields": _aligned_local_double_fields(section),
                "previous_cobdao_section": _compact_neighbor_section(
                    _previous_next_sections(section, sections_by_fixture[section["fixture"]])[0]
                ),
                "next_cobdao_section": _compact_neighbor_section(
                    _previous_next_sections(section, sections_by_fixture[section["fixture"]])[1]
                ),
            }
            for section in anchor[:5]
        ],
        "anchor_byte_stability": _byte_stability_ranges(anchor, -24, 128),
        "grouped_not_grouped_local_record_comparison": _grouped_not_grouped_local_record_comparison(fixtures),
        "stable_byte_claim": "The listed marker/u32 fields are stable in current anchor-bearing sections; bytes containing anchor x/y values vary by object.",
        "variable_byte_claim": "The contiguous double3 at +34 varies with the stored anchor; z is currently near zero in all anchor-bearing sections.",
        "record_boundary_evidence": {
            "status": "candidate_only",
            "objectinfos_to_cobdao_distance": 24,
            "next_cobdao_distance_distribution_for_anchor_bearing": _value_counts(
                [section["neighbor_relation"]["distance_to_next_cobdao"] for section in anchor]
            ),
            "section_length_candidate_distribution_for_anchor_bearing": _value_counts(
                [section["section_length_candidate"] for section in anchor]
            ),
            "interpretation": (
                "OBJETINFOS_CLASSNAME at -24 is a stable local preamble, but next-CObDao distances vary with the "
                "surrounding CPropertyExtend layout; the true binary record start/length is not confirmed."
            ),
        },
    }


def _signature_match_detail(section: dict[str, Any]) -> dict[str, Any]:
    matched = []
    failed = []
    for component in SIGNATURE_COMPONENTS:
        name = component["component"]
        if _signature_component_passes(section, component):
            matched.append(name)
        else:
            failed.append(name)
    return {"matched_components": matched, "failed_components": failed}


def _partial_match_near_miss_analysis(fixtures: list[dict[str, Any]]) -> dict[str, Any]:
    sections = [
        section
        for section in _all_cobdao_sections([fx for fx in fixtures if fx["fixture"] in MULTI_OBJECT_FIXTURES])
        if not section["known_anchor_triple_hit"]
    ]
    near_misses = []
    for section in sections:
        detail = _signature_match_detail(section)
        strong_components = {
            "u32le_CObDao_plus_12",
            "u32le_CObDao_plus_56",
            "u32le_CObDao_plus_108",
            "u32le_CObDao_plus_112",
        }
        strong_matched = sorted(strong_components.intersection(detail["matched_components"]))
        near_misses.append(
            {
                "fixture": section["fixture"],
                "section_index": section["section_index"],
                "cobdao_marker_offset": section["cobdao_marker_offset"],
                "section_length_candidate": section["section_length_candidate"],
                "matched_components": detail["matched_components"],
                "failed_components": detail["failed_components"],
                "strong_separator_fields_matched": strong_matched,
                "coordinate_like_at_CObDao_plus_34": section["cobdao_plus_34_triple_analysis"]["is_coordinate_like"],
                "decoded_CObDao_plus_34_mm": section["cobdao_plus_34_triple_analysis"]["decoded_double_triple_mm"],
                "rejection_reason": (
                    "passes coordinate-like payload check but fails one or more strong u32 separator fields"
                    if section["cobdao_plus_34_triple_analysis"]["is_coordinate_like"]
                    else "fails coordinate-like payload check and one or more signature fields"
                ),
            }
        )
    near_misses.sort(key=lambda row: (-len(row["matched_components"]), row["fixture"], row["section_index"]))
    one_field_failures = [row for row in near_misses if len(row["failed_components"]) == 1]
    coordinate_like = [row for row in near_misses if row["coordinate_like_at_CObDao_plus_34"]]
    return {
        "status": "observed_provisional",
        "non_anchor_section_count": len(sections),
        "one_field_away_non_anchor_count": len(one_field_failures),
        "coordinate_like_non_anchor_partial_count": len(coordinate_like),
        "nearest_non_anchor_sections": near_misses[:20],
        "one_field_away_non_anchor_sections": one_field_failures[:20],
        "hierarchy_suggestion": (
            "Current non-anchor near misses show coordinate-like +34 is supporting context only; "
            "the full local record signature is more selective than the payload triple alone."
        ),
    }


def _neighbor_relation_analysis(fixtures: list[dict[str, Any]]) -> dict[str, Any]:
    anchor = [
        section
        for section in _all_cobdao_sections([fx for fx in fixtures if fx["fixture"] in MULTI_OBJECT_FIXTURES])
        if section["known_anchor_triple_hit"]
    ]
    rows = []
    previous_roles = []
    next_roles = []
    previous_lengths = []
    next_lengths = []
    by_grouping: dict[str, dict[str, int]] = {}
    for section in anchor:
        metadata = ORDER_METADATA.get(section["fixture"], {})
        grouping = str(metadata.get("grouping_state", "unknown"))
        previous_role = section["neighbor_relation"]["previous_section_role_candidate"]
        next_role = section["neighbor_relation"]["next_section_role_candidate"]
        previous_roles.append(previous_role)
        next_roles.append(next_role)
        previous_lengths.append(section["neighbor_relation"]["previous_section_length_candidate"])
        next_lengths.append(section["neighbor_relation"]["next_section_length_candidate"])
        by_grouping.setdefault(grouping, {}).setdefault(str(section["section_index"]), 0)
        by_grouping[grouping][str(section["section_index"])] += 1
        rows.append(
            {
                "fixture": section["fixture"],
                "grouping_state": grouping,
                "section_index": section["section_index"],
                "cobdao_marker_offset": section["cobdao_marker_offset"],
                "previous_section_type_signature": {
                    "role": previous_role,
                    "length_candidate": section["neighbor_relation"]["previous_section_length_candidate"],
                    "distance_from_previous_cobdao": section["neighbor_relation"]["distance_from_previous_cobdao"],
                },
                "next_section_type_signature": {
                    "role": next_role,
                    "length_candidate": section["neighbor_relation"]["next_section_length_candidate"],
                    "distance_to_next_cobdao": section["neighbor_relation"]["distance_to_next_cobdao"],
                },
                "matched_chains": section["matched_chains"],
            }
        )
    return {
        "status": "observed_provisional",
        "anchor_bearing_section_count": len(anchor),
        "previous_role_distribution": _value_counts(previous_roles),
        "next_role_distribution": _value_counts(next_roles),
        "previous_length_distribution": _value_counts(previous_lengths),
        "next_length_distribution": _value_counts(next_lengths),
        "anchor_section_index_distribution_by_grouping": by_grouping,
        "rows": rows,
        "interpretation": (
            "Neighbor context shows repeated local placement patterns, but previous/next non-anchor records are not yet semantically identified. "
            "Grouping changes section indexes and inserted 148-byte section counts, so neighbor context helps alignment but is not a standalone selector."
        ),
    }


def _semantic_hypothesis() -> dict[str, Any]:
    return {
        "status": "provisional",
        "signature_kind_assessment": {
            "current_judgment": "record_type_more_likely_than_unrelated_field_combination",
            "confidence": "weak",
            "evidence_supporting": [
                "The marker pair, fixed u32 fields, and anchor payload repeat across all current anchor-bearing sections.",
                "The same composite signature has 0 current non-anchor matches.",
            ],
            "evidence_against_or_limits": [
                "The signature was discovered using analyzer labels.",
                "The semantics of the stable u32 values are unknown.",
                "u32@+56 overlaps the +34 double3 payload and may partly reflect z=0 rather than an independent field.",
            ],
        },
        "field_hypotheses": [
            {
                "field": "u32le@CObDao+12",
                "possible_meaning": "record_type_or_subtype",
                "evidence_supporting": "Stable value 131072 in all current anchor-bearing sections and absent from non-anchor sections.",
                "evidence_against": "No independent format documentation or controlled fixture varies this field.",
                "confidence": "provisional",
            },
            {
                "field": "u32le@CObDao+56",
                "possible_meaning": "unknown_flag_or_overlap_artifact",
                "evidence_supporting": "Stable current separator value 262144.",
                "evidence_against": "The u32 read begins inside the z double at +50..+57, so it is not safely aligned as an independent local field.",
                "confidence": "weak",
            },
            {
                "field": "u32le@CObDao+108",
                "possible_meaning": "record_subtype_or_trailing_metadata",
                "evidence_supporting": "Stable value 65536 in all current anchor-bearing sections and absent from non-anchor sections.",
                "evidence_against": "No known ownership/order relation has been mapped to this field.",
                "confidence": "provisional",
            },
            {
                "field": "u32le@CObDao+112",
                "possible_meaning": "record_subtype_or_trailing_metadata",
                "evidence_supporting": "Stable value 262144 in all current anchor-bearing sections and absent from non-anchor sections.",
                "evidence_against": "Adjacent to +108, but record boundary and trailing structure are still unknown.",
                "confidence": "provisional",
            },
        ],
        "parser_readiness": "not_ready_analyzer_only",
    }


def _candidate_parser_rule_draft() -> dict[str, Any]:
    return {
        "status": "draft_do_not_implement_yet",
        "prose": (
            "Within CPropertyExtend, scan CObDao local sections. A provisional anchor-record candidate is a CObDao "
            "section with OBJETINFOS_CLASSNAME 24 bytes before CObDao, u32 fields 2/4/1/4 at local offsets "
            "+12/+56/+108/+112, and a finite coordinate-like double triple at CObDao+34 with z near zero. "
            "If validated, that triple would be decoded as a CPropertyExtend text anchor candidate."
        ),
        "pseudocode": [
            "for section in CPropertyExtend.CObDao_sections:",
            "    if objectinfos_distance(section) != 24: continue",
            "    if u32(section, +12) != 131072: continue",
            "    if u32(section, +56) != 262144: continue",
            "    if u32(section, +108) != 65536: continue",
            "    if u32(section, +112) != 262144: continue",
            "    triple = double3(section, +34)",
            "    if not finite(triple) or not coordinate_like(triple) or not z_near_zero(triple): continue",
            "    yield analyzer-only CPropertyExtend anchor candidate",
        ],
        "would_decode": "CPropertyExtend CObDao-local anchor record candidates matching the full local signature",
        "would_not_decode": [
            "CParagraphe direct anchors",
            "non-anchor CObDao sections",
            "coordinate-like CObDao+34 triples without the full record signature",
            "sections selected by absolute payload offsets, fixture names, or baseline equality",
        ],
        "why_provisional": [
            "local field semantics at +12/+56/+108/+112 are still unknown",
            "signature was discovered using baseline-derived analyzer labels",
            "chain ownership mapping still needs a parser-safe rule",
            "more independent fixtures should validate the record signature before implementation",
        ],
        "additional_validation_needed": [
            "more fonts and non-Arial font families",
            "multi-line and separated text-run cases",
            "larger object counts",
            "negative/zero/non-grid anchors if Type3 allows them",
            "fixtures that vary grouping/order without relying on current baseline ownership",
        ],
    }


def _rejected_single_field_rules(field_summary: dict[str, Any]) -> list[dict[str, Any]]:
    by_feature = {row["feature"]: row for row in field_summary["rows"]}
    rows = []
    for feature in (
        "coordinate_like_at_CObDao+34",
        "u32le@CObDao+12",
        "u32le@CObDao+56",
        "u32le@CObDao+108",
        "u32le@CObDao+112",
    ):
        row = by_feature[feature]
        rows.append(
            {
                "selector": f"only {feature}",
                "rejected_for_parser": True,
                "false_positive_count": row["false_positive_count"],
                "false_negative_count": row["false_negative_count"],
                "reason": (
                    "single field lacks confirmed record semantics; use only as part of a composite signature candidate"
                    if feature != "coordinate_like_at_CObDao+34"
                    else "coordinate-like CObDao+34 has non-anchor false positives"
                ),
            }
        )
    rows.extend(
        [
            {
                "selector": "section index",
                "rejected_for_parser": True,
                "reason": "anchor-bearing indexes vary across grouped/not-grouped and object-count variants",
            },
            {
                "selector": "payload offset",
                "rejected_for_parser": True,
                "reason": "payload offsets shift across grouping/object-count variants and are diagnostic only",
            },
            {
                "selector": "baseline equality",
                "rejected_for_parser": True,
                "reason": "baseline equality is allowed for analyzer evaluation only and would be circular as parser selection",
            },
        ]
    )
    return rows


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


def _limits_payload() -> dict[str, Any]:
    ctx = _context()
    return {
        "limits": ctx.limits.as_dict(),
        "truncated": ctx.truncated,
        "warnings": ctx.warnings,
    }


def _partial_report(fixture_reports: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        **_limits_payload(),
        "policy": {
            "scope": "CPropertyExtend anchor context structure/evidence audit only",
            "parser_behavior": "not_modified",
            "cproperty_anchor_promotion": "not_applied",
            "absolute_offsets": "diagnostic_only",
            "active_anchor_fallback": "baseline_midpoint remains active",
        },
        "fixtures": fixture_reports,
        "status": "partial",
        "answers": {"parser_readiness": "not_ready_analyzer_only"},
    }


def _build_lightweight_summary_report() -> dict[str, Any]:
    ctx = _context()
    fixture_rows: list[dict[str, Any]] = []
    for fixture_index, name in enumerate(FIXTURES):
        if fixture_index >= ctx.limits.max_fixtures:
            ctx.warn(f"fixture scan capped at {ctx.limits.max_fixtures} fixtures in safe summary mode")
            break
        if not ctx.check_deadline("lightweight fixture scan"):
            break
        blob: bytes | None = None
        try:
            blob = _read_fixture(name)
            nodes = _read_nodes(blob)
            cproperty_count = sum(1 for node in nodes if node.header.class_name == "CPropertyExtend")
            cparagraphe_count = sum(1 for node in nodes if node.header.class_name == "CParagraphe")
            fixture_rows.append(
                {
                    "fixture": name,
                    "bytes": len(blob),
                    "node_count": len(nodes),
                    "cproperty_node_count": cproperty_count,
                    "cparagraphe_node_count": cparagraphe_count,
                }
            )
        except Exception as exc:  # noqa: BLE001
            ctx.warn(f"{name}: lightweight parse failed ({type(exc).__name__})")
            fixture_rows.append(
                {
                    "fixture": name,
                    "bytes": len(blob) if blob is not None else None,
                    "node_count": None,
                    "cproperty_node_count": None,
                    "cparagraphe_node_count": None,
                }
            )

    return {
        **_limits_payload(),
        "mode": "safe_summary",
        "policy": {
            "scope": "safe lightweight summary only",
            "parser_behavior": "not_modified",
            "heavy_analysis": "disabled_by_default",
            "deep_option_required": True,
            "cproperty_anchor_promotion": "not_applied",
        },
        "fixtures": fixture_rows[: ctx.limits.max_output_rows],
        "summary": {
            "fixture_rows": min(len(fixture_rows), ctx.limits.max_output_rows),
            "heavy_sections_included": False,
        },
        "answers": {"parser_readiness": "safe_summary_only"},
    }


def build_report(limits: AnalysisLimits | None = None, *, deep: bool = False) -> dict[str, Any]:
    global _ACTIVE_CONTEXT
    _ACTIVE_CONTEXT = AnalysisContext(limits=limits or AnalysisLimits())
    ctx = _context()
    if not deep:
        return _build_lightweight_summary_report()
    fixture_reports = []
    for fixture_index, name in enumerate(FIXTURES):
        if fixture_index >= ctx.limits.max_fixtures:
            ctx.truncate(f"fixture scan truncated at {ctx.limits.max_fixtures} fixtures")
            break
        if not ctx.check_deadline("fixture scan"):
            break
        fixture_reports.append(_fixture_report(name))
        if ctx.truncated and ctx.total_cobdao_sections >= ctx.limits.max_total_cobdao_sections:
            break
    if ctx.truncated:
        return _partial_report(fixture_reports)
    comparison = _compare_grouped_non_grouped(fixture_reports)
    if not ctx.check_deadline("grouped_non_grouped_comparison"):
        return _partial_report(fixture_reports)
    aggregate = _anchor_bearing_aggregate(fixture_reports)
    alignment = _section_alignment_analysis(fixture_reports)
    anchor_storage_summary = _anchor_storage_scaling_summary(fixture_reports)
    section_scaling_summary = _grouped_not_grouped_section_scaling_summary(fixture_reports)
    selection_order_summary = _selection_order_primary_owner_summary(fixture_reports)
    field_difference_summary = _anchor_vs_non_anchor_field_difference_summary(fixture_reports)
    if ctx.truncated or not ctx.check_deadline("field_difference_summary"):
        return _partial_report(fixture_reports)
    local_record_signature_summary = _local_record_signature_summary(fixture_reports)
    anchor_record_layout = _anchor_record_layout_candidate(fixture_reports)
    partial_match_near_miss = _partial_match_near_miss_analysis(fixture_reports)
    neighbor_relation = _neighbor_relation_analysis(fixture_reports)
    semantic_hypothesis = _semantic_hypothesis()
    return {
        **_limits_payload(),
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
        "anchor_vs_non_anchor_field_difference_summary": field_difference_summary,
        "local_record_signature_summary": local_record_signature_summary,
        "anchor_record_layout_candidate": anchor_record_layout,
        "partial_match_near_miss_analysis": partial_match_near_miss,
        "neighbor_relation_analysis": neighbor_relation,
        "semantic_hypothesis": semantic_hypothesis,
        "signature_components": _signature_components_summary(fixture_reports),
        "candidate_parser_rule_draft": _candidate_parser_rule_draft(),
        "rejected_single_field_rules": _rejected_single_field_rules(field_difference_summary),
        "stable_anchor_bearing_signature_candidates": _stable_anchor_bearing_signature_candidates(
            field_difference_summary
        ),
        "rejected_selector_candidates": _rejected_selector_candidates(field_difference_summary),
        "answers": _answers(fixture_reports, comparison, alignment),
    }
    report.update(_limits_payload())
    return report


def _print_text(report: dict[str, Any]) -> None:
    print("Text CPropertyExtend Anchor Context Analysis")
    print(f"policy.scope: {report['policy']['scope']}")
    print(f"policy.parser_behavior: {report['policy']['parser_behavior']}")
    print(f"truncated: {str(report.get('truncated', False)).lower()}")
    print("[Limits]")
    print(json.dumps(report.get("limits", {}), ensure_ascii=False, indent=2))
    print("[Warnings]")
    if report.get("warnings"):
        for warning in report["warnings"]:
            print(f"- {warning}")
    else:
        print("- none")
    print()
    if report.get("mode") == "safe_summary":
        print(f"heavy_sections_included: {str(report.get('summary', {}).get('heavy_sections_included', False)).lower()}")
        print("[Safe Summary Fixtures]")
        for fx in report.get("fixtures", [])[: report.get("limits", {}).get("max_output_rows", 0)]:
            print(
                f"- {fx['fixture']}: bytes={fx['bytes']} node_count={fx['node_count']} "
                f"cproperty_node_count={fx['cproperty_node_count']} cparagraphe_node_count={fx['cparagraphe_node_count']}"
            )
        return

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
    if report.get("status") == "partial":
        print(json.dumps({"status": "partial", "warnings": report.get("warnings", [])}, ensure_ascii=False, indent=2))
        return
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
    print("[Anchor vs Non-anchor Field Difference Summary]")
    print(json.dumps(report["anchor_vs_non_anchor_field_difference_summary"], ensure_ascii=False, indent=2))
    print("[Local Record Signature Summary]")
    print(json.dumps(report["local_record_signature_summary"], ensure_ascii=False, indent=2))
    print("[Anchor Record Layout Candidate]")
    print(json.dumps(report["anchor_record_layout_candidate"], ensure_ascii=False, indent=2))
    print("[Partial Match / Near Miss Analysis]")
    print(json.dumps(report["partial_match_near_miss_analysis"], ensure_ascii=False, indent=2))
    print("[Neighbor Relation Analysis]")
    print(json.dumps(report["neighbor_relation_analysis"], ensure_ascii=False, indent=2))
    print("[Semantic Hypothesis]")
    print(json.dumps(report["semantic_hypothesis"], ensure_ascii=False, indent=2))
    print("[Signature Components]")
    print(json.dumps(report["signature_components"], ensure_ascii=False, indent=2))
    print("[Candidate Parser Rule Draft]")
    print(json.dumps(report["candidate_parser_rule_draft"], ensure_ascii=False, indent=2))
    print("[Rejected Single-field Rules]")
    print(json.dumps(report["rejected_single_field_rules"], ensure_ascii=False, indent=2))
    print("[Stable Anchor-bearing Signature Candidates]")
    print(json.dumps(report["stable_anchor_bearing_signature_candidates"], ensure_ascii=False, indent=2))
    print("[Rejected Selector Candidates]")
    print(json.dumps(report["rejected_selector_candidates"], ensure_ascii=False, indent=2))
    print("[Answers]")
    print(json.dumps(report["answers"], ensure_ascii=False, indent=2))


def _print_markdown(report: dict[str, Any]) -> None:
    print("# Text CPropertyExtend Anchor Context Analysis")
    print()
    print("## Limits")
    print()
    print(f"- truncated: `{report.get('truncated', False)}`")
    print(f"- limits: `{report.get('limits', {})}`")
    print()
    print("## Warnings")
    print()
    if report.get("warnings"):
        for warning in report["warnings"]:
            print(f"- {warning}")
    else:
        print("- none")
    print()
    if report.get("mode") == "safe_summary":
        print("## Safe Summary Fixtures")
        print()
        print("| fixture | bytes | node_count | cproperty_node_count | cparagraphe_node_count |")
        print("|---|---:|---:|---:|---:|")
        for row in report.get("fixtures", [])[: report.get("limits", {}).get("max_output_rows", 0)]:
            print(
                f"| {row['fixture']} | {row['bytes']} | {row['node_count']} | "
                f"{row['cproperty_node_count']} | {row['cparagraphe_node_count']} |"
            )
        return

    if report.get("status") == "partial":
        print("## Partial Result")
        print()
        print("- analysis stopped before full comparison summaries completed")
        return
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
    print()
    print("## Anchor vs Non-anchor Field Difference Summary")
    print()
    print("| feature | type | separation | false positives | usefulness |")
    print("|---|---|---:|---:|---|")
    for row in report["anchor_vs_non_anchor_field_difference_summary"]["top_current_separators"][:12]:
        print(
            f"| {row['feature']} | {row['decoded_type']} | {row['separation_score']} | "
            f"{row['false_positive_count']} | {row['candidate_usefulness']} |"
        )
    print()
    print("## Local Record Signature Summary")
    print()
    sig = report["local_record_signature_summary"]
    print(f"- signature: `{sig['signature_name']}`")
    print(f"- matched sections: `{sig['matched_section_count']}`")
    print(f"- false positives: `{sig['false_positive_count']}`")
    print(f"- false negatives: `{sig['false_negative_count']}`")
    print(f"- parser safe: `{sig['parser_safe_candidate']}`")
    print()
    print("## Anchor Record Layout Candidate")
    print()
    print("| offset | byte range | anchor stability | candidate role | note |")
    print("|---:|---|---|---|---|")
    for row in report["anchor_record_layout_candidate"]["layout_rows"]:
        print(
            f"| {row['local_offset_from_cobdao']} | {row['byte_range']} | "
            f"{row['stability_across_anchor_bearing_sections']} | {row['candidate_role']} | "
            f"{row['interpretation_note']} |"
        )
    print()
    print("## Partial Match / Near Miss Analysis")
    print()
    near = report["partial_match_near_miss_analysis"]
    print(f"- one-field-away non-anchor sections: `{near['one_field_away_non_anchor_count']}`")
    print(f"- coordinate-like non-anchor partial sections: `{near['coordinate_like_non_anchor_partial_count']}`")
    print()
    print("## Neighbor Relation Analysis")
    print()
    neighbors = report["neighbor_relation_analysis"]
    print(f"- previous roles: `{neighbors['previous_role_distribution']}`")
    print(f"- next roles: `{neighbors['next_role_distribution']}`")
    print()
    print("## Semantic Hypothesis")
    print()
    print(f"- parser readiness: `{report['semantic_hypothesis']['parser_readiness']}`")
    print(f"- signature kind: `{report['semantic_hypothesis']['signature_kind_assessment']['current_judgment']}`")
    print()
    print("## Signature Components")
    print()
    print("| component | anchor pass | non-anchor pass | FP | FN | usefulness |")
    print("|---|---:|---:|---:|---:|---|")
    for row in report["signature_components"]:
        print(
            f"| {row['component']} | {row['anchor_bearing_pass_count']} | {row['non_anchor_pass_count']} | "
            f"{row['false_positive_count']} | {row['false_negative_count']} | {row['usefulness']} |"
        )
    print()
    print("## Candidate Parser Rule Draft")
    print()
    print(f"- status: `{report['candidate_parser_rule_draft']['status']}`")
    print(f"- would decode: {report['candidate_parser_rule_draft']['would_decode']}")
    print()
    print("## Rejected Single-field Rules")
    print()
    print("| selector | rejected | reason |")
    print("|---|---|---|")
    for row in report["rejected_single_field_rules"]:
        print(f"| {row['selector']} | {row['rejected_for_parser']} | {row['reason']} |")
    print()
    print("## Stable Anchor-bearing Signature Candidates")
    print()
    print("| candidate | false positives | false negatives | parser safe | reason |")
    print("|---|---:|---:|---|---|")
    for row in report["stable_anchor_bearing_signature_candidates"]:
        print(
            f"| {row['candidate']} | {row['false_positives']} | {row['false_negatives']} | "
            f"{row['parser_safe_candidate']} | {row['reason']} |"
        )
    print()
    print("## Rejected Selector Candidates")
    print()
    print("| selector | rejected | reason |")
    print("|---|---|---|")
    for row in report["rejected_selector_candidates"]:
        print(f"| {row['selector']} | {row['rejected_for_parser']} | {row['reason']} |")


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit CPropertyExtend anchor triple local context.")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--markdown", action="store_true")
    parser.add_argument("--max-runtime-seconds", type=int, default=MAX_RUNTIME_SECONDS)
    parser.add_argument("--max-sections", type=int, default=MAX_TOTAL_COBDAO_SECTIONS)
    parser.add_argument("--max-comparisons", type=int, default=MAX_SECTION_COMPARISONS)
    parser.add_argument("--max-output-rows", type=int, default=MAX_FIELD_DIFF_ROWS)
    parser.add_argument("--debug-limits", action="store_true")
    parser.add_argument("--deep", action="store_true")
    args = parser.parse_args()

    if args.deep:
        limits = AnalysisLimits(
            max_fixtures=min(12, MAX_FIXTURES),
            max_total_cobdao_sections=args.max_sections * 4,
            max_section_comparisons=args.max_comparisons * 4,
            max_runtime_seconds=args.max_runtime_seconds * 4,
            max_near_miss_rows=min(MAX_NEAR_MISS_ROWS * 4, args.max_output_rows * 4),
            max_signature_rows=min(MAX_SIGNATURE_ROWS * 4, args.max_output_rows * 4),
            max_field_diff_rows=args.max_output_rows * 4,
            max_output_rows=args.max_output_rows * 4,
            max_local_hex_bytes=min(64, MAX_LOCAL_HEX_BYTES),
            max_decoded_values_per_section=min(16, args.max_output_rows),
        )
    else:
        limits = AnalysisLimits(
            max_fixtures=min(DEFAULT_SAFE_MAX_FIXTURES, MAX_FIXTURES),
            max_runtime_seconds=min(DEFAULT_SAFE_MAX_RUNTIME_SECONDS, args.max_runtime_seconds),
            max_total_cobdao_sections=min(64, args.max_sections),
            max_section_comparisons=min(256, args.max_comparisons),
            max_near_miss_rows=min(DEFAULT_SAFE_MAX_OUTPUT_ROWS, args.max_output_rows),
            max_signature_rows=min(DEFAULT_SAFE_MAX_OUTPUT_ROWS, args.max_output_rows),
            max_field_diff_rows=min(DEFAULT_SAFE_MAX_OUTPUT_ROWS, args.max_output_rows),
            max_output_rows=min(DEFAULT_SAFE_MAX_OUTPUT_ROWS, args.max_output_rows),
            max_local_hex_bytes=min(64, MAX_LOCAL_HEX_BYTES),
            max_decoded_values_per_section=min(16, MAX_DECODED_VALUES_PER_SECTION),
            max_marker_scan_iterations=min(200, MAX_MARKER_SCAN_ITERATIONS),
        )
    report = build_report(limits, deep=args.deep)
    if args.debug_limits:
        report.setdefault("warnings", []).append(f"debug limits active: {report['limits']}")
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    elif args.markdown:
        _print_markdown(report)
    else:
        _print_text(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
