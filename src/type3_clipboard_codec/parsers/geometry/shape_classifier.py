from typing import List, Optional, Sequence

from ...models.geometry import BBox3D, ContourPoint


def classify_shape_type(
    contour_records: Sequence[ContourPoint],
    bbox: Optional[BBox3D],
    markers: Optional[Sequence[str]] = None,
) -> str:
    """
    Thin shape classification helper that preserves current heuristic behavior.
    """
    _ = markers  # reserved for future marker-aware heuristics
    count = len(contour_records)
    anchors = len([r for r in contour_records if r.role == "anchor"])
    controls = len([r for r in contour_records if r.role == "control"])

    if count == 4:
        return "rectangle"
    if count == 8:
        if bbox and abs(bbox.width_m - bbox.height_m) < 0.001:
            return "circle"
        if anchors == 4 and controls == 4:
            return "rounded_rectangle"
    if count == 12:
        return "rounded_rectangle"
    if count == 3:
        return "circular_arc"
    if count == 2:
        return "circular_arc"
    return "geometry"


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
