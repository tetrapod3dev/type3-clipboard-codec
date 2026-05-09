import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from type3_clipboard_codec import parse_type3_clipboard_bytes_with_parser
from type3_clipboard_codec.inspect.hex_input import hex_text_to_bytes
from type3_clipboard_codec.parsers.type3_chain_parser import Type3ChainParser


TEXT_SAMPLES_DIR = REPO_ROOT / "tests" / "samples" / "text"


def _ascii_strings(data: bytes, min_len: int = 3) -> list[str]:
    out: list[str] = []
    buf: list[int] = []
    for b in data:
        if 32 <= b <= 126:
            buf.append(b)
            continue
        if len(buf) >= min_len:
            out.append(bytes(buf).decode("ascii", errors="ignore"))
        buf = []
    if len(buf) >= min_len:
        out.append(bytes(buf).decode("ascii", errors="ignore"))
    return out


def _font_candidates(data: bytes) -> list[str]:
    deny = {"CZone", "CCourbe", "CContour", "CPropertyExtend", "CParagraphe", "OBJECTINFOS_CLASSNAME", "CObDao"}
    fonts: list[str] = []
    for s in _ascii_strings(data, min_len=3):
        if s in deny:
            continue
        if "Arial" in s or s.startswith("HY"):
            if s not in fonts:
                fonts.append(s)
    return fonts


def _text_candidates_from_paragraphe(data: bytes) -> list[str]:
    parser = Type3ChainParser()
    nodes = parser._extract_nodes(data[6:])
    runs: list[str] = []
    for node in nodes:
        if node.header.class_name != "CParagraphe":
            continue
        for recs in parser._read_paragraphe_slot_record_runs(node.payload):
            run = parser._records_to_text_run(recs)
            if run is None:
                continue
            text = run["text"]
            if text not in runs:
                runs.append(text)
    return runs


def _color_candidates(parsed_obj) -> list[dict]:
    items: list[dict] = []
    for chain in getattr(parsed_obj, "object_chains", []) or []:
        for c in chain.style.color_candidates:
            rec = {
                "offset": c.get("offset"),
                "raw_hex": c.get("raw_hex"),
                "name": c.get("name"),
                "hex_rgb": c.get("hex_rgb"),
                "confidence": c.get("confidence"),
                "source": c.get("source"),
            }
            if rec not in items:
                items.append(rec)
    return items


def build_inventory_entry(path: Path) -> dict:
    raw_hex = path.read_text(encoding="utf-8")
    data = hex_text_to_bytes(raw_hex)
    parsed, parser_name = parse_type3_clipboard_bytes_with_parser(data)
    markers = list(getattr(parsed, "markers", []) or [])
    text_candidates = _text_candidates_from_paragraphe(data)
    return {
        "file": path.name,
        "normalized_bytes": len(data),
        "parser": parser_name,
        "declared_object_count": getattr(parsed, "declared_object_count", None),
        "markers": markers,
        "has_CZone": "CZone" in markers,
        "has_CParagraphe": "CParagraphe" in markers,
        "has_CCourbe": "CCourbe" in markers,
        "has_CContour": "CContour" in markers,
        "has_CPropertyExtend": "CPropertyExtend" in markers,
        "font_candidates_ascii": _font_candidates(data),
        "visible_text_candidates": text_candidates,
        "color_candidates": _color_candidates(parsed),
    }


def render_text(entries: list[dict]) -> str:
    lines: list[str] = []
    lines.append("=" * 72)
    lines.append("Type3 Text Fixture Inventory")
    lines.append("=" * 72)
    for item in entries:
        lines.append(f"[{item['file']}]")
        lines.append(f"  bytes: {item['normalized_bytes']}")
        lines.append(f"  parser: {item['parser']}")
        lines.append(f"  declared_object_count: {item['declared_object_count']}")
        lines.append(f"  markers: {', '.join(item['markers']) if item['markers'] else 'none'}")
        lines.append(
            "  has: "
            f"CZone={item['has_CZone']} "
            f"CParagraphe={item['has_CParagraphe']} "
            f"CCourbe={item['has_CCourbe']} "
            f"CContour={item['has_CContour']} "
            f"CPropertyExtend={item['has_CPropertyExtend']}"
        )
        lines.append(f"  font_candidates: {item['font_candidates_ascii'] or []}")
        lines.append(f"  visible_text_candidates: {item['visible_text_candidates'] or []}")
        lines.append(f"  color_candidates: {len(item['color_candidates'])}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scan tests/samples/text fixtures and print quick inventory.")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)

    entries = [build_inventory_entry(path) for path in sorted(TEXT_SAMPLES_DIR.glob("*.txt"))]
    if args.as_json:
        print(json.dumps(entries, ensure_ascii=False, indent=2))
    else:
        print(render_text(entries))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
