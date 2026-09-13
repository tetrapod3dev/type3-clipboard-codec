"""Production current/empty hardening: whole-run rejection and exact corpus preservation."""

import importlib.util
import inspect
import json
from dataclasses import asdict
from pathlib import Path

import pytest

from tests import frozen_text_slot_candidate_v2 as before_gate
from tests.source_integrity import canonical_source_sha256, source_baseline
from tests.unit.test_text_slot_candidate import make_run
from type3_clipboard_codec import parse_type3_clipboard_bytes_with_parser
from type3_clipboard_codec.exceptions import InvalidHexError
from type3_clipboard_codec.inspect.hex_input import hex_text_to_bytes
from type3_clipboard_codec.parsers import type3_chain_parser
from type3_clipboard_codec.parsers.text import text_slot_candidate as runtime

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "production_gate_shadow", ROOT / "tools/analyze_text_slot_layout_applicability.py")
SHADOW = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SHADOW)
VALIDATE = runtime._validate_current_empty_slot_layout
VERSIONS = (0, 1, 2, 3, 4, 6, 0x7fffffff, 0xffffffff)
GUARDS = (132, 152, 188, 192, 196, 200)


def test_constants_match_frozen_archive_order_and_f4_is_unchanged():
    model = json.loads((ROOT / "tools/text_slot_empty_extension_layout.json").read_text())
    fixed = sum(op["empty_path_width"] for op in model["fixed_operations"])
    cursor = fixed
    guards = []
    for op in model["extension_operations"]:
        if op.get("empty_guard"):
            guards.append(cursor)
        cursor += op["empty_path_width"]
    assert runtime.RECORD_SIZE == runtime.STRIDE == cursor == 204
    assert runtime.EXTENSION_OFFSET == runtime.EXTENSION_VERSION_OFFSET == fixed == 92
    assert runtime.ATTRCHAR_VERSION_OFFSET == 0
    assert runtime.ATTRCHAR_CURRENT_VERSION == runtime.EXTENSION_CURRENT_VERSION == 5
    assert tuple(offset for offset, _ in runtime.EMPTY_FIELDS) == tuple(guards) == GUARDS
    assert inspect.getsource(runtime._family) == inspect.getsource(before_gate._family)


def test_pre_gate_snapshot_retains_approved_source_provenance():
    entry = source_baseline("current")["src/type3_clipboard_codec/parsers/text/text_slot_candidate.py"]
    previous = entry["previous_baselines"][-1]
    assert canonical_source_sha256(Path(before_gate.__file__)) == previous["canonical_source_sha256"]
    assert previous["baseline_commit_or_snapshot"] == "a220a4830239b94fb6690c4c7aa42e4005f84ff4"
    assert entry["legacy_raw_sha256"] == previous["legacy_raw_sha256"]
    assert entry["reason"] == "Approved production current-layout gate; current AttrChar v5 / extension v5 / empty only."


@pytest.mark.parametrize("offset", [0, 92])
@pytest.mark.parametrize("version", VERSIONS)
def test_every_record_version_mutation_abstains(offset, version):
    original = make_run()
    assert runtime.extract_text_slot_candidate([original]) is not None
    for ordinal in range(3):  # First, interior visible, and terminal use identical rules.
        payload = bytearray(original)
        start = 40 + ordinal * 204
        payload[start + offset:start + offset + 4] = version.to_bytes(4, "little")
        reason = "attrchar_version_mismatch" if offset == 0 else "extension_version_mismatch"
        assert VALIDATE(payload[start:start + 204]) == reason
        assert runtime.extract_text_slot_candidate([payload]) is None
        if offset == 92:
            assert runtime._family(payload, start) == "F4"
            assert before_gate.extract_text_slot_candidate([payload]) is not None


@pytest.mark.parametrize("offset", GUARDS)
def test_each_nonempty_field_rejects_whole_run_and_parser_does_not_crash(offset):
    fixture = ROOT / "tests/samples/text/text_slotstyle_a8_baseline.txt"
    raw = hex_text_to_bytes(fixture.read_text())
    obj, chain = parse_type3_clipboard_bytes_with_parser(raw)
    candidate = obj.candidate_fields["text_slot_run"]
    origin = candidate["payload_span"]["start"]
    for slot in candidate["slots"]:
        for value in (1, 0xffffffff):
            changed = bytearray(raw)
            start = origin + slot["prefix_relative_offset"]
            changed[start + offset:start + offset + 4] = value.to_bytes(4, "little")
            result, after_chain = parse_type3_clipboard_bytes_with_parser(bytes(changed))
            assert result.candidate_fields.get("text_slot_run") is None
            assert after_chain == chain
            assert VALIDATE(changed[start:start + 204]) is not None


