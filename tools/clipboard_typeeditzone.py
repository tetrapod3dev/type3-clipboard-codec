from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from type3_clipboard_codec.adapters.input_base import InputAdapter
from type3_clipboard_codec.adapters.win32_clipboard import (
    OBSERVED_TYPE_EDIT_ZONE_FORMAT_ID,
    OBSERVED_TYPE_EDIT_ZONE_VERSION_FORMAT_ID,
    TYPE_EDIT_ZONE_FORMAT_NAME,
    TYPE_EDIT_ZONE_VERSION_FORMAT_NAME,
    Win32ClipboardAdapter,
    Win32ClipboardError,
)
from type3_clipboard_codec.services.inspect_service import InspectService


class _BinaryFileInputAdapter(InputAdapter):
    def __init__(self, payload: bytes):
        self._payload = payload

    def fetch_data(self) -> bytes:
        return self._payload


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="TypeEditZone clipboard raw I/O tool")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("probe", help="probe TypeEditZone format registration and clipboard availability")

    dump_parser = subparsers.add_parser("dump", help="dump TypeEditZone clipboard bytes to binary file")
    dump_parser.add_argument("--out", required=True, help="output binary path")

    dump_version_parser = subparsers.add_parser(
        "dump-version", help="dump TypeEditZoneVersion clipboard bytes to binary file"
    )
    dump_version_parser.add_argument("--out", required=True, help="output binary path")

    dump_hex_parser = subparsers.add_parser("dump-hex", help="dump TypeEditZone clipboard bytes as hex text")
    dump_hex_parser.add_argument("--out", required=True, help="output text path")

    load_parser = subparsers.add_parser("load", help="load binary file bytes into TypeEditZone clipboard format")
    load_parser.add_argument("--in", dest="in_path", required=True, help="input binary path")
    load_parser.add_argument("--version-in", dest="version_in_path", help="TypeEditZoneVersion input binary path")

    inspect_parser = subparsers.add_parser("inspect", help="inspect a binary file via existing decoder flow")
    inspect_parser.add_argument("--in", dest="in_path", required=True, help="input binary path")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        adapter = Win32ClipboardAdapter()

        if args.command == "probe":
            format_id = adapter.get_typeeditzone_format_id()
            version_format_id = adapter.get_typeeditzone_version_format_id()
            has_format = adapter.has_typeeditzone()
            has_version_format = adapter.has_typeeditzone_version()
            formats = adapter.list_formats()
            print(f"format_name={TYPE_EDIT_ZONE_FORMAT_NAME}")
            print(f"registered_format_id={format_id}")
            print(f"observed_format_id={OBSERVED_TYPE_EDIT_ZONE_FORMAT_ID}")
            print(f"has_typeeditzone={str(has_format).lower()}")
            print(f"version_format_name={TYPE_EDIT_ZONE_VERSION_FORMAT_NAME}")
            print(f"version_registered_format_id={version_format_id}")
            print(f"version_observed_format_id={OBSERVED_TYPE_EDIT_ZONE_VERSION_FORMAT_ID}")
            print(f"has_typeeditzone_version={str(has_version_format).lower()}")
            print(f"clipboard_formats={formats}")
            return 0

        if args.command == "dump":
            payload = adapter.read_typeeditzone_bytes()
            out_path = Path(args.out)
            out_path.write_bytes(payload)
            print(f"dumped_bytes={len(payload)}")
            print(f"out={out_path}")
            return 0

        if args.command == "dump-version":
            payload = adapter.read_typeeditzone_version_bytes()
            out_path = Path(args.out)
            out_path.write_bytes(payload)
            print(f"dumped_version_bytes={len(payload)}")
            print(f"out={out_path}")
            return 0

        if args.command == "dump-hex":
            payload = adapter.read_typeeditzone_bytes()
            out_path = Path(args.out)
            out_path.write_text(payload.hex(), encoding="utf-8")
            print(f"dumped_bytes={len(payload)}")
            print(f"out={out_path}")
            return 0

        if args.command == "load":
            in_path = Path(args.in_path)
            payload = in_path.read_bytes()
            version_payload = None
            version_in_path = None
            if args.version_in_path is not None:
                version_in_path = Path(args.version_in_path)
                version_payload = version_in_path.read_bytes()
                adapter.write_typeeditzone_bundle(payload, version_payload)
            else:
                adapter.write_typeeditzone_bytes(payload)
            print(f"loaded_bytes={len(payload)}")
            print(f"in={in_path}")
            if version_payload is not None and version_in_path is not None:
                print(f"loaded_version_bytes={len(version_payload)}")
                print(f"version_in={version_in_path}")
            return 0

        if args.command == "inspect":
            in_path = Path(args.in_path)
            payload = in_path.read_bytes()
            service = InspectService()
            text = service.inspect(_BinaryFileInputAdapter(payload), verbose=True)
            print(text)
            return 0

        parser.print_help()
        return 1
    except FileNotFoundError as exc:
        print(f"[ERROR] File not found: {exc}", file=sys.stderr)
        return 2
    except Win32ClipboardError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 3
    except Exception as exc:
        print(f"[ERROR] Unexpected failure: {exc}", file=sys.stderr)
        return 4


if __name__ == "__main__":
    raise SystemExit(main())
