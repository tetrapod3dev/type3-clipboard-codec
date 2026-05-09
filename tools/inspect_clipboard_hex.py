import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from type3_clipboard_codec import parse_type3_clipboard_bytes_with_parser
from type3_clipboard_codec.exceptions import InvalidHexError, Type3CodecError
from type3_clipboard_codec.inspect.formatters import (
    build_diff_dict,
    render_diff_text,
    render_inspection_text,
    render_style_debug_text,
    to_inspection_dict,
)
from type3_clipboard_codec.inspect.hex_input import hex_text_to_bytes


def _read_hex_text_interactive() -> str:
    print("=" * 60)
    print("TYPE3 Clipboard Hex Inspector")
    print("=" * 60)
    print("Paste Type3 clipboard hex text. End input with an empty line.")
    print("- whitespace and 0x prefixes are ignored")
    print("- invalid/non-hex input will be rejected")
    print("-" * 60)
    lines: list[str] = []
    while True:
        try:
            line = input("> ")
        except EOFError:
            break
        if line.strip() == "":
            break
        lines.append(line)
    return "\n".join(lines)


def _parse_hex_source(raw_hex_text: str, source_label: str) -> tuple[dict, bytes]:
    data = hex_text_to_bytes(raw_hex_text)
    if not data:
        raise InvalidHexError("No hex payload provided after normalization.")
    parsed, parser_name = parse_type3_clipboard_bytes_with_parser(data)
    return to_inspection_dict(parsed, parser_name=parser_name, source=source_label), data


def _parse_file(path: Path) -> tuple[dict, bytes]:
    raw = path.read_text(encoding="utf-8")
    return _parse_hex_source(raw, source_label=str(path))


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Inspect Type3 clipboard hex data quickly.")
    parser.add_argument("path", nargs="?", help="hex fixture file path; omit for interactive paste mode")
    parser.add_argument("--json", action="store_true", dest="as_json", help="output machine-readable JSON")
    parser.add_argument(
        "--debug-style",
        action="store_true",
        help="print CPropertyExtend style/color candidate debug info",
    )
    parser.add_argument(
        "--diff",
        nargs=2,
        metavar=("LEFT", "RIGHT"),
        help="compare two hex fixture files (especially useful for 결합 structure analysis)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        if args.diff:
            left_path = Path(args.diff[0])
            right_path = Path(args.diff[1])
            left_payload, left_data = _parse_file(left_path)
            right_payload, right_data = _parse_file(right_path)
            diff = build_diff_dict(
                left_label=str(left_path),
                left_payload=left_payload,
                left_data=left_data,
                right_label=str(right_path),
                right_payload=right_payload,
                right_data=right_data,
            )
            if args.as_json:
                print(json.dumps(diff, ensure_ascii=False, indent=2))
            else:
                print(render_diff_text(diff))
            return 0

        if args.path:
            payload, _data = _parse_file(Path(args.path))
        else:
            pasted = _read_hex_text_interactive()
            payload, _data = _parse_hex_source(pasted, source_label="<paste>")

        if args.as_json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(render_inspection_text(payload))
            if args.debug_style:
                print()
                print(render_style_debug_text(payload))
        return 0
    except FileNotFoundError as exc:
        print(f"[ERROR] File not found: {exc}", file=sys.stderr)
        return 2
    except (InvalidHexError, Type3CodecError, ValueError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"[ERROR] Unexpected failure: {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
