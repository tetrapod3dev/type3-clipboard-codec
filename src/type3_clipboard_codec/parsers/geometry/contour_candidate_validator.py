from __future__ import annotations

import math
import struct
from typing import Any, Optional

from ...models.geometry import BBox3D
from ...utils.bytes_reader import BytesReader
from ..common import read_contour_points


def validate_contour_header_candidate(
    *,
    payload: bytes,
    header_offset: int,
    stride: int,
    bbox: Optional[BBox3D],
    max_safe_contour_count: int,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "header_offset_in_bounds": False,
        "kind_count_decode_ok": False,
        "count_positive": False,
        "count_within_safety_limit": False,
        "record_region_in_bounds": False,
        "record_region_end_offset": None,
        "record_decode_ok": False,
        "record_decode_status": "not_attempted",
        "all_coordinates_finite": False,
        "bbox_consistency_status": "unknown_no_bbox",
        "structural_valid": False,
        "structural_failure_reasons": [],
        "structural_score": 0,
        "kind": None,
        "count": None,
        "raw_8b_hex": None,
    }

    if header_offset < 0 or header_offset + 8 > len(payload):
        result["structural_failure_reasons"].append("header_out_of_bounds")
        return result

    result["header_offset_in_bounds"] = True
    header_8b = payload[header_offset : header_offset + 8]
    result["raw_8b_hex"] = header_8b.hex()

    try:
        kind = struct.unpack("<I", header_8b[:4])[0]
        count = struct.unpack("<I", header_8b[4:8])[0]
        result["kind"] = kind
        result["count"] = count
        result["kind_count_decode_ok"] = True
    except Exception:
        result["structural_failure_reasons"].append("kind_count_decode_failed")
        return result

    if result["count"] > 0:
        result["count_positive"] = True
    else:
        result["structural_failure_reasons"].append("count_not_positive")

    if result["count"] <= max_safe_contour_count:
        result["count_within_safety_limit"] = True
    else:
        result["structural_failure_reasons"].append("count_exceeds_safety_limit")

    if not (result["count_positive"] and result["count_within_safety_limit"]):
        return result

    record_start_offset = header_offset + 8
    record_region_end_offset = record_start_offset + (result["count"] * stride)
    result["record_region_end_offset"] = record_region_end_offset
    if record_region_end_offset <= len(payload):
        result["record_region_in_bounds"] = True
    else:
        result["structural_failure_reasons"].append("record_region_out_of_bounds")
        return result

    try:
        local_reader = BytesReader(payload[record_start_offset:])
        records = read_contour_points(local_reader, int(result["count"]), stride=stride)
        result["record_decode_ok"] = True
        result["record_decode_status"] = "ok"
    except Exception:
        result["record_decode_status"] = "decode_failed"
        result["structural_failure_reasons"].append("record_decode_failed")
        return result

    finite_ok = all(
        math.isfinite(r.x_m)
        and math.isfinite(r.y_m)
        and math.isfinite(r.z_m)
        and math.isfinite(r.w)
        for r in records
    )
    result["all_coordinates_finite"] = finite_ok
    if not finite_ok:
        result["structural_failure_reasons"].append("non_finite_coordinates")

    # Soft signal only: never hard-reject in this phase.
    if bbox is None:
        result["bbox_consistency_status"] = "unknown_no_bbox"
    else:
        xs = [r.x_m for r in records]
        ys = [r.y_m for r in records]
        if not xs or not ys:
            result["bbox_consistency_status"] = "not_applicable_no_records"
        else:
            margin = 0.05
            overlaps = not (
                max(xs) < bbox.xmin_m - margin
                or min(xs) > bbox.xmax_m + margin
                or max(ys) < bbox.ymin_m - margin
                or min(ys) > bbox.ymax_m + margin
            )
            result["bbox_consistency_status"] = "consistent" if overlaps else "mismatch_soft"

    result["structural_valid"] = (
        result["header_offset_in_bounds"]
        and result["kind_count_decode_ok"]
        and result["count_positive"]
        and result["count_within_safety_limit"]
        and result["record_region_in_bounds"]
        and result["record_decode_ok"]
        and result["all_coordinates_finite"]
    )
    result["structural_score"] = score_contour_header_candidate(result)
    return result


def score_contour_header_candidate(candidate_result: dict[str, Any]) -> int:
    score = 0
    if candidate_result.get("header_offset_in_bounds"):
        score += 1
    if candidate_result.get("kind_count_decode_ok"):
        score += 1
    if candidate_result.get("count_positive"):
        score += 1
    if candidate_result.get("count_within_safety_limit"):
        score += 1
    if candidate_result.get("record_region_in_bounds"):
        score += 1
    if candidate_result.get("record_decode_ok"):
        score += 1
    if candidate_result.get("all_coordinates_finite"):
        score += 1
    if candidate_result.get("bbox_consistency_status") == "consistent":
        score += 1
    return score
