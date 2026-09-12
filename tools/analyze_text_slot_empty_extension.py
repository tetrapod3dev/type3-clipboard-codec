"""Bounded serializer-derived empty-extension SHADOW evidence; no parser gate."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from type3_clipboard_codec import parse_type3_clipboard_bytes_with_parser
from type3_clipboard_codec.exceptions import InvalidHexError
from type3_clipboard_codec.inspect.hex_input import hex_text_to_bytes
from type3_clipboard_codec.parsers.text.text_slot_candidate import extract_text_slot_candidate
from type3_clipboard_codec.parsers.type3_chain_parser import Type3ChainParser

ROOT = Path(__file__).resolve().parents[1]
LAYOUT = json.loads(Path(__file__).with_name("text_slot_empty_extension_layout.json").read_text(encoding="utf-8"))
FIXED_LENGTH = sum(op["empty_path_width"] for op in LAYOUT["fixed_operations"])
EXTENSION_LENGTH = sum(op["empty_path_width"] for op in LAYOUT["extension_operations"])
RECORD_LENGTH = FIXED_LENGTH + EXTENSION_LENGTH
STATES = ("confirmed_empty_extension_layout", "supported_empty_extension_layout",
          "not_empty_extension_layout", "truncated", "unresolved")
MAX_FILES = 512
MAX_FILE_BYTES = 8_388_608
MAX_RECORDS = 32768


def extension_operations():
    """Compute offsets from ordered code emissions, never observed stride."""
    cursor = 0
    result = []
    for operation in LAYOUT["extension_operations"]:
        result.append({**operation, "extension_relative_start": cursor,
                       "extension_relative_end": cursor + operation["empty_path_width"]})
        cursor += operation["empty_path_width"]
    return result


def inspect_empty_extension(record: bytes) -> dict:
    """Receive one aligned record window. Never discover alignment, scan or mutate."""
    result = {
        "status": "unresolved", "parser_safe": False,
        "input_length": len(record), "raw_window": bytes(record[:RECORD_LENGTH]),
        "raw_window_truncated": len(record) > RECORD_LENGTH,
        "record_relative_extension_start": FIXED_LENGTH, "checks": [],
        "applicability": "reviewed_current_store_candidate_not_serializer_identity_proof",
    }
    if len(record) > RECORD_LENGTH:
        result["reason"] = "oversized_record_window"
        return result
    if len(record) < 4:
        result.update(status="truncated", reason="incomplete_version_word")
        return result
    if int.from_bytes(record[:4], "little") != LAYOUT["attrchar_version"]:
        result["reason"] = "unsupported_attrchar_version"
        return result
    if len(record) < RECORD_LENGTH:
        result.update(status="truncated", reason="incomplete_fixed_or_empty_extension_window")
        return result
    result["fixed_portion_evidence"] = "supported_current_attrchar_v5_layout"
    for operation in extension_operations():
        guard = operation.get("empty_guard")
        if not guard:
            continue
        start = FIXED_LENGTH + operation["extension_relative_start"]
        value = int.from_bytes(record[start:start + 4], "little")
        check = {"condition": guard, "record_relative_offset": start,
                 "extension_relative_offset": operation["extension_relative_start"],
                 "raw_hex": bytes(record[start:start + 4]).hex(), "observed_word": value,
                 "expected_empty_word": 0, "operation_rva": operation["operation_rva"]}
        result["checks"].append(check)
        if value:
            # Subsequent offsets apply only if earlier variable components are absent.
            invalid = (guard.startswith("zone") and value != 1) or (
                not guard.startswith("zone") and value >= 0x80000000)
            result.update(status="unresolved" if invalid else "not_empty_extension_layout",
                          reason="noncanonical_condition_word" if invalid else "nonempty_component",
                          failed_condition=guard)
            return result
    result.update(
        status="supported_empty_extension_layout", reason="all_six_empty_words_match_in_order",
        extension_length_candidate=EXTENSION_LENGTH,
        record_length_evidence={"code_derived_candidate": RECORD_LENGTH,
                                "applicable_condition": "reviewed_current_attrchar_empty_extension",
                                "confidence": "supported"},
    )
    return result


def fixture_family(path: Path) -> str:
    """Display grouping AFTER inspection; never an input to the predicate."""
    name = path.stem
    if "maxlength" in name:
        return "maximum_length_boundary" if any(s in name for s in ("74p", "74_", "74.")) else "maximum_length"
    if "spacing" in name:
        return "spacing"
    if any(s in name for s in ("two_objects", "multi", "group")):
        return "multiobject"
    if any(s in name for s in ("color", "navy", "rgb")):
        return "color"
    if "slotstyle" in name:
        return "style"
    return "legacy_text_or_other"


def _counts(values=()):
    counts = Counter(values)
    return {state: counts[state] for state in STATES}


def build_report(paths=None) -> dict:
    paths = sorted(ROOT.joinpath("tests/samples").rglob("*.txt")) if paths is None else list(paths)
    if len(paths) > MAX_FILES:
        raise ValueError("fixture budget exceeded")
    rows = []
    input_issues = []
    records_examined = 0
    for path in paths:
        path = Path(path)
        if path.stat().st_size > MAX_FILE_BYTES:
            raise ValueError("fixture byte budget exceeded")
        file_bytes = path.read_bytes()
        try:
            raw = hex_text_to_bytes(file_bytes.decode("utf-8"))
        except (InvalidHexError, UnicodeDecodeError) as exc:
            input_issues.append({"fixture": path.name, "reason": "not_hex_capture", "detail": str(exc)})
            continue
        obj, chain = parse_type3_clipboard_bytes_with_parser(raw)
        runtime_candidate = obj.candidate_fields.get("text_slot_run")
        parser = Type3ChainParser()
        _, _, base = parser._read_top_level_header(raw)
        nodes = parser._extract_nodes(raw[base:])
        paragraphs = [node for node in nodes if node.header.class_name == "CParagraphe"]
        if len(nodes) > 128 or len(paragraphs) > 32 or sum(len(n.payload) for n in paragraphs) > 1_048_576:
            raise ValueError("paragraph budget exceeded")
        records = []
        unaligned = []
        for paragraph_index, node in enumerate(paragraphs):
            # Existing bounded recognizer supplies alignment per paragraph only.
            # Global production abstention/selection remains untouched.
            candidate = extract_text_slot_candidate([node.payload])
            if candidate is None:
                unaligned.append(paragraph_index)
                continue
            for slot in candidate["slots"]:
                start = slot["prefix_relative_offset"]
                result = inspect_empty_extension(node.payload[start:start + RECORD_LENGTH])
                records_examined += 1
                if records_examined > MAX_RECORDS:
                    raise ValueError("record budget exceeded")
                records.append({
                    "paragraph_index": paragraph_index, "ordinal": slot["ordinal"],
                    "terminal_candidate": slot["terminal_candidate"],
                    "prefix_family": candidate["prefix_family"], "status": result["status"],
                    "reason": result["reason"], "failed_condition": result.get("failed_condition"),
                    "observed_word": result["checks"][-1]["observed_word"] if result.get("failed_condition") else None,
                })
        rows.append({
            "fixture": path.name, "family": fixture_family(path),
            "fixture_raw_sha256": hashlib.sha256(file_bytes).hexdigest(),
            "paragraphs": len(paragraphs), "unaligned_paragraphs": unaligned,
            "production_candidate_present": runtime_candidate is not None, "production_chain": chain,
            "records": records, "counts": _counts(r["status"] for r in records),
        })
    all_records = [r for row in rows for r in row["records"]]
    groups = {}
    for row in rows:
        group = groups.setdefault(row["family"], {"fixtures": 0, "records": 0, **_counts()})
        group["fixtures"] += 1
        group["records"] += len(row["records"])
        for state in STATES:
            group[state] += row["counts"][state]
    contradictions = any(r["status"] in ("not_empty_extension_layout", "truncated") for r in all_records)
    readiness = "contradicted" if contradictions else "structurally_supported_but_incomplete"
    if not all_records:
        readiness = "unresolved"
    return {
        "policy": "shadow_only_no_production_gate", "parser_safe": False,
        "readiness": readiness,
        "readiness_blocker": ("observed_aligned_record_contradiction" if contradictions else
                              "no_aligned_records" if not all_records else
                              "local_v5_layout_match_does_not_prove_serializer_identity_or_all_version_applicability"),
        "alignment_scope": "existing_F4_candidates_per_paragraph; unaligned paragraphs explicitly unexamined",
        "files_examined": len(paths), "fixtures_examined": len(rows), "input_issues": input_issues,
        "records_examined": len(all_records),
        "fixtures_with_paragraphs": sum(bool(row["paragraphs"]) for row in rows),
        "unaligned_paragraph_count": sum(len(row["unaligned_paragraphs"]) for row in rows),
        "unaligned_fixtures": [row["fixture"] for row in rows if row["unaligned_paragraphs"]],
        "counts": _counts(r["status"] for r in all_records),
        "visible_counts": _counts(r["status"] for r in all_records if not r["terminal_candidate"]),
        "terminal_counts": _counts(r["status"] for r in all_records if r["terminal_candidate"]),
        "groups": groups, "fixtures": rows,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Emit complete bounded corpus evidence")
    args = parser.parse_args()
    report = build_report()
    print(json.dumps(report if args.json else {k: v for k, v in report.items() if k != "fixtures"}, indent=2))


if __name__ == "__main__":
    main()
