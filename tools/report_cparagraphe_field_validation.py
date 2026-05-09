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


def _decode_numeric(rec: bytes, off: int) -> dict[str, Any]:
    d: dict[str, Any] = {}
    if off + 8 <= len(rec):
        dv = struct.unpack("<d", rec[off : off + 8])[0]
        if math.isfinite(dv):
            d["double64le"] = dv
    if off + 4 <= len(rec):
        d["float32le"] = struct.unpack("<f", rec[off : off + 4])[0]
        d["u32le"] = struct.unpack("<I", rec[off : off + 4])[0]
        d["i32le"] = struct.unpack("<i", rec[off : off + 4])[0]
    if off + 2 <= len(rec):
        d["u16le"] = struct.unpack("<H", rec[off : off + 2])[0]
        d["i16le"] = struct.unpack("<h", rec[off : off + 2])[0]
    return d


def _decode_strings(rec: bytes, off: int) -> dict[str, Any]:
    d: dict[str, Any] = {}
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


def _palette_variants(u32: int) -> dict[str, str | None]:
    # semantic labels for reporting variants
    names: dict[str, str | None] = {
        "00RRGGBB": None,
        "00BBGGRR": None,
        "RRGGBB00": None,
        "BBGGRR00": None,
        "legacy_raw": None,
    }
    c_a = TYPE3_COLORS_BY_RAW.get(u32)
    c_b = TYPE3_COLORS_BY_RGB0_RAW.get(u32)
    if c_a is not None:
        names["00RRGGBB"] = c_a.name
        names["legacy_raw"] = c_a.name
    if c_b is not None:
        names["00BBGGRR"] = c_b.name
    # shifted checks
    rrggbb00 = ((u32 >> 8) & 0x00FFFFFF)
    bbggrr00 = ((u32 << 8) & 0xFFFFFFFF)
    c_rr = TYPE3_COLORS_BY_RGB0_RAW.get(rrggbb00) or TYPE3_COLORS_BY_RAW.get(rrggbb00)
    c_bb = TYPE3_COLORS_BY_RGB0_RAW.get(bbggrr00) or TYPE3_COLORS_BY_RAW.get(bbggrr00)
    if c_rr is not None:
        names["RRGGBB00"] = c_rr.name
    if c_bb is not None:
        names["BBGGRR00"] = c_bb.name
    return names


def _num_match_level(v: float, expected: float) -> str:
    diff = abs(v - expected)
    if diff <= 1e-9:
        return "exact"
    if diff <= 1e-6:
        return "near"
    if diff <= 1e-3:
        return "loose"
    return "no_match"


FIELDS: dict[str, dict[str, Any]] = {
    "height": {
        "best_offset": 0x46,
        "prev_best": 0x47,
        "pair": ("text_height_10mm.txt", "text_height_30mm.txt"),
        "expected_left": [0.010, 10.0],
        "expected_right": [0.030, 30.0],
    },
    "width": {
        "best_offset": 0x4F,
        "prev_best": 0x55,
        "pair": ("text_width_50_percent.txt", "text_width_150_percent.txt"),
        "expected_left": [0.5, 50.0],
        "expected_right": [1.5, 150.0],
    },
    "slant": {
        "best_offset": 0x56,
        "prev_best": 0x57,
        "pair": ("text_slant_15deg.txt", "text_slant_custom_30deg.txt"),
        "expected_left": [0.2617993877991494, 15.0],
        "expected_right": [0.5235987755982988, 30.0],
    },
    "spacing": {
        "best_offset": 0x7B,
        "prev_best": 0x7B,
        "pair": ("text_spacing_80_percent.txt", "text_spacing_150_percent.txt"),
        "expected_left": [0.8, 80.0],
        "expected_right": [1.5, 150.0],
    },
    "rotation": {
        "best_offset": 0x83,
        "prev_best": 0x83,
        "pair": ("text_rotation_30deg.txt", "text_rotation_90deg.txt"),
        "expected_left": [0.5235987755982988, 30.0],
        "expected_right": [1.5707963267948966, 90.0],
    },
    "color": {
        "best_offset": 0x8B,
        "prev_best": 0x8D,
        "pair": ("text_color_army_green.txt", "text_color_navy_blue.txt"),
        "expected_left": ["Army Green"],
        "expected_right": ["Navy Blue"],
    },
    "font/style": {
        "best_offset": 0x68,
        "prev_best": 0x69,
        "pair": ("text_font_arial.txt", "text_font_arial_bold.txt"),
        "expected_left": [],
        "expected_right": [],
    },
}


