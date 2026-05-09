import argparse
import json
import math
import struct
import sys
from collections import defaultdict
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
STRIDE = 204
DEFAULT_START = 47
BASELINE = "default_text.txt"

TARGETS = [
    "default_text.txt",
    "text_height_10mm.txt",
    "text_height_30mm.txt",
    "text_width_50_percent.txt",
    "text_width_150_percent.txt",
    "text_slant_15deg.txt",
    "text_slant_custom_30deg.txt",
    "text_spacing_80_percent.txt",
    "text_spacing_150_percent.txt",
    "text_underline_on_default.txt",
    "text_rotation_30deg.txt",
    "text_rotation_90deg.txt",
    "text_color_army_green.txt",
    "text_color_navy_blue.txt",
    "text_font_arial.txt",
    "text_font_arial_bold.txt",
    "text_font_hy_gyeongo_dik.txt",
    "text_font_hy_se_gothic.txt",
    "text_font_hy_tae_gothic.txt",
    "text_font_hy_teuktae_gothic.txt",
    "text_ascii_lowercase.txt",
    "text_ascii_uppercase.txt",
    "text_digits.txt",
    "text_alphanumeric.txt",
    "text_multiline_basic.txt",
]

PAIR_PLAN: list[tuple[str, str, str]] = [
    ("height", "text_height_10mm.txt", "text_height_30mm.txt"),
    ("width", "text_width_50_percent.txt", "text_width_150_percent.txt"),
    ("slant", "text_slant_15deg.txt", "text_slant_custom_30deg.txt"),
    ("slant", "default_text.txt", "text_slant_15deg.txt"),
    ("slant", "default_text.txt", "text_slant_custom_30deg.txt"),
    ("spacing", "text_spacing_80_percent.txt", "text_spacing_150_percent.txt"),
    ("spacing", "default_text.txt", "text_spacing_80_percent.txt"),
    ("spacing", "default_text.txt", "text_spacing_150_percent.txt"),
    ("rotation", "text_rotation_30deg.txt", "text_rotation_90deg.txt"),
    ("rotation", "default_text.txt", "text_rotation_30deg.txt"),
    ("rotation", "default_text.txt", "text_rotation_90deg.txt"),
    ("color", "text_color_army_green.txt", "text_color_navy_blue.txt"),
    ("color", "default_text.txt", "text_color_army_green.txt"),
    ("color", "default_text.txt", "text_color_navy_blue.txt"),
    ("font", "text_font_arial.txt", "text_font_arial_bold.txt"),
    ("font", "text_font_arial.txt", "text_font_hy_gyeongo_dik.txt"),
    ("font", "text_font_hy_gyeongo_dik.txt", "text_font_hy_se_gothic.txt"),
    ("font", "text_font_hy_tae_gothic.txt", "text_font_hy_teuktae_gothic.txt"),
    ("text_value", "text_ascii_lowercase.txt", "text_ascii_uppercase.txt"),
    ("text_value", "text_ascii_lowercase.txt", "text_digits.txt"),
    ("text_value", "text_ascii_lowercase.txt", "text_alphanumeric.txt"),
    ("multiline", "default_text.txt", "text_multiline_basic.txt"),
]

CANDIDATE_NAMES = [
    "candidate_text_height",
    "candidate_width_percent",
    "candidate_slant_angle",
    "candidate_spacing_percent",
    "candidate_rotation_angle",
    "candidate_text_color",
    "candidate_font_or_style_flag",
    "candidate_visible_character_or_run_code",
    "candidate_linebreak_or_multiline_marker",
]


def _read_hex(name: str) -> bytes:
    return hex_text_to_bytes((TEXT_DIR / name).read_text(encoding="utf-8"))


def _extract_payload(name: str) -> dict[str, Any] | None:
    blob = _read_hex(name)
    parser = Type3ChainParser()
    nodes = parser._extract_nodes(blob[6:])
    for i, node in enumerate(nodes):
        if node.header.class_name == "CParagraphe":
            return {
                "fixture": name,
                "chain_index": i,
                "class_payload_start_absolute": node.payload_offset + 6,  # diagnostic only
                "class_payload_length": len(node.payload),
                "payload": node.payload,
            }
    return None


def _record_chunks(payload: bytes, start: int, stride: int) -> list[tuple[int, int, bytes]]:
    chunks = []
    i = start
    ridx = 0
    while i + stride <= len(payload):
        chunks.append((ridx, i, payload[i : i + stride]))
        ridx += 1
        i += stride
    return chunks


