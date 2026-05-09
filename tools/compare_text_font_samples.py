import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from type3_clipboard_codec.inspect.hex_input import hex_text_to_bytes
from type3_clipboard_codec.parsers.type3_chain_parser import Type3ChainParser


TEXT_DIR = REPO_ROOT / "tests" / "samples" / "text"
BASELINE = "text_font_arial.txt"
TARGETS = [
    "text_font_arial_bold.txt",
    "text_font_hy_gyeongo_dik.txt",
    "text_font_hy_teuktae_gothic.txt",
    "text_font_hy_tae_gothic.txt",
    "text_font_hy_se_gothic.txt",
]


def _read_sample(name: str) -> bytes:
    return hex_text_to_bytes((TEXT_DIR / name).read_text(encoding="utf-8"))


def _ascii_strings(data: bytes, min_len: int = 3) -> list[str]:
    out: list[str] = []
    buf: list[int] = []
    for b in data:
        if 32 <= b <= 126:
            buf.append(b)
        else:
            if len(buf) >= min_len:
                out.append(bytes(buf).decode("ascii", errors="ignore"))
            buf = []
    if len(buf) >= min_len:
        out.append(bytes(buf).decode("ascii", errors="ignore"))
    return out


def _diff_ranges(a: bytes, b: bytes) -> list[tuple[int, int]]:
    n = min(len(a), len(b))
    ranges: list[tuple[int, int]] = []
    start = -1
    for i in range(n):
        if a[i] != b[i]:
            if start < 0:
                start = i
        elif start >= 0:
            ranges.append((start, i))
            start = -1
    if start >= 0:
        ranges.append((start, n))
    if len(a) != len(b):
        ranges.append((n, max(len(a), len(b))))
    return ranges


def _node_spans(data: bytes) -> list[tuple[int, int, str]]:
    parser = Type3ChainParser()
    nodes = parser._extract_nodes(data[6:])
    return [(n.start_offset + 6, n.end_offset + 6, n.header.class_name) for n in nodes]


def _classify_offset(off: int, spans: list[tuple[int, int, str]]) -> str:
    if off < 6:
        return "pre-CZone header area"
    for s, e, c in spans:
        if s <= off < e:
            return c
    return "outside-known-node-range"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Compare text font fixtures against text_font_arial.txt baseline.")
    ap.add_argument("--baseline", default=BASELINE)
    ap.add_argument("--targets", nargs="*", default=TARGETS)
    args = ap.parse_args(argv)

    base = _read_sample(args.baseline)
    base_spans = _node_spans(base)

    print(f"Baseline: {args.baseline}")
    print(f"  size: {len(base)} bytes")
    print(f"  ascii_strings(sample): {_ascii_strings(base)[:12]}")
    print("")

    for name in args.targets:
        data = _read_sample(name)
        spans = _node_spans(data)
        diffs = _diff_ranges(base, data)
        print(f"[{name}]")
        print(f"  size: {len(data)} bytes")
        print(f"  ascii_strings(sample): {_ascii_strings(data)[:12]}")
        print(f"  changed_ranges: {len(diffs)}")
        for i, (s, e) in enumerate(diffs[:12], start=1):
            where = _classify_offset(s, spans if spans else base_spans)
            ctx_s = max(0, s - 8)
            ctx_e = min(len(data), e + 8)
            print(f"    - #{i}: [{s}, {e}) len={e-s} class={where}")
            print(f"      context_hex={data[ctx_s:ctx_e].hex()}")
        if len(diffs) > 12:
            print(f"    ... {len(diffs)-12} more ranges")
        print("  notes:")
        print("    - Changed ranges are observational only; semantic mapping is provisional.")
        print("    - CParagraphe/CPropertyExtend-adjacent changes are candidates for font/style encoding.")
        print("")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

