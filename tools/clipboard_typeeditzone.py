from __future__ import annotations

import argparse
import json
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

TYPE_EDIT_ZONE_FILE_NAME = "typeeditzone.bin"
TYPE_EDIT_ZONE_VERSION_FILE_NAME = "typeeditzone_version.bin"
MANIFEST_FILE_NAME = "manifest.json"


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

    dump_bundle_parser = subparsers.add_parser("dump-bundle", help="dump TypeEditZone bundle to a directory")
    dump_bundle_parser.add_argument("--dir", dest="dir_path", required=True, help="output directory")

    dump_hex_parser = subparsers.add_parser("dump-hex", help="dump TypeEditZone clipboard bytes as hex text")
    dump_hex_parser.add_argument("--out", required=True, help="output text path")

    load_parser = subparsers.add_parser("load", help="load binary file bytes into TypeEditZone clipboard format")
    load_parser.add_argument("--in", dest="in_path", required=True, help="input binary path")
    load_parser.add_argument("--version-in", dest="version_in_path", help="TypeEditZoneVersion input binary path")

    load_bundle_parser = subparsers.add_parser("load-bundle", help="load TypeEditZone bundle from a directory")
    load_bundle_parser.add_argument("--dir", dest="dir_path", required=True, help="input directory")

    verify_bundle_parser = subparsers.add_parser(
        "verify-bundle", help="compare current clipboard TypeEditZone bundle with a directory"
    )
    verify_bundle_parser.add_argument("--dir", dest="dir_path", required=True, help="bundle directory")

    inspect_parser = subparsers.add_parser("inspect", help="inspect a binary file via existing decoder flow")
    inspect_parser.add_argument("--in", dest="in_path", required=True, help="input binary path")

    subparsers.add_parser("inspect-clipboard", help="inspect current clipboard TypeEditZone bytes")

    return parser


def _bundle_manifest(zone_format_id: int, version_format_id: int, zone_bytes: bytes, version_bytes: bytes) -> dict:
    return {
        "formats": [
            {
                "format_name": TYPE_EDIT_ZONE_FORMAT_NAME,
                "observed_id": OBSERVED_TYPE_EDIT_ZONE_FORMAT_ID,
                "registered_id": zone_format_id,
                "file_name": TYPE_EDIT_ZONE_FILE_NAME,
                "byte_length": len(zone_bytes),
            },
            {
                "format_name": TYPE_EDIT_ZONE_VERSION_FORMAT_NAME,
                "observed_id": OBSERVED_TYPE_EDIT_ZONE_VERSION_FORMAT_ID,
                "registered_id": version_format_id,
                "file_name": TYPE_EDIT_ZONE_VERSION_FILE_NAME,
                "byte_length": len(version_bytes),
            },
        ]
    }


def _read_bundle_files(dir_path: Path) -> tuple[bytes, bytes]:
    zone_file_name = TYPE_EDIT_ZONE_FILE_NAME
    version_file_name = TYPE_EDIT_ZONE_VERSION_FILE_NAME
    manifest_path = dir_path / MANIFEST_FILE_NAME
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for item in manifest.get("formats", []):
            if item.get("format_name") == TYPE_EDIT_ZONE_FORMAT_NAME:
                zone_file_name = item.get("file_name", zone_file_name)
            if item.get("format_name") == TYPE_EDIT_ZONE_VERSION_FORMAT_NAME:
                version_file_name = item.get("file_name", version_file_name)
    zone_path = dir_path / zone_file_name
    version_path = dir_path / version_file_name
    return zone_path.read_bytes(), version_path.read_bytes()


def _print_verify_result(format_name: str, expected: bytes, actual: bytes) -> bool:
    match = expected == actual
    print(f"{format_name}_match={str(match).lower()}")
    print(f"{format_name}_expected_length={len(expected)}")
    print(f"{format_name}_actual_length={len(actual)}")
    return match


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

        if args.command == "dump-bundle":
            dir_path = Path(args.dir_path)
            dir_path.mkdir(parents=True, exist_ok=True)
            zone_payload = adapter.read_typeeditzone_bytes()
            version_payload = adapter.read_typeeditzone_version_bytes()
            zone_format_id = adapter.get_typeeditzone_format_id()
            version_format_id = adapter.get_typeeditzone_version_format_id()
            (dir_path / TYPE_EDIT_ZONE_FILE_NAME).write_bytes(zone_payload)
            (dir_path / TYPE_EDIT_ZONE_VERSION_FILE_NAME).write_bytes(version_payload)
            manifest = _bundle_manifest(zone_format_id, version_format_id, zone_payload, version_payload)
            (dir_path / MANIFEST_FILE_NAME).write_text(
                json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            print(f"dumped_bytes={len(zone_payload)}")
            print(f"dumped_version_bytes={len(version_payload)}")
            print(f"dir={dir_path}")
            print(f"manifest={dir_path / MANIFEST_FILE_NAME}")
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

        if args.command == "load-bundle":
            dir_path = Path(args.dir_path)
            zone_payload, version_payload = _read_bundle_files(dir_path)
            adapter.write_typeeditzone_bundle(zone_payload, version_payload)
            print(f"loaded_bytes={len(zone_payload)}")
            print(f"loaded_version_bytes={len(version_payload)}")
            print(f"dir={dir_path}")
            return 0

        if args.command == "verify-bundle":
            dir_path = Path(args.dir_path)
            expected_zone, expected_version = _read_bundle_files(dir_path)
            actual_zone = adapter.read_typeeditzone_bytes()
            actual_version = adapter.read_typeeditzone_version_bytes()
            zone_match = _print_verify_result("typeeditzone", expected_zone, actual_zone)
            version_match = _print_verify_result("typeeditzone_version", expected_version, actual_version)
            return 0 if zone_match and version_match else 1

        if args.command == "inspect":
            in_path = Path(args.in_path)
            payload = in_path.read_bytes()
            service = InspectService()
            text = service.inspect(_BinaryFileInputAdapter(payload), verbose=True)
            print(text)
            return 0

        if args.command == "inspect-clipboard":
            service = InspectService()
            text = service.inspect(adapter, verbose=True)
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