def _best_start(payload: bytes, stride: int) -> dict[str, int]:
    best = {"start": 0, "score": -1, "count": 0}
    for s in range(0, min(stride, len(payload))):
        recs = _record_chunks(payload, s, stride)
        if len(recs) < 3:
            continue
        stable = 0
        for rel in range(stride):
            vals = {r[2][rel] for r in recs}
            if len(vals) == 1:
                stable += 1
        newline = sum(1 for _ri, _s0, rec in recs if (10 in rec or 13 in rec))
        score = stable + newline
        if score > best["score"]:
            best = {"start": s, "score": score, "count": len(recs)}
    return best


def _candidate_name(tag: str) -> str:
    return {
        "height": "candidate_text_height",
        "width": "candidate_width_percent",
        "slant": "candidate_slant_angle",
        "spacing": "candidate_spacing_percent",
        "rotation": "candidate_rotation_angle",
        "underline": "candidate_underline_offset",
        "color": "candidate_text_color",
        "font": "candidate_font_or_style_flag",
        "text_value": "candidate_visible_character_or_run_code",
        "multiline": "candidate_linebreak_or_multiline_marker",
    }.get(tag, "provisional_unknown")


def _known_numeric_match(tag: str, val: float) -> str | None:
    eps = 1e-4
    target_map = {
        "height": [0.01, 0.03, 10.0, 30.0],
        "width": [0.5, 1.5, 50.0, 150.0],
        "slant": [15.0, 30.0, 0.261799, 0.523599],
        "spacing": [0.8, 1.5, 80.0, 150.0],
        "rotation": [30.0, 90.0, 0.523599, 1.570796],
    }
    for t in target_map.get(tag, []):
        if abs(val - t) < eps:
            return str(t)
    return None


def _value_candidates(buf: bytes, off: int, tag: str) -> dict[str, Any]:
    out: dict[str, Any] = {}
    if off < len(buf):
        out["u8"] = buf[off]
    if off + 1 < len(buf):
        out["u16"] = struct.unpack("<H", buf[off : off + 2])[0]
    if off + 3 < len(buf):
        u32 = struct.unpack("<I", buf[off : off + 4])[0]
        out["u32"] = u32
        color = TYPE3_COLORS_BY_RAW.get(u32) or TYPE3_COLORS_BY_RGB0_RAW.get(u32)
        if color:
            out["palette_match"] = color.name
    if off + 7 < len(buf):
        d = struct.unpack("<d", buf[off : off + 8])[0]
        if math.isfinite(d):
            out["double"] = d
            k = _known_numeric_match(tag, d)
            if k is not None:
                out["numeric_match"] = k
    if off + 3 < len(buf):
        asc = buf[off : min(len(buf), off + 20)]
        if len(asc) >= 4 and all((32 <= b <= 126) for b in asc[:4]):
            s = asc.decode("ascii", errors="ignore")
            if s:
                out["ascii"] = s
    return out


def _value_types(left: dict[str, Any], right: dict[str, Any]) -> list[str]:
    keys = set(left.keys()) | set(right.keys())
    return sorted(k for k in keys if k in {"u8", "u16", "u32", "double", "ascii", "palette_match"})


def _low_signal(values: tuple[dict[str, Any], dict[str, Any]]) -> bool:
    markers = ("OBJETINFOS_CLASSNAME", "CObDao", "CZone", "CParagraphe", "CCourbe", "CContour")
    has_marker = False
    only_zero_or_one = True
    for side in values:
        asc = side.get("ascii")
        if isinstance(asc, str) and any(m in asc for m in markers):
            has_marker = True
        d = side.get("double")
        if d is not None and abs(d) > 1e-12 and abs(d - 1.0) > 1e-12:
            only_zero_or_one = False
    return has_marker or only_zero_or_one


def _evidence_level(score: float) -> str:
    if score >= 11.0:
        return "strong_candidate"
    if score >= 7.0:
        return "cross_fixture_candidate"
    if score >= 3.5:
        return "weak_candidate"
    return "provisional"


