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
TARGET_FILES = [
    "default_text.txt",
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
    ("default_text.txt", "text_height_30mm.txt"),
    ("default_text.txt", "text_width_50_percent.txt"),
    ("default_text.txt", "text_width_150_percent.txt"),
    ("default_text.txt", "text_slant_15deg.txt"),
    ("default_text.txt", "text_slant_custom_30deg.txt"),
    ("default_text.txt", "text_spacing_80_percent.txt"),
    ("default_text.txt", "text_spacing_150_percent.txt"),
    ("default_text.txt", "text_color_army_green.txt"),
    ("text_color_army_green.txt", "text_color_navy_blue.txt"),
    ("text_font_arial.txt", "text_font_arial_bold.txt"),
    ("default_text.txt", "text_multiline_basic.txt"),
]

STRIDES = [16, 20, 24, 28, 32, 36, 40, 48, 64, 80, 96, 128, 160, 204, 256]


def _read_hex_fixture(name: str) -> bytes:
    return hex_text_to_bytes((TEXT_DIR / name).read_text(encoding="utf-8"))


def _extract_cparagraphe_nodes(blob: bytes) -> list[dict[str, Any]]:
    parser = Type3ChainParser()
    payload = blob[6:] if len(blob) >= 6 else blob
    nodes = parser._extract_nodes(payload)
    out: list[dict[str, Any]] = []
    for i, node in enumerate(nodes):
        if node.header.class_name != "CParagraphe":
            continue
        out.append(
            {
                "chain_index": i,
                "class_name": node.header.class_name,
                "class_start_absolute": node.start_offset + 6,
                "class_payload_start_absolute": node.payload_offset + 6,
                "class_payload_length": len(node.payload),
                "bbox": node.bbox.to_mm_dict() if node.bbox is not None else None,
                "payload": node.payload,
            }
        )
    return out


def _ascii_candidates(data: bytes, min_len: int = 4) -> list[dict[str, Any]]:
    out = []
    i = 0
    while i < len(data):
        if 32 <= data[i] <= 126:
            s = i
            while i < len(data) and 32 <= data[i] <= 126:
                i += 1
            if i - s >= min_len:
                out.append({"class_payload_relative_offset": s, "value": data[s:i].decode("ascii", errors="ignore")})
        else:
            i += 1
    return out[:20]


def _utf16le_candidates(data: bytes, min_chars: int = 3) -> list[dict[str, Any]]:
    out = []
    for i in range(0, max(0, len(data) - 2), 2):
        chars = []
        j = i
        while j + 1 < len(data):
            code = struct.unpack("<H", data[j : j + 2])[0]
            if code == 0:
                break
            if 32 <= code <= 126 or 0xAC00 <= code <= 0xD7A3:
                chars.append(chr(code))
                j += 2
            else:
                break
        if len(chars) >= min_chars:
            out.append({"class_payload_relative_offset": i, "value": "".join(chars)})
    uniq = []
    seen = set()
    for item in out:
        key = (item["class_payload_relative_offset"], item["value"])
        if key not in seen:
            seen.add(key)
            uniq.append(item)
    return uniq[:20]


def _palette_hits(data: bytes) -> list[dict[str, Any]]:
    out = []
    for i in range(0, max(0, len(data) - 3)):
        raw = struct.unpack("<I", data[i : i + 4])[0]
        color = TYPE3_COLORS_BY_RAW.get(raw) or TYPE3_COLORS_BY_RGB0_RAW.get(raw)
        if color:
            out.append(
                {
                    "class_payload_relative_offset": i,
                    "candidate_raw": f"0x{raw:08X}",
                    "palette_match": color.name,
                }
            )
    return out[:30]


def _known_numeric_hits(data: bytes) -> list[dict[str, Any]]:
    # mm and degree/percent candidates -> meter/value forms
    targets = [
        ("anchor_x_mm", 111.111, 0.111111),
        ("anchor_y_mm", 222.222, 0.222222),
        ("height_10mm", 10.0, 0.01),
        ("height_30mm", 30.0, 0.03),
        ("max_len_50mm", 50.0, 0.05),
        ("width_50_percent", 50.0, 50.0),
        ("width_100_percent", 100.0, 100.0),
        ("width_150_percent", 150.0, 150.0),
        ("slant_15", 15.0, 15.0),
        ("slant_30", 30.0, 30.0),
        ("spacing_80", 80.0, 80.0),
        ("spacing_100", 100.0, 100.0),
        ("spacing_150", 150.0, 150.0),
        ("rotation_30", 30.0, 30.0),
        ("rotation_90", 90.0, 90.0),
        ("underline_default_minus40", -40.0, -40.0),
    ]
    out = []
    for i in range(0, max(0, len(data) - 7)):
        val = struct.unpack("<d", data[i : i + 8])[0]
        if not math.isfinite(val):
            continue
        for name, a, b in targets:
            if abs(val - a) < 1e-6 or abs(val - b) < 1e-6:
                out.append({"class_payload_relative_offset": i, "kind": name, "double_value": val})
    return out[:40]


def _u32_hits(data: bytes) -> list[dict[str, Any]]:
    out = []
    for i in range(0, max(0, len(data) - 3)):
        v = struct.unpack("<I", data[i : i + 4])[0]
        if v in (0, 1, 2, 3, 4, 5, 7, 10, 13, 30, 50, 80, 90, 100, 150):
            out.append({"class_payload_relative_offset": i, "u32": v})
    return out[:60]


