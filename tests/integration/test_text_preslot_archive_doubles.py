"""Optional parent-derived doubles must never tighten existing slot acceptance."""

import json
import math
import struct
from dataclasses import asdict
from pathlib import Path

import pytest

from tests.integration.test_text_preslot_crosswalk import SHADOW, paragraph
from tests.text_slot_typed_output import without_preslot_candidate, without_preslot_object
from type3_clipboard_codec import parse_type3_clipboard_bytes_with_parser
from type3_clipboard_codec.exceptions import InvalidHexError
from type3_clipboard_codec.inspect.formatters import _json_safe
from type3_clipboard_codec.inspect.hex_input import hex_text_to_bytes
from type3_clipboard_codec.parsers.text import text_slot_candidate as runtime

ROOT = Path(__file__).resolve().parents[2]
KEY = "preslot_archive_double_candidates"
FIELDS = (("P+0x20", 32, "CTxtAttrPara+0x20"),
          ("P+0x50", 80, "CTxtAttrLine[0]+0x30"),
          ("P+0x68", 104, "CTxtAttrLine[0]+0x10"))


def extract(payload):
    return runtime.extract_text_slot_candidate([bytes(payload)])


@pytest.mark.parametrize("lines", [1, 2])
@pytest.mark.parametrize("shift", [181, 182, 183, 213])
def test_three_doubles_at_dynamic_positions_and_general_line_equation(lines, shift):
    payload, p, first = paragraph(value=b"v" * (shift - 176), lines=lines)
    values = (-0.125, -0.06, 1234.5)  # Distinct fields, deliberately unequal.
    for (_, relative, _), value in zip(FIELDS, values, strict=True):
        payload[p + relative:p + relative + 8] = struct.pack("<d", value)
    raw = bytes(payload)
    candidate = extract(payload)
    assert candidate is not None
    assert candidate["first_prefix_relative_offset"] == first == p + 60 + 68 * lines
    assert runtime._derive_current_preslot_layout(payload) == (p, first, 3, lines)
    assert list(candidate[KEY]) == [key for key, *_ in FIELDS]
    for (key, relative, source), value in zip(FIELDS, values, strict=True):
        assert candidate[KEY][key] == {
            "raw_bytes": struct.pack("<d", value), "f64le": value, "typed_width": 8,
            "payload_relative_offset": p + relative, "source": source,
        }
    assert p == shift and bytes(payload) == raw
    assert all(KEY not in slot for slot in candidate["slots"])


@pytest.mark.parametrize("serializer,current", [("base", 8), ("guid", 2), ("para", 4), ("line", 4)])
@pytest.mark.parametrize("kind", ["zero", "legacy", "future", "high", "negative"])
def test_unsupported_parent_keeps_existing_candidate(monkeypatch, serializer, current, kind):
    payload, p, _ = paragraph(lines=2)
    offsets = {"base": 52, "guid": 72, "para": p, "line": p + 56 + 68}
    value = {"zero": 0, "legacy": current - 1, "future": current + 1,
             "high": 0x7fffffff, "negative": 0xffffffff}[kind]
    offset = offsets[serializer]
    # Opaque parent bytes keep a version=5 word from resembling the existing F4 core.
    # This isolates the new parent-only gate without changing that old scanner rule.
    payload[offset + 8:offset + 12] = b"\x02" * 4
    payload[offset:offset + 4] = struct.pack("<I", value)
    with monkeypatch.context() as patch:
        patch.setattr(runtime, "_preslot_archive_double_candidates", lambda *_: None)
        previous = extract(payload)
    actual = extract(payload)
    assert previous is not None and actual == previous and KEY not in actual


@pytest.mark.parametrize("state", ["map", "ambiguous", "invalid_flags", "no_line"])
def test_unsupported_state_omits_only_new_group(monkeypatch, state):
    payload, _, _ = paragraph(lines=0 if state == "no_line" else 1)
    if state == "map":
        payload[130:138] = struct.pack("<Q", 1)
    elif state == "ambiguous":
        payload[48:52] = struct.pack("<I", 0x01001100)
    elif state == "invalid_flags":
        payload[48:52] = bytes(4)
    with monkeypatch.context() as patch:
        patch.setattr(runtime, "_preslot_archive_double_candidates", lambda *_: None)
        previous = extract(payload)
    assert previous is not None and extract(payload) == previous
    assert KEY not in previous


def test_all_parent_truncations_abstain_without_oob():
    payload, _, first = paragraph(lines=2)
    for end in range(first):
        assert runtime._derive_current_preslot_layout(payload[:end]) is None, end
        assert runtime._preslot_archive_double_candidates(payload[:end], first, 3) is None


@pytest.mark.parametrize("offset", [92, 96, 234])
def test_impossible_counts_and_lengths_are_bounded(offset):
    payload, _, first = paragraph()
    payload[offset:offset + 4] = b"\xff" * 4
    assert runtime._preslot_archive_double_candidates(payload, first, 3) is None
    assert extract(payload) is not None and KEY not in extract(payload)


