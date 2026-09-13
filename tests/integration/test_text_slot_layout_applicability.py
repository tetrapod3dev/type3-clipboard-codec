"""Local version conjunction, negative evidence, and frozen production behavior."""

import importlib.util
from dataclasses import asdict
from pathlib import Path

import pytest

from tests.source_integrity import canonical_source_sha256

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "layout_applicability_shadow", ROOT / "tools/analyze_text_slot_layout_applicability.py")
SHADOW = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SHADOW)


def current_record():
    record = bytearray(SHADOW.EMPTY.RECORD_LENGTH)
    for _, offset, value in SHADOW.MARKERS:
        record[offset:offset + 4] = value.to_bytes(4, "little")
    return record


def current_parent(lines=1):
    prefix = bytearray(SHADOW.PARA_WIDTH + 8 + lines * SHADOW.LINE_WIDTH)
    prefix[:4] = (4).to_bytes(4, "little")
    prefix[52:56] = lines.to_bytes(4, "little")
    for i in range(lines):
        offset = 56 + i * SHADOW.LINE_WIDTH
        prefix[offset:offset + 4] = (4).to_bytes(4, "little")
    prefix[-4:] = (1).to_bytes(4, "little")
    return prefix


def test_current_code_positions_and_combination():
    assert [(m["record_relative_offset"], m["width"], m["current"])
            for m in SHADOW.EVIDENCE["markers"]] == [(0, 4, 5), (92, 4, 5)]
    assert SHADOW.MARKERS == (("attrchar", 0, 5), ("extension", 92, 5))
    record = current_record()
    before = bytes(record)
    result = SHADOW.current_slot_layout_evidence(record)
    assert result["status"] == "current_layout_supported"
    assert result["combined_future_204_supported"]
    assert not result["parser_safe"]
    assert bytes(record) == before


@pytest.mark.parametrize("offset", [0, 92])
@pytest.mark.parametrize("value", [0, 1, 2, 3, 4, 6, 0x7fffffff, 0xffffffff])
def test_version_mutations_fail_closed(offset, value):
    record = current_record()
    record[offset:offset + 4] = value.to_bytes(4, "little")
    result = SHADOW.current_slot_layout_evidence(record)
    assert result["status"] == ("legacy_or_other_layout" if 1 <= value < 5 else "unsupported_version")
    assert not result["combined_future_204_supported"]
    assert len(result["checks"]) == (1 if offset == 0 else 2)
    if offset == 92:
        # Existing helper intentionally remains frozen: six zero words alone can accept this window.
        assert SHADOW.EMPTY.inspect_empty_extension(record)["status"] == "supported_empty_extension_layout"


def test_all_proper_prefixes_and_oversize_fail_closed():
    record = current_record()
    for size in range(len(record)):
        result = SHADOW.current_slot_layout_evidence(record[:size])
        assert result["status"] == "truncated"
        assert not result["combined_future_204_supported"]
    assert SHADOW.current_slot_layout_evidence(record + b"x")["status"] == "unresolved"


@pytest.mark.parametrize("guard", [op for op in SHADOW.EMPTY.extension_operations() if op.get("empty_guard")])
def test_nonempty_condition_is_separate_from_current_versions(guard):
    record = current_record()
    offset = SHADOW.EMPTY.FIXED_LENGTH + guard["extension_relative_start"]
    record[offset:offset + 4] = (1).to_bytes(4, "little")
    result = SHADOW.current_slot_layout_evidence(record)
    assert result["status"] == "current_layout_supported"
    assert result["empty_extension_status"] == "not_empty_extension_layout"
    assert not result["combined_future_204_supported"]


def test_parent_context_optional_required_and_multiple_lines():
    record = current_record()
    assert SHADOW.current_slot_layout_evidence(record, require_parent=True)["status"] == "insufficient_parent_context"
    for lines in (0, 1, 3):
        result = SHADOW.current_slot_layout_evidence(record, parent_prefix=current_parent(lines), require_parent=True)
        assert result["status"] == "current_layout_supported"
        assert result["parent_evidence"]["line_count"] == lines


@pytest.mark.parametrize("offset", [0, 56])
@pytest.mark.parametrize("version", [3, 5, 0xffffffff])
def test_contradictory_parent_versions_veto_local_current(offset, version):
    parent = current_parent()
    parent[offset:offset + 4] = version.to_bytes(4, "little")
    result = SHADOW.current_slot_layout_evidence(current_record(), parent_prefix=parent)
    assert result["status"] == ("legacy_or_other_layout" if version == 3 else "unsupported_version")
    assert not result["combined_future_204_supported"]


