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
TARGET_FILES = [
    "default_text.txt",
    "text_ascii_lowercase.txt",
    "text_ascii_uppercase.txt",
    "text_digits.txt",
    "text_alphanumeric.txt",
    "text_color_army_green.txt",
    "text_color_navy_blue.txt",
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
    "text_font_arial.txt",
    "text_font_arial_bold.txt",
    "text_multiline_basic.txt",
]

DIFF_PAIRS = [
    ("default_text.txt", "text_height_30mm.txt", "height"),
    ("default_text.txt", "text_width_50_percent.txt", "width"),
    ("default_text.txt", "text_width_150_percent.txt", "width"),
    ("default_text.txt", "text_slant_15deg.txt", "slant"),
    ("default_text.txt", "text_slant_custom_30deg.txt", "slant"),
    ("default_text.txt", "text_spacing_80_percent.txt", "spacing"),
    ("default_text.txt", "text_spacing_150_percent.txt", "spacing"),
    ("default_text.txt", "text_underline_on_default.txt", "underline"),
    ("default_text.txt", "text_rotation_30deg.txt", "rotation"),
    ("default_text.txt", "text_rotation_90deg.txt", "rotation"),
    ("default_text.txt", "text_color_army_green.txt", "color"),
    ("text_color_army_green.txt", "text_color_navy_blue.txt", "color"),
    ("text_font_arial.txt", "text_font_arial_bold.txt", "font"),
    ("default_text.txt", "text_multiline_basic.txt", "multiline"),
]

STRIDE = 204
START_SINGLE = 47


def _read_hex_fixture(name: str) -> bytes:
    return hex_text_to_bytes((TEXT_DIR / name).read_text(encoding="utf-8"))


def _extract_first_cparagraphe(blob: bytes) -> dict[str, Any] | None:
    parser = Type3ChainParser()
    payload = blob[6:] if len(blob) >= 6 else blob
    nodes = parser._extract_nodes(payload)
    for i, node in enumerate(nodes):
        if node.header.class_name == "CParagraphe":
            return {
                "chain_index": i,
                "class_name": node.header.class_name,
                "class_start_absolute": node.start_offset + 6,
                "class_payload_start_absolute": node.payload_offset + 6,
                "class_payload_length": len(node.payload),
                "payload": node.payload,
            }
    return None


def _ascii_candidates(buf: bytes) -> list[str]:
    out = []
    i = 0
    while i < len(buf):
        if 32 <= buf[i] <= 126:
            s = i
            while i < len(buf) and 32 <= buf[i] <= 126:
                i += 1
            if i - s >= 3:
                out.append(buf[s:i].decode("ascii", errors="ignore"))
        else:
            i += 1
    return out[:4]


def _utf16_candidates(buf: bytes) -> list[str]:
    out = []
    for i in range(0, max(0, len(buf) - 2), 2):
        chars = []
        j = i
        while j + 1 < len(buf):
            code = struct.unpack("<H", buf[j : j + 2])[0]
            if code == 0:
                break
            if 32 <= code <= 126 or 0xAC00 <= code <= 0xD7A3:
                chars.append(chr(code))
                j += 2
            else:
                break
        if len(chars) >= 3:
            out.append("".join(chars))
    return out[:3]


def _u32_candidates(buf: bytes) -> list[tuple[int, int]]:
    out = []
    for i in range(0, max(0, len(buf) - 3)):
        val = struct.unpack("<I", buf[i : i + 4])[0]
        if val in (0, 1, 2, 3, 4, 5, 7, 10, 13, 15, 30, 40, 50, 80, 90, 100, 150):
            out.append((i, val))
    return out[:8]


