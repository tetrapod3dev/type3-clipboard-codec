import math
import struct
from typing import List, Optional, Tuple

from ...models.geometry import BBox3D, ContourPoint
from ...utils.bytes_reader import BytesReader
from ..common import read_contour_points
from .contour_candidate_validator import validate_contour_header_candidate


def is_plausible_contour_count(count: int) -> bool:
    return count in {2, 3, 4, 8, 12}


def analyze_contour_header_candidates(
    payload: bytes,
    *,
    bbox: Optional[BBox3D] = None,
    stride: int = 36,
    max_safe_contour_count: int = 4096,
) -> Tuple[Optional[List[Tuple[int, int, int]]], List[dict]]:
    """
    Analyze contour-header candidates while preserving current selection behavior.
    Returns:
    - selected headers: list[(kind, count, offset)] or None
    - diagnostics: marker-by-marker candidate/selection traces
    """
    marker = b"CObDao"
    idx = 0
    found_headers: List[Tuple[int, int, int]] = []
    diagnostics: List[dict] = []
    candidate_shifts = [8, 14, 12, 16, 20]

    while True:
        marker_pos = payload.find(marker, idx)
        if marker_pos == -1:
            break

        base = marker_pos + len(marker)
        marker_diag = {
            "marker_offset": marker_pos,
            "candidate_shifts": list(candidate_shifts),
            "candidates": [],
            "selected_shift": None,
            "selected_header_offset": None,
            "selected_kind": None,
            "selected_count": None,
            "selected_payload_offset": None,
            "selected_raw_header_hex": None,
            "selection_reason": None,
            "legacy_selected_candidate": None,
            "structurally_valid_candidates": [],
            "structural_recommended_candidate": None,
            "selection_mode": "legacy_count_whitelist",
            "structural_policy_status": "diagnostic_only",
            "confidence": "provisional",
        }

        found_for_this_marker = False
        structural_candidate_rows: List[dict] = []
        for shift in candidate_shifts:
            header_start = base + shift
            structural = validate_contour_header_candidate(
                payload=payload,
                header_offset=header_start,
                stride=stride,
                bbox=bbox,
                max_safe_contour_count=max_safe_contour_count,
            )
            candidate = {
                "shift": shift,
                "header_offset": header_start,
                "kind": None,
                "count": None,
                "plausible": False,
                "legacy_plausible": False,
                "rejection_reason": None,
                "raw_8b_hex": structural.get("raw_8b_hex"),
                "structural_valid": structural.get("structural_valid"),
                "structural_score": structural.get("structural_score"),
                "structural_failure_reasons": structural.get("structural_failure_reasons", []),
                "record_region_end_offset": structural.get("record_region_end_offset"),
                "record_decode_status": structural.get("record_decode_status"),
                "record_decode_ok": structural.get("record_decode_ok"),
                "bbox_consistency_status": structural.get("bbox_consistency_status"),
            }
            structural_candidate_rows.append(candidate)
            if header_start + 8 > len(payload):
                candidate["rejection_reason"] = "header_out_of_bounds"
                marker_diag["candidates"].append(candidate)
                continue

            try:
                kind = struct.unpack("<I", payload[header_start : header_start + 4])[0]
                count = struct.unpack("<I", payload[header_start + 4 : header_start + 8])[0]
                candidate["kind"] = kind
                candidate["count"] = count
                candidate["plausible"] = is_plausible_contour_count(count)
                candidate["legacy_plausible"] = candidate["plausible"]
                if not candidate["plausible"]:
                    candidate["rejection_reason"] = "count_not_plausible"
                    marker_diag["candidates"].append(candidate)
                    continue

                offset = header_start + 8
                candidate["selected_payload_offset"] = offset
                if any(h[2] == offset for h in found_headers):
                    candidate["rejection_reason"] = "duplicate_selected_offset"
                    marker_diag["candidates"].append(candidate)
                    continue

                found_headers.append((kind, count, offset))
                marker_diag["selected_shift"] = shift
                marker_diag["selected_header_offset"] = header_start
                marker_diag["selected_kind"] = kind
                marker_diag["selected_count"] = count
                marker_diag["selected_payload_offset"] = offset
                marker_diag["selected_raw_header_hex"] = candidate["raw_8b_hex"]
                marker_diag["legacy_selected_candidate"] = {
                    "shift": shift,
                    "header_offset": header_start,
                    "kind": kind,
                    "count": count,
                    "payload_offset": offset,
                    "raw_8b_hex": candidate["raw_8b_hex"],
                }
                marker_diag["selection_reason"] = "first_plausible_shift_with_unique_offset"
                marker_diag["candidates"].append(candidate)
                idx = offset
                found_for_this_marker = True
                break
            except Exception:
                candidate["rejection_reason"] = "unpack_error"
                marker_diag["candidates"].append(candidate)
                continue

        if not found_for_this_marker:
            marker_diag["selection_reason"] = "no_plausible_candidate"
            idx = marker_pos + 1

        marker_diag["structurally_valid_candidates"] = [
            {
                "shift": c["shift"],
                "header_offset": c["header_offset"],
                "kind": c.get("kind"),
                "count": c.get("count"),
                "raw_8b_hex": c.get("raw_8b_hex"),
                "structural_score": c.get("structural_score"),
                "record_region_end_offset": c.get("record_region_end_offset"),
                "bbox_consistency_status": c.get("bbox_consistency_status"),
            }
            for c in structural_candidate_rows
            if c.get("structural_valid")
        ]
        if marker_diag["structurally_valid_candidates"]:
            shift_order = {value: idx for idx, value in enumerate(candidate_shifts)}
            sorted_valid = sorted(
                marker_diag["structurally_valid_candidates"],
                key=lambda item: (
                    -(item.get("structural_score") or -1),
                    shift_order.get(item.get("shift"), 9999),
                    item.get("header_offset") if item.get("header_offset") is not None else 10**9,
                ),
            )
            marker_diag["structural_recommended_candidate"] = sorted_valid[0]

        diagnostics.append(marker_diag)

    return (found_headers if found_headers else None), diagnostics


