from __future__ import annotations

import argparse
import json
import math
import struct
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from type3_clipboard_codec import parse_type3_clipboard_bytes_with_parser
from type3_clipboard_codec.inspect.hex_input import hex_text_to_bytes
from type3_clipboard_codec.models.geometry import GeometryObject
from type3_clipboard_codec.parsers.type3_chain_parser import Type3ChainParser

TEXT_DIR = REPO_ROOT / "tests" / "samples" / "text"
STRIDE = 204
RECORD_START = 47

PAIR_FIXTURES = [
    ("default_text.txt", "text_origin_0_0.txt"),
    ("default_text.txt", "text_origin_offset.txt"),
    ("text_origin_0_0.txt", "text_origin_offset.txt"),
]

MULTI_OBJECT_FIXTURES = [
    "text_group_same_color_two_objects.txt",
    "text_group_mixed_color_two_objects.txt",
    "text_two_objects_mixed_color_not_grouped.txt",
]

EXPECTED_ANCHORS_MM: dict[str, list[tuple[float, float, float]]] = {
    "default_text.txt": [(111.111, 222.222, 0.0)],
    "text_origin_0_0.txt": [(0.0, 0.0, 0.0)],
    "text_origin_offset.txt": [(333.333, 444.444, 0.0)],
    "text_group_same_color_two_objects.txt": [(111.111, 222.222, 0.0), (211.111, 322.222, 0.0)],
    "text_group_mixed_color_two_objects.txt": [(111.111, 222.222, 0.0), (211.111, 322.222, 0.0)],
    "text_two_objects_mixed_color_not_grouped.txt": [(111.111, 222.222, 0.0), (211.111, 322.222, 0.0)],
}


def _to_m(mm: float) -> float:
    return mm / 1000.0


def _level(diff_mm: float) -> str:
    if diff_mm <= 1e-6:
        return "exact"
    if diff_mm <= 0.05:
        return "near"
    if diff_mm <= 1.0:
        return "loose"
    return "no_match"


def _read_fixture(name: str) -> bytes:
    return hex_text_to_bytes((TEXT_DIR / name).read_text(encoding="utf-8"))


def _extract_cparagraphe_payloads(blob: bytes) -> list[dict[str, Any]]:
    parser = Type3ChainParser()
    nodes = parser._extract_nodes(blob[6:])
    out: list[dict[str, Any]] = []
    for idx, node in enumerate(nodes):
        if node.header.class_name != "CParagraphe":
            continue
        out.append(
            {
                "node_index": idx,
                "class_name": node.header.class_name,
                "class_payload_length": len(node.payload),
                "class_payload_start_absolute": node.payload_offset + 6,  # diagnostic only
                "payload": node.payload,
            }
        )
    return out


def _decode_direct_anchor_from_payload(payload: bytes) -> dict[str, Any] | None:
    if len(payload) < 182:
        return None
    x_m, y_m, z_m = struct.unpack("<ddd", payload[158:182])
    if not (math.isfinite(x_m) and math.isfinite(y_m) and math.isfinite(z_m)):
        return None
    return {
        "x_offset": 158,
        "y_offset": 166,
        "z_offset": 174,
        "decoded_anchor_m": {"x": x_m, "y": y_m, "z": z_m},
        "decoded_anchor_mm": {"x": round(x_m * 1000.0, 6), "y": round(y_m * 1000.0, 6), "z": round(z_m * 1000.0, 6)},
        "is_contiguous_triple": True,
        "candidate_type": "double64le_contiguous_triple",
    }


def _chain_anchors_from_parser(blob: bytes) -> list[dict[str, Any]]:
    parsed, _ = parse_type3_clipboard_bytes_with_parser(blob)
    if not isinstance(parsed, GeometryObject):
        return []
    rows = []
    for i, chain in enumerate(parsed.object_chains):
        anchor = chain.text_anchor
        rows.append(
            {
                "chain_index": i,
                "source_text_candidate": chain.source_text_candidate,
                "text_anchor_mm": (
                    {"x": anchor.x, "y": anchor.y, "z": anchor.z} if anchor is not None else None
                ),
                "anchor_parse_method": chain.text_anchor_parse_method or chain.text_anchor_source,
                "anchor_parse_confidence": chain.text_anchor_parse_confidence or chain.text_anchor_confidence,
            }
        )
    return rows