KNOWN_VALUES = [
    ("anchor_x_111.111mm", 0.111111, "strong"),
    ("anchor_y_222.222mm", 0.222222, "strong"),
    ("anchor2_x_211.111mm", 0.211111, "strong"),
    ("anchor2_y_322.222mm", 0.322222, "strong"),
    ("height_10mm", 0.01, "strong"),
    ("height_30mm", 0.03, "strong"),
    ("max_length_50mm", 0.05, "strong"),
    ("width_50_percent", 50.0, "strong"),
    ("width_100_percent", 100.0, "strong"),
    ("width_150_percent", 150.0, "strong"),
    ("spacing_80_percent", 80.0, "strong"),
    ("spacing_100_percent", 100.0, "strong"),
    ("spacing_150_percent", 150.0, "strong"),
    ("slant_15_degree", 15.0, "strong"),
    ("slant_30_degree", 30.0, "strong"),
    ("rotation_30_degree", 30.0, "strong"),
    ("rotation_90_degree", 90.0, "strong"),
    ("underline_default_minus40", -40.0, "strong"),
    ("common_one", 1.0, "low_signal"),
    ("common_zero", 0.0, "low_signal"),
]


def _double_candidates(buf: bytes) -> list[tuple[int, float]]:
    out = []
    for i in range(0, max(0, len(buf) - 7)):
        val = struct.unpack("<d", buf[i : i + 8])[0]
        if math.isfinite(val) and abs(val) < 10000:
            if abs(val) < 1e-12 or abs(val - 1.0) < 1e-12 or abs(val - round(val)) < 1e-12:
                out.append((i, val))
    return out[:8]


def _known_matches(buf: bytes) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for i in range(0, max(0, len(buf) - 7)):
        v = struct.unpack("<d", buf[i : i + 8])[0]
        if not math.isfinite(v):
            continue
        for name, target, signal in KNOWN_VALUES:
            if abs(v - target) < 1e-6:
                out.append({"record_relative_offset": i, "name": name, "value": v, "signal": signal})
    return out[:10]


def _palette_candidates(buf: bytes) -> list[dict[str, Any]]:
    out = []
    for i in range(0, max(0, len(buf) - 3)):
        raw = struct.unpack("<I", buf[i : i + 4])[0]
        c = TYPE3_COLORS_BY_RAW.get(raw) or TYPE3_COLORS_BY_RGB0_RAW.get(raw)
        if c is not None:
            out.append(
                {
                    "record_relative_offset": i,
                    "candidate_raw": f"0x{raw:08X}",
                    "palette_match": c.name,
                }
            )
    return out[:8]


def _record_chunks(payload: bytes, start: int, stride: int) -> list[tuple[int, int, bytes]]:
    out = []
    idx = start
    ridx = 0
    while idx + stride <= len(payload):
        out.append((ridx, idx, payload[idx : idx + stride]))
        idx += stride
        ridx += 1
    return out


def _score_start(payload: bytes, start: int, stride: int) -> dict[str, Any]:
    chunks = _record_chunks(payload, start, stride)
    if len(chunks) < 3:
        return {"start": start, "count": len(chunks), "score": -1}
    stable = 0
    for rel in range(stride):
        values = {chunk[2][rel] for chunk in chunks}
        if len(values) == 1:
            stable += 1
    newline_hits = 0
    for _ri, _s, rec in chunks:
        if 10 in rec or 13 in rec:
            newline_hits += 1
    return {"start": start, "count": len(chunks), "score": stable + newline_hits}


def _best_start(payload: bytes, stride: int) -> dict[str, Any]:
    best = None
    for s in range(0, min(stride, len(payload))):
        c = _score_start(payload, s, stride)
        if best is None or c["score"] > best["score"]:
            best = c
    return best or {"start": 0, "count": 0, "score": -1}


def _record_diff(left: bytes, right: bytes, start: int, stride: int) -> list[dict[str, Any]]:
    lrecs = _record_chunks(left, start, stride)
    rrecs = _record_chunks(right, start, stride)
    n = min(len(lrecs), len(rrecs))
    out: list[dict[str, Any]] = []
    for i in range(n):
        l = lrecs[i][2]
        r = rrecs[i][2]
        diffs = []
        ds = -1
        for off in range(stride):
            if l[off] != r[off]:
                if ds < 0:
                    ds = off
            elif ds >= 0:
                diffs.append((ds, off))
                ds = -1
        if ds >= 0:
            diffs.append((ds, stride))
        if diffs:
            changed_offsets = sorted({o for a, b in diffs for o in range(a, b)})
            out.append(
                {
                    "record_index": i,
                    "changed_record_relative_offsets": changed_offsets[:32],
                    "changed_byte_ranges": diffs[:10],
                }
            )
    return out