def read_contour_header(payload: bytes) -> Optional[List[Tuple[int, int, int]]]:
    """
    Conservatively locates probable contour headers.
    Returns a list of all plausible (kind, count, offset) tuples found.
    """
    found_headers, _diagnostics = analyze_contour_header_candidates(payload)
    return found_headers


def read_contour_records(
    payload: bytes,
    offset: int,
    count: int,
    stride: int,
) -> List[ContourPoint]:
    total_size = count * stride
    if offset < 0 or offset + total_size > len(payload):
        return []

    local_reader = BytesReader(payload[offset:])
    try:
        return read_contour_points(local_reader, count, stride=stride)
    except Exception:
        return []


def validate_records(
    records: List[ContourPoint],
    bbox: Optional[BBox3D],
    max_reasonable_coord_m: float,
) -> bool:
    if not records:
        return False

    for r in records:
        if not (
            math.isfinite(r.x_m)
            and math.isfinite(r.y_m)
            and math.isfinite(r.z_m)
            and math.isfinite(r.w)
        ):
            return False

        if abs(r.x_m) > max_reasonable_coord_m:
            return False
        if abs(r.y_m) > max_reasonable_coord_m:
            return False
        if abs(r.z_m) > max_reasonable_coord_m:
            return False

    if all(
        abs(r.x_m) < 1e-12 and abs(r.y_m) < 1e-12 and abs(r.z_m) < 1e-12
        for r in records
    ):
        return False

    if bbox is None:
        return True

    xs = [r.x_m for r in records]
    ys = [r.y_m for r in records]
    px_min = min(xs)
    px_max = max(xs)
    py_min = min(ys)
    py_max = max(ys)

    margin = 0.05
    if px_max < bbox.xmin_m - margin:
        return False
    if px_min > bbox.xmax_m + margin:
        return False
    if py_max < bbox.ymin_m - margin:
        return False
    if py_min > bbox.ymax_m + margin:
        return False

    return True


def assign_semantic_roles(records: List[ContourPoint]) -> None:
    for r in records:
        low = r.tag & 0xFF
        if low == 0x0C:
            r.role = "control"
        elif low in (0x0D, 0x0F):
            r.role = "anchor"
        else:
            r.role = "unknown"
