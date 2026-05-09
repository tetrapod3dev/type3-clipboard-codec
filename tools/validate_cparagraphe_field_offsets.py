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

from type3_clipboard_codec.inspect.hex_input import hex_text_to_bytes
from type3_clipboard_codec.models.colors import TYPE3_COLORS_BY_RAW, TYPE3_COLORS_BY_RGB0_RAW
from type3_clipboard_codec.parsers.type3_chain_parser import Type3ChainParser

TEXT_DIR = REPO_ROOT / "tests" / "samples" / "text"
START_OFFSET = 47
STRIDE = 204


def _read_hex(name: str) -> bytes:
    return hex_text_to_bytes((TEXT_DIR / name).read_text(encoding="utf-8"))


def _extract_payload(name: str) -> bytes:
    blob = _read_hex(name)
    parser = Type3ChainParser()
    nodes = parser._extract_nodes(blob[6:])
    for node in nodes:
        if node.header.class_name == "CParagraphe":
            return node.payload
    return b""


def _records(payload: bytes) -> list[bytes]:
    out = []
    i = START_OFFSET
    while i + STRIDE <= len(payload):
        out.append(payload[i : i + STRIDE])
        i += STRIDE
    return out


def _decode(rec: bytes, off: int) -> dict[str, Any]:
    d: dict[str, Any] = {}
    if 0 <= off < len(rec):
        d["u8"] = rec[off]
        d["i8"] = struct.unpack("<b", rec[off : off + 1])[0]
    if off + 2 <= len(rec):
        d["u16le"] = struct.unpack("<H", rec[off : off + 2])[0]
        d["i16le"] = struct.unpack("<h", rec[off : off + 2])[0]
    if off + 4 <= len(rec):
        u32 = struct.unpack("<I", rec[off : off + 4])[0]
        d["u32le"] = u32
        d["i32le"] = struct.unpack("<i", rec[off : off + 4])[0]
        d["float32le"] = struct.unpack("<f", rec[off : off + 4])[0]
        c1 = TYPE3_COLORS_BY_RAW.get(u32)
        c2 = TYPE3_COLORS_BY_RGB0_RAW.get(u32)
        if c1:
            d["palette_00RRGGBB"] = c1.name
        if c2:
            d["palette_00BBGGRR"] = c2.name
    if off + 8 <= len(rec):
        dv = struct.unpack("<d", rec[off : off + 8])[0]
        if math.isfinite(dv):
            d["double64le"] = dv
    frag = rec[off : min(len(rec), off + 16)]
    if len(frag) >= 4 and all(32 <= b <= 126 for b in frag[:4]):
        d["ascii_fragment"] = frag.decode("ascii", errors="ignore")
    chars = []
    for i in range(off, min(len(rec) - 1, off + 16), 2):
        code = struct.unpack("<H", rec[i : i + 2])[0]
        if code == 0:
            break
        if 32 <= code <= 126 or 0xAC00 <= code <= 0xD7A3:
            chars.append(chr(code))
        else:
            break
    if len(chars) >= 2:
        d["utf16le_fragment"] = "".join(chars)
    return d


def _num_level(v: float, expected: float) -> str:
    diff = abs(v - expected)
    if diff <= 1e-9:
        return "exact"
    if diff <= 1e-6:
        return "near"
    if diff <= 1e-3:
        return "loose"
    return "no_match"


def _level_score(level: str) -> float:
    return {"exact": 5.0, "near": 3.0, "loose": 1.5, "changed_only": 0.5, "no_match": 0.0}.get(level, 0.0)