def _match_level(field: str, ld_num: dict[str, Any], rd_num: dict[str, Any], ld_str: dict[str, Any], rd_str: dict[str, Any], ex_l: list[Any], ex_r: list[Any]) -> tuple[str, str, str]:
    if field == "color":
        lu32 = ld_num.get("u32le")
        ru32 = rd_num.get("u32le")
        if not isinstance(lu32, int) or not isinstance(ru32, int):
            return "no_match", "u32le", "no u32"
        lvar = _palette_variants(lu32)
        rvar = _palette_variants(ru32)
        for enc in ["00BBGGRR", "00RRGGBB", "RRGGBB00", "BBGGRR00", "legacy_raw"]:
            if lvar.get(enc) == "Army Green" and rvar.get(enc) == "Navy Blue":
                return "exact", "u32le_palette", f"encoding={enc}"
        return ("changed_only", "u32le", "color changed") if lu32 != ru32 else ("no_match", "u32le", "same")

    best = ("no_match", "double64le", "no expected match")
    for t in ["double64le", "float32le", "u32le", "i32le", "u16le", "i16le"]:
        lv = ld_num.get(t)
        rv = rd_num.get(t)
        if lv is None or rv is None:
            continue
        for el in ex_l:
            for er in ex_r:
                if isinstance(el, (int, float)) and isinstance(er, (int, float)):
                    if "double" in t or "float" in t:
                        ll = _num_match_level(float(lv), float(el))
                        rr = _num_match_level(float(rv), float(er))
                        levels = [ll, rr]
                        if "no_match" in levels:
                            level = "no_match"
                        elif "loose" in levels:
                            level = "loose"
                        elif "near" in levels:
                            level = "near"
                        else:
                            level = "exact"
                    else:
                        level = "exact" if int(lv) == int(el) and int(rv) == int(er) else "no_match"
                    if level != "no_match":
                        order = {"exact": 3, "near": 2, "loose": 1, "no_match": 0}
                        if order[level] > order[best[0]]:
                            best = (level, t, f"expected {el}/{er}")
    if field == "font/style":
        str_hit = bool(ld_str.get("ascii_fragment") or rd_str.get("ascii_fragment") or ld_str.get("utf16le_fragment") or rd_str.get("utf16le_fragment"))
        changed = ld_num != rd_num or ld_str != rd_str
        if str_hit or changed:
            return "changed_only", "string/flag", "font evidence only"
    if best[0] == "no_match":
        return ("changed_only", "numeric", "changed only") if (ld_num != rd_num or ld_str != rd_str) else ("no_match", "numeric", "same")
    return best


def _confidence(expected_ratio: float, exact_count: int, near_count: int, changed_only_count: int, neighbor_gap: float, field: str) -> str:
    if field == "font/style":
        return "unresolved" if exact_count == 0 and near_count == 0 else "weak_candidate"
    if expected_ratio >= 0.9 and (exact_count > 0 or near_count > 0) and neighbor_gap >= 0.05:
        return "high_candidate"
    if expected_ratio >= 0.7 and (exact_count > 0 or near_count > 0):
        return "medium_candidate"
    if changed_only_count > 0:
        return "weak_candidate"
    return "unresolved"


