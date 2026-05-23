from __future__ import annotations

import argparse
import json
import math
import struct
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from type3_clipboard_codec.inspect.hex_input import hex_text_to_bytes
from type3_clipboard_codec.models.geometry import Type3Node
from type3_clipboard_codec.parsers.type3_chain_parser import Type3ChainParser

TEXT_DIR = REPO_ROOT / "tests" / "samples" / "text"
DEFAULT_FIXTURES = [
    "text_three_objects_grouped_order_abc.txt",
    "text_three_objects_grouped_order_abc_content_variation.txt",
]
TOP_LEVEL_HEADER_LEN = 6
COBDAO_MARKER = b"CObDao"
OBJECTINFOS_MARKERS = (b"OBJECTINFOS_CLASSNAME", b"OBJETINFOS_CLASSNAME")
LOCAL_WINDOW_START = -24
LOCAL_WINDOW_END = 128


@dataclass
class Limits:
    max_fixtures: int = 2
    max_anchor_sections: int = 4
    max_local_hex_bytes: int = 64

    def as_dict(self) -> dict[str, int]:
        return {
            "max_fixtures": self.max_fixtures,
            "max_anchor_sections": self.max_anchor_sections,
            "max_local_hex_bytes": self.max_local_hex_bytes,
        }


@dataclass
class Context:
    limits: Limits
    warnings: list[str] = field(default_factory=list)

    def warn(self, message: str) -> None:
        if message not in self.warnings:
            self.warnings.append(message)


def _read_fixture(name: str) -> bytes:
    return hex_text_to_bytes((TEXT_DIR / name).read_text(encoding="utf-8"))


def _read_nodes(blob: bytes) -> list[Type3Node]:
    return Type3ChainParser()._extract_nodes(blob[TOP_LEVEL_HEADER_LEN:])


def _u32(payload: bytes, base: int, rel: int) -> int | None:
    off = base + rel
    if off < 0 or off + 4 > len(payload):
        return None
    return struct.unpack("<I", payload[off : off + 4])[0]


def _i32(payload: bytes, base: int, rel: int) -> int | None:
    off = base + rel
    if off < 0 or off + 4 > len(payload):
        return None
    return struct.unpack("<i", payload[off : off + 4])[0]


def _double3_mm(payload: bytes, base: int, rel: int) -> dict[str, float] | None:
    off = base + rel
    if off < 0 or off + 24 > len(payload):
        return None
    x_m, y_m, z_m = struct.unpack("<ddd", payload[off : off + 24])
    if not all(math.isfinite(v) for v in (x_m, y_m, z_m)):
        return None
    return {"x": round(x_m * 1000.0, 6), "y": round(y_m * 1000.0, 6), "z": round(z_m * 1000.0, 6)}


def _is_coordinate_like_mm(triple: dict[str, float] | None) -> bool:
    if triple is None:
        return False
    return all(abs(triple[axis]) <= 1_000_000 for axis in ("x", "y", "z"))


def _has_objectinfos_at_minus_24(payload: bytes, cobdao_offset: int) -> bool:
    marker_off = cobdao_offset - 24
    if marker_off < 0:
        return False
    for marker in OBJECTINFOS_MARKERS:
        end = marker_off + len(marker)
        if end <= len(payload) and payload[marker_off:end] == marker:
            return True
    return False


def _local_hex(payload: bytes, cobdao_offset: int, max_bytes: int) -> str:
    start = max(0, cobdao_offset + LOCAL_WINDOW_START)
    end = min(len(payload), start + max_bytes, cobdao_offset + LOCAL_WINDOW_END)
    return payload[start:end].hex(" ")


def _signature_match(payload: bytes, cobdao_offset: int) -> dict[str, Any]:
    triple = _double3_mm(payload, cobdao_offset, 34)
    fields = {
        "u32le@+12": _u32(payload, cobdao_offset, 12),
        "u32le@+56": _u32(payload, cobdao_offset, 56),
        "u32le@+108": _u32(payload, cobdao_offset, 108),
        "u32le@+112": _u32(payload, cobdao_offset, 112),
    }
    checks = {
        "objectinfos_at_minus_24": _has_objectinfos_at_minus_24(payload, cobdao_offset),
        "u32@+12_eq_131072": fields["u32le@+12"] == 131072,
        "u32@+56_eq_262144": fields["u32le@+56"] == 262144,
        "u32@+108_eq_65536": fields["u32le@+108"] == 65536,
        "u32@+112_eq_262144": fields["u32le@+112"] == 262144,
        "triple_at_+34_finite": triple is not None,
        "triple_at_+34_coordinate_like": _is_coordinate_like_mm(triple),
        "triple_at_+34_z_near_zero": triple is not None and abs(triple["z"]) <= 1e-6,
    }
    return {
        "matched": all(checks.values()),
        "checks": checks,
        "fields": fields,
        "triple_mm_at_+34": triple,
    }