def main() -> int:
    print("CParagraphe 204-byte Record Analyzer")
    print("Policy: absolute offset is diagnostic only.")
    print("Primary axes: class_payload_relative_offset / record_index / record_relative_offset")
    print("=" * 90)

    payloads: dict[str, dict[str, Any]] = {}
    start47_count = 0

    for name in TARGET_FILES:
        blob = _read_hex_fixture(name)
        node = _extract_first_cparagraphe(blob)
        if node is None:
            continue
        payload = node["payload"]
        payloads[name] = node
        best = _best_start(payload, STRIDE)
        uses_47 = best["start"] == START_SINGLE
        if uses_47:
            start47_count += 1
        print(f"[FILE] {name}")
        print(
            f"  payload_length={len(payload)} candidate_stride={STRIDE} "
            f"candidate_start_offset=47 best_candidate_start_offset={best['start']} "
            f"candidate_record_count(start=47)={len(_record_chunks(payload, 47, STRIDE))} "
            f"candidate_record_count(best)={best['count']}"
        )
        print("  note: absolute_offset is diagnostic only.")

        starts = [47] if name != "text_multiline_basic.txt" else [47, best["start"]]
        seen = set()
        for start in starts:
            if start in seen:
                continue
            seen.add(start)
            recs = _record_chunks(payload, start, STRIDE)
            print(f"  [record_dump] candidate_start_offset={start} candidate_stride={STRIDE}")
            for ridx, rec_start, rec in recs:
                rec_end = rec_start + STRIDE
                abs_start = node["class_payload_start_absolute"] + rec_start
                print(
                    f"    - record_index={ridx} class_payload_relative_start={rec_start} "
                    f"class_payload_relative_end={rec_end} absolute_offset={abs_start} (diagnostic only)"
                )
                ascii_vals = _ascii_candidates(rec)
                utf16_vals = _utf16_candidates(rec)
                u32_vals = _u32_candidates(rec)
                dbl_vals = _double_candidates(rec)
                known_vals = _known_matches(rec)
                palette_vals = _palette_candidates(rec)
                if ascii_vals:
                    print(f"      ascii_candidates={ascii_vals}")
                if utf16_vals:
                    print(f"      utf16_candidates={utf16_vals}")
                if u32_vals:
                    print(
                        "      u32_candidates="
                        + str([{"record_relative_offset": o, "u32": v} for o, v in u32_vals])
                    )
                if dbl_vals:
                    print(
                        "      double_candidates="
                        + str([{"record_relative_offset": o, "double": v} for o, v in dbl_vals])
                    )
                if known_vals:
                    print(f"      known_value_matches={known_vals}")
                if palette_vals:
                    print(f"      palette_candidates={palette_vals}")
            if name == "text_multiline_basic.txt":
                print(
                    "  multiline_note: comparing start_offset=47 vs best_candidate_start_offset "
                    "to test multiline header/paragraph shift (provisional)."
                )

    print("\n[Record-relative diff matrix]")
    field_observations: dict[int, dict[str, Any]] = defaultdict(
        lambda: {"fixtures": set(), "tags": set(), "samples": []}
    )

    for left, right, tag in DIFF_PAIRS:
        ln = payloads.get(left)
        rn = payloads.get(right)
        if ln is None or rn is None:
            continue
        lp = ln["payload"]
        rp = rn["payload"]
        best_left = _best_start(lp, STRIDE)
        best_right = _best_start(rp, STRIDE)
        # For multiline pair, show both 47 and best; otherwise use 47 baseline.
        selected_start = 47
        if right == "text_multiline_basic.txt":
            selected_start = best_right["start"]
        diffs = _record_diff(lp, rp, selected_start, STRIDE)
        changed_records = [d["record_index"] for d in diffs]
        changed_offsets = sorted(
            {off for d in diffs for off in d["changed_record_relative_offsets"]}
        )
        if len(changed_records) >= 3 and len(changed_offsets) >= 3:
            level = "cross_fixture_candidate"
        elif len(changed_records) >= 2:
            level = "repeated_within_fixture"
        elif len(changed_records) == 1:
            level = "weak"
        else:
            level = "unresolved"
        if tag in {"height", "width", "slant", "spacing", "rotation"} and len(changed_offsets) <= 6 and len(changed_offsets) > 0:
            level = "strong_candidate"

        print(f"- left={left} right={right}")
        print(
            f"  selected_candidate_start_offset={selected_start} stride={STRIDE} "
            f"record_count_left={len(_record_chunks(lp, selected_start, STRIDE))} "
            f"record_count_right={len(_record_chunks(rp, selected_start, STRIDE))}"
        )
        print(f"  changed_record_indexes={changed_records[:20]}")
        print(f"  changed_record_relative_offsets={changed_offsets[:40]}")
        print(f"  evidence_level={level}")

        for d in diffs[:6]:
            print(
                f"    * record_index={d['record_index']} "
                f"changed_byte_ranges={d['changed_byte_ranges']} "
                f"changed_record_relative_offsets={d['changed_record_relative_offsets'][:20]}"
            )
            # interpret nearby candidates from right record
            rchunks = _record_chunks(rp, selected_start, STRIDE)
            if d["record_index"] < len(rchunks):
                rec = rchunks[d["record_index"]][2]
                print(f"      nearby_known={_known_matches(rec)[:4]}")
                print(f"      nearby_palette={_palette_candidates(rec)[:3]}")
                print(
                    f"      nearby_strings={{'ascii': {_ascii_candidates(rec)[:2]}, 'utf16': {_utf16_candidates(rec)[:2]}}}"
                )

        for off in changed_offsets:
            fo = field_observations[off]
            fo["fixtures"].add((left, right))
            fo["tags"].add(tag)
            fo["samples"].append(level)

    print("\n[Field map candidate summary]")
    print("  note: provisional candidate map only; no confirmed parser fields.")
    for off in sorted(field_observations.keys())[:80]:
        fo = field_observations[off]
        tags = sorted(fo["tags"])
        lvl = "unresolved"
        if "strong_candidate" in fo["samples"]:
            lvl = "strong_candidate"
        elif "cross_fixture_candidate" in fo["samples"]:
            lvl = "cross_fixture_candidate"
        elif "repeated_within_fixture" in fo["samples"]:
            lvl = "repeated_within_fixture"
        elif "weak" in fo["samples"]:
            lvl = "weak"
        meaning = "provisional_unknown"
        if "height" in tags:
            meaning = "candidate_text_height"
        elif "width" in tags:
            meaning = "candidate_width_percent"
        elif "slant" in tags:
            meaning = "candidate_slant_angle"
        elif "spacing" in tags:
            meaning = "candidate_spacing_percent"
        elif "rotation" in tags:
            meaning = "candidate_rotation_angle"
        elif "color" in tags:
            meaning = "candidate_text_color"
        elif "font" in tags:
            meaning = "candidate_font_or_style_flag"
        elif "multiline" in tags:
            meaning = "candidate_linebreak_or_multiline_marker"
        print(
            f"  - record_relative_offset=0x{off:02X} observed_tags={tags} "
            f"candidate_meaning={meaning} evidence={lvl}"
        )

    print("\n[Summary]")
    print(
        f"  start_offset=47 preserved in {start47_count}/{len(payloads)} fixtures (best-candidate basis, provisional)."
    )
    if "text_multiline_basic.txt" in payloads:
        m = payloads["text_multiline_basic.txt"]["payload"]
        b = _best_start(m, STRIDE)
        c47 = len(_record_chunks(m, 47, STRIDE))
        cb = len(_record_chunks(m, b["start"], STRIDE))
        print(
            f"  multiline_compare: start=47 -> record_count={c47}, "
            f"start={b['start']} -> record_count={cb} (provisional)."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