CONFIG: dict[str, dict[str, Any]] = {
    "candidate_text_height": {
        "field_name": "height",
        "ranked_offset": 0x47,
        "pairs": [("text_height_10mm.txt", "text_height_30mm.txt", [0.010, 10.0], [0.030, 30.0])],
    },
    "candidate_width_percent": {
        "field_name": "width",
        "ranked_offset": 0x55,
        "pairs": [("text_width_50_percent.txt", "text_width_150_percent.txt", [0.5, 50.0], [1.5, 150.0])],
    },
    "candidate_slant_angle": {
        "field_name": "slant",
        "ranked_offset": 0x57,
        "pairs": [
            ("text_slant_15deg.txt", "text_slant_custom_30deg.txt", [0.2617993877991494, 15.0], [0.5235987755982988, 30.0]),
            ("default_text.txt", "text_slant_15deg.txt", [0.0], [0.2617993877991494, 15.0]),
            ("default_text.txt", "text_slant_custom_30deg.txt", [0.0], [0.5235987755982988, 30.0]),
        ],
    },
    "candidate_spacing_percent": {
        "field_name": "spacing",
        "ranked_offset": 0x7B,
        "pairs": [("text_spacing_80_percent.txt", "text_spacing_150_percent.txt", [0.8, 80.0], [1.5, 150.0])],
    },
    "candidate_rotation_angle": {
        "field_name": "rotation",
        "ranked_offset": 0x83,
        "pairs": [
            ("text_rotation_30deg.txt", "text_rotation_90deg.txt", [0.5235987755982988, 30.0], [1.5707963267948966, 90.0]),
            ("default_text.txt", "text_rotation_30deg.txt", [0.0], [0.5235987755982988, 30.0]),
            ("default_text.txt", "text_rotation_90deg.txt", [0.0], [1.5707963267948966, 90.0]),
        ],
    },
    "candidate_text_color": {
        "field_name": "color",
        "ranked_offset": 0x8D,
        "pairs": [
            ("text_color_army_green.txt", "text_color_navy_blue.txt", ["Army Green"], ["Navy Blue"]),
            ("default_text.txt", "text_color_army_green.txt", ["Black"], ["Army Green"]),
            ("default_text.txt", "text_color_navy_blue.txt", ["Black"], ["Navy Blue"]),
        ],
    },
    "candidate_font_or_style_flag": {
        "field_name": "font",
        "ranked_offset": 0x69,
        "pairs": [
            ("text_font_arial.txt", "text_font_arial_bold.txt", [], []),
            ("text_font_arial.txt", "text_font_hy_gyeongo_dik.txt", [], []),
        ],
    },
}


def _match_level_for_field(field: str, ld: dict[str, Any], rd: dict[str, Any], ex_l: list[Any], ex_r: list[Any]) -> tuple[str, float, str]:
    if field == "color":
        left_names = {ld.get("palette_00RRGGBB"), ld.get("palette_00BBGGRR")} - {None}
        right_names = {rd.get("palette_00RRGGBB"), rd.get("palette_00BBGGRR")} - {None}
        if any(x in left_names for x in ex_l) and any(x in right_names for x in ex_r):
            return "exact", 6.0, "palette exact"
        return ("changed_only", 0.5, "palette changed_only") if ld != rd else ("no_match", 0.0, "no palette match")

    numeric_types = ["double64le", "float32le", "u32le", "i32le", "u16le", "i16le"]
    best = ("no_match", 0.0, "no expected numeric match")
    for t in numeric_types:
        lv = ld.get(t)
        rv = rd.get(t)
        if not isinstance(lv, (int, float)) or not isinstance(rv, (int, float)):
            continue
        for el in ex_l:
            for er in ex_r:
                if isinstance(el, (int, float)) and isinstance(er, (int, float)):
                    if t.endswith("32le") or t.endswith("16le") and "u" in t or "i" in t:
                        level = "exact" if int(lv) == int(el) and int(rv) == int(er) else "no_match"
                    else:
                        ll = _num_level(float(lv), float(el))
                        rr = _num_level(float(rv), float(er))
                        level = min(ll, rr, key=lambda x: ["exact", "near", "loose", "no_match"].index(x))
                    if level != "no_match":
                        score = _level_score(level)
                        if score > best[1]:
                            best = (level, score, f"{t} expected")
    if field == "font":
        # keep conservative for font/style
        str_sig = bool(ld.get("ascii_fragment") or rd.get("ascii_fragment") or ld.get("utf16le_fragment") or rd.get("utf16le_fragment"))
        enum_sig = isinstance(ld.get("u32le"), int) and isinstance(rd.get("u32le"), int) and ld.get("u32le") != rd.get("u32le")
        if str_sig or enum_sig:
            return "changed_only", 1.0, "font evidence only"
    if best[0] == "no_match" and ld != rd:
        return "changed_only", 0.5, "changed only"
    return best