def _mm_point_equal(a: dict[str, float] | None, b: dict[str, float] | None, tol_mm: float = 1e-6) -> bool:
    if a is None or b is None:
        return False
    return (
        abs(float(a["x"]) - float(b["x"])) <= tol_mm
        and abs(float(a["y"]) - float(b["y"])) <= tol_mm
        and abs(float(a["z"]) - float(b["z"])) <= tol_mm
    )


def _build_chain_direct_anchor_summary(
    cpar_nodes: list[dict[str, Any]],
    parser_chains: list[dict[str, Any]],
    expected: list[tuple[float, float, float]],
) -> list[dict[str, Any]]:
    cpar_direct_rows: list[dict[str, Any]] = []
    for cpar in cpar_nodes:
        dec = _decode_direct_anchor_from_payload(cpar["payload"])
        cpar_direct_rows.append(
            {
                "node_index": cpar["node_index"],
                "class_payload_length": cpar["class_payload_length"],
                "direct_triple": dec,
            }
        )

    summaries: list[dict[str, Any]] = []
    used_nodes: set[int] = set()
    for i, chain in enumerate(parser_chains):
        baseline_mm = chain.get("text_anchor_mm")
        expected_mm = expected[i] if i < len(expected) else None
        expected_point = (
            {"x": expected_mm[0], "y": expected_mm[1], "z": expected_mm[2]}
            if expected_mm is not None
            else None
        )

        associated = None
        for row in cpar_direct_rows:
            if row["node_index"] in used_nodes:
                continue
            direct = row.get("direct_triple")
            if direct is None:
                continue
            if _mm_point_equal(direct["decoded_anchor_mm"], baseline_mm):
                associated = row
                used_nodes.add(row["node_index"])
                break

        direct_mm = associated["direct_triple"]["decoded_anchor_mm"] if associated and associated.get("direct_triple") else None
        summaries.append(
            {
                "chain_index": chain["chain_index"],
                "source_text_candidate": chain.get("source_text_candidate"),
                "associated_cparagraphe_node_index": associated["node_index"] if associated else None,
                "associated_cparagraphe_payload_length": associated["class_payload_length"] if associated else None,
                "direct_triple_offsets": {"x": 158, "y": 166, "z": 174},
                "direct_anchor_mm": direct_mm,
                "parser_baseline_midpoint_anchor_mm": baseline_mm,
                "expected_anchor_mm": expected_point,
                "direct_vs_baseline_match": _mm_point_equal(direct_mm, baseline_mm),
                "direct_vs_expected_match": _mm_point_equal(direct_mm, expected_point),
                "candidate_ownership_status": (
                    "matched_to_chain_by_anchor_equality"
                    if associated is not None
                    else "unmatched_chain_or_missing_direct_triple"
                ),
            }
        )

    return summaries


def _scan_double_candidates(payload: bytes, expected_mm: tuple[float, float, float], fixture: str) -> list[dict[str, Any]]:
    ex_m = [_to_m(v) for v in expected_mm]
    out: list[dict[str, Any]] = []
    for off in range(0, len(payload) - 8 + 1):
        val = struct.unpack("<d", payload[off : off + 8])[0]
        if not math.isfinite(val):
            continue
        for axis, target_m in (("x", ex_m[0]), ("y", ex_m[1]), ("z", ex_m[2])):
            diff_mm = abs(val - target_m) * 1000.0
            lv = _level(diff_mm)
            if lv == "no_match":
                continue
            rec_rel = off - RECORD_START
            around = payload[max(0, off - 4) : min(len(payload), off + 12)].hex()
            out.append(
                {
                    "fixture": fixture,
                    "axis": axis,
                    "class_payload_relative_offset": off,
                    "record_relative_offset": rec_rel if rec_rel >= 0 else None,
                    "record_relative_offset_mod_stride": (rec_rel % STRIDE) if rec_rel >= 0 else None,
                    "decoded_double_m": val,
                    "expected_m": target_m,
                    "diff_mm": round(diff_mm, 6),
                    "match_level": lv,
                    "nearby_bytes_hex": around,
                    "candidate_type": "double64_le",
                }
            )
    out.sort(key=lambda r: ({"exact": 0, "near": 1, "loose": 2}[r["match_level"]], r["diff_mm"], r["class_payload_relative_offset"]))
    return out