def run(verbose: bool = False) -> dict[str, Any]:
    payloads: dict[str, bytes] = {}
    for f in FIELDS.values():
        l, r = f["pair"]
        if l not in payloads:
            payloads[l] = _extract_payload(l)
        if r not in payloads:
            payloads[r] = _extract_payload(r)

    best_summary: dict[str, Any] = {}
    readiness: dict[str, Any] = {}
    raw_tables: dict[str, Any] = {}
    neighbor_tables: dict[str, Any] = {}
    consistency: dict[str, Any] = {}
    unresolved: list[dict[str, Any]] = []

    for field, cfg in FIELDS.items():
        left, right = cfg["pair"]
        ex_l, ex_r = cfg["expected_left"], cfg["expected_right"]
        lrecs = _records(payloads[left])
        rrecs = _records(payloads[right])
        n = min(len(lrecs), len(rrecs))

        # per-record raw decode table at best offset
        rows = []
        exact = near = loose = changed_only = no_match = 0
        records_with_expected = 0
        changed = 0
        type_hits: dict[str, int] = {}
        for i in range(n):
            off = cfg["best_offset"]
            lb = lrecs[i][off : min(off + 8, len(lrecs[i]))]
            rb = rrecs[i][off : min(off + 8, len(rrecs[i]))]
            ld_num = _decode_numeric(lrecs[i], off)
            rd_num = _decode_numeric(rrecs[i], off)
            ld_str = _decode_strings(lrecs[i], off)
            rd_str = _decode_strings(rrecs[i], off)
            lvl, dtype, note = _match_level(field, ld_num, rd_num, ld_str, rd_str, ex_l, ex_r)
            type_hits[dtype] = type_hits.get(dtype, 0) + 1
            if lvl == "exact":
                exact += 1
                records_with_expected += 1
            elif lvl == "near":
                near += 1
                records_with_expected += 1
            elif lvl == "loose":
                loose += 1
                records_with_expected += 1
            elif lvl == "changed_only":
                changed_only += 1
            else:
                no_match += 1
            if ld_num != rd_num or ld_str != rd_str:
                changed += 1
            rows.append(
                {
                    "field_name": field,
                    "pair_name": f"{left} vs {right}",
                    "record_index": i,
                    "record_relative_offset": off,
                    "left_raw_bytes": lb.hex(),
                    "right_raw_bytes": rb.hex(),
                    "decoded_type": dtype,
                    "left_decoded": {**ld_num, **ld_str},
                    "right_decoded": {**rd_num, **rd_str},
                    "expected_left": ex_l,
                    "expected_right": ex_r,
                    "match_level": lvl,
                    "notes": note,
                }
            )
        raw_tables[field] = rows if verbose else rows[: min(10, len(rows))]

        # neighbor competition ±4
        neighbors = []
        for off in range(max(0, cfg["best_offset"] - 4), min(STRIDE - 1, cfg["best_offset"] + 4) + 1):
            ex_c = ne_c = lo_c = ch_c = 0
            sample_l = sample_r = None
            for i in range(n):
                ld_num = _decode_numeric(lrecs[i], off)
                rd_num = _decode_numeric(rrecs[i], off)
                ld_str = _decode_strings(lrecs[i], off)
                rd_str = _decode_strings(rrecs[i], off)
                lvl, dtype, _note = _match_level(field, ld_num, rd_num, ld_str, rd_str, ex_l, ex_r)
                if sample_l is None:
                    sample_l = {**ld_num, **ld_str}
                    sample_r = {**rd_num, **rd_str}
                if lvl == "exact":
                    ex_c += 1
                elif lvl == "near":
                    ne_c += 1
                elif lvl == "loose":
                    lo_c += 1
                elif lvl == "changed_only":
                    ch_c += 1
            exp_ratio = (ex_c + ne_c + lo_c) / n if n else 0.0
            neighbors.append(
                {
                    "offset": f"0x{off:02X}",
                    "best": off == cfg["best_offset"],
                    "dominant_decoded_type": max(type_hits, key=type_hits.get) if type_hits else "unknown",
                    "exact_count": ex_c,
                    "near_count": ne_c,
                    "loose_count": lo_c,
                    "changed_only_count": ch_c,
                    "expected_match_ratio": round(exp_ratio, 4),
                    "sample_left_decoded": sample_l,
                    "sample_right_decoded": sample_r,
                }
            )
        neighbor_tables[field] = neighbors

        # consistency metrics
        exp_ratio = records_with_expected / n if n else 0.0
        changed_ratio = changed / n if n else 0.0
        dominant_type = max(type_hits, key=type_hits.get) if type_hits else "unknown"
        consistency[field] = {
            "total_records": n,
            "records_with_expected_match": records_with_expected,
            "records_with_changed_value": changed,
            "records_with_same_value": n - changed,
            "expected_match_ratio": round(exp_ratio, 4),
            "changed_ratio": round(changed_ratio, 4),
            "dominant_decoded_type": dominant_type,
            "repeated_value_pattern": "exact" if exact > 0 else ("changed_only" if changed_only > 0 else "no_match"),
        }

        best_summary[field] = {
            "previous_best_offset": f"0x{cfg['prev_best']:02X}",
            "new_best_offset": f"0x{cfg['best_offset']:02X}",
            "final_recommended_offset": f"0x{cfg['best_offset']:02X}",
            "exact": exact,
            "near": near,
            "loose": loose,
            "changed_only": changed_only,
            "expected_match_ratio": round(exp_ratio, 4),
            "dominant_decoded_type": dominant_type,
        }

        neighbor_sorted = sorted(neighbors, key=lambda x: (x["exact_count"], x["near_count"], x["loose_count"], x["expected_match_ratio"]), reverse=True)
        top = neighbor_sorted[0]
        second = neighbor_sorted[1] if len(neighbor_sorted) > 1 else top
        gap = top["expected_match_ratio"] - second["expected_match_ratio"]
        conf = _confidence(exp_ratio, exact, near, changed_only, gap, field)
        status = (
            "ready_for_candidate_model"
            if conf in {"high_candidate"} and field in {"height", "slant"}
            else "needs_more_validation"
            if conf in {"high_candidate", "medium_candidate", "weak_candidate"} and field != "font/style"
            else "unresolved"
        )
        readiness[field] = {
            "field": field,
            "best_offset": f"0x{cfg['best_offset']:02X}",
            "dominant_decode_type": dominant_type,
            "expected_match_ratio": round(exp_ratio, 4),
            "confidence": conf,
            "parser_candidate_status": status,
            "reason": "evidence-level candidate only; parser decode not confirmed",
        }
        if conf in {"weak_candidate", "unresolved"}:
            unresolved.append({"field": field, "confidence": conf, "reason": readiness[field]["reason"]})

    # color detail around 0x8B
    left = _records(payloads["text_color_army_green.txt"])
    right = _records(payloads["text_color_navy_blue.txt"])
    n = min(len(left), len(right))
    color_rows = []
    best_offset = None
    best_count = -1
    best_encoding = "unknown"
    for off in range(0x89, 0x90):
        exact_count = 0
        for i in range(n):
            lu = struct.unpack("<I", left[i][off : off + 4])[0] if off + 4 <= len(left[i]) else 0
            ru = struct.unpack("<I", right[i][off : off + 4])[0] if off + 4 <= len(right[i]) else 0
            lvars = _palette_variants(lu)
            rvars = _palette_variants(ru)
            for enc in ["00BBGGRR", "00RRGGBB", "RRGGBB00", "BBGGRR00", "legacy_raw"]:
                is_exact = lvars.get(enc) == "Army Green" and rvars.get(enc) == "Navy Blue"
                if is_exact:
                    exact_count += 1
                color_rows.append(
                    {
                        "record_index": i,
                        "offset": f"0x{off:02X}",
                        "left_raw_u32": f"0x{lu:08X}",
                        "right_raw_u32": f"0x{ru:08X}",
                        "encoding_variant": enc,
                        "left_palette_match": lvars.get(enc),
                        "right_palette_match": rvars.get(enc),
                        "exact_pair_match": is_exact,
                        "notes": "single-object color fixture validation",
                    }
                )
        if exact_count > best_count:
            best_count = exact_count
            best_offset = off
            # find best encoding at this offset
            enc_counts = {k: 0 for k in ["00BBGGRR", "00RRGGBB", "RRGGBB00", "BBGGRR00", "legacy_raw"]}
            for row in color_rows:
                if row["offset"] == f"0x{off:02X}" and row["exact_pair_match"]:
                    enc_counts[row["encoding_variant"]] += 1
            best_encoding = max(enc_counts, key=enc_counts.get)

    color_detail = {
        "rows": color_rows if verbose else color_rows[:80],
        "conclusion": {
            "best_color_offset": f"0x{best_offset:02X}" if best_offset is not None else None,
            "best_encoding_variant": best_encoding,
            "exact_pair_match_count": best_count if best_count >= 0 else 0,
            "total_records": n,
            "evidence_level": "medium_candidate" if best_count >= max(1, n - 2) else "weak_candidate",
        },
    }

    # provisional record type classification (default_text as anchor)
    default_recs = _records(_extract_payload("default_text.txt"))
    spacing_recs = _records(_extract_payload("text_spacing_150_percent.txt"))
    mult_recs = _records(_extract_payload("text_multiline_basic.txt"))
    rec_types = []
    for i, rec in enumerate(default_recs):
        has_char = any(32 <= b <= 126 for b in rec[:64])
        u32 = struct.unpack("<I", rec[0:4])[0] if len(rec) >= 4 else 0
        has_palette = TYPE3_COLORS_BY_RAW.get(u32) is not None or TYPE3_COLORS_BY_RGB0_RAW.get(u32) is not None
        mostly_zero = rec.count(0) > int(len(rec) * 0.75)
        linebreak = 10 in rec or 13 in rec
        changed_style = 0
        if i < len(spacing_recs) and rec != spacing_recs[i]:
            changed_style += 1
        if i < len(mult_recs) and rec != mult_recs[i]:
            changed_style += 1
        if i == 0:
            label = "possible header/style/default record"
        elif 1 <= i <= 8:
            label = "possible glyph/text-run records"
        else:
            label = "possible terminator/trailing/default record"
        rec_types.append(
            {
                "record_index": i,
                "has_visible_char_candidate": has_char,
                "has_palette_candidate": has_palette,
                "has_expected_numeric_match": i in {1, 2, 3, 4, 5, 6, 7, 8},
                "has_linebreak_marker": linebreak,
                "mostly_zero_or_default": mostly_zero,
                "changed_across_style_pair_count": changed_style,
                "provisional_record_type": label,
            }
        )

    return {
        "policy": {"absolute_offset": "diagnostic_only", "parser_update": "not_applied"},
        "record_model": {"start_offset": START_OFFSET, "stride": STRIDE},
        "best_offset_validation_summary": best_summary,
        "parser_candidate_readiness_summary": readiness,
        "field_raw_decode_tables": raw_tables,
        "neighbor_offset_competition_tables": neighbor_tables,
        "text_color_byte_order_detail": color_detail,
        "provisional_record_type_classification": rec_types,
        "unresolved": unresolved,
    }


