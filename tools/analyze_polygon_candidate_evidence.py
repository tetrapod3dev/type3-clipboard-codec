from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from type3_clipboard_codec import parse_type3_clipboard_bytes_with_parser
from type3_clipboard_codec.inspect.hex_input import hex_text_to_bytes
from type3_clipboard_codec.models.geometry import GeometryObject


REPO_ROOT = Path(__file__).resolve().parents[1]
SAMPLES_ROOT = REPO_ROOT / "tests" / "samples"
TARGETS = [
    "polygon_5_sides.txt",
    "polygon_6_sides.txt",
    "polygon_6_sides_rotated_start.txt",
    "polyline_from_polygon_5_points.txt",
    "default_rectangle.txt",
    "polyline_5_points.txt",
]
INTENDED_LABEL = {
    "polygon_5_sides.txt": "polygon_5_sides (fixture intent)",
    "polygon_6_sides.txt": "polygon_6_sides (fixture intent)",
    "polygon_6_sides_rotated_start.txt": "polygon_6_sides_rotated_start (fixture intent)",
    "polyline_from_polygon_5_points.txt": "polyline_from_polygon_5_points (fixture intent)",
    "default_rectangle.txt": "rectangle (fixture intent)",
    "polyline_5_points.txt": "polyline_5_points (fixture intent)",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze polygon candidate evidence and role assignment details.")
    parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    return parser.parse_args()


def _decode(path: Path) -> GeometryObject:
    raw_hex = path.read_text(encoding="utf-8")
    data = hex_text_to_bytes(raw_hex)
    parsed, _ = parse_type3_clipboard_bytes_with_parser(data)
    if not isinstance(parsed, GeometryObject):
        raise ValueError(f"Fixture did not decode to GeometryObject: {path.name}")
    return parsed


def _record_row(records: list[Any], idx: int) -> dict[str, Any]:
    r = records[idx]
    first = records[0]
    prev = records[idx - 1] if idx > 0 else None
    eq_first = (
        abs(r.x_m - first.x_m) <= 1e-6 and abs(r.y_m - first.y_m) <= 1e-6 and abs(r.z_m - first.z_m) <= 1e-6
    )
    eq_prev = False
    if prev is not None:
        eq_prev = abs(r.x_m - prev.x_m) <= 1e-6 and abs(r.y_m - prev.y_m) <= 1e-6 and abs(r.z_m - prev.z_m) <= 1e-6
    return {
        "index": idx + 1,
        "x_mm": round(r.x_mm, 3),
        "y_mm": round(r.y_mm, 3),
        "z_mm": round(r.z_mm, 3),
        "w": round(r.w, 6),
        "raw_tag": f"0x{r.tag:08X}",
        "assigned_role": r.role,
        "equals_first_point": eq_first,
        "equals_previous_point": eq_prev,
        "note": "unknown_role_record" if r.role == "unknown" else "",
    }


def _fixture_report(name: str) -> dict[str, Any]:
    parsed = _decode(SAMPLES_ROOT / name)
    chain = parsed.object_chains[0]
    records = chain.contour_records
    role_pattern = [r.role for r in records]
    unknown_count = len([r for r in records if r.role == "unknown"])
    first_equals_last = False
    if len(records) >= 2:
        a, b = records[0], records[-1]
        first_equals_last = (
            abs(a.x_m - b.x_m) <= 1e-6 and abs(a.y_m - b.y_m) <= 1e-6 and abs(a.z_m - b.z_m) <= 1e-6
        )

    shape_diag_rows = parsed.candidate_fields.get("shape_classification", [])
    shape_diag = shape_diag_rows[0] if shape_diag_rows else {}
    kind_observed = None
    contour_diags = chain.contour_header_diagnostics
    if contour_diags:
        kind_observed = contour_diags[0].get("selected_kind")

    return {
        "fixture": name,
        "intended_geometry_label": INTENDED_LABEL.get(name, "unknown"),
        "shape_type": chain.shape_type,
        "classification_reason": chain.shape_classification_reason,
        "classification_confidence": chain.shape_classification_confidence,
        "record_count": len(records),
        "anchor_record_count": chain.anchor_record_count,
        "control_record_count": chain.control_record_count,
        "unknown_record_count": chain.unknown_record_count if hasattr(chain, "unknown_record_count") else unknown_count,
        "role_pattern": role_pattern,
        "arc_like_control_evidence": chain.arc_like_control_evidence,
        "closed_like_evidence": chain.closed_like_evidence,
        "closed_like_evidence_sources": chain.closed_like_evidence_sources,
        "record_table": [_record_row(records, i) for i in range(len(records))],
        "closure_evidence_detail": {
            "first_equals_last": chain.first_equals_last if hasattr(chain, "first_equals_last") else first_equals_last,
            "all_roles_anchor_like": all(r in {"anchor", "unknown"} for r in role_pattern),
            "role_pattern_closed_like": chain.role_pattern_closed_like,
            "kind_observed": kind_observed,
            "any_other_signal_used": chain.closed_like_evidence_sources,
            "final_closed_like_evidence": chain.closed_like_evidence,
            "confidence_note": "provisional evidence; kind semantics and role/tag mapping are not confirmed",
        },
        "shape_diagnostics": shape_diag,
    }


def _build() -> dict[str, Any]:
    fixtures = [_fixture_report(name) for name in TARGETS]
    by_name = {f["fixture"]: f for f in fixtures}

    def _find_03_point(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
        for row in rows:
            if row["raw_tag"].endswith("03"):
                return row
        return None

    comp_a_left = by_name["polygon_6_sides.txt"]
    comp_a_right = by_name["polygon_6_sides_rotated_start.txt"]
    left_03 = _find_03_point(comp_a_left["record_table"])
    right_03 = _find_03_point(comp_a_right["record_table"])

    comp_b_left = by_name["polygon_5_sides.txt"]
    comp_b_right = by_name["polyline_from_polygon_5_points.txt"]

    return {
        "policy": "evidence-first audit; polygon_candidate remains provisional",
        "fixtures": fixtures,
        "comparisons": {
            "polygon_6_vs_rotated_start": {
                "base_fixture": "polygon_6_sides.txt",
                "rotated_fixture": "polygon_6_sides_rotated_start.txt",
                "base_unknown_03_point": left_03,
                "rotated_unknown_03_point": right_03,
                "observation": (
                    "0x03 occurrence remains present; coordinate/record-position dependency is observed-only and unresolved."
                ),
                "confidence": "provisional",
            },
            "polygon5_vs_polyline_from_polygon5": {
                "closed_fixture": "polygon_5_sides.txt",
                "open_fixture": "polyline_from_polygon_5_points.txt",
                "closed_unknown_03_count": comp_b_left["unknown_record_count"],
                "open_unknown_03_count": comp_b_right["unknown_record_count"],
                "closed_shape_type": comp_b_left["shape_type"],
                "open_shape_type": comp_b_right["shape_type"],
                "observation": (
                    "0x03 remains present in both fixtures with current parser output; closed/open dependency is unresolved."
                ),
                "confidence": "provisional",
            },
        },
    }


def _print_text(report: dict[str, Any]) -> None:
    print("Polygon Candidate Evidence Analysis")
    print(f"policy: {report['policy']}")
    for item in report["fixtures"]:
        print(f"\n[{item['fixture']}]")
        print(
            f"intent={item['intended_geometry_label']} shape={item['shape_type']} "
            f"reason={item['classification_reason']} confidence={item['classification_confidence']}"
        )
        print(
            f"records={item['record_count']} anchor={item['anchor_record_count']} "
            f"control={item['control_record_count']} unknown={item['unknown_record_count']}"
        )
        print(
            f"role_pattern={item['role_pattern']} arc_like_control={item['arc_like_control_evidence']} "
            f"closed_like={item['closed_like_evidence']} sources={item['closed_like_evidence_sources']}"
        )
        c = item["closure_evidence_detail"]
        print(
            "closure_detail: "
            f"first_equals_last={c['first_equals_last']} all_roles_anchor_like={c['all_roles_anchor_like']} "
            f"role_pattern_closed_like={c['role_pattern_closed_like']} kind_observed={c['kind_observed']} "
            f"final_closed_like={c['final_closed_like_evidence']}"
        )
        print("record_table:")
        for row in item["record_table"]:
            print(
                f"  idx={row['index']} xyz=({row['x_mm']},{row['y_mm']},{row['z_mm']}) w={row['w']} "
                f"tag={row['raw_tag']} role={row['assigned_role']} "
                f"eq_first={row['equals_first_point']} eq_prev={row['equals_previous_point']} note={row['note']}"
            )
    print("\n[Comparison: polygon_6_sides vs polygon_6_sides_rotated_start]")
    c1 = report["comparisons"]["polygon_6_vs_rotated_start"]
    print(f"base_03={c1['base_unknown_03_point']}")
    print(f"rotated_03={c1['rotated_unknown_03_point']}")
    print(f"observation={c1['observation']} confidence={c1['confidence']}")
    print("\n[Comparison: polygon_5_sides vs polyline_from_polygon_5_points]")
    c2 = report["comparisons"]["polygon5_vs_polyline_from_polygon5"]
    print(
        f"closed_unknown_03_count={c2['closed_unknown_03_count']} "
        f"open_unknown_03_count={c2['open_unknown_03_count']} "
        f"closed_shape={c2['closed_shape_type']} open_shape={c2['open_shape_type']}"
    )
    print(f"observation={c2['observation']} confidence={c2['confidence']}")


def main() -> int:
    args = parse_args()
    report = _build()
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        _print_text(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
