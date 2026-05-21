from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from type3_clipboard_codec import parse_type3_clipboard_bytes_with_parser
from type3_clipboard_codec.adapters.input_base import InputAdapter
from type3_clipboard_codec.adapters.win32_clipboard import (
    OBSERVED_TYPE_EDIT_ZONE_FORMAT_ID,
    OBSERVED_TYPE_EDIT_ZONE_VERSION_FORMAT_ID,
    TYPE_EDIT_ZONE_FORMAT_NAME,
    TYPE_EDIT_ZONE_VERSION_FORMAT_NAME,
    Win32ClipboardAdapter,
    Win32ClipboardError,
)
from type3_clipboard_codec.inspect.hex_input import hex_text_to_bytes
from type3_clipboard_codec.models.geometry import GeometryObject
from type3_clipboard_codec.services.inspect_service import InspectService

TYPE_EDIT_ZONE_FILE_NAME = "typeeditzone.bin"
TYPE_EDIT_ZONE_VERSION_FILE_NAME = "typeeditzone_version.bin"
MANIFEST_FILE_NAME = "manifest.json"


class _BytesInputAdapter(InputAdapter):
    def __init__(self, payload: bytes):
        self._payload = payload

    def fetch_data(self) -> bytes:
        return self._payload


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Capture a Type3 clipboard sample fixture and raw bundle.")
    parser.add_argument("--name", required=True, help="sample name without extension")
    parser.add_argument("--category", required=True, choices=["geometry", "text"], help="sample category")
    parser.add_argument("--description", default="", help="short sample description")
    parser.add_argument("--overwrite", action="store_true", help="overwrite existing generated files")
    parser.add_argument("--git-add", action="store_true", help="git add generated files")
    parser.add_argument("--print-readme-snippet", action="store_true", help="print README snippet")
    parser.add_argument("--inspect", dest="inspect", action="store_true", default=True, help="write inspect reports")
    parser.add_argument("--no-inspect", dest="inspect", action="store_false", help="skip inspect reports")
    parser.add_argument("--object-count", help="intended selected/copied object count")
    parser.add_argument("--grouping", help="grouped/not_grouped/unknown")
    parser.add_argument("--text", help="text content, use | to separate objects")
    parser.add_argument("--anchors", help="anchor list, e.g. 111.111,222.222,0;211.111,322.222,0")
    parser.add_argument("--color", help="intended color")
    parser.add_argument("--intent-file", help="optional extra intent/source markdown file path to reference")
    return parser


def _fixture_path(name: str, category: str) -> Path:
    if category == "text":
        return REPO_ROOT / "tests" / "samples" / "text" / f"{name}.txt"
    return REPO_ROOT / "tests" / "samples" / f"{name}.txt"


def _bundle_dir(name: str, category: str) -> Path:
    return REPO_ROOT / "tests" / "samples" / "bundles" / category / name


def _report_paths(name: str, category: str) -> tuple[Path, Path]:
    report_dir = REPO_ROOT / "tests" / "samples" / "reports" / category
    return report_dir / f"{name}.inspect.txt", report_dir / f"{name}.inspect.json"


def _intent_path(name: str, category: str) -> Path:
    return REPO_ROOT / "tests" / "samples" / "intents" / category / f"{name}.md"


def _wrap_hex(data: bytes, width: int = 64) -> str:
    hex_text = data.hex()
    return "\n".join(hex_text[i : i + width] for i in range(0, len(hex_text), width)) + "\n"


def _ensure_can_write(paths: list[Path], overwrite: bool) -> None:
    existing = [path for path in paths if path.exists()]
    if existing and not overwrite:
        formatted = "\n".join(str(path) for path in existing)
        raise FileExistsError(f"Refusing to overwrite existing file(s):\n{formatted}")


def _capture_manifest(
    *,
    name: str,
    category: str,
    description: str,
    created_at: str,
    zone_bytes: bytes,
    version_bytes: bytes,
    zone_format_id: int,
    version_format_id: int,
) -> dict[str, Any]:
    return {
        "sample_name": name,
        "category": category,
        "created_at": created_at,
        "typeeditzone_size": len(zone_bytes),
        "typeeditzone_version_size": len(version_bytes),
        "format_names": {
            "typeeditzone": TYPE_EDIT_ZONE_FORMAT_NAME,
            "typeeditzone_version": TYPE_EDIT_ZONE_VERSION_FORMAT_NAME,
        },
        "observed_format_ids": {
            "typeeditzone": OBSERVED_TYPE_EDIT_ZONE_FORMAT_ID,
            "typeeditzone_version": OBSERVED_TYPE_EDIT_ZONE_VERSION_FORMAT_ID,
        },
        "registered_format_ids": {
            "typeeditzone": zone_format_id,
            "typeeditzone_version": version_format_id,
        },
        "files": {
            "fixture": str(_fixture_path(name, category).relative_to(REPO_ROOT)),
            "typeeditzone": TYPE_EDIT_ZONE_FILE_NAME,
            "typeeditzone_version": TYPE_EDIT_ZONE_VERSION_FILE_NAME,
        },
        "description": description,
        "source": "windows_clipboard",
    }


