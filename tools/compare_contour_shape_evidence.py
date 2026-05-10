from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from type3_clipboard_codec import parse_type3_clipboard_bytes_with_parser
from type3_clipboard_codec.inspect.hex_input import hex_text_to_bytes
from type3_clipboard_codec.models.geometry import GeometryObject, Type3ObjectChain
from type3_clipboard_codec.parsers.geometry.shape_classifier import classify_shape_type


REPO_ROOT = Path(__file__).resolve().parents[1]
SAMPLES_ROOT = REPO_ROOT / "tests" / "samples"

FIXTURE_INTENT: dict[str, dict[str, str]] = {
    "default_circular_arc.txt": {"ground_truth_intent": "circular_arc_intent", "open_or_closed_intent": "open"},
    "polyline_2_points.txt": {"ground_truth_intent": "polyline_2_points_intent", "open_or_closed_intent": "open"},
    "polyline_3_points.txt": {"ground_truth_intent": "polyline_3_points_intent", "open_or_closed_intent": "open"},
    "polyline_5_points.txt": {"ground_truth_intent": "polyline_5_points_intent", "open_or_closed_intent": "open"},
    "polygon_5_sides.txt": {"ground_truth_intent": "polygon_5_sides_intent", "open_or_closed_intent": "closed"},
    "polygon_6_sides.txt": {"ground_truth_intent": "polygon_6_sides_intent", "open_or_closed_intent": "closed"},
}

