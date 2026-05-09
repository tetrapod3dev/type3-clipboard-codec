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
from type3_clipboard_codec.models.colors import TYPE3_PALETTE
from type3_clipboard_codec.parsers.type3_chain_parser import Type3ChainParser

TEXT_DIR = REPO_ROOT / "tests" / "samples" / "text"
PAIRS = [
    ("text_color_army_green.txt", "text_color_navy_blue.txt"),
    ("default_text.txt", "text_color_army_green.txt"),
    ("default_text.txt", "text_color_navy_blue.txt"),
]


def _read(name: str) -> bytes:
    return hex_text_to_bytes((TEXT_DIR / name).read_text(encoding="utf-8"))


def _declared_count(data: bytes) -> int | None:
    if len(data) < 6:
        return None
    try:
        return struct.unpack("<I", data[2:6])[0]
    except Exception:
        return None


def _changed_ranges(a: bytes, b: bytes) -> list[tuple[int, int]]:
    n = min(len(a), len(b))
    out: list[tuple[int, int]] = []
    start = -1
    for i in range(n):
        if a[i] != b[i]:
            if start < 0:
                start = i
        elif start >= 0:
            out.append((start, i))
            start = -1
    if start >= 0:
        out.append((start, n))
    if len(a) != len(b):
        out.append((n, max(len(a), len(b))))
    return out


def _node_spans(data: bytes) -> list[tuple[int, int, str]]:
    nodes = Type3ChainParser()._extract_nodes(data[6:])
    return [(n.start_offset + 6, n.end_offset + 6, n.header.class_name) for n in nodes]


def _region(offset: int, spans: list[tuple[int, int, str]]) -> str:
    if offset < 6:
        return "pre-CZone"
    for s, e, cls in spans:
        if s <= offset < e:
            return cls
    return "trailing/unknown"


def _hex_ctx(data: bytes, s: int, e: int, win: int = 12) -> str:
    cs = max(0, s - win)
    ce = min(len(data), e + win)
    return data[cs:ce].hex()


def _palette_encodings() -> dict[str, dict[int, str]]:
    maps: dict[str, dict[int, str]] = {
        "legacy_raw(GBR0)": {},
        "rgb0_raw(RGB0)": {},
        "00RRGGBB": {},
        "00BBGGRR": {},
        "RRGGBB00": {},
        "BBGGRR00": {},
    }
    for color in TYPE3_PALETTE:
        rr = int(color.hex_rgb[0:2], 16)
        gg = int(color.hex_rgb[2:4], 16)
        bb = int(color.hex_rgb[4:6], 16)
        maps["legacy_raw(GBR0)"][color.raw_candidate] = color.name
        maps["rgb0_raw(RGB0)"][color.raw_candidate_rgb0] = color.name
        maps["00RRGGBB"][(rr << 16) | (gg << 8) | bb] = color.name
        maps["00BBGGRR"][(bb << 16) | (gg << 8) | rr] = color.name
        maps["RRGGBB00"][(rr << 24) | (gg << 16) | (bb << 8)] = color.name
        maps["BBGGRR00"][(bb << 24) | (gg << 16) | (rr << 8)] = color.name
    return maps


def _u32_candidates(data: bytes, s: int, e: int) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    start = max(0, s - 4)
    end = min(len(data) - 3, e + 4)
    for off in range(start, max(start, end)):
        raw = struct.unpack("<I", data[off : off + 4])[0]
        out.append({"absolute_offset": off, "raw": raw})
    return out


def _class_payload_relative_offset(absolute_offset: int, spans: list[tuple[int, int, str]]) -> int | None:
    for s, e, _cls in spans:
        if s <= absolute_offset < e:
            return absolute_offset - s
    return None


def _classify_volatile(length: int) -> str:
    if length == 16:
        return "possible GUID/identifier-like 16-byte volatile field"
    if length <= 2:
        return "small field (possibly flag/counter)"
    return "unknown"