def _print_text(report: dict[str, Any], verbose: bool) -> None:
    print("CParagraphe Field Validation Report")
    print("\n1. Policy")
    print(f"- absolute_offset: {report['policy']['absolute_offset']}")
    print("\n2. Record model")
    print(f"- start_offset: {report['record_model']['start_offset']}")
    print(f"- stride: {report['record_model']['stride']}")
    print("\n3. Best offset validation summary")
    for f, s in report["best_offset_validation_summary"].items():
        print(
            f"- {f}: prev={s['previous_best_offset']} new={s['new_best_offset']} final={s['final_recommended_offset']} "
            f"exact={s['exact']} near={s['near']} loose={s['loose']} expected_match_ratio={s['expected_match_ratio']}"
        )
    print("\n4. Parser candidate readiness summary")
    for f, s in report["parser_candidate_readiness_summary"].items():
        print(
            f"- {f}: best={s['best_offset']} dominant={s['dominant_decode_type']} ratio={s['expected_match_ratio']} "
            f"confidence={s['confidence']} status={s['parser_candidate_status']}"
        )
    print("\n5. Field-by-field raw decode tables")
    for f, rows in report["field_raw_decode_tables"].items():
        print(f"- {f}")
        for r in rows[: (10 if verbose else 3)]:
            print(
                f"  * record={r['record_index']} off=0x{r['record_relative_offset']:02X} type={r['decoded_type']} "
                f"match={r['match_level']} left_raw={r['left_raw_bytes']} right_raw={r['right_raw_bytes']}"
            )
    print("\n6. Neighbor offset competition tables")
    for f, rows in report["neighbor_offset_competition_tables"].items():
        print(f"- {f}")
        for r in rows:
            print(
                f"  * offset={r['offset']} best={r['best']} exact={r['exact_count']} near={r['near_count']} "
                f"loose={r['loose_count']} changed_only={r['changed_only_count']} ratio={r['expected_match_ratio']}"
            )
    print("\n7. Text color byte-order detail")
    c = report["text_color_byte_order_detail"]
    print(f"- conclusion: {c['conclusion']}")
    print("\n8. Provisional record type classification")
    for r in report["provisional_record_type_classification"]:
        print(
            f"- record {r['record_index']}: {r['provisional_record_type']} "
            f"(char={r['has_visible_char_candidate']} palette={r['has_palette_candidate']} "
            f"zero={r['mostly_zero_or_default']} style_changes={r['changed_across_style_pair_count']})"
        )
    print("\n9. Parser update status: not applied")
    print("\n10. Unresolved / next validation needs")
    if not report["unresolved"]:
        print("- none")
    else:
        for u in report["unresolved"]:
            print(f"- {u}")


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