def _analyze_pair(tag: str, left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    start = DEFAULT_START
    if tag == "multiline":
        start = right["best_start_offset"]
    left_recs = _record_chunks(left["payload"], start, STRIDE)
    right_recs = _record_chunks(right["payload"], start, STRIDE)
    n = min(len(left_recs), len(right_recs))
    offset_stats: dict[int, dict[str, Any]] = defaultdict(
        lambda: {
            "changed_record_indexes": set(),
            "changed_count": 0,
            "value_type_candidates": set(),
            "left_values": [],
            "right_values": [],
            "palette_match_if_any": set(),
            "numeric_match_if_any": set(),
            "low_signal_hits": 0,
        }
    )

    for ri in range(n):
        lrec = left_recs[ri][2]
        rrec = right_recs[ri][2]
        for off in range(min(len(lrec), len(rrec))):
            if lrec[off] == rrec[off]:
                continue
            stat = offset_stats[off]
            stat["changed_record_indexes"].add(ri)
            stat["changed_count"] += 1
            lval = _value_candidates(lrec, off, tag)
            rval = _value_candidates(rrec, off, tag)
            stat["value_type_candidates"].update(_value_types(lval, rval))
            if len(stat["left_values"]) < 3:
                stat["left_values"].append(lval)
            if len(stat["right_values"]) < 3:
                stat["right_values"].append(rval)
            p = lval.get("palette_match") or rval.get("palette_match")
            if p:
                stat["palette_match_if_any"].add(str(p))
            num = lval.get("numeric_match") or rval.get("numeric_match")
            if num:
                stat["numeric_match_if_any"].add(str(num))
            if _low_signal((lval, rval)):
                stat["low_signal_hits"] += 1

    rows = []
    for off, stat in offset_stats.items():
        changed_rec_cnt = len(stat["changed_record_indexes"])
        score = (changed_rec_cnt * 1.2) + (stat["changed_count"] * 0.35)
        if stat["palette_match_if_any"]:
            score += 2.2
        if stat["numeric_match_if_any"]:
            score += 2.8
        if stat["low_signal_hits"] > 0:
            score *= 0.5
        row = {
            "field_tag": tag,
            "left_file": left["fixture"],
            "right_file": right["fixture"],
            "record_relative_offset_hex": f"0x{off:02X}",
            "record_relative_offset_dec": off,
            "changed_record_indexes": sorted(stat["changed_record_indexes"]),
            "changed_count": stat["changed_count"],
            "value_type_candidates": sorted(stat["value_type_candidates"]),
            "left_values": stat["left_values"],
            "right_values": stat["right_values"],
            "palette_match_if_any": sorted(stat["palette_match_if_any"]),
            "numeric_match_if_any": sorted(stat["numeric_match_if_any"]),
            "signal_score": round(score, 3),
            "evidence_level": _evidence_level(score),
            "notes": "low_signal" if stat["low_signal_hits"] > 0 else "candidate",
            "candidate_name": _candidate_name(tag),
        }
        rows.append(row)
    rows.sort(key=lambda x: (-x["signal_score"], x["record_relative_offset_dec"]))
    return {
        "field_tag": tag,
        "left_file": left["fixture"],
        "right_file": right["fixture"],
        "candidate_start_offset": start,
        "candidate_stride": STRIDE,
        "record_count_left": len(left_recs),
        "record_count_right": len(right_recs),
        "top_offsets": rows[:10],
        "all_offsets": rows,
    }


def _ranked_candidates(pairs: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    global_stats: dict[str, dict[int, dict[str, Any]]] = defaultdict(
        lambda: defaultdict(
            lambda: {
                "signal_score": 0.0,
                "changed_in_tags": set(),
                "stable_in_tags": set(),
                "value_types": set(),
                "examples": [],
                "record_indexes": set(),
            }
        )
    )
    all_tags = {p["field_tag"] for p in pairs}

    for p in pairs:
        tag = p["field_tag"]
        rows = p["all_offsets"]
        changed_offsets = {r["record_relative_offset_dec"] for r in rows}
        for r in rows:
            cname = r["candidate_name"]
            off = r["record_relative_offset_dec"]
            s = global_stats[cname][off]
            s["signal_score"] += r["signal_score"]
            s["changed_in_tags"].add(tag)
            s["value_types"].update(r["value_type_candidates"])
            s["record_indexes"].update(r["changed_record_indexes"])
            if len(s["examples"]) < 2:
                s["examples"].append(
                    {
                        "before": r["left_values"][0] if r["left_values"] else {},
                        "after": r["right_values"][0] if r["right_values"] else {},
                    }
                )
        for off in range(STRIDE):
            if off not in changed_offsets:
                for cname in CANDIDATE_NAMES:
                    global_stats[cname][off]["stable_in_tags"].add(tag)

    ranked: dict[str, list[dict[str, Any]]] = {}
    for cname in CANDIDATE_NAMES:
        rows = []
        for off, s in global_stats[cname].items():
            if not s["changed_in_tags"]:
                continue
            score = s["signal_score"]
            stable_bonus = len(s["stable_in_tags"] - s["changed_in_tags"]) * 0.2
            score += stable_bonus
            level = _evidence_level(score)
            rows.append(
                {
                    "candidate_name": cname,
                    "record_relative_offset_hex": f"0x{off:02X}",
                    "record_relative_offset_dec": off,
                    "value_type": sorted(s["value_types"]),
                    "signal_score": round(score, 3),
                    "evidence_level": level,
                    "changed_in_tags": sorted(s["changed_in_tags"]),
                    "stable_in_tags": sorted((all_tags - s["changed_in_tags"])),
                    "example_before": s["examples"][0]["before"] if s["examples"] else {},
                    "example_after": s["examples"][0]["after"] if s["examples"] else {},
                    "record_indexes": sorted(s["record_indexes"]),
                    "notes": "ranked_record_relative_candidate",
                }
            )
        rows.sort(key=lambda x: (-x["signal_score"], x["record_relative_offset_dec"]))
        ranked[cname] = rows[:5]
    return ranked


def _multiline_window(fixtures: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    multi = fixtures.get("text_multiline_basic.txt")
    if not multi:
        return None
    payload = multi["payload"]
    w0, w1 = 47, 187
    window = payload[w0:w1]
    u32s = []
    doubles = []
    asciis = []
    utf16s = []
    crlf = []
    for i in range(max(0, len(window) - 3)):
        u = struct.unpack("<I", window[i : i + 4])[0]
        if u <= 200:
            u32s.append({"class_payload_relative_offset": w0 + i, "u32": u})
        if i + 8 <= len(window):
            d = struct.unpack("<d", window[i : i + 8])[0]
            if math.isfinite(d) and abs(d) < 1000 and d in (0.0, 1.0, 0.01, 0.03, 15.0, 30.0, 80.0, 100.0, 150.0):
                doubles.append({"class_payload_relative_offset": w0 + i, "double": d})
        if window[i] in (10, 13):
            crlf.append({"class_payload_relative_offset": w0 + i, "byte": window[i]})
    i = 0
    while i < len(window):
        if 32 <= window[i] <= 126:
            s = i
            while i < len(window) and 32 <= window[i] <= 126:
                i += 1
            if i - s >= 3:
                asciis.append({"class_payload_relative_offset": w0 + s, "value": window[s:i].decode("ascii", errors="ignore")})
        else:
            i += 1
    for i in range(0, max(0, len(window) - 2), 2):
        chars = []
        j = i
        while j + 1 < len(window):
            c = struct.unpack("<H", window[j : j + 2])[0]
            if c == 0:
                break
            if 32 <= c <= 126 or 0xAC00 <= c <= 0xD7A3:
                chars.append(chr(c))
                j += 2
            else:
                break
        if len(chars) >= 3:
            utf16s.append({"class_payload_relative_offset": w0 + i, "value": "".join(chars)})
    return {
        "window_start": 47,
        "window_end": 187,
        "byte_length": 140,
        "cr_lf_candidates": crlf[:20],
        "possible_line_count_candidates": "CR/LF observed" if crlf else "none",
        "possible_header_selector_u32_candidates": u32s[:20],
        "possible_utf16_ascii_candidates": {"ascii": asciis[:10], "utf16": utf16s[:10]},
        "double_candidates": doubles[:20],
        "conclusion": "provisional_multiline_pre_record_header_possible",
    }


def run_analysis(verbose: bool = False) -> dict[str, Any]:
    fixtures: dict[str, dict[str, Any]] = {}
    for name in TARGETS:
        info = _extract_payload(name)
        if info is None:
            continue
        best = _best_start(info["payload"], STRIDE)
        info["best_start_offset"] = best["start"]
        info["best_record_count"] = best["count"]
        info["record_count_default_start"] = len(_record_chunks(info["payload"], DEFAULT_START, STRIDE))
        fixtures[name] = info

    paired = []
    for tag, left_name, right_name in PAIR_PLAN:
        left = fixtures.get(left_name)
        right = fixtures.get(right_name)
        if left is None or right is None:
            continue
        paired.append(_analyze_pair(tag, left, right))

    ranked = _ranked_candidates(paired)
    multiline = _multiline_window(fixtures)

    summary = []
    for name, info in fixtures.items():
        summary.append(
            {
                "fixture_name": name,
                "candidate_start_offset": DEFAULT_START,
                "best_candidate_start_offset": info["best_start_offset"],
                "candidate_stride": STRIDE,
                "record_count": info["record_count_default_start"],
            }
        )

    report = {
        "policy": {
            "absolute_offset": "diagnostic_only",
            "parser_update": "not_applied",
        },
        "record_model": {
            "default_start_offset": DEFAULT_START,
            "stride": STRIDE,
        },
        "fixture_results": summary,
        "paired_comparisons": paired,
        "ranked_field_candidates": ranked,
        "multiline_pre_record_window": multiline,
        "notes_unresolved": [
            "absolute_offset output is diagnostic only",
            "record_relative candidates are not parser decode rules",
            "strong/cross/weak/provisional labels are analyzer evidence levels",
        ],
    }
    if not verbose:
        for p in report["paired_comparisons"]:
            p.pop("all_offsets", None)
    return report


def _print_policy_and_model(report: dict[str, Any]) -> None:
    print("CParagraphe Field Candidate Analyzer")
    print("\n1) Policy")
    print(f"- absolute_offset: {report['policy']['absolute_offset']}")
    print(f"- parser_update: {report['policy']['parser_update']}")
    print("\n2) Record model")
    print(f"- default_start_offset: {report['record_model']['default_start_offset']}")
    print(f"- stride: {report['record_model']['stride']}")


def _print_pair_summary(report: dict[str, Any], pair_detail: bool) -> None:
    print("\n3) Paired comparison summary")
    for p in report["paired_comparisons"]:
        print(
            f"- [{p['field_tag']}] {p['left_file']} vs {p['right_file']} "
            f"(start={p['candidate_start_offset']} stride={p['candidate_stride']} "
            f"records={p['record_count_left']}/{p['record_count_right']})"
        )
        rows = p["top_offsets"]
        if pair_detail:
            for r in rows:
                print(
                    f"  * record_relative_offset_hex={r['record_relative_offset_hex']} "
                    f"dec={r['record_relative_offset_dec']} changed_count={r['changed_count']} "
                    f"signal_score={r['signal_score']} evidence={r['evidence_level']} "
                    f"value_type={','.join(r['value_type_candidates']) or '-'} "
                    f"palette={','.join(r['palette_match_if_any']) or '-'} "
                    f"numeric={','.join(r['numeric_match_if_any']) or '-'}"
                )
        else:
            head = ", ".join(r["record_relative_offset_hex"] for r in rows[:5])
            print(f"  top offsets: {head}")


def _print_ranked(report: dict[str, Any]) -> None:
    print("\n4) Ranked field candidate summary")
    for cname, rows in report["ranked_field_candidates"].items():
        print(f"- {cname}")
        for i, r in enumerate(rows, start=1):
            print(
                f"  rank={i} record_relative_offset_hex={r['record_relative_offset_hex']} "
                f"dec={r['record_relative_offset_dec']} signal_score={r['signal_score']} "
                f"evidence={r['evidence_level']} changed_in={','.join(r['changed_in_tags']) or '-'} "
                f"stable_in={','.join(r['stable_in_tags']) or '-'} value_type={','.join(r['value_type']) or '-'}"
            )


def _print_multiline(report: dict[str, Any]) -> None:
    print("\n5) Multiline pre-record window summary")
    m = report["multiline_pre_record_window"]
    if not m:
        print("- unavailable")
        return
    print(f"- window_start={m['window_start']}")
    print(f"- window_end={m['window_end']}")
    print(f"- byte_length={m['byte_length']}")
    print(f"- CR/LF candidates: {m['cr_lf_candidates'][:8]}")
    print(f"- possible line count candidates: {m['possible_line_count_candidates']}")
    print(f"- possible header/selector u32 candidates: {m['possible_header_selector_u32_candidates'][:8]}")
    print(f"- possible UTF-16/ASCII candidates: {m['possible_utf16_ascii_candidates']}")
    print(f"- conclusion={m['conclusion']}")


def _print_notes(report: dict[str, Any]) -> None:
    print("\n6) Notes / unresolved")
    for n in report["notes_unresolved"]:
        print(f"- {n}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--pair-detail", action="store_true")
    args = ap.parse_args()

    report = run_analysis(verbose=args.verbose)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0

    _print_policy_and_model(report)
    _print_pair_summary(report, pair_detail=args.pair_detail or args.verbose)
    _print_ranked(report)
    _print_multiline(report)
    _print_notes(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