def _eval_candidate(name: str, cfg: dict[str, Any], payloads: dict[str, bytes], verbose: bool) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    ranked = cfg["ranked_offset"]
    offsets = sorted(set(range(max(0, ranked - 16), min(STRIDE - 1, ranked + 16) + 1)))
    details: list[dict[str, Any]] = []
    per_offset: dict[int, dict[str, Any]] = {}

    for off in offsets:
        ex_count = near_count = loose_count = changed_only_count = no_match_count = 0
        records_with_match = set()
        records_changed = set()
        value_types = set()
        pair_hits = []
        for left, right, ex_l, ex_r in cfg["pairs"]:
            lrecs = _records(payloads[left])
            rrecs = _records(payloads[right])
            n = min(len(lrecs), len(rrecs))
            if n == 0:
                continue
            for i in range(n):
                ld = _decode(lrecs[i], off)
                rd = _decode(rrecs[i], off)
                lvl, score, note = _match_level_for_field(cfg["field_name"], ld, rd, ex_l, ex_r)
                if ld != rd:
                    records_changed.add(i)
                if lvl != "no_match":
                    records_with_match.add(i)
                if lvl == "exact":
                    ex_count += 1
                elif lvl == "near":
                    near_count += 1
                elif lvl == "loose":
                    loose_count += 1
                elif lvl == "changed_only":
                    changed_only_count += 1
                else:
                    no_match_count += 1
                value_types.update(ld.keys())
                value_types.update(rd.keys())
                row = {
                    "field_name": cfg["field_name"],
                    "pair_name": f"{left} vs {right}",
                    "record_relative_offset": off,
                    "decoded_type": sorted(set(ld.keys()) | set(rd.keys())),
                    "left_decoded": ld,
                    "right_decoded": rd,
                    "expected_left": ex_l,
                    "expected_right": ex_r,
                    "match_level": lvl,
                    "match_score": score,
                    "record_indexes_with_match": [i] if lvl != "no_match" else [],
                    "record_indexes_changed": [i] if ld != rd else [],
                    "notes": note,
                }
                if verbose:
                    details.append(row)
        score_total = ex_count * 100 + near_count * 50 + loose_count * 20 + changed_only_count * 3
        score_total += len(records_with_match) * 2 + len(records_changed)
        if score_total == 0 and no_match_count > 0:
            score_total = -no_match_count
        per_offset[off] = {
            "record_relative_offset": off,
            "record_relative_offset_hex": f"0x{off:02X}",
            "exact_count": ex_count,
            "near_count": near_count,
            "loose_count": loose_count,
            "changed_only_count": changed_only_count,
            "no_match_count": no_match_count,
            "records_with_expected_match": len(records_with_match),
            "records_with_changed_value": len(records_changed),
            "dominant_decoded_type": sorted(value_types)[:6],
            "score": score_total,
        }
    ranked_offsets = sorted(per_offset.values(), key=lambda x: (-x["score"], -x["exact_count"], -x["near_count"], -x["loose_count"], x["record_relative_offset"]))
    best = ranked_offsets[0]
    ev = "strong_candidate" if best["exact_count"] >= 3 else "cross_fixture_candidate" if best["exact_count"] >= 1 or best["near_count"] >= 2 else "weak_candidate" if best["changed_only_count"] > 0 else "provisional"
    if cfg["field_name"] == "font":
        ev = "cross_fixture_candidate" if best["changed_only_count"] > 0 else "provisional"

    best_entry = {
        "candidate_name": name,
        "originally_ranked_offset": f"0x{ranked:02X}",
        "best_field_start_offset_hex": best["record_relative_offset_hex"],
        "best_field_start_offset_dec": best["record_relative_offset"],
        "decoded_type": best["dominant_decoded_type"],
        "expected_match": {"exact": best["exact_count"], "near": best["near_count"], "loose": best["loose_count"]},
        "left_value": "see field_validation_details",
        "right_value": "see field_validation_details",
        "score": best["score"],
        "evidence_level": ev,
        "notes": "expected-value scoring priority: exact > near > loose > changed_only",
    }

    # Cross-record consistency for best offset using first pair
    l, r, exl, exr = cfg["pairs"][0]
    lrecs = _records(payloads[l])
    rrecs = _records(payloads[r])
    n = min(len(lrecs), len(rrecs))
    recs = []
    expected_hits = changed_hits = same_hits = 0
    match_levels = []
    for i in range(n):
        ld = _decode(lrecs[i], best["record_relative_offset"])
        rd = _decode(rrecs[i], best["record_relative_offset"])
        lvl, _sc, note = _match_level_for_field(cfg["field_name"], ld, rd, exl, exr)
        changed = ld != rd
        if lvl in {"exact", "near", "loose"}:
            expected_hits += 1
        if changed:
            changed_hits += 1
        else:
            same_hits += 1
        match_levels.append(lvl)
        if verbose:
            recs.append(
                {
                    "record_index": i,
                    "field_offset": best["record_relative_offset"],
                    "decoded_value": {"left": ld, "right": rd},
                    "expected_or_repeated": lvl,
                    "is_changed": changed,
                    "notes": note,
                }
            )
    dominant = max(set(match_levels), key=match_levels.count) if match_levels else "none"
    consistency = {
        "pair": [l, r],
        "field_offset": best["record_relative_offset"],
        "total_records": n,
        "records_with_expected_match": expected_hits,
        "records_with_changed_value": changed_hits,
        "records_with_same_value": same_hits,
        "expected_match_ratio": round(expected_hits / n, 4) if n else 0.0,
        "changed_ratio": round(changed_hits / n, 4) if n else 0.0,
        "dominant_decoded_type": best["dominant_decoded_type"],
        "repeated_value_pattern": dominant,
        "records": recs if verbose else [],
    }
    weak = []
    if best["exact_count"] == 0 and best["near_count"] == 0:
        weak.append({"candidate_name": name, "reason": "no exact/near expected match", "best_offset": best["record_relative_offset_hex"]})
    return best_entry, {"top_offsets": ranked_offsets[: (40 if verbose else 10)]}, consistency, weak