def _parsed_summary(data: bytes) -> tuple[int, list[str]]:
    parsed, _ = parse_type3_clipboard_bytes_with_parser(data)
    count = len(getattr(parsed, "object_chains", []) or [])
    markers = sorted(getattr(parsed, "markers", []) or [])
    return count, markers


def main() -> int:
    palette_maps = _palette_encodings()
    print("Type3 Text Color Diff Analysis (Evidence-first)")
    print("=" * 78)
    print("Policy: absolute offset is diagnostic only; parser rules must be class/record-relative.")
    print("")
    for left_name, right_name in PAIRS:
        left = _read(left_name)
        right = _read(right_name)
        ranges = _changed_ranges(left, right)
        left_spans = _node_spans(left)
        right_spans = _node_spans(right)
        left_count, left_markers = _parsed_summary(left)
        right_count, right_markers = _parsed_summary(right)

        print(f"[COMPARE] {left_name}  <->  {right_name}")
        print(f"  normalized_byte_size: left={len(left)}, right={len(right)}")
        print(f"  declared_object_count: left={_declared_count(left)}, right={_declared_count(right)}")
        print(f"  parsed_chain_count: left={left_count}, right={right_count}")
        print(f"  class_chain_markers: left={left_markers}, right={right_markers}")
        print(f"  changed_ranges: {len(ranges)}")

        for idx, (s, e) in enumerate(ranges[:20], start=1):
            region_l = _region(s, left_spans)
            region_r = _region(s, right_spans)
            print(f"    - range#{idx}: [{s}, {e}) size={e-s} left={region_l} right={region_r}")
            print(f"      context_hex(right): {_hex_ctx(right, s, e)}")
            print(f"      volatile_hint: {_classify_volatile(e-s)}")
            candidates = _u32_candidates(right, s, e)
            found = []
            for c in candidates:
                raw = c["raw"]
                for enc_name, enc_map in palette_maps.items():
                    if raw in enc_map:
                        class_payload_rel = _class_payload_relative_offset(c["absolute_offset"], right_spans)
                        found.append(
                            {
                                "absolute_offset": c["absolute_offset"],
                                "chain_relative_offset": c["absolute_offset"] - 6,
                                "class_name": _region(c["absolute_offset"], right_spans),
                                "class_payload_relative_offset": class_payload_rel,
                                "local_context_hex": _hex_ctx(right, c["absolute_offset"], c["absolute_offset"] + 4, win=6),
                                "candidate_raw": f"0x{raw:08X}",
                                "palette_match": enc_map[raw],
                                "encoding": enc_name,
                                "evidence_level": "diagnostic_absolute_match",
                            }
                        )
            if found:
                print("      palette_candidates:")
                for row in found[:12]:
                    print(
                        "        * "
                        f"absolute_offset={row['absolute_offset']} "
                        f"chain_relative_offset={row['chain_relative_offset']} "
                        f"class_name={row['class_name']} "
                        f"class_payload_relative_offset={row['class_payload_relative_offset']} "
                        f"candidate_raw={row['candidate_raw']} "
                        f"palette_match={row['palette_match']} "
                        f"encoding={row['encoding']} "
                        f"evidence_level={row['evidence_level']} "
                        f"local_context_hex={row['local_context_hex']}"
                    )
            else:
                print("      palette_candidates: not found")

        if len(ranges) > 20:
            print(f"    ... {len(ranges)-20} more ranges")

        print("  semantic_candidate_rule:")
        print("    - differs between Army Green/Navy Blue fixture pair")
        print("    - appears in class/style-related region (CParagraphe/CPropertyExtend/etc.)")
        print("    - has palette exact/nearby candidate")
        print("  note:")
        print("    - This tool reports evidence; it does not confirm per-object color ownership.")
        print("    - absolute offset is diagnostic only; class_payload_relative_offset is preferred for hypotheses.")
        print("")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
