import struct
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from type3_clipboard_codec import parse_type3_clipboard_bytes_with_parser
from type3_clipboard_codec.inspect.hex_input import hex_text_to_bytes
from type3_clipboard_codec.models.colors import TYPE3_COLORS_BY_RAW, TYPE3_COLORS_BY_RGB0_RAW
from type3_clipboard_codec.parsers.type3_chain_parser import Type3ChainParser


TEXT_DIR = REPO_ROOT / "tests" / "samples" / "text"
PAIRS = [
    ("text_color_army_green.txt", "text_color_navy_blue.txt"),
    ("text_group_same_color_two_objects.txt", "text_group_mixed_color_two_objects.txt"),
    ("text_group_same_color_two_objects.txt", "text_two_objects_mixed_color_not_grouped.txt"),
]


def _read(name: str) -> bytes:
    return hex_text_to_bytes((TEXT_DIR / name).read_text(encoding="utf-8"))


def _ranges(a: bytes, b: bytes) -> list[tuple[int, int]]:
    n = min(len(a), len(b))
    out: list[tuple[int, int]] = []
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


def _node_spans(data: bytes) -> list[tuple[int, int, str]]:
    nodes = Type3ChainParser()._extract_nodes(data[6:])
    return [(n.start_offset + 6, n.end_offset + 6, n.header.class_name) for n in nodes]


def _class(off: int, spans: list[tuple[int, int, str]]) -> str:
    if off < 6:
        return "pre-CZone header"
    for s, e, c in spans:
        if s <= off < e:
            return c
    return "unknown/trailing region"


def _class_payload_relative_offset(absolute_offset: int, spans: list[tuple[int, int, str]]) -> int | None:
    for s, e, _cls in spans:
        if s <= absolute_offset < e:
            return absolute_offset - s
    return None


def _color_like_vals(data: bytes, s: int, e: int) -> list[str]:
    out: list[str] = []
    for i in range(s, max(s, e - 3)):
        if i + 4 > len(data):
            break
        raw = struct.unpack("<I", data[i : i + 4])[0]
        c = TYPE3_COLORS_BY_RAW.get(raw) or TYPE3_COLORS_BY_RGB0_RAW.get(raw)
        if c:
            out.append(
                f"offset={i} raw=0x{raw:08X} name={c.name} hex=#{c.hex_rgb}"
            )
    return out[:6]


def _print_summary(name: str, data: bytes) -> None:
    obj, _parser = parse_type3_clipboard_bytes_with_parser(data)
    print(f"  - {name}: size={len(data)} declared={getattr(obj,'declared_object_count',None)} parsed_chain_candidate_count={len(getattr(obj,'object_chains',[]) or [])}")
    print(f"    class_markers={getattr(obj,'markers',[])}")


def main() -> int:
    print("Type3 Text Color Comparison Diagnostic")
    print("=" * 72)
    for a_name, b_name in PAIRS:
        a = _read(a_name)
        b = _read(b_name)
        a_spans = _node_spans(a)
        b_spans = _node_spans(b)
        d = _ranges(a, b)
        print(f"[COMPARE] {a_name}  <->  {b_name}")
        _print_summary(a_name, a)
        _print_summary(b_name, b)
        print(f"  changed_ranges={len(d)}")
        for idx, (s, e) in enumerate(d[:16], start=1):
            cls_a = _class(s, a_spans)
            cls_b = _class(s, b_spans)
            ctx_s = max(0, s - 8)
            ctx_e = min(len(b), e + 8)
            print(f"    - #{idx}: [{s},{e}) len={e-s} a={cls_a} b={cls_b}")
            print(f"      absolute_offset={s} chain_relative_offset={s-6} class_payload_relative_offset={_class_payload_relative_offset(s, b_spans)}")
            print(f"      context_hex={b[ctx_s:ctx_e].hex()}")
            color_hits = _color_like_vals(b, s, e)
            if color_hits:
                print("      color_like_values:")
                for hit in color_hits:
                    print(f"        * {hit}")
        if len(d) > 16:
            print(f"    ... {len(d)-16} more ranges")
        print("  notes:")
        print("    - Byte-range classification is observed evidence only.")
        print("    - absolute offset is diagnostic only; do not promote it to parser rule.")
        print("    - Semantic color ownership across multiple text objects is provisional.")
        print("")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