def _triple_candidates(payload: bytes, expected_mm: tuple[float, float, float], fixture: str) -> list[dict[str, Any]]:
    ex = [_to_m(v) for v in expected_mm]
    rows = []
    for off in range(0, len(payload) - 24 + 1):
        x, y, z = struct.unpack("<ddd", payload[off : off + 24])
        if not (math.isfinite(x) and math.isfinite(y) and math.isfinite(z)):
            continue
        diffs = [abs(x - ex[0]) * 1000.0, abs(y - ex[1]) * 1000.0, abs(z - ex[2]) * 1000.0]
        levels = [_level(d) for d in diffs]
        if all(l == "no_match" for l in levels):
            continue
        score = sum({"exact": 3, "near": 2, "loose": 1, "no_match": 0}[l] for l in levels)
        rec_rel = off - RECORD_START
        rows.append(
            {
                "fixture": fixture,
                "x_offset": off,
                "y_offset": off + 8,
                "z_offset": off + 16,
                "record_relative_x_offset": rec_rel if rec_rel >= 0 else None,
                "record_relative_x_mod_stride": (rec_rel % STRIDE) if rec_rel >= 0 else None,
                "decoded_xyz_m": {"x": x, "y": y, "z": z},
                "expected_xyz_m": {"x": ex[0], "y": ex[1], "z": ex[2]},
                "diffs_mm": {"x": round(diffs[0], 6), "y": round(diffs[1], 6), "z": round(diffs[2], 6)},
                "levels": {"x": levels[0], "y": levels[1], "z": levels[2]},
                "triple_score": score,
                "is_contiguous_triple": True,
            }
        )
    rows.sort(
        key=lambda r: (
            -r["triple_score"],
            r["record_relative_x_offset"] is None,
            r["diffs_mm"]["x"] + r["diffs_mm"]["y"] + r["diffs_mm"]["z"],
            r["x_offset"],
        )
    )
    return rows[:20]


def _pairwise_diff_rows(left_payload: bytes, right_payload: bytes) -> list[dict[str, Any]]:
    n = min(len(left_payload), len(right_payload))
    rows: list[dict[str, Any]] = []
    for off in range(n):
        if left_payload[off] == right_payload[off]:
            continue
        rec_rel = off - RECORD_START
        rows.append(
            {
                "class_payload_relative_offset": off,
                "record_relative_offset": rec_rel if rec_rel >= 0 else None,
                "record_relative_offset_mod_stride": (rec_rel % STRIDE) if rec_rel >= 0 else None,
                "left_u8": left_payload[off],
                "right_u8": right_payload[off],
            }
        )
    return rows


def _build_fixture_report(name: str) -> dict[str, Any]:
    blob = _read_fixture(name)
    payloads = _extract_cparagraphe_payloads(blob)
    chains = _chain_anchors_from_parser(blob)
    expected = EXPECTED_ANCHORS_MM.get(name, [(111.111, 222.222, 0.0)])
    node_reports = []
    for node_idx, node in enumerate(payloads):
        exp = expected[min(node_idx, len(expected) - 1)]
        candidates = _scan_double_candidates(node["payload"], exp, name)
        triples = _triple_candidates(node["payload"], exp, name)
        node_reports.append(
            {
                "node_index": node["node_index"],
                "class_payload_length": node["class_payload_length"],
                "expected_anchor_mm": {"x": exp[0], "y": exp[1], "z": exp[2]},
                "double_candidates_top": candidates[:30],
                "triple_candidates_top": triples[:10],
                "direct_triple_at_158_166_174": _decode_direct_anchor_from_payload(node["payload"]),
            }
        )
    chain_direct_anchor_summary = _build_chain_direct_anchor_summary(payloads, chains, expected)
    return {
        "fixture": name,
        "expected_anchors_mm": [{"x": x, "y": y, "z": z} for x, y, z in expected],
        "cparagraphe_node_count": len(payloads),
        "parser_baseline_midpoint_anchors": chains,
        "chain_direct_anchor_summary": chain_direct_anchor_summary,
        "nodes": node_reports,
    }


