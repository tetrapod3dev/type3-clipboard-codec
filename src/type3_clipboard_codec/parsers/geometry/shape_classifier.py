from __future__ import annotations

from typing import Any, List, Optional, Sequence

from ...models.geometry import BBox3D, ContourPoint


def _is_arc_like_control(record: ContourPoint) -> bool:
    return abs(record.w - 0.707106) <= 0.1


def classify_shape_with_evidence(
    contour_records: Sequence[ContourPoint],
    bbox: Optional[BBox3D],
    markers: Optional[Sequence[str]] = None,
) -> dict[str, Any]:
    _ = markers
    records = list(contour_records)
    count = len(records)
    anchors = [r for r in records if r.role == "anchor"]
    controls = [r for r in records if r.role == "control"]
    unknowns = [r for r in records if r.role == "unknown"]
    role_pattern = [r.role for r in records]
    first_last_equal = False
    if count >= 2:
        first, last = records[0], records[-1]
        first_last_equal = (
            abs(first.x_m - last.x_m) <= 1e-6
            and abs(first.y_m - last.y_m) <= 1e-6
            and abs(first.z_m - last.z_m) <= 1e-6
        )

    arc_like_control_evidence = any(_is_arc_like_control(c) for c in controls)
    role_pattern_closed_like = (
        count >= 5
        and not controls
        and (len(anchors) + len(unknowns) == count)
        and len(unknowns) <= 1
        and len(anchors) >= 4
    )
    closed_like_evidence = first_last_equal or role_pattern_closed_like
    closed_like_evidence_sources: list[str] = []
    if first_last_equal:
        closed_like_evidence_sources.append("first_equals_last")
    if role_pattern_closed_like:
        closed_like_evidence_sources.append("role_pattern_closed_like")

    if count == 4:
        return {
            "shape_type": "rectangle",
            "reason": "four_record_contour_pattern",
            "confidence": "confirmed",
            "role_pattern": role_pattern,
            "anchor_record_count": len(anchors),
            "control_record_count": len(controls),
            "unknown_record_count": len(unknowns),
            "arc_like_control_evidence": arc_like_control_evidence,
            "closed_like_evidence": closed_like_evidence,
            "closed_like_evidence_sources": closed_like_evidence_sources,
            "first_equals_last": first_last_equal,
            "role_pattern_closed_like": role_pattern_closed_like,
        }

    if count == 8:
        if bbox and abs(bbox.width_m - bbox.height_m) < 0.001:
            return {
                "shape_type": "circle",
                "reason": "eight_record_square_bbox_pattern",
                "confidence": "confirmed",
                "role_pattern": role_pattern,
                "anchor_record_count": len(anchors),
                "control_record_count": len(controls),
                "unknown_record_count": len(unknowns),
                "arc_like_control_evidence": arc_like_control_evidence,
                "closed_like_evidence": True,
                "closed_like_evidence_sources": ["circle_pattern"],
                "first_equals_last": first_last_equal,
                "role_pattern_closed_like": role_pattern_closed_like,
            }
        if len(anchors) == 4 and len(controls) == 4:
            return {
                "shape_type": "rounded_rectangle",
                "reason": "eight_record_anchor_control_alternation_pattern",
                "confidence": "confirmed",
                "role_pattern": role_pattern,
                "anchor_record_count": len(anchors),
                "control_record_count": len(controls),
                "unknown_record_count": len(unknowns),
                "arc_like_control_evidence": arc_like_control_evidence,
                "closed_like_evidence": True,
                "closed_like_evidence_sources": ["rounded_rectangle_pattern"],
                "first_equals_last": first_last_equal,
                "role_pattern_closed_like": role_pattern_closed_like,
            }

    if count == 12:
        return {
            "shape_type": "rounded_rectangle",
            "reason": "twelve_record_rounded_rectangle_pattern",
            "confidence": "confirmed",
            "role_pattern": role_pattern,
            "anchor_record_count": len(anchors),
            "control_record_count": len(controls),
            "unknown_record_count": len(unknowns),
            "arc_like_control_evidence": arc_like_control_evidence,
            "closed_like_evidence": True,
            "closed_like_evidence_sources": ["rounded_rectangle_pattern"],
            "first_equals_last": first_last_equal,
            "role_pattern_closed_like": role_pattern_closed_like,
        }

    if (
        count >= 3
        and len(controls) >= 1
        and len(anchors) >= 2
        and not first_last_equal
        and arc_like_control_evidence
    ):
        return {
            "shape_type": "circular_arc",
            "reason": "anchor_control_arc_like_w_pattern",
            "confidence": "confirmed",
            "role_pattern": role_pattern,
            "anchor_record_count": len(anchors),
            "control_record_count": len(controls),
            "unknown_record_count": len(unknowns),
            "arc_like_control_evidence": True,
            "closed_like_evidence": False,
            "closed_like_evidence_sources": [],
            "first_equals_last": first_last_equal,
            "role_pattern_closed_like": role_pattern_closed_like,
        }

    if count >= 3 and len(controls) == 0 and (closed_like_evidence or first_last_equal):
        return {
            "shape_type": "polygon_candidate",
            "reason": "closed_like_without_control_evidence",
            "confidence": "provisional",
            "role_pattern": role_pattern,
            "anchor_record_count": len(anchors),
            "control_record_count": len(controls),
            "unknown_record_count": len(unknowns),
            "arc_like_control_evidence": arc_like_control_evidence,
            "closed_like_evidence": True,
            "closed_like_evidence_sources": closed_like_evidence_sources,
            "first_equals_last": first_last_equal,
            "role_pattern_closed_like": role_pattern_closed_like,
        }

    if count >= 2 and len(controls) == 0 and not first_last_equal:
        return {
            "shape_type": "polyline_candidate",
            "reason": "open_like_without_control_evidence",
            "confidence": "provisional",
            "role_pattern": role_pattern,
            "anchor_record_count": len(anchors),
            "control_record_count": len(controls),
            "unknown_record_count": len(unknowns),
            "arc_like_control_evidence": arc_like_control_evidence,
            "closed_like_evidence": False,
            "closed_like_evidence_sources": [],
            "first_equals_last": first_last_equal,
            "role_pattern_closed_like": role_pattern_closed_like,
        }

    return {
        "shape_type": "geometry",
        "reason": "no_strong_shape_pattern",
        "confidence": "provisional",
        "role_pattern": role_pattern,
        "anchor_record_count": len(anchors),
        "control_record_count": len(controls),
        "unknown_record_count": len(unknowns),
        "arc_like_control_evidence": arc_like_control_evidence,
        "closed_like_evidence": closed_like_evidence,
        "closed_like_evidence_sources": closed_like_evidence_sources,
        "first_equals_last": first_last_equal,
        "role_pattern_closed_like": role_pattern_closed_like,
    }


def classify_shape_type(
    contour_records: Sequence[ContourPoint],
    bbox: Optional[BBox3D],
    markers: Optional[Sequence[str]] = None,
) -> str:
    return classify_shape_with_evidence(contour_records, bbox, markers)["shape_type"]


def bbox_from_contour_records(records: List[ContourPoint]) -> BBox3D:
    xs = [r.x_m for r in records]
    ys = [r.y_m for r in records]
    zs = [r.z_m for r in records]
    return BBox3D(
        xmin_m=min(xs),
        ymin_m=min(ys),
        zmin_m=min(zs),
        xmax_m=max(xs),
        ymax_m=max(ys),
        zmax_m=max(zs),
    )