def run(verbose: bool = False) -> dict[str, Any]:
    needed = set()
    for cfg in CONFIG.values():
        for l, r, _a, _b in cfg["pairs"]:
            needed.add(l)
            needed.add(r)
    payloads = {name: _extract_payload(name) for name in needed}

    best_map: dict[str, list[dict[str, Any]]] = {}
    field_details: dict[str, Any] = {}
    consistency: dict[str, Any] = {}
    weak_all: list[dict[str, Any]] = []
    scoring_summary: dict[str, Any] = {}

    for name, cfg in CONFIG.items():
        best, details, cons, weak = _eval_candidate(name, cfg, payloads, verbose)
        best_map[name] = [best]
        field_details[name] = details
        consistency[name] = cons
        weak_all.extend(weak)
        scoring_summary[name] = {
            "ranked_offset": best["originally_ranked_offset"],
            "best_offset": best["best_field_start_offset_hex"],
            "score": best["score"],
            "evidence_level": best["evidence_level"],
            "expected_match": best["expected_match"],
        }

    # Color-only detailed report (single-object fixtures)
    color_cfg = CONFIG["candidate_text_color"]
    color_offsets = sorted(set([0x8B, 0x8C, 0x8D] + list(range(0x8B - 8, 0x8D + 9))))
    color_rows = []
    left = _records(payloads["text_color_army_green.txt"])
    right = _records(payloads["text_color_navy_blue.txt"])
    n = min(len(left), len(right))
    for off in color_offsets:
        exact = 0
        samples = []
        for i in range(n):
            ld = _decode(left[i], off)
            rd = _decode(right[i], off)
            ln = ld.get("palette_00RRGGBB") or ld.get("palette_00BBGGRR")
            rn = rd.get("palette_00RRGGBB") or rd.get("palette_00BBGGRR")
            enc = "00RRGGBB" if ld.get("palette_00RRGGBB") or rd.get("palette_00RRGGBB") else "00BBGGRR" if ld.get("palette_00BBGGRR") or rd.get("palette_00BBGGRR") else "unknown"
            is_exact = ln == "Army Green" and rn == "Navy Blue"
            if is_exact:
                exact += 1
            if len(samples) < 2:
                samples.append({"record_index": i, "left_raw_u32": ld.get("u32le"), "right_raw_u32": rd.get("u32le"), "left_palette": ln, "right_palette": rn, "encoding_variant": enc, "exact_match": is_exact})
        color_rows.append({"record_relative_offset_hex": f"0x{off:02X}", "record_relative_offset_dec": off, "exact_match_count": exact, "samples": samples})
    color_rows.sort(key=lambda x: (-x["exact_match_count"], x["record_relative_offset_dec"]))
    color_best = color_rows[0] if color_rows else None
    color_report = {
        "candidate_offsets": ["0x8B", "0x8C", "0x8D"],
        "nearby_offsets_checked": [f"0x{o:02X}" for o in color_offsets],
        "rows": color_rows[: (40 if verbose else 12)],
        "conclusion": {
            "best_offset": color_best["record_relative_offset_hex"] if color_best else None,
            "best_encoding": color_best["samples"][0]["encoding_variant"] if color_best and color_best["samples"] else "unknown",
            "evidence_level": "cross_fixture_candidate" if color_best and color_best["exact_match_count"] > 0 else "provisional",
        },
    }

    return {
        "policy": {"absolute_offset": "diagnostic_only", "parser_update": "not_applied"},
        "record_model": {"start_offset": START_OFFSET, "stride": STRIDE},
        "expected_value_scoring_summary": scoring_summary,
        "best_field_start_candidates": best_map,
        "field_validation_details": field_details,
        "text_color_byte_order_validation": color_report,
        "cross_record_consistency": consistency,
        "rejected_or_weak_candidates": weak_all,
    }


