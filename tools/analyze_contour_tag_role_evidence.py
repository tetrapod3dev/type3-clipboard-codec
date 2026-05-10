from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from type3_clipboard_codec import parse_type3_clipboard_bytes_with_parser
from type3_clipboard_codec.inspect.hex_input import hex_text_to_bytes
from type3_clipboard_codec.models.geometry import GeometryObject


REPO_ROOT = Path(__file__).resolve().parents[1]
SAMPLES_ROOT = REPO_ROOT / "tests" / "samples"
TEXT_SAMPLES_ROOT = SAMPLES_ROOT / "text"
FOCUS_FIXTURES = [
    "default_rectangle.txt",
    "default_circle.txt",
    "default_circular_arc.txt",
    "default_rounded_rectangle.txt",
    "polyline_2_points.txt",
    "polyline_3_points.txt",
    "polyline_5_points.txt",
    "polygon_5_sides.txt",
    "polygon_6_sides.txt",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze contour tag/role evidence across fixtures.")
    parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    parser.add_argument("--markdown", action="store_true", help="Emit markdown output.")
    parser.add_argument("--include-text", action="store_true", help="Include text fixtures.")
    return parser.parse_args()


def _iter_fixture_paths(include_text: bool) -> list[Path]:
    paths = sorted(SAMPLES_ROOT.glob("*.txt"))
    if include_text:
        paths.extend(sorted(TEXT_SAMPLES_ROOT.glob("*.txt")))
    return paths


def _decode_fixture(path: Path) -> GeometryObject | None:
    raw_hex = path.read_text(encoding="utf-8")
    data = hex_text_to_bytes(raw_hex)
    parsed, _ = parse_type3_clipboard_bytes_with_parser(data)
    if not isinstance(parsed, GeometryObject):
        return None
    return parsed


def _position_name(idx: int, count: int) -> str:
    if idx == 0:
        return "first"
    if idx == count - 1:
        return "last"
    return "middle"


def _collect(include_text: bool) -> dict[str, Any]:
    tag_stats: dict[str, dict[str, Any]] = {}
    role_distribution = Counter()
    unknown_by_tag = Counter()
    family_stats: dict[str, dict[str, Any]] = {}
    records_rows: list[dict[str, Any]] = []
    focus_rows: list[dict[str, Any]] = []

    for fixture in _iter_fixture_paths(include_text):
        parsed = _decode_fixture(fixture)
        if parsed is None:
            continue
        for chain in parsed.object_chains:
            shape_type = chain.shape_type or "geometry"
            recs = chain.contour_records
            for idx, rec in enumerate(recs):
                tag_hex = f"0x{rec.tag:08X}"
                low_byte = f"0x{(rec.tag & 0xFF):02X}"
                role = rec.role
                role_distribution[role] += 1
                if role == "unknown":
                    unknown_by_tag[tag_hex] += 1

                if tag_hex not in tag_stats:
                    tag_stats[tag_hex] = {
                        "raw_tag_hex": tag_hex,
                        "current_assigned_roles": Counter(),
                        "occurrence_count": 0,
                        "fixtures": set(),
                        "shape_type_distribution": Counter(),
                        "record_index_distribution": Counter(),
                        "position_distribution": Counter(),
                        "w_values": [],
                        "example_fixtures": set(),
                    }
                stat = tag_stats[tag_hex]
                stat["current_assigned_roles"][role] += 1
                stat["occurrence_count"] += 1
                stat["fixtures"].add(fixture.name)
                stat["shape_type_distribution"][shape_type] += 1
                stat["record_index_distribution"][idx + 1] += 1
                stat["position_distribution"][_position_name(idx, len(recs))] += 1
                stat["w_values"].append(round(rec.w, 6))
                if len(stat["example_fixtures"]) < 6:
                    stat["example_fixtures"].add(fixture.name)

                if low_byte not in family_stats:
                    family_stats[low_byte] = {
                        "family_low_byte": low_byte,
                        "occurrence_count": 0,
                        "current_roles": Counter(),
                        "common_shape_types": Counter(),
                        "common_positions": Counter(),
                        "example_tags": set(),
                    }
                fam = family_stats[low_byte]
                fam["occurrence_count"] += 1
                fam["current_roles"][role] += 1
                fam["common_shape_types"][shape_type] += 1
                fam["common_positions"][_position_name(idx, len(recs))] += 1
                if len(fam["example_tags"]) < 10:
                    fam["example_tags"].add(tag_hex)

                row = {
                    "fixture": fixture.name,
                    "shape_type": shape_type,
                    "record_index": idx + 1,
                    "x_mm": round(rec.x_mm, 3),
                    "y_mm": round(rec.y_mm, 3),
                    "z_mm": round(rec.z_mm, 3),
                    "w": round(rec.w, 6),
                    "raw_tag": tag_hex,
                    "low_byte": low_byte,
                    "current_role": role,
                    "position": _position_name(idx, len(recs)),
                    "control_evidence": role == "control",
                    "notes": "unknown_role_record" if role == "unknown" else "",
                }
                records_rows.append(row)
                if fixture.name in FOCUS_FIXTURES:
                    focus_rows.append(row)

    tag_distribution = []
    for tag, s in sorted(tag_stats.items(), key=lambda item: item[0]):
        tag_distribution.append(
            {
                "raw_tag_hex": s["raw_tag_hex"],
                "current_assigned_role": dict(s["current_assigned_roles"]),
                "occurrence_count": s["occurrence_count"],
                "fixture_count": len(s["fixtures"]),
                "shape_type_distribution": dict(s["shape_type_distribution"]),
                "record_index_distribution": dict(s["record_index_distribution"]),
                "position_distribution": dict(s["position_distribution"]),
                "w_values": sorted(set(s["w_values"])),
                "observed_fixture_examples": sorted(s["example_fixtures"]),
            }
        )

    family_summary = []
    for low in sorted(family_stats.keys()):
        f = family_stats[low]
        family_summary.append(
            {
                "family_low_byte": low,
                "occurrence_count": f["occurrence_count"],
                "current_roles": dict(f["current_roles"]),
                "common_shape_types": dict(f["common_shape_types"]),
                "common_positions": dict(f["common_positions"]),
                "example_tags": sorted(f["example_tags"]),
            }
        )

    selected_families = [f for f in family_summary if f["family_low_byte"] in {"0x03", "0x0D", "0x0F", "0x0C"}]

    return {
        "policy": "evidence collection only; role mapping remains provisional",
        "tag_distribution": tag_distribution,
        "role_distribution": {
            "anchor_count": role_distribution.get("anchor", 0),
            "control_count": role_distribution.get("control", 0),
            "unknown_count": role_distribution.get("unknown", 0),
            "unknown_tag_count_by_value": dict(sorted(unknown_by_tag.items(), key=lambda item: item[0])),
        },
        "unknown_tag_family_summary": selected_families,
        "all_tag_family_summary": family_summary,
        "fixture_record_table_focus": focus_rows,
    }


def _print_text(report: dict[str, Any]) -> None:
    print("Contour Tag/Role Evidence Analysis")
    print(f"policy: {report['policy']}")
    print()
    print("[Role Distribution]")
    rd = report["role_distribution"]
    print(f"anchor={rd['anchor_count']} control={rd['control_count']} unknown={rd['unknown_count']}")
    print(f"unknown_tag_count_by_value={rd['unknown_tag_count_by_value']}")
    print()
    print("[Unknown Tag Family Summary]")
    for fam in report["unknown_tag_family_summary"]:
        print(
            f"{fam['family_low_byte']}: occ={fam['occurrence_count']} roles={fam['current_roles']} "
            f"shapes={fam['common_shape_types']} positions={fam['common_positions']} examples={fam['example_tags']}"
        )
    print()
    print("[Focus Fixture Record Table]")
    for row in report["fixture_record_table_focus"]:
        print(
            f"{row['fixture']} shape={row['shape_type']} idx={row['record_index']} "
            f"xyz=({row['x_mm']},{row['y_mm']},{row['z_mm']}) w={row['w']} "
            f"tag={row['raw_tag']} low={row['low_byte']} role={row['current_role']} pos={row['position']} note={row['notes']}"
        )


def _print_markdown(report: dict[str, Any]) -> None:
    print("# Contour Tag/Role Evidence")
    print()
    rd = report["role_distribution"]
    print(f"- anchor: {rd['anchor_count']}")
    print(f"- control: {rd['control_count']}")
    print(f"- unknown: {rd['unknown_count']}")
    print()
    print("| family | occ | roles | common shapes |")
    print("|---|---:|---|---|")
    for fam in report["unknown_tag_family_summary"]:
        print(
            f"| {fam['family_low_byte']} | {fam['occurrence_count']} | {fam['current_roles']} | {fam['common_shape_types']} |"
        )


def main() -> int:
    args = parse_args()
    report = _collect(include_text=args.include_text)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    elif args.markdown:
        _print_markdown(report)
    else:
        _print_text(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
