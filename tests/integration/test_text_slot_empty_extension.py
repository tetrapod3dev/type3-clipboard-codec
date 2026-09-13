"""Empty extension evidence stays local, bounded and outside production decisions."""

import importlib.util
import inspect
from dataclasses import asdict
from pathlib import Path

import pytest

from tests.source_integrity import canonical_source_sha256, source_baseline
from type3_clipboard_codec import parse_type3_clipboard_bytes_with_parser
from type3_clipboard_codec.exceptions import InvalidHexError
from type3_clipboard_codec.inspect.hex_input import hex_text_to_bytes
from type3_clipboard_codec.parsers.text.text_slot_candidate import extract_text_slot_candidate

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("empty_extension_shadow", ROOT / "tools/analyze_text_slot_empty_extension.py")
SHADOW = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SHADOW)
GUARDS = [op for op in SHADOW.extension_operations() if op.get("empty_guard")]


def empty_record():
    # Generated from the frozen code model, not any capture's style/UI values.
    record = bytearray(SHADOW.RECORD_LENGTH)
    record[:4] = SHADOW.LAYOUT["attrchar_version"].to_bytes(4, "little")
    return bytes(record)


def baseline_payload():
    raw = hex_text_to_bytes((ROOT / "tests/samples/text/text_slotstyle_a8_baseline.txt").read_text())
    obj, _ = parse_type3_clipboard_bytes_with_parser(raw)
    candidate = obj.candidate_fields["text_slot_run"]
    span = candidate["payload_span"]
    return raw[span["start"]:span["start"] + span["length"]], candidate["first_prefix_relative_offset"]


def test_code_emission_arithmetic_and_boundary():
    fixed = SHADOW.LAYOUT["fixed_operations"]
    assert len([o for o in fixed if o["empty_path_width"] == 4]) == 5
    assert len([o for o in fixed if o["empty_path_width"] == 8]) == 9
    assert sum(o["empty_path_width"] for o in fixed) == SHADOW.FIXED_LENGTH == 92
    assert SHADOW.LAYOUT["extension_call"]["rva"] == "0x4d882"
    assert SHADOW.LAYOUT["extension_call"]["source"] == "CTxtAttrChar+0x68"
    extension = SHADOW.extension_operations()
    assert len([o for o in extension if o["empty_path_width"] == 4]) == 16
    assert len([o for o in extension if o["empty_path_width"] == 8]) == 6
    assert extension[-1]["extension_relative_end"] == SHADOW.EXTENSION_LENGTH == 112
    assert SHADOW.RECORD_LENGTH == 204
    assert [o["extension_relative_start"] for o in GUARDS] == [40, 60, 96, 100, 104, 108]
    assert all(o["binary"] == "Maude.dll" for o in extension)
    # Variable emissions contribute zero only to this conditional path.
    assert len([o for o in extension if o["empty_path_width"] == 0]) == 6


def test_structurally_empty_and_raw_preservation():
    record = bytearray(empty_record())
    before = bytes(record)
    result = SHADOW.inspect_empty_extension(record)
    assert bytes(record) == before == result["raw_window"]
    assert result["status"] == "supported_empty_extension_layout"
    assert result["extension_length_candidate"] == 112
    assert result["record_length_evidence"]["code_derived_candidate"] == 204
    assert result["parser_safe"] is False
    assert len(result["checks"]) == 6


def test_every_truncation_fails_closed():
    record = empty_record()
    for length in range(SHADOW.RECORD_LENGTH):
        result = SHADOW.inspect_empty_extension(record[:length])
        assert result["status"] == "truncated"
        assert "extension_length_candidate" not in result
        assert "record_length_evidence" not in result
        assert result["raw_window"] == record[:length]


@pytest.mark.parametrize("operation", GUARDS, ids=lambda o: o["empty_guard"])
def test_nonempty_component_and_production_candidate_independence(operation):
    payload, first = baseline_payload()
    production_before = extract_text_slot_candidate([payload])
    mutation = bytearray(payload)
    offset = first + SHADOW.FIXED_LENGTH + operation["extension_relative_start"]
    mutation[offset:offset + 4] = (1).to_bytes(4, "little")
    record = mutation[first:first + SHADOW.RECORD_LENGTH]
    result = SHADOW.inspect_empty_extension(record)
    assert result["status"] == "not_empty_extension_layout"
    assert result["failed_condition"] == operation["empty_guard"]
    assert result["checks"][-1]["extension_relative_offset"] == operation["extension_relative_start"]
    assert len(result["checks"]) == GUARDS.index(operation) + 1
    assert "record_length_evidence" not in result
    assert production_before is not None
    # F4 still aligns; the approved production layout gate now vetoes nonempty data.
    assert extract_text_slot_candidate([bytes(mutation)]) is None


@pytest.mark.parametrize("operation", GUARDS, ids=lambda o: o["empty_guard"])
def test_noncanonical_condition_word_is_unresolved(operation):
    record = bytearray(empty_record())
    offset = SHADOW.FIXED_LENGTH + operation["extension_relative_start"]
    value = 2 if operation["empty_guard"].startswith("zone") else 0xFFFFFFFF
    record[offset:offset + 4] = value.to_bytes(4, "little")
    result = SHADOW.inspect_empty_extension(record)
    assert result["status"] == "unresolved"
    assert "extension_length_candidate" not in result