def _print_text(report: dict[str, Any], verbose: bool) -> None:
    print("CParagraphe Field Offset Validation")
    print("\n1) Policy")
    print(f"- absolute_offset: {report['policy']['absolute_offset']}")
    print("\n2) Record model")
    print(f"- start_offset: {report['record_model']['start_offset']}")
    print(f"- stride: {report['record_model']['stride']}")
    print("\n3) Expected-value scoring summary")
    for k, v in report["expected_value_scoring_summary"].items():
        print(f"- {k}: ranked={v['ranked_offset']} best={v['best_offset']} score={v['score']} evidence={v['evidence_level']} exact={v['expected_match']['exact']} near={v['expected_match']['near']} loose={v['expected_match']['loose']}")
    print("\n4) Best field-start candidates")
    for k, rows in report["best_field_start_candidates"].items():
        r = rows[0]
        print(f"- {k}: ranked={r['originally_ranked_offset']} -> best={r['best_field_start_offset_hex']} ({r['best_field_start_offset_dec']})")
    print("\n5) Field-by-field validation details")
    for k, d in report["field_validation_details"].items():
        print(f"- {k}")
        for row in d["top_offsets"][: (12 if verbose else 5)]:
            print(f"  * record_relative_offset_hex={row['record_relative_offset_hex']} exact={row['exact_count']} near={row['near_count']} loose={row['loose_count']} changed_only={row['changed_only_count']} score={row['score']}")
    print("\n6) Text color byte-order validation")
    c = report["text_color_byte_order_validation"]
    print(f"- candidate offsets: {', '.join(c['candidate_offsets'])}")
    for row in c["rows"][: (12 if verbose else 6)]:
        print(f"  * offset={row['record_relative_offset_hex']} exact_match_count={row['exact_match_count']} samples={row['samples'][:1]}")
    print(f"- conclusion: {c['conclusion']}")
    print("\n7) Cross-record consistency")
    for k, v in report["cross_record_consistency"].items():
        print(
            f"- {k}: total_records={v['total_records']} records_with_expected_match={v['records_with_expected_match']} "
            f"records_with_changed_value={v['records_with_changed_value']} records_with_same_value={v['records_with_same_value']} "
            f"expected_match_ratio={v['expected_match_ratio']} changed_ratio={v['changed_ratio']} "
            f"dominant_decoded_type={v['dominant_decoded_type']} repeated_value_pattern={v['repeated_value_pattern']}"
        )
    print("\n8) Rejected / weak candidates")
    if not report["rejected_or_weak_candidates"]:
        print("- none")
    else:
        for x in report["rejected_or_weak_candidates"]:
            print(f"- {x}")
    print("\n9) Parser update status: not applied")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()
    report = run(verbose=args.verbose)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        _print_text(report, verbose=args.verbose)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