def test_parent_truncation_boundary_and_budgets():
    parent = current_parent()
    for size in range(len(parent)):
        result = SHADOW.current_slot_layout_evidence(current_record(), parent_prefix=parent[:size])
        assert result["status"] == "truncated"
    assert SHADOW.inspect_parent_prefix(parent + b"x")["status"] == "unresolved"
    parent[52:56] = (0xffffffff).to_bytes(4, "little")
    assert SHADOW.inspect_parent_prefix(parent)["status"] == "unresolved"
    assert SHADOW.inspect_parent_prefix(b"x" * 20000)["status"] == "unresolved"


def test_f4_partial_correlation_and_extension_version_independence():
    path = ROOT / "tests/samples/text/text_slotstyle_a8_baseline.txt"
    raw = SHADOW.hex_text_to_bytes(path.read_text())
    obj, _ = SHADOW.EMPTY.parse_type3_clipboard_bytes_with_parser(raw)
    candidate = obj.candidate_fields["text_slot_run"]
    span = candidate["payload_span"]
    payload = bytearray(raw[span["start"]:span["start"] + span["length"]])
    before = SHADOW.EMPTY.extract_text_slot_candidate([bytes(payload)])
    first = before["first_prefix_relative_offset"]
    payload[first + 92:first + 96] = (4).to_bytes(4, "little")
    from type3_clipboard_codec.parsers.text.text_slot_candidate import _family

    assert _family(payload, first) == "F4"
    assert SHADOW.EMPTY.extract_text_slot_candidate([bytes(payload)]) is None
    assert SHADOW.current_slot_layout_evidence(payload[first:first + 204])["status"] == "legacy_or_other_layout"
    # Both version markers may match without the other F4 constants.
    assert SHADOW.current_slot_layout_evidence(current_record())["status"] == "current_layout_supported"
    payload[first:first + 4] = (4).to_bytes(4, "little")
    assert SHADOW.EMPTY.extract_text_slot_candidate([bytes(payload)]) != before


def test_corpus_matrix_and_all_observations():
    report = SHADOW.build_report()
    assert report["records_examined"] == report["counts"]["current_layout_supported"] == 700
    assert report["visible_counts"]["current_layout_supported"] == 616
    assert report["terminal_counts"]["current_layout_supported"] == 84
    assert sum(report["counts"].values()) == 700
    assert report["serializer_applicability_readiness"] == "ready_for_production_gate_review"
    assert report["combined_future_gate_readiness"] == "ready_for_production_gate_review"
    for values in report["observed_versions"].values():
        assert values == {"all": {5: 700}, "visible": {5: 616}, "terminal": {5: 84}}
    assert report["diagnostic_parent_version_values"] == {"attrpara": {4: 84}, "attrline": {4: 88}}
    assert report["descriptor_second_word_values"] == {6: 84}
    assert report["parent_candidates_ambiguous_or_missing"] == 0
    assert report["real_nonempty_records"] == report["unaligned_paragraph_count"] == 0
    assert (report["files_examined"], report["fixtures_examined"], len(report["input_issues"])) == (126, 116, 10)


def test_name_order_and_enclosing_offset_independence(tmp_path):
    original = ROOT / "tests/samples/text/text_slotstyle_a8_baseline.txt"
    renamed = tmp_path / "unrelated.txt"
    renamed.write_bytes(original.read_bytes())  # Existing bytes only; never a synthetic capture.
    a = SHADOW.build_report([original, renamed])
    b = SHADOW.build_report([renamed, original])
    assert a["counts"] == b["counts"]
    assert a["fixtures"][0]["records"] == a["fixtures"][1]["records"] == b["fixtures"][0]["records"]
    record = bytes(current_record())
    for offset in (0, 1, 19, 512):
        envelope = b"x" * offset + record
        assert SHADOW.current_slot_layout_evidence(envelope[offset:]) == SHADOW.current_slot_layout_evidence(record)
    assert SHADOW.build_report([])["serializer_applicability_readiness"] == "unresolved"


def test_production_sources_fixtures_runtime_and_empty_outputs_preserved():
    sources = {p: canonical_source_sha256(p) for p in (ROOT / "src/type3_clipboard_codec").rglob("*.py")}
    fixtures = {p: p.read_bytes() for p in (ROOT / "tests/samples").rglob("*") if p.is_file()}

    def runtime():
        outputs = []
        for path, content in fixtures.items():
            if path.suffix != ".txt":
                continue
            try:
                raw = SHADOW.hex_text_to_bytes(content.decode("utf-8"))
            except (SHADOW.EMPTY.InvalidHexError, UnicodeDecodeError):
                continue
            obj, chain = SHADOW.EMPTY.parse_type3_clipboard_bytes_with_parser(raw)
            outputs.append((asdict(obj), chain))
        return outputs

    before = runtime()
    empty_before = SHADOW.EMPTY.build_report()
    SHADOW.build_report()
    assert runtime() == before
    assert SHADOW.EMPTY.build_report() == empty_before
    assert {p: canonical_source_sha256(p) for p in sources} == sources
    assert all(p.read_bytes() == content for p, content in fixtures.items())