@pytest.mark.parametrize("mismatch", ["alignment", "count"])
def test_final_cross_check_only_gates_optional_output(monkeypatch, mismatch):
    payload, p, first = paragraph()
    before = extract(payload)
    # A contradictory independently derived parent must not veto the accepted run.
    result = (p, first + (mismatch == "alignment"), 3 + (mismatch == "count"), 1)
    monkeypatch.setattr(runtime, "_derive_current_preslot_layout", lambda _: result)
    after = extract(payload)
    assert after == without_preslot_candidate(before)
    assert runtime._preslot_archive_double_candidates(payload, first, 3) is None


@pytest.mark.parametrize("bits", [0x7ff8000000001234, 0xfff8000000005678,
                                  0x7ff0000000000001, 0x7ff0000000000000,
                                  0xfff0000000000000, 0x8000000000000000])
def test_nonfinite_and_signed_zero_preserve_raw_and_selection(bits):
    payload, p, _ = paragraph()
    before = extract(payload)
    for key, relative, _ in FIELDS:
        raw = bits.to_bytes(8, "little")
        payload[p + relative:p + relative + 8] = raw
        after = extract(payload)
        assert without_preslot_candidate(after) == without_preslot_candidate(before)
        field = after[KEY][key]
        assert field["raw_bytes"] == raw and field["typed_width"] == 8
        value = struct.unpack("<d", raw)[0]
        if math.isfinite(value):
            assert struct.pack("<d", field["f64le"]) == raw
        else:
            assert field["f64le"] == repr(value)
        json.dumps(_json_safe(after), allow_nan=False)


def test_all_84_groups_agree_with_frozen_shadow_and_old_outputs(monkeypatch):
    captures = groups = multiline = failures = 0
    for path in sorted((ROOT / "tests/samples").rglob("*.txt")):
        try:
            raw = hex_text_to_bytes(path.read_bytes().decode("utf-8"))
        except (InvalidHexError, UnicodeDecodeError):
            continue
        captures += 1
        with monkeypatch.context() as patch:
            patch.setattr(runtime, "_preslot_archive_double_candidates", lambda *_: None)
            previous, old_chain = parse_type3_clipboard_bytes_with_parser(raw)
        actual, new_chain = parse_type3_clipboard_bytes_with_parser(raw)
        assert (without_preslot_object(actual), new_chain) == (asdict(previous), old_chain)
        parser = SHADOW.Type3ChainParser()
        _, _, base = parser._read_top_level_header(raw)
        for node in parser._extract_nodes(raw[base:]):
            if node.header.class_name != "CParagraphe":
                continue
            candidate = extract(node.payload)
            shadow = SHADOW.derive_preslot(node.payload)
            assert SHADOW.compare_alignment(shadow, candidate) == "exact_match"
            fields = SHADOW.field_evidence(node.payload, shadow)
            if candidate is None or KEY not in candidate:
                failures += 1
                continue
            groups += 1
            multiline += shadow["line_count"] == 2
            for (key, relative, source), old_key in zip(FIELDS, ("A", "length", "B"), strict=True):
                field = candidate[KEY][key]
                assert field["payload_relative_offset"] == shadow["p_origin"] + relative
                assert field["raw_bytes"].hex() == fields[old_key]["raw_hex"]
                assert field["f64le"] == fields[old_key]["value"]
                assert field["source"] == source and field["typed_width"] == 8
    assert (captures, groups, multiline, failures) == (116, 84, 4, 0)


def test_node_order_offsets_and_names_do_not_select_fields(tmp_path):
    descriptor = bytes.fromhex("ffff06000b00") + b"CParagraphe"
    header = bytes.fromhex("010000004172")
    one, _, _ = paragraph(value=b"v" * 5)
    two, _, _ = paragraph(value=b"v" * 7, lines=2)
    bad, p, _ = paragraph()
    bad[p:p + 4] = struct.pack("<I", 3)
    for offset in (0, 31, 2048):
        for buffers in ((one, two, bad), (bad, two, one)):
            raw = header + b"\xcc" * offset + b"".join(descriptor + data for data in buffers)
            parser = SHADOW.Type3ChainParser()
            _, _, base = parser._read_top_level_header(raw)
            nodes = [n for n in parser._extract_nodes(raw[base:]) if n.header.class_name == "CParagraphe"]
            assert len(nodes) == 3
            for node, original in zip(nodes, buffers, strict=True):
                assert extract(node.payload) == extract(original)
    source = ROOT / "tests/samples/text/text_slotstyle_a8_baseline.txt"
    renamed = tmp_path / "unrelated.txt"
    renamed.write_bytes(source.read_bytes())
    a, ac = parse_type3_clipboard_bytes_with_parser(hex_text_to_bytes(source.read_text()))
    b, bc = parse_type3_clipboard_bytes_with_parser(hex_text_to_bytes(renamed.read_text()))
    assert (asdict(a), ac) == (asdict(b), bc)