def _stride_candidates(data: bytes) -> list[dict[str, Any]]:
    cands: list[dict[str, Any]] = []
    for stride in STRIDES:
        best = None
        for start in range(0, min(stride, len(data))):
            chunks = []
            idx = start
            while idx + stride <= len(data):
                chunks.append(data[idx : idx + stride])
                idx += stride
            if len(chunks) < 3:
                continue
            stable = []
            changed = []
            for rel in range(stride):
                vals = {chunk[rel] for chunk in chunks}
                if len(vals) == 1:
                    stable.append(rel)
                else:
                    changed.append(rel)
            score = len(stable)
            if best is None or score > best["score"]:
                best = {
                    "candidate_stride": stride,
                    "candidate_start_offset": start,
                    "candidate_record_count": len(chunks),
                    "repeated_relative_offsets": stable[:16],
                    "changed_relative_offsets": changed[:16],
                    "score": score,
                }
        if best is not None:
            if best["candidate_record_count"] >= 8 and best["score"] >= max(4, stride // 8):
                level = "cross_fixture_candidate"
            elif best["candidate_record_count"] >= 5 and best["score"] >= 3:
                level = "repeated_candidate"
            elif best["candidate_record_count"] >= 3:
                level = "weak_pattern"
            else:
                level = "unresolved"
            best["evidence_level"] = level
            cands.append(best)
    cands.sort(key=lambda x: (-x["score"], -x["candidate_record_count"]))
    return cands[:10]


def _ranges(a: bytes, b: bytes) -> list[tuple[int, int]]:
    n = min(len(a), len(b))
    out = []
    s = -1
    for i in range(n):
        if a[i] != b[i]:
            if s < 0:
                s = i
        elif s >= 0:
            out.append((s, i))
            s = -1
    if s >= 0:
        out.append((s, n))
    if len(a) != len(b):
        out.append((n, max(len(a), len(b))))
    return out


def main() -> int:
    print("CParagraphe Structure Analysis")
    print("Policy: absolute offset is diagnostic only.")
    print("Priority: class_payload_relative_offset, record_relative_offset")
    print("=" * 78)

    extracted: dict[str, list[dict[str, Any]]] = {}
    for name in TARGET_FILES:
        blob = _read_hex_fixture(name)
        nodes = _extract_cparagraphe_nodes(blob)
        extracted[name] = nodes
        print(f"[FILE] {name}")
        if not nodes:
            print("  - CParagraphe: not found")
            continue
        for n in nodes:
            payload = n["payload"]
            print(
                f"  - chain_index={n['chain_index']} class={n['class_name']} "
                f"absolute_class_start={n['class_start_absolute']} "
                f"absolute_payload_start={n['class_payload_start_absolute']} "
                f"class_payload_length={n['class_payload_length']}"
            )
            print(f"    bbox={n['bbox']}")
            print("    offsets: absolute_offset / chain_relative_offset / class_payload_relative_offset")
            print("    ascii_candidates:")
            for item in _ascii_candidates(payload)[:8]:
                abs_off = n["class_payload_start_absolute"] + item["class_payload_relative_offset"]
                print(
                    f"      - absolute_offset={abs_off} "
                    f"chain_relative_offset={abs_off-6} "
                    f"class_payload_relative_offset={item['class_payload_relative_offset']} "
                    f"value={item['value']!r}"
                )
            utf16 = _utf16le_candidates(payload)
            print(f"    utf16_or_korean_evidence_count={len(utf16)}")
            known = _known_numeric_hits(payload)
            print(f"    known_numeric_candidate_count={len(known)}")
            colors = _palette_hits(payload)
            print(f"    palette_candidate_count={len(colors)}")
            print("    stride_candidates:")
            for s in _stride_candidates(payload)[:5]:
                print(
                    f"      - candidate_stride={s['candidate_stride']} "
                    f"candidate_start_offset={s['candidate_start_offset']} "
                    f"candidate_record_count={s['candidate_record_count']} "
                    f"evidence_level={s['evidence_level']}"
                )

    print("\n[Cross-fixture diff by class_payload_relative_offset]")
    for left, right in DIFF_PAIRS:
        l_nodes = extracted.get(left) or []
        r_nodes = extracted.get(right) or []
        if not l_nodes or not r_nodes:
            continue
        lp = l_nodes[0]["payload"]
        rp = r_nodes[0]["payload"]
        diff = _ranges(lp, rp)
        print(f"- left={left} right={right}")
        print(f"  CParagraphe payload length: left={len(lp)} right={len(rp)}")
        print(f"  changed_ranges={len(diff)}")
        for i, (s, e) in enumerate(diff[:8], start=1):
            print(f"    * #{i} class_payload_relative_range=[{s},{e})")
            # nearby numeric/color/string evidence
            local_colors = [c for c in _palette_hits(rp) if s - 4 <= c["class_payload_relative_offset"] <= e + 4][:3]
            local_u32 = [u for u in _u32_hits(rp) if s - 4 <= u["class_payload_relative_offset"] <= e + 4][:3]
            local_ascii = [a for a in _ascii_candidates(rp) if s - 8 <= a["class_payload_relative_offset"] <= e + 8][:2]
            if local_colors:
                print(f"      color_candidates_nearby={local_colors}")
            if local_u32:
                print(f"      u32_candidates_nearby={local_u32}")
            if local_ascii:
                print(f"      string_candidates_nearby={local_ascii}")
        print("  note: absolute_offset is diagnostic only; parser rule is not confirmed.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

