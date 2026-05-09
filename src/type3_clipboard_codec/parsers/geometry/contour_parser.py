import math
import struct
from typing import List, Optional, Tuple

from ...models.geometry import BBox3D, ContourPoint
from ...utils.bytes_reader import BytesReader
from ..common import read_contour_points


def is_plausible_contour_count(count: int) -> bool:
    return count in {2, 3, 4, 8, 12}


def read_contour_header(payload: bytes) -> Optional[List[Tuple[int, int, int]]]:
    """
    Conservatively locates probable contour headers.
    Returns a list of all plausible (kind, count, offset) tuples found.
    """
    marker = b"CObDao"
    idx = 0
    found_headers = []
    while True:
        marker_pos = payload.find(marker, idx)
        if marker_pos == -1:
            break

        base = marker_pos + len(marker)
        candidate_shifts = [8, 14, 12, 16, 20]

        found_for_this_marker = False
        for shift in candidate_shifts:
            header_start = base + shift
            if header_start + 8 > len(payload):
                continue

            try:
                kind = struct.unpack("<I", payload[header_start : header_start + 4])[0]
                count = struct.unpack("<I", payload[header_start + 4 : header_start + 8])[0]

                if is_plausible_contour_count(count):
                    offset = header_start + 8
                    if not any(h[2] == offset for h in found_headers):
                        found_headers.append((kind, count, offset))

                    idx = offset
                    found_for_this_marker = True
                    break
            except Exception:
                continue

        if not found_for_this_marker:
            idx = marker_pos + 1

    return found_headers if found_headers else None


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
