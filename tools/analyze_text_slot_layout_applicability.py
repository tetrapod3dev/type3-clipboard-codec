"""Serializer version evidence for already aligned slots; never a production gate."""

from __future__ import annotations

import argparse
import importlib.util
import json
from collections import Counter
from pathlib import Path

from type3_clipboard_codec.inspect.hex_input import hex_text_to_bytes

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "applicability_empty_shadow", Path(__file__).with_name("analyze_text_slot_empty_extension.py"))
EMPTY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(EMPTY)
EVIDENCE = json.loads(Path(__file__).with_name("text_slot_layout_version_evidence.json").read_text(encoding="utf-8"))
STATES = ("current_layout_supported", "legacy_or_other_layout", "insufficient_parent_context",
          "truncated", "unsupported_version", "unresolved")
# Positions freeze from archive order before corpus observation. No variable emission precedes either marker.
MARKERS = (("attrchar", 0, 5), ("extension", EMPTY.FIXED_LENGTH, 5))
PARA_WIDTH = 4 + 4 + 5 * 8 + 4
LINE_WIDTH = 4 + 4 + 6 * 8 + 4 + 8
COUNT_WIDTH = 4
MAX_LINES = 256


def _word(data, offset):
    return int.from_bytes(data[offset:offset + 4], "little")


def _version_state(value, current):
    if value == current:
        return "current_layout_supported"
    return "legacy_or_other_layout" if 1 <= value < current else "unsupported_version"


def inspect_parent_prefix(prefix: bytes) -> dict:
    """Optional CTxtPara bytes, from its entry through the character count, exclusively.

    Caller must establish its origin. This function never scans for a parent or guesses a version.
    CTxtPara has no own version: the first DWORD belongs to embedded AttrPara.
    """
    result = {"status": "truncated", "parser_safe": False, "checks": []}
    if len(prefix) > PARA_WIDTH + 8 + MAX_LINES * LINE_WIDTH:
        return {**result, "status": "unresolved", "reason": "parent_budget"}
    if len(prefix) < 4:
        return result
    version = _word(prefix, 0)
    result["checks"].append({"serializer": "attrpara", "offset": 0, "value": version})
    state = _version_state(version, 4)
    if state != "current_layout_supported":
        return {**result, "status": state}
    if len(prefix) < PARA_WIDTH + COUNT_WIDTH:
        return result
    lines = _word(prefix, PARA_WIDTH)
    if lines > MAX_LINES:
        return {**result, "status": "unresolved", "reason": "line_budget"}
    cursor = PARA_WIDTH + COUNT_WIDTH
    for _ in range(lines):
        if len(prefix) < cursor + 4:
            return result
        version = _word(prefix, cursor)
        result["checks"].append({"serializer": "attrline", "offset": cursor, "value": version})
        state = _version_state(version, 4)
        if state != "current_layout_supported":
            return {**result, "status": state}
        cursor += LINE_WIDTH
    if len(prefix) < cursor + COUNT_WIDTH:
        return result
    if len(prefix) != cursor + COUNT_WIDTH:
        return {**result, "status": "unresolved", "reason": "parent_boundary_mismatch"}
    count = _word(prefix, cursor)
    if not 1 <= count <= EMPTY.MAX_RECORDS:
        return {**result, "status": "unresolved", "reason": "character_count_budget"}
    return {**result, "status": "current_layout_supported", "line_count": lines,
            "character_count": count}


def current_slot_layout_evidence(record: bytes, *, parent_prefix: bytes | None = None,
                                 require_parent: bool = False) -> dict:
    """Only byte structure is an input. Support is conditional on existing structural alignment.

    The extension version is independent of empty guards. A supported result does not promise
    204 bytes for a nonempty record. Parent bytes, when supplied, may veto local support.
    """
    result = {"status": "unresolved", "parser_safe": False, "checks": [],
              "alignment_precondition": "existing_structurally_aligned_attrchar_candidate",
              "combined_future_204_supported": False}
    if len(record) > EMPTY.RECORD_LENGTH:
        return {**result, "reason": "oversized_record_window"}
    for name, offset, expected in MARKERS:
        if len(record) < offset + 4:
            return {**result, "status": "truncated", "reason": "incomplete_" + name + "_version"}
        value = _word(record, offset)
        result["checks"].append({"serializer": name, "record_relative_offset": offset,
                                 "width": 4, "expected": expected, "observed": value})
        state = _version_state(value, expected)
        if state != "current_layout_supported":
            return {**result, "status": state, "reason": name + "_version_mismatch"}
    if len(record) < EMPTY.RECORD_LENGTH:
        return {**result, "status": "truncated", "reason": "incomplete_reviewed_window"}
    if parent_prefix is not None:
        parent = inspect_parent_prefix(parent_prefix)
        result["parent_evidence"] = parent
        if parent["status"] != "current_layout_supported":
            return {**result, "status": parent["status"], "reason": "parent_not_current_or_incomplete"}
    elif require_parent:
        return {**result, "status": "insufficient_parent_context", "reason": "requested_parent_missing"}
    empty = EMPTY.inspect_empty_extension(record)
    return {**result, "status": "current_layout_supported", "reason": "both_serialized_versions_exactly_current",
            "empty_extension_status": empty["status"],
            "combined_future_204_supported": empty["status"] == "supported_empty_extension_layout"}