def _compare_pair(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    left_name = left["fixture"]
    right_name = right["fixture"]
    left_blob = _read_fixture(left_name)
    right_blob = _read_fixture(right_name)
    left_payloads = _extract_cparagraphe_payloads(left_blob)
    right_payloads = _extract_cparagraphe_payloads(right_blob)
    pairs = []
    for i in range(min(len(left_payloads), len(right_payloads))):
        l = left_payloads[i]["payload"]
        r = right_payloads[i]["payload"]
        diffs = _pairwise_diff_rows(l, r)
        pairs.append(
            {
                "node_index": i,
                "left_payload_length": len(l),
                "right_payload_length": len(r),
                "diff_count": len(diffs),
                "diff_rows_top": diffs[:120],
            }
        )
    return {"left_fixture": left_name, "right_fixture": right_name, "node_pairs": pairs}


def _summarize(report: dict[str, Any]) -> dict[str, Any]:
    axis_hits: dict[str, dict[int, dict[str, Any]]] = {"x": {}, "y": {}, "z": {}}
    for fx in report["fixtures"]:
        for node in fx["nodes"]:
            for row in node["double_candidates_top"]:
                axis = row["axis"]
                off = row["class_payload_relative_offset"]
                stat = axis_hits[axis].setdefault(
                    off,
                    {"offset": off, "exact": 0, "near": 0, "loose": 0, "fixtures": set(), "records": set()},
                )
                stat[row["match_level"]] += 1
                stat["fixtures"].add(fx["fixture"])
                mod = row["record_relative_offset_mod_stride"]
                if mod is not None:
                    stat["records"].add(mod)

    def _rank(axis: str) -> list[dict[str, Any]]:
        rows = []
        for v in axis_hits[axis].values():
            score = v["exact"] * 5 + v["near"] * 3 + v["loose"] + len(v["fixtures"]) * 2
            rows.append(
                {
                    "axis": axis,
                    "candidate_offset": v["offset"],
                    "exact": v["exact"],
                    "near": v["near"],
                    "loose": v["loose"],
                    "fixture_coverage": len(v["fixtures"]),
                    "record_relative_offsets_mod_stride": sorted(v["records"]),
                    "candidate_score": score,
                }
            )
        rows.sort(key=lambda r: (-r["candidate_score"], -r["fixture_coverage"], r["candidate_offset"]))
        return rows

    x_rank = _rank("x")
    y_rank = _rank("y")
    z_rank = _rank("z")

    triple_hits: dict[int, dict[str, Any]] = {}
    for fx in report["fixtures"]:
        for node in fx["nodes"]:
            for tri in node["triple_candidates_top"]:
                if tri["triple_score"] < 7:
                    continue
                x_off = tri["x_offset"]
                bucket = triple_hits.setdefault(
                    x_off,
                    {
                        "x_offset": x_off,
                        "y_offset": x_off + 8,
                        "z_offset": x_off + 16,
                        "exact_xyz_matches": 0,
                        "near_xyz_matches": 0,
                        "fixture_coverage": set(),
                        "record_relative_mods": set(),
                    },
                )
                levels = tri["levels"]
                if levels["x"] == "exact" and levels["y"] == "exact" and levels["z"] == "exact":
                    bucket["exact_xyz_matches"] += 1
                else:
                    bucket["near_xyz_matches"] += 1
                bucket["fixture_coverage"].add(fx["fixture"])
                mod = tri["record_relative_x_mod_stride"]
                if mod is not None:
                    bucket["record_relative_mods"].add(mod)

    triple_rank = []
    for row in triple_hits.values():
        score = row["exact_xyz_matches"] * 10 + row["near_xyz_matches"] * 4 + len(row["fixture_coverage"]) * 3
        triple_rank.append(
            {
                "x_offset": row["x_offset"],
                "y_offset": row["y_offset"],
                "z_offset": row["z_offset"],
                "exact_xyz_matches": row["exact_xyz_matches"],
                "near_xyz_matches": row["near_xyz_matches"],
                "fixture_coverage": len(row["fixture_coverage"]),
                "record_relative_offsets_mod_stride": sorted(row["record_relative_mods"]),
                "candidate_score": score,
                "is_contiguous_triple": True,
            }
        )
    triple_rank.sort(key=lambda r: (-r["candidate_score"], -r["fixture_coverage"], r["x_offset"]))
    best_triple = triple_rank[0] if triple_rank else None

    best_x = x_rank[0] if x_rank else None
    best_y = y_rank[0] if y_rank else None
    best_z = z_rank[0] if z_rank else None
    contiguous = bool(best_triple)
    return {
        "anchor_candidate_summary": {
            "x_candidates": x_rank[:10],
            "y_candidates": y_rank[:10],
            "z_candidates": z_rank[:10],
            "xyz_triple_candidates": triple_rank[:10],
        },
        "best_candidate_summary": {
            "best_x_offset": best_triple["x_offset"] if best_triple else (best_x["candidate_offset"] if best_x else None),
            "best_y_offset": best_triple["y_offset"] if best_triple else (best_y["candidate_offset"] if best_y else None),
            "best_z_offset": best_triple["z_offset"] if best_triple else (best_z["candidate_offset"] if best_z else None),
            "is_contiguous_xyz_triple": contiguous,
            "best_triple_support": best_triple,
            "offset_basis": "class_payload_relative_offset (record-relative reported as evidence)",
            "confidence": "provisional",
            "parser_readiness": "needs_more_validation",
            "why_not_confirmed": "cross-fixture repeatability and multi-object ownership consistency are not sufficient yet",
        },
    }


def build_report() -> dict[str, Any]:
    fixture_names = sorted({name for pair in PAIR_FIXTURES for name in pair} | set(MULTI_OBJECT_FIXTURES))
    fixtures = [_build_fixture_report(name) for name in fixture_names]
    by_name = {f["fixture"]: f for f in fixtures}
    pairwise = [_compare_pair(by_name[left], by_name[right]) for left, right in PAIR_FIXTURES]
    summary = _summarize({"fixtures": fixtures})
    return {
        "policy": {
            "focus": "text anchor direct payload field candidate evidence",
            "absolute_offset": "diagnostic_only",
            "parser_update": "not_applied",
            "baseline_midpoint_note": "baseline_midpoint is current recovery path, not direct binary field decode",
        },
        "fixtures": fixtures,
        "pairwise_comparisons": pairwise,
        "multi_object_verification": [by_name[name] for name in MULTI_OBJECT_FIXTURES],
        **summary,
    }


def _print_text(report: dict[str, Any]) -> None:
    print("Text Anchor Field Candidate Analysis")
    print(f"policy.absolute_offset: {report['policy']['absolute_offset']}")
    print(f"policy.parser_update: {report['policy']['parser_update']}")
    print(f"policy.note: {report['policy']['baseline_midpoint_note']}")
    print()
    print("[Pairwise Fixtures]")
    for pair in report["pairwise_comparisons"]:
        print(f"- {pair['left_fixture']} vs {pair['right_fixture']}")
        for node in pair["node_pairs"]:
            print(
                f"  node={node['node_index']} diff_count={node['diff_count']} "
                f"(class-relative + record-relative evidence)"
            )
    print()
    b = report["best_candidate_summary"]
    print("[Best Candidate Summary]")
    print(
        f"x={b['best_x_offset']} y={b['best_y_offset']} z={b['best_z_offset']} "
        f"contiguous_triple={b['is_contiguous_xyz_triple']} confidence={b['confidence']}"
    )
    print(f"parser_readiness={b['parser_readiness']} reason={b['why_not_confirmed']}")
    print()
    print("[Multi-object Chain Direct Anchor Summary]")
    for fx in report["multi_object_verification"]:
        print(f"- {fx['fixture']} (cparagraphe_nodes={fx['cparagraphe_node_count']})")
        for row in fx.get("chain_direct_anchor_summary", []):
            d = row.get("direct_anchor_mm")
            base = row.get("parser_baseline_midpoint_anchor_mm")
            exp = row.get("expected_anchor_mm")
            print(
                f"  chain={row['chain_index']} cpar_node={row['associated_cparagraphe_node_index']} "
                f"direct={d} baseline={base} expected={exp} "
                f"direct_vs_baseline={row['direct_vs_baseline_match']} "
                f"direct_vs_expected={row['direct_vs_expected_match']} "
                f"ownership={row['candidate_ownership_status']}"
            )


def _print_markdown(report: dict[str, Any]) -> None:
    print("# Text Anchor Field Candidate Analysis")
    print()
    b = report["best_candidate_summary"]
    print("| best_x | best_y | best_z | contiguous_xyz | confidence | parser_readiness |")
    print("|---:|---:|---:|---|---|---|")
    print(
        f"| {b['best_x_offset']} | {b['best_y_offset']} | {b['best_z_offset']} | "
        f"{b['is_contiguous_xyz_triple']} | {b['confidence']} | {b['parser_readiness']} |"
    )


def main() -> int:
    ap = argparse.ArgumentParser(description="Analyze text anchor direct-field candidates from CParagraphe payloads.")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--markdown", action="store_true")
    args = ap.parse_args()

    report = build_report()
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    elif args.markdown:
        _print_markdown(report)
    else:
        _print_text(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