COMPARISON_SETS = [
    ("A", "same_count_3_different_intent", ["default_circular_arc.txt", "polyline_3_points.txt"]),
    ("B", "same_count_5_open_vs_closed", ["polyline_5_points.txt", "polygon_5_sides.txt"]),
    ("C", "closed_polygon_count_extension", ["polygon_5_sides.txt", "polygon_6_sides.txt"]),
    ("D", "aux_polyline2_vs_arc", ["polyline_2_points.txt", "default_circular_arc.txt"]),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare contour shape evidence across selected fixtures.")
    parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    return parser.parse_args()


def _decode_fixture(path: Path) -> GeometryObject:
    raw_hex = path.read_text(encoding="utf-8")
    data = hex_text_to_bytes(raw_hex)
    parsed, _ = parse_type3_clipboard_bytes_with_parser(data)
    if not isinstance(parsed, GeometryObject):
        raise ValueError(f"Fixture did not decode to GeometryObject: {path.name}")
    return parsed


def _first_chain(parsed: GeometryObject) -> Type3ObjectChain:
    if not parsed.object_chains:
        raise ValueError("No object chain found.")
    return parsed.object_chains[0]


def _selected_diag(parsed: GeometryObject) -> dict[str, Any] | None:
    blocks = parsed.candidate_fields.get("contour_header_diagnostics", [])
    for block in blocks:
        for diag in block.get("diagnostics", []):
            if diag.get("selected_shift") is not None:
                return diag
    return None


def _candidate_shift8_raw_counts(parsed: GeometryObject) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    blocks = parsed.candidate_fields.get("contour_header_diagnostics", [])
    for block in blocks:
        for diag in block.get("diagnostics", []):
            for cand in diag.get("candidates", []):
                if cand.get("shift") == 8:
                    out.append(
                        {
                            "kind": cand.get("kind"),
                            "count": cand.get("count"),
                            "raw_8b_hex": cand.get("raw_8b_hex"),
                            "plausible": cand.get("plausible"),
                            "rejection_reason": cand.get("rejection_reason"),
                        }
                    )
    return out


def _bbox_mm(chain: Type3ObjectChain) -> dict[str, float] | None:
    if chain.bbox is None:
        return None
    return {
        "xmin": round(chain.bbox.xmin_mm, 3),
        "ymin": round(chain.bbox.ymin_mm, 3),
        "xmax": round(chain.bbox.xmax_mm, 3),
        "ymax": round(chain.bbox.ymax_mm, 3),
    }


def _records(chain: Type3ObjectChain) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for idx, rec in enumerate(chain.contour_records, start=1):
        rows.append(
            {
                "index": idx,
                "x_mm": round(rec.x_mm, 3),
                "y_mm": round(rec.y_mm, 3),
                "z_mm": round(rec.z_mm, 3),
                "w": rec.w,
                "tag_raw_hex": f"0x{rec.tag:08X}",
                "role": rec.role,
            }
        )
    return rows


def _shape_result(chain: Type3ObjectChain) -> str:
    return classify_shape_type(chain.contour_records, chain.bbox, chain.markers)


def _first_last_equal(chain: Type3ObjectChain, tol_mm: float = 1e-3) -> bool | None:
    if not chain.contour_records:
        return None
    a = chain.contour_records[0]
    b = chain.contour_records[-1]
    return (
        abs(a.x_mm - b.x_mm) <= tol_mm
        and abs(a.y_mm - b.y_mm) <= tol_mm
        and abs(a.z_mm - b.z_mm) <= tol_mm
    )


def _fixture_row(name: str) -> dict[str, Any]:
    parsed = _decode_fixture(SAMPLES_ROOT / name)
    chain = _first_chain(parsed)
    selected = _selected_diag(parsed)
    intent = FIXTURE_INTENT.get(name, {"ground_truth_intent": "unknown", "open_or_closed_intent": "unknown"})
    record_rows = _records(chain)
    anchor_count = sum(1 for r in record_rows if r["role"] == "anchor")
    control_count = sum(1 for r in record_rows if r["role"] == "control")
    role_pattern = [r["role"] for r in record_rows]
    return {
        "fixture": name,
        "ground_truth_intent": intent["ground_truth_intent"],
        "open_or_closed_intent": intent["open_or_closed_intent"],
        "selected_shift": selected.get("selected_shift") if selected else None,
        "selected_kind": selected.get("selected_kind") if selected else None,
        "selected_count": selected.get("selected_count") if selected else None,
        "selected_raw_header_hex": selected.get("selected_raw_header_hex") if selected else None,
        "raw_count_candidates_shift8": _candidate_shift8_raw_counts(parsed),
        "parsed_record_count": len(chain.contour_records),
        "current_classifier_result": _shape_result(chain),
        "contour_bbox_mm": _bbox_mm(chain),
        "records": record_rows,
        "summary": {
            "anchor_count": anchor_count,
            "control_count": control_count,
            "role_tag_pattern": role_pattern,
            "first_last_point_equal": _first_last_equal(chain),
            "open_closed_evidence_candidate": (
                "likely_closed_if_first_last_equal"
                if _first_last_equal(chain) is True
                else "likely_open_or_non-explicit-close"
            ),
            "note": "diagnostic-only evidence; contour semantics remain provisional",
        },
    }


def _build_report() -> dict[str, Any]:
    groups = []
    for key, title, fixtures in COMPARISON_SETS:
        groups.append(
            {
                "set_id": key,
                "title": title,
                "fixtures": [_fixture_row(name) for name in fixtures],
            }
        )
    return {
        "policy": {
            "absolute_offset": "diagnostic only",
            "count_gate_status": "known incomplete whitelist",
            "semantic_status": "provisional",
        },
        "comparison_sets": groups,
    }


def _print_text(report: dict[str, Any]) -> None:
    print("Type3 Contour Shape Evidence Comparison")
    print("policy: absolute offset is diagnostic only; semantic interpretation remains provisional")
    print("count gate status: known incomplete whitelist")
    print()
    for group in report["comparison_sets"]:
        print(f"[Set {group['set_id']}] {group['title']}")
        for row in group["fixtures"]:
            print(
                f"- {row['fixture']}: intent={row['ground_truth_intent']} ({row['open_or_closed_intent']}), "
                f"selected_shift={row['selected_shift']}, selected_kind={row['selected_kind']}, "
                f"selected_count={row['selected_count']}, selected_raw={row['selected_raw_header_hex']}, "
                f"parsed_records={row['parsed_record_count']}, classifier={row['current_classifier_result']}"
            )
            raw_counts = ", ".join(
                f"{item.get('count')}[{item.get('raw_8b_hex')}]/{item.get('rejection_reason') or 'accepted'}"
                for item in row["raw_count_candidates_shift8"]
            )
            print(f"  shift8_raw_candidates: {raw_counts}")
            print(
                f"  summary: anchors={row['summary']['anchor_count']}, controls={row['summary']['control_count']}, "
                f"first_last_equal={row['summary']['first_last_point_equal']}, "
                f"open_closed_evidence={row['summary']['open_closed_evidence_candidate']}"
            )
        print()


def main() -> int:
    args = parse_args()
    report = _build_report()
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        _print_text(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