def parent_candidates(payload, first, count):
    """Diagnostics only: solve code-derived prefix length for bounded line counts.

    Does not discover or move any record. Candidate origins are not parent-framing proof.
    Never used by the local applicability predicate or production selector.
    """
    found = []
    for lines in range(MAX_LINES + 1):
        size = PARA_WIDTH + COUNT_WIDTH + lines * LINE_WIDTH + COUNT_WIDTH
        start = first - size
        if start < 0:
            break
        if _word(payload, start + PARA_WIDTH) != lines:
            continue
        parent = inspect_parent_prefix(payload[start:first])
        if parent["status"] == "current_layout_supported" and parent["character_count"] == count:
            found.append(parent)
    return found


def _counts(records):
    counts = Counter(r["status"] for r in records)
    return {state: counts[state] for state in STATES}


def build_report(paths=None):
    # Reuse the broad content-validated corpus inventory and its established bounds/alignment.
    paths = sorted((ROOT / "tests/samples").rglob("*.txt")) if paths is None else list(paths)
    inventory = EMPTY.build_report(paths)
    rows = []
    observations = []
    schema_values = Counter()
    parent_values = {"attrpara": Counter(), "attrline": Counter()}
    nonversion_words = {"record+8": Counter(), "record+44": Counter()}
    parent_ambiguous_or_missing = 0
    for path in paths:
        path = Path(path)
        try:
            raw = hex_text_to_bytes(path.read_bytes().decode("utf-8"))
        except (EMPTY.InvalidHexError, UnicodeDecodeError):
            continue
        parser = EMPTY.Type3ChainParser()
        _, _, base = parser._read_top_level_header(raw)
        nodes = parser._extract_nodes(raw[base:])
        records = []
        for node in nodes:
            if node.header.class_name != "CParagraphe":
                continue
            schema_values[node.header.class_id] += 1  # Existing descriptor label; no schema semantic promotion.
            candidate = EMPTY.extract_text_slot_candidate([node.payload])
            if candidate is None:
                continue
            parents = parent_candidates(node.payload, candidate["first_prefix_relative_offset"],
                                        len(candidate["slots"]))
            if len(parents) == 1:
                for check in parents[0]["checks"]:
                    parent_values[check["serializer"]][check["value"]] += 1
            else:
                parent_ambiguous_or_missing += 1
            for slot in candidate["slots"]:
                start = slot["prefix_relative_offset"]
                window = node.payload[start:start + EMPTY.RECORD_LENGTH]
                for label, offset in (("record+8", 8), ("record+44", 44)):
                    if len(window) >= offset + 4:
                        nonversion_words[label][_word(window, offset)] += 1
                evidence = current_slot_layout_evidence(window)
                record = {"terminal": slot["terminal_candidate"], **evidence}
                records.append(record)
                observations.extend({**check, "terminal": record["terminal"]} for check in evidence["checks"])
        rows.append({"fixture": path.name, "records": records})
    records = [record for row in rows for record in row["records"]]
    values = {}
    for name, _, _ in MARKERS:
        checks = [c for c in observations if c["serializer"] == name]
        values[name] = {group: dict(Counter(c["observed"] for c in checks
                                          if group == "all" or c["terminal"] == (group == "terminal")))
                        for group in ("all", "visible", "terminal")}
    supported = bool(records) and all(r["status"] == "current_layout_supported" for r in records)
    combined = supported and all(r["combined_future_204_supported"] for r in records)
    return {"policy": "shadow_only_no_production_gate", "parser_safe": False,
            "serializer_applicability_readiness": "ready_for_production_gate_review" if supported else
            "contradicted" if records else "unresolved",
            "combined_future_gate_readiness": "ready_for_production_gate_review" if combined else "unresolved",
            "scope": "already aligned candidates in reviewed serializer family; not arbitrary byte identity",
            "records_examined": len(records), "counts": _counts(records),
            "visible_counts": _counts([r for r in records if not r["terminal"]]),
            "terminal_counts": _counts([r for r in records if r["terminal"]]),
            "observed_versions": values, "descriptor_second_word_values": dict(schema_values),
            "nonversion_word_observations": {k: dict(v) for k, v in nonversion_words.items()},
            "diagnostic_parent_version_values": {k: dict(v) for k, v in parent_values.items()},
            "parent_candidates_ambiguous_or_missing": parent_ambiguous_or_missing,
            "files_examined": inventory["files_examined"], "fixtures_examined": inventory["fixtures_examined"],
            "input_issues": inventory["input_issues"],
            "unaligned_paragraph_count": inventory["unaligned_paragraph_count"],
            "variation_search_limitation": "F4 alignment preselects AttrChar v5; unaligned legacy records not excluded",
            "real_nonempty_records": inventory["counts"]["not_empty_extension_layout"],
            "fixtures": rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = build_report()
    print(json.dumps(report if args.json else {k: v for k, v in report.items() if k != "fixtures"}, indent=2))


if __name__ == "__main__":
    main()