def _intent_markdown(args: argparse.Namespace, created_at: str, zone_len: int, version_len: int, parser_text: str) -> str:
    return f"""# {args.name}

## Capture metadata

- category: {args.category}
- captured from: Type3 Windows clipboard
- TypeEditZone bytes: {zone_len}
- TypeEditZoneVersion bytes: {version_len}
- created at: {created_at}
- description: {args.description or ""}
- external intent file: {args.intent_file or ""}

## User intent / ground truth

- source object:
- selected/copied object count: {args.object_count or ""}
- grouped/not grouped: {args.grouping or ""}
- text content: {args.text or ""}
- font:
- color: {args.color or ""}
- anchor / position: {args.anchors or ""}
- geometry:
- changed variable:
- fixed variables:

## Notes

- actual stored order unresolved unless explicitly verified
- Type3 UI terms should be preserved in Korean when applicable
- TypeEditZone raw bytes are preserved without strip/decode/normalize/trailing-zero removal
- TypeEditZoneVersion bytes are preserved without interpretation

## Parser observation

Generated by capture CLI:

```text
{parser_text.rstrip()}
```
"""


def _readme_snippet(args: argparse.Namespace) -> str:
    fixture = _fixture_path(args.name, args.category).relative_to(REPO_ROOT)
    bundle = _bundle_dir(args.name, args.category).relative_to(REPO_ROOT)
    intent = _intent_path(args.name, args.category).relative_to(REPO_ROOT)
    return f"""### `{fixture.name}`

- category: {args.category}
- bundle: `{bundle}/`
- intent: `{intent}`
- description: {args.description or ""}
- reverse-engineering status: captured, parser observation pending
"""


def _inspect_reports(zone_bytes: bytes) -> tuple[str, dict[str, Any]]:
    try:
        text = InspectService().inspect(_BytesInputAdapter(zone_bytes), verbose=True)
        parsed, parser_name = parse_type3_clipboard_bytes_with_parser(zone_bytes)
        payload: dict[str, Any] = {
            "status": "ok",
            "parser_name": parser_name,
            "object_type": getattr(parsed, "object_type", None),
            "raw_size": getattr(parsed, "raw_size", len(zone_bytes)),
            "text_candidate": getattr(parsed, "text_content", None),
            "class_markers": getattr(parsed, "markers", []),
            "object_count": len(getattr(parsed, "object_chains", []) or []),
        }
        if isinstance(parsed, GeometryObject):
            payload["is_text_object"] = parsed.is_text_object
            payload["font_name"] = parsed.font_name
            payload["bbox"] = _bbox_to_json(parsed.bbox)
            payload["chains"] = [
                {
                    "chain_index": idx,
                    "shape_type": chain.shape_type,
                    "markers": chain.markers,
                    "bbox": _bbox_to_json(chain.bbox),
                    "text_candidate": chain.source_text_candidate or chain.text_candidate,
                    "text_anchor": (
                        {"x": chain.text_anchor.x, "y": chain.text_anchor.y, "z": chain.text_anchor.z}
                        if chain.text_anchor is not None
                        else None
                    ),
                }
                for idx, chain in enumerate(parsed.object_chains)
            ]
        return text, payload
    except Exception as exc:
        return f"[INSPECT ERROR] {exc}", {"status": "error", "error": str(exc)}


def _bbox_to_json(bbox) -> dict[str, float] | None:
    if bbox is None:
        return None
    return {
        "xmin_mm": bbox.xmin_mm,
        "ymin_mm": bbox.ymin_mm,
        "zmin_mm": bbox.zmin_mm,
        "xmax_mm": bbox.xmax_mm,
        "ymax_mm": bbox.ymax_mm,
        "zmax_mm": bbox.zmax_mm,
    }


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def _git_add(paths: list[Path]) -> None:
    rels = [str(path.relative_to(REPO_ROOT)) for path in paths]
    subprocess.run(["git", "add", *rels], cwd=str(REPO_ROOT), check=True)