@pytest.mark.parametrize("version", [0, 4, 6, 0xFFFFFFFF])
def test_unsupported_version_is_unresolved(version):
    record = bytearray(empty_record())
    record[:4] = version.to_bytes(4, "little")
    result = SHADOW.inspect_empty_extension(record)
    assert result["status"] == "unresolved"
    assert result["checks"] == []
    assert "record_length_evidence" not in result


def test_oversized_window_is_bounded():
    record = empty_record() + b"extra"
    result = SHADOW.inspect_empty_extension(record)
    assert result["status"] == "unresolved"
    assert result["raw_window"] == record[:SHADOW.RECORD_LENGTH]
    assert result["raw_window_truncated"]
    assert result["input_length"] == len(record)


def test_opaque_extension_fields_need_not_be_zero():
    record = bytearray(empty_record())
    for op in SHADOW.extension_operations():
        if op["empty_path_width"] and not op.get("empty_guard"):
            start = SHADOW.FIXED_LENGTH + op["extension_relative_start"]
            record[start:start + op["empty_path_width"]] = b"\xff" * op["empty_path_width"]
    assert SHADOW.inspect_empty_extension(record)["status"] == "supported_empty_extension_layout"


def test_no_independent_search_or_offset_or_order_dependency():
    first = empty_record()
    second = bytearray(first)
    second[SHADOW.FIXED_LENGTH] = 7  # Opaque serialized member, not an empty condition.
    records = [first, bytes(second)]
    direct = [SHADOW.inspect_empty_extension(r) for r in records]
    assert [SHADOW.inspect_empty_extension(r) for r in reversed(records)] == list(reversed(direct))
    for offset in (1, 17, 555):
        surrounded = b"x" * offset + first + b"suffix"
        assert SHADOW.inspect_empty_extension(surrounded[offset:offset + len(first)]) == direct[0]
    assert list(inspect.signature(SHADOW.inspect_empty_extension).parameters) == ["record"]


def test_f4_and_empty_extension_are_independent():
    # v5 plus all-zero fixed fields fails F4's nonzero constant, but matches the empty extension.
    assert SHADOW.inspect_empty_extension(empty_record())["status"] == "supported_empty_extension_layout"
    payload, first = baseline_payload()
    production = extract_text_slot_candidate([payload])
    assert production["prefix_family"] == "F4"
    changed = bytearray(payload)
    changed[first + 8] = 2  # Break F4 only, keeping the version and extension intact.
    assert extract_text_slot_candidate([bytes(changed)]) is None
    assert SHADOW.inspect_empty_extension(changed[first:first + 204])["status"] == "supported_empty_extension_layout"


def production_snapshot(paths):
    snapshots = {}
    for path in paths:
        file_bytes = path.read_bytes()
        try:
            raw = hex_text_to_bytes(file_bytes.decode("utf-8"))
        except (InvalidHexError, UnicodeDecodeError) as exc:
            snapshots[path] = (file_bytes, type(exc).__name__)
            continue
        obj, chain = parse_type3_clipboard_bytes_with_parser(raw)
        snapshots[path] = (file_bytes, chain, asdict(obj))
    return snapshots


def test_entire_corpus_production_and_fixture_bytes_unchanged():
    paths = sorted((ROOT / "tests/samples").rglob("*.txt"))
    before = production_snapshot(paths)
    report = SHADOW.build_report(paths)
    assert production_snapshot(paths) == before
    assert report["files_examined"] == len(paths)
    assert report["fixtures_examined"] + len(report["input_issues"]) == len(paths)
    assert report["records_examined"] == sum(report["counts"].values())
    assert report["terminal_counts"]["supported_empty_extension_layout"] > 0
    assert report["visible_counts"]["supported_empty_extension_layout"] > 0
    assert report["counts"]["confirmed_empty_extension_layout"] == 0
    assert {"style", "spacing", "color", "multiobject", "maximum_length", "maximum_length_boundary"} <= report["groups"].keys()
    for path, expected in source_baseline("current").items():
        assert canonical_source_sha256(ROOT / path) == expected["canonical_source_sha256"]


def test_fixture_name_is_only_a_report_label(tmp_path):
    source = ROOT / "tests/samples/text/text_slotstyle_a8_baseline.txt"
    renamed = tmp_path / "unrelated_maxlength_spacing_label.txt"
    renamed.write_bytes(source.read_bytes())
    left = SHADOW.build_report([source])
    right = SHADOW.build_report([renamed])
    assert left["counts"] == right["counts"]
    assert left["fixtures"][0]["records"] == right["fixtures"][0]["records"]
    assert left["readiness"] == right["readiness"]


def test_empty_corpus_cannot_claim_readiness():
    report = SHADOW.build_report([])
    assert report["readiness"] == "unresolved"
    assert report["records_examined"] == 0