def _analyze_fixture(name: str, ctx: Context) -> dict[str, Any]:
    blob = _read_fixture(name)
    nodes = _read_nodes(blob)
    rows: list[dict[str, Any]] = []
    cproperty_nodes = [n for n in nodes if n.header.class_name == "CPropertyExtend"]
    anchor_sections = 0

    for node_index, node in enumerate(cproperty_nodes):
        payload = node.payload
        start = 0
        while True:
            pos = payload.find(COBDAO_MARKER, start)
            if pos < 0:
                break
            match = _signature_match(payload, pos)
            if match["matched"]:
                anchor_sections += 1
                if anchor_sections > ctx.limits.max_anchor_sections:
                    ctx.warn(f"{name}: anchor sections capped at {ctx.limits.max_anchor_sections}")
                    break
                rows.append(
                    {
                        "fixture": name,
                        "cproperty_node_index": node_index,
                        "cobdao_offset": pos,
                        "local_window": {"start": LOCAL_WINDOW_START, "end": LOCAL_WINDOW_END},
                        "local_context_hex": _local_hex(payload, pos, ctx.limits.max_local_hex_bytes),
                        "signature_v1": match["checks"],
                        "fields": {
                            "u32le@+12": match["fields"]["u32le@+12"],
                            "i32le@+12": _i32(payload, pos, 12),
                            "double3_mm@+34": match["triple_mm_at_+34"],
                            "u32le@+56": match["fields"]["u32le@+56"],
                            "i32le@+56": _i32(payload, pos, 56),
                            "u32le@+108": match["fields"]["u32le@+108"],
                            "i32le@+108": _i32(payload, pos, 108),
                            "u32le@+112": match["fields"]["u32le@+112"],
                            "i32le@+112": _i32(payload, pos, 112),
                        },
                    }
                )
            start = pos + 1

    return {
        "fixture": name,
        "raw_size": len(blob),
        "node_count": len(nodes),
        "cproperty_node_count": len(cproperty_nodes),
        "anchor_record_sections": rows,
        "anchor_record_section_count": len(rows),
    }


def build_report(fixtures: list[str], limits: Limits) -> dict[str, Any]:
    ctx = Context(limits=limits)
    reports = []
    for i, name in enumerate(fixtures):
        if i >= limits.max_fixtures:
            ctx.warn(f"fixtures capped at {limits.max_fixtures}")
            break
        if not (TEXT_DIR / name).exists():
            ctx.warn(f"fixture not found: {name}")
            continue
        reports.append(_analyze_fixture(name, ctx))

    all_sections = [s for fx in reports for s in fx["anchor_record_sections"]]
    summary = {
        "signature_name": "CPropertyExtend_CObDao_anchor_record_candidate_v1",
        "fixture_count": len(reports),
        "matched_anchor_section_count": len(all_sections),
        "parser_behavior": "not_modified",
    }
    layout = {
        "fields": [
            {"offset": "+12", "role_candidate": "record_type_or_subtype", "current_value_distribution": _counts(all_sections, "u32le@+12")},
            {"offset": "+34", "role_candidate": "anchor_x_y_z_payload", "current_value_distribution": "double3_mm"},
            {"offset": "+56", "role_candidate": "unknown_flag_or_overlap", "current_value_distribution": _counts(all_sections, "u32le@+56")},
            {"offset": "+108", "role_candidate": "record_subtype_or_trailing", "current_value_distribution": _counts(all_sections, "u32le@+108")},
            {"offset": "+112", "role_candidate": "record_subtype_or_trailing", "current_value_distribution": _counts(all_sections, "u32le@+112")},
        ]
    }
    stability = _signature_layout_stability_summary(all_sections, group_name=None, fixture_count=len(reports))
    group_result = {
        "group_name": None,
        "fixtures_analyzed": [fx["fixture"] for fx in reports],
        "output_size_chars": 0,
        "layout_stable": len(stability["variable_offsets"]) == 0,
        "warnings": ctx.warnings,
    }
    return {
        "mode": "small_anchor_record_semantics",
        "limits": limits.as_dict(),
        "warnings": ctx.warnings,
        "fixtures": reports,
        "signature_v1_summary": summary,
        "signature_layout_stability_summary": stability,
        "fixture_group_results": [group_result],
        "record_layout_candidate": layout,
        "semantic_hypothesis": {
            "status": "provisional",
            "judgment": "signature_v1_local_pattern_is_consistent_in_current_small_fixture_set",
            "parser_readiness": "not_ready_analyzer_only",
        },
        "answers": {
            "parser_behavior": "not_modified",
            "default_context_analyzer_mode": "safe_summary_only",
            "signature_v1_semantics": "provisional",
        },
    }


