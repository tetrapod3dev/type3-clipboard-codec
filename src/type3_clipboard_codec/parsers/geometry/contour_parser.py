import math
import struct
from typing import List, Optional, Tuple

from ...models.geometry import BBox3D, ContourPoint
from ...utils.bytes_reader import BytesReader
from ..common import read_contour_points


def is_plausible_contour_count(count: int) -> bool:
    return count in {2, 3, 4, 8, 12}


def analyze_contour_header_candidates(payload: bytes) -> Tuple[Optional[List[Tuple[int, int, int]]], List[dict]]:
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
            "confidence": "provisional",
        }

        found_for_this_marker = False
        for shift in candidate_shifts:
            header_start = base + shift
            candidate = {
                "shift": shift,
                "header_offset": header_start,
                "kind": None,
                "count": None,
                "plausible": False,
                "rejection_reason": None,
                "raw_8b_hex": None,
            }
            if header_start + 8 > len(payload):
                candidate["rejection_reason"] = "header_out_of_bounds"
                marker_diag["candidates"].append(candidate)
                continue

            try:
                candidate["raw_8b_hex"] = payload[header_start : header_start + 8].hex()
                kind = struct.unpack("<I", payload[header_start : header_start + 4])[0]
                count = struct.unpack("<I", payload[header_start + 4 : header_start + 8])[0]
                candidate["kind"] = kind
                candidate["count"] = count
                candidate["plausible"] = is_plausible_contour_count(count)
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