def test_all_truncations_and_meaningful_payload_boundaries():
    data = make_run(codes=(0,))
    record = data[40:244]
    assert VALIDATE(record) is None
    for length in range(204):
        assert VALIDATE(record[:length]) == "truncated"
    assert VALIDATE(record + b"x") == "oversized_record_window"
    boundaries = {0, 4, 92, 96, 204, *(offset + 4 for offset in GUARDS), *GUARDS}
    for end in boundaries:
        for delta in (-1, 0, 1):
            length = max(0, end + delta)
            assert runtime.extract_text_slot_candidate([data[:40 + length]]) is None


def test_first_record_fails_before_advancing_and_later_failures_are_not_partial(monkeypatch):
    validate = runtime._validate_current_empty_slot_layout
    for failing in range(3):
        calls = []

        def observe(record, calls=calls):
            calls.append(bytes(record))
            return validate(record)

        monkeypatch.setattr(runtime, "_validate_current_empty_slot_layout", observe)
        payload = make_run()
        start = 40 + failing * 204
        payload[start + 92:start + 96] = (4).to_bytes(4, "little")
        candidate, audit = runtime._evaluate([payload])
        assert candidate is None
        assert audit["failing_layer"] == "layout"
        assert audit["reason"] == "extension_version_mismatch"
        assert audit["traversed_slots"] == failing
        assert len(calls) == failing + 1


def test_arbitrary_fixed_extension_bytes_preserved_without_semantic_promotion():
    payload = make_run()
    original = bytes(payload)
    candidate = runtime.extract_text_slot_candidate([payload])
    assert candidate == before_gate.extract_text_slot_candidate([payload])
    assert bytes(payload) == original
    for slot in candidate["slots"]:
        start = slot["prefix_relative_offset"]
        record = payload[start:start + 204]
        assert VALIDATE(record) is None
        assert any(b == 0xcc for b in record[96:])
        assert SHADOW.current_slot_layout_evidence(record)["combined_future_204_supported"]
        assert slot["slot_code_candidate"]["typed_width"] is None
        assert slot["rgb_bytes_candidate"]["typed_width"] is None
        assert len(slot["rgb_bytes_candidate"]["raw_bytes"]) == 3
    assert not candidate["parser_safe"]


def test_filename_offset_and_input_order_independence(tmp_path):
    source = ROOT / "tests/samples/text/text_slotstyle_a8_baseline.txt"
    renamed = tmp_path / "unrelated_name.txt"
    renamed.write_bytes(source.read_bytes())
    a, ac = parse_type3_clipboard_bytes_with_parser(hex_text_to_bytes(source.read_text()))
    b, bc = parse_type3_clipboard_bytes_with_parser(hex_text_to_bytes(renamed.read_text()))
    assert (asdict(a), ac) == (asdict(b), bc)
    for start in (16, 40, 177, 1100):
        payload = make_run(start=start)
        a = runtime.extract_text_slot_candidate([b"opaque", payload])
        b = runtime.extract_text_slot_candidate([payload, b"opaque"])
        assert a.pop("payload_index") == 1
        assert b.pop("payload_index") == 0
        assert a == b
        assert a["first_prefix_relative_offset"] == start


def test_full_corpus_pre_gate_outputs_and_shadow_agreement(monkeypatch):
    records = visible = terminal = captures = 0
    for path in sorted((ROOT / "tests/samples").rglob("*.txt")):
        file_bytes = path.read_bytes()
        try:
            raw = hex_text_to_bytes(file_bytes.decode("utf-8"))
        except (InvalidHexError, UnicodeDecodeError):
            continue
        captures += 1
        with monkeypatch.context() as patch:
            patch.setattr(type3_chain_parser, "extract_text_slot_candidate", before_gate.extract_text_slot_candidate)
            before, old_chain = parse_type3_clipboard_bytes_with_parser(raw)
        after, new_chain = parse_type3_clipboard_bytes_with_parser(raw)
        assert (asdict(after), new_chain) == (asdict(before), old_chain), path.name
        parser = type3_chain_parser.Type3ChainParser()
        _, _, base = parser._read_top_level_header(raw)
        for node in parser._extract_nodes(raw[base:]):
            if node.header.class_name != "CParagraphe":
                continue
            old = before_gate.extract_text_slot_candidate([node.payload])
            new = runtime.extract_text_slot_candidate([node.payload])
            assert old == new, path.name
            if old is None:
                continue
            # Use pre-gate alignment so rejection cannot silently reduce the comparison population.
            for slot in old["slots"]:
                start = slot["prefix_relative_offset"]
                record = node.payload[start:start + 204]
                assert (VALIDATE(record) is None) == SHADOW.current_slot_layout_evidence(
                    record)["combined_future_204_supported"] is True
                records += 1
                terminal += bool(slot["terminal_candidate"])
                visible += not slot["terminal_candidate"]
        assert path.read_bytes() == file_bytes
    assert (captures, records, visible, terminal) == (116, 700, 616, 84)