def _verify_written(fixture_path: Path, zone_path: Path, version_path: Path, zone_bytes: bytes, version_bytes: bytes) -> None:
    if zone_path.read_bytes() != zone_bytes:
        raise RuntimeError("typeeditzone.bin verification failed")
    if version_path.read_bytes() != version_bytes:
        raise RuntimeError("typeeditzone_version.bin verification failed")
    if hex_text_to_bytes(fixture_path.read_text(encoding="utf-8")) != zone_bytes:
        raise RuntimeError("fixture txt hex round-trip verification failed")


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    fixture_path = _fixture_path(args.name, args.category)
    bundle_dir = _bundle_dir(args.name, args.category)
    zone_path = bundle_dir / TYPE_EDIT_ZONE_FILE_NAME
    version_path = bundle_dir / TYPE_EDIT_ZONE_VERSION_FILE_NAME
    manifest_path = bundle_dir / MANIFEST_FILE_NAME
    inspect_txt_path, inspect_json_path = _report_paths(args.name, args.category)
    intent_path = _intent_path(args.name, args.category)

    generated_paths = [fixture_path, zone_path, version_path, manifest_path, intent_path]
    if args.inspect:
        generated_paths.extend([inspect_txt_path, inspect_json_path])

    try:
        _ensure_can_write(generated_paths, args.overwrite)
        adapter = Win32ClipboardAdapter()
        zone_format_id = adapter.get_typeeditzone_format_id()
        version_format_id = adapter.get_typeeditzone_version_format_id()
        if not adapter.has_typeeditzone():
            raise Win32ClipboardError(f"{TYPE_EDIT_ZONE_FORMAT_NAME} is not available in clipboard")
        if not adapter.has_typeeditzone_version():
            raise Win32ClipboardError(f"{TYPE_EDIT_ZONE_VERSION_FORMAT_NAME} is not available in clipboard")

        zone_bytes = adapter.read_typeeditzone_bytes()
        version_bytes = adapter.read_typeeditzone_version_bytes()
        created_at = datetime.now(timezone.utc).isoformat()

        print(f"TypeEditZone found: format id {zone_format_id}, size {len(zone_bytes)} bytes")
        print(f"TypeEditZoneVersion found: format id {version_format_id}, size {len(version_bytes)} bytes")
        if args.overwrite:
            print("[WARN] overwrite enabled")

        inspect_text = "inspection skipped"
        inspect_json: dict[str, Any] = {"status": "skipped"}
        if args.inspect:
            inspect_text, inspect_json = _inspect_reports(zone_bytes)

        _write_text(fixture_path, _wrap_hex(zone_bytes))
        _write_bytes(zone_path, zone_bytes)
        _write_bytes(version_path, version_bytes)
        manifest = _capture_manifest(
            name=args.name,
            category=args.category,
            description=args.description,
            created_at=created_at,
            zone_bytes=zone_bytes,
            version_bytes=version_bytes,
            zone_format_id=zone_format_id,
            version_format_id=version_format_id,
        )
        _write_text(manifest_path, json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
        if args.inspect:
            _write_text(inspect_txt_path, inspect_text.rstrip() + "\n")
            _write_text(inspect_json_path, json.dumps(inspect_json, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
        _write_text(intent_path, _intent_markdown(args, created_at, len(zone_bytes), len(version_bytes), inspect_text))

        _verify_written(fixture_path, zone_path, version_path, zone_bytes, version_bytes)
        print("verify typeeditzone.bin: OK")
        print("verify fixture txt -> bytes: OK")
        print("verify typeeditzone_version.bin: OK")

        print(f"fixture={fixture_path}")
        print(f"bundle_dir={bundle_dir}")
        print(f"intent={intent_path}")
        if args.inspect:
            print(f"inspect_txt={inspect_txt_path}")
            print(f"inspect_json={inspect_json_path}")

        if args.print_readme_snippet:
            print()
            print(_readme_snippet(args).rstrip())

        if args.git_add:
            try:
                _git_add(generated_paths)
                print("git_add=ok")
            except Exception as exc:
                print(f"[WARN] git add failed: {exc}", file=sys.stderr)
        return 0
    except FileExistsError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2
    except Win32ClipboardError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 3
    except Exception as exc:
        print(f"[ERROR] Unexpected failure: {exc}", file=sys.stderr)
        return 4


if __name__ == "__main__":
    raise SystemExit(main())