def _counts(sections: list[dict[str, Any]], key: str) -> dict[str, int]:
    out: dict[str, int] = {}
    for section in sections:
        value = section["fields"][key]
        out[str(value)] = out.get(str(value), 0) + 1
    return out


def _signature_layout_stability_summary(
    sections: list[dict[str, Any]], *, group_name: str | None, fixture_count: int
) -> dict[str, Any]:
    offsets = ["+12", "+34", "+56", "+108", "+112"]
    d12 = _counts(sections, "u32le@+12")
    d56 = _counts(sections, "u32le@+56")
    d108 = _counts(sections, "u32le@+108")
    d112 = _counts(sections, "u32le@+112")
    coord_like_true = 0
    z_near_zero_true = 0
    z_values: dict[str, int] = {}
    for section in sections:
        triple = section["fields"]["double3_mm@+34"]
        if triple is not None:
            coord_like_true += 1
            if abs(float(triple["z"])) <= 1e-6:
                z_near_zero_true += 1
            key = str(triple["z"])
            z_values[key] = z_values.get(key, 0) + 1
    stable_offsets: list[str] = []
    variable_offsets: list[str] = []
    for key, dist in (("+12", d12), ("+56", d56), ("+108", d108), ("+112", d112)):
        if len(dist) == 1:
            stable_offsets.append(key)
        else:
            variable_offsets.append(key)
    if sections and coord_like_true == len(sections) and z_near_zero_true == len(sections):
        stable_offsets.append("+34")
    else:
        variable_offsets.append("+34")
    layout_stable = len(variable_offsets) == 0
    return {
        "fixture_count": fixture_count,
        "anchor_section_count": len(sections),
        "offsets_checked": offsets,
        "stable_offsets": stable_offsets,
        "variable_offsets": variable_offsets,
        "per_offset_value_distribution": {
            "+12": d12,
            "+34": {
                "coordinate_like_true_count": coord_like_true,
                "z_near_zero_true_count": z_near_zero_true,
                "z_value_distribution": z_values,
            },
            "+56": d56,
            "+108": d108,
            "+112": d112,
        },
        "group_name": group_name,
        "conclusion": (
            "layout_stable_for_checked_offsets_in_current_group"
            if layout_stable
            else "layout_has_variable_offsets_in_current_group"
        ),
        "confidence": "provisional",
    }


def _print_text(report: dict[str, Any]) -> None:
    print("Text CPropertyExtend Anchor Record Semantics (Small Analyzer)")
    print(f"mode: {report['mode']}")
    print(f"parser_behavior: {report['answers']['parser_behavior']}")
    print(f"signature: {report['signature_v1_summary']['signature_name']}")
    print(f"matched_anchor_sections: {report['signature_v1_summary']['matched_anchor_section_count']}")
    stability = report["signature_layout_stability_summary"]
    print(
        f"layout_stable: {str(len(stability['variable_offsets']) == 0).lower()} "
        f"stable_offsets={stability['stable_offsets']} variable_offsets={stability['variable_offsets']}"
    )
    print("[Fixtures]")
    print("fixture | cproperty_nodes | matched_anchor_sections")
    for row in report["fixtures"]:
        print(f"{row['fixture']} | {row['cproperty_node_count']} | {row['anchor_record_section_count']}")
    if report["warnings"]:
        print("[Warnings]")
        for warning in report["warnings"]:
            print(f"- {warning}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Small analyzer for CPropertyExtend CObDao anchor-record semantics.")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--fixture", action="append", dest="fixtures")
    parser.add_argument("--group-name")
    parser.add_argument("--max-fixtures", type=int, default=2)
    parser.add_argument("--max-anchor-sections", type=int, default=4)
    parser.add_argument("--max-local-hex-bytes", type=int, default=64)
    args = parser.parse_args()

    fixtures = args.fixtures if args.fixtures else DEFAULT_FIXTURES
    limits = Limits(
        max_fixtures=max(1, args.max_fixtures),
        max_anchor_sections=max(1, args.max_anchor_sections),
        max_local_hex_bytes=max(16, args.max_local_hex_bytes),
    )
    report = build_report(fixtures, limits)
    if args.group_name:
        report["signature_layout_stability_summary"]["group_name"] = args.group_name
        report["fixture_group_results"][0]["group_name"] = args.group_name

    if args.json:
        json_text = json.dumps(report, ensure_ascii=False, separators=(",", ":"))
        report["fixture_group_results"][0]["output_size_chars"] = len(json_text)
        json_text = json.dumps(report, ensure_ascii=False, separators=(",", ":"))
        print(json_text)
    else:
        _print_text(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
