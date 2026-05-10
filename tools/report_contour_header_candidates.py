from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from type3_clipboard_codec import parse_type3_clipboard_bytes_with_parser
from type3_clipboard_codec.inspect.hex_input import hex_text_to_bytes
from type3_clipboard_codec.models.geometry import GeometryObject


REPO_ROOT = Path(__file__).resolve().parents[1]
SAMPLES_ROOT = REPO_ROOT / "tests" / "samples"
TEXT_SAMPLES_ROOT = SAMPLES_ROOT / "text"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Report contour header candidate diagnostics from fixtures.")
    parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    parser.add_argument(
        "--include-text",
        action="store_true",
        help="Include text fixtures under tests/samples/text.",
    )
    return parser.parse_args()


def _iter_fixture_paths(include_text: bool) -> list[Path]:
    paths = sorted(SAMPLES_ROOT.glob("*.txt"))
    if include_text:
        paths.extend(sorted(TEXT_SAMPLES_ROOT.glob("*.txt")))
    return paths


def _decode_fixture(path: Path) -> GeometryObject:
    raw_hex = path.read_text(encoding="utf-8")
    data = hex_text_to_bytes(raw_hex)
    parsed, _parser_name = parse_type3_clipboard_bytes_with_parser(data)
    if not isinstance(parsed, GeometryObject):
        raise ValueError(f"Fixture did not decode to GeometryObject: {path.name}")
    return parsed


def _collect_rows(include_text: bool) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for fixture in _iter_fixture_paths(include_text):
        parsed = _decode_fixture(fixture)
        diag_blocks = parsed.candidate_fields.get("contour_header_diagnostics", [])
        for block in diag_blocks:
            chain_index = block.get("chain_index")
            source_stream_offset = block.get("source_stream_offset")
            diagnostics = block.get("diagnostics", [])
            for marker_index, diag in enumerate(diagnostics):
                rows.append(
                    {
                        "fixture": fixture.name,
                        "chain_index": chain_index,
                        "marker_index": marker_index,
                        "source_stream_offset": source_stream_offset,
                        "marker_offset": diag.get("marker_offset"),
                        "selected_shift": diag.get("selected_shift"),
                        "selected_kind": diag.get("selected_kind"),
                        "selected_count": diag.get("selected_count"),
                        "selected_header_offset": diag.get("selected_header_offset"),
                        "selected_payload_offset": diag.get("selected_payload_offset"),
                        "selected_raw_header_hex": diag.get("selected_raw_header_hex"),
                        "selection_reason": diag.get("selection_reason"),
                        "confidence": diag.get("confidence"),
                        "candidate_shifts": diag.get("candidate_shifts") or [],
                        "candidates": diag.get("candidates") or [],
                    }
                )
    return rows


def _summaries(rows: list[dict[str, Any]]) -> dict[str, Any]:
    selected_shift_dist = Counter()
    rejection_reason_dist = Counter()
    candidate_shift_dist = Counter()
    by_fixture: dict[str, list[dict[str, Any]]] = {}

    for row in rows:
        by_fixture.setdefault(row["fixture"], []).append(row)
        if row.get("selected_shift") is not None:
            selected_shift_dist[int(row["selected_shift"])] += 1
        for candidate in row.get("candidates", []):
            candidate_shift_dist[int(candidate["shift"])] += 1
            reason = candidate.get("rejection_reason")
            if reason:
                rejection_reason_dist[str(reason)] += 1

    fixture_selected = []
    for fixture, entries in sorted(by_fixture.items(), key=lambda item: item[0]):
        selected_entry = next((e for e in entries if e.get("selected_shift") is not None), None)
        fixture_selected.append(
            {
                "fixture": fixture,
                "selected_shift": selected_entry.get("selected_shift") if selected_entry else None,
                "selected_kind": selected_entry.get("selected_kind") if selected_entry else None,
                "selected_count": selected_entry.get("selected_count") if selected_entry else None,
                "selected_raw_header_hex": selected_entry.get("selected_raw_header_hex") if selected_entry else None,
            }
        )

    return {
        "fixture_selected": fixture_selected,
        "selected_shift_distribution": dict(sorted(selected_shift_dist.items(), key=lambda item: item[0])),
        "rejection_reason_distribution": dict(rejection_reason_dist),
        "candidate_shift_observations": dict(sorted(candidate_shift_dist.items(), key=lambda item: item[0])),
        "policy": "absolute offset is diagnostic only; current contour header interpretation remains provisional",
        "rows": rows,
    }


def _print_text(summary: dict[str, Any]) -> None:
    print("Type3 Contour Header Candidate Report (Geometry Fixtures)")
    print()
    print("[Per Fixture Selected Header]")
    for row in summary["fixture_selected"]:
        print(
            f"{row['fixture']}: shift={row['selected_shift']}, kind={row['selected_kind']}, "
            f"count={row['selected_count']}, raw_8b={row['selected_raw_header_hex']}"
        )
    print()
    print("[Selected Shift Distribution]")
    for shift, count in summary["selected_shift_distribution"].items():
        print(f"shift={shift}: {count}")
    print()
    print("[Rejection Reason Distribution]")
    for reason, count in summary["rejection_reason_distribution"].items():
        print(f"{reason}: {count}")
    print()
    print("[Candidate Shift Observations]")
    for shift, count in summary["candidate_shift_observations"].items():
        print(f"shift={shift}: {count}")
    print()
    print(f"policy: {summary['policy']}")


def main() -> int:
    args = parse_args()
    rows = _collect_rows(include_text=args.include_text)
    summary = _summaries(rows)
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        _print_text(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
