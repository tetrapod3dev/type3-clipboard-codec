"""Two internal-role references; canonical fields and selection remain authoritative."""

import json
import math
import struct
from collections import Counter
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path

import pytest

from tests.integration.test_text_preslot_crosswalk import SHADOW, paragraph
from tests.text_slot_typed_output import without_preslot_alias_object, without_preslot_aliases
from type3_clipboard_codec import parse_type3_clipboard_bytes_with_parser
from type3_clipboard_codec.exceptions import InvalidHexError
from type3_clipboard_codec.inspect.formatters import _json_safe
from type3_clipboard_codec.inspect.hex_input import hex_text_to_bytes
from type3_clipboard_codec.parsers.text import text_slot_candidate as runtime

ROOT = Path(__file__).resolve().parents[2]
KEY = "preslot_archive_double_aliases"
CANONICAL = "preslot_archive_double_candidates"
ALIASES = {"stored_minimum_line_layout_scale": "P+0x20",
           "stored_first_line_layout_scale": "P+0x68"}


@pytest.mark.parametrize("lines", [1, 2])
def test_reference_map_only_and_unequal_values(lines):
    payload, p, first = paragraph(lines=lines)
    for offset, value in ((32, -2.5), (80, 0.06), (104, 7.25)):
        payload[p + offset:p + offset + 8] = struct.pack("<d", value)
    expected = runtime._preslot_archive_double_candidates(payload, first, 3)
    frozen = deepcopy(expected)
    candidate = runtime.extract_text_slot_candidate([bytes(payload)])
    assert candidate[KEY] == ALIASES
    assert list(candidate[CANONICAL]) == ["P+0x20", "P+0x50", "P+0x68"]
    assert candidate[CANONICAL] == frozen == expected
    assert candidate[CANONICAL]["P+0x20"]["f64le"] != candidate[CANONICAL]["P+0x68"]["f64le"]
    assert candidate[CANONICAL]["P+0x68"]["source"] == "CTxtAttrLine[0]+0x10"
    assert "P+0x50" not in candidate[KEY].values()
    assert all(isinstance(target, str) and target in candidate[CANONICAL] for target in candidate[KEY].values())
    assert all(KEY not in slot for slot in candidate["slots"])
    assert candidate["first_prefix_relative_offset"] == p + 60 + 68 * lines


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf"), -1e200, -0.0])
def test_nonfinite_negative_and_raw_bits_do_not_gate_aliases(value):
    payload, p, _ = paragraph()
    for offset in (32, 104):
        payload[p + offset:p + offset + 8] = struct.pack("<d", value)
    candidate = runtime.extract_text_slot_candidate([bytes(payload)])
    assert candidate[KEY] == ALIASES
    for target in ALIASES.values():
        field = candidate[CANONICAL][target]
        assert field["raw_bytes"] == struct.pack("<d", value)
        assert field["typed_width"] == 8
        if math.isfinite(value):
            assert struct.pack("<d", field["f64le"]) == field["raw_bytes"]
        else:
            assert field["f64le"] == repr(value)
    encoded = json.dumps(_json_safe(candidate), allow_nan=False)
    assert encoded == json.dumps(_json_safe(runtime.extract_text_slot_candidate([bytes(payload)])), allow_nan=False)
    assert json.loads(encoded)[KEY] == ALIASES


@pytest.mark.parametrize("keys", [(), ("P+0x20",), ("P+0x68",), ("P+0x50",), ("P+0x20", "P+0x68")])
def test_individual_canonical_availability_and_no_value_access(monkeypatch, keys):
    payload, _, _ = paragraph()
    group = {key: object() for key in keys}  # Any attempt to inspect numbers would fail.
    monkeypatch.setattr(runtime, "_preslot_archive_double_candidates", lambda *_: group)
    candidate = runtime.extract_text_slot_candidate([bytes(payload)])
    expected = {name: key for name, key in ALIASES.items() if key in group}
    assert candidate[CANONICAL] is group
    assert candidate.get(KEY, {}) == expected
    assert (KEY in candidate) == bool(expected)


@pytest.mark.parametrize("failure", ["version", "map", "no_line"])
def test_parent_failure_omits_group_and_aliases_without_rejecting_slots(failure):
    payload, p, _ = paragraph(lines=0 if failure == "no_line" else 1)
    if failure == "version":
        payload[p:p + 4] = struct.pack("<I", 3)
    elif failure == "map":
        payload[130:138] = struct.pack("<Q", 1)
    candidate = runtime.extract_text_slot_candidate([bytes(payload)])
    assert candidate is not None
    assert CANONICAL not in candidate and KEY not in candidate


def test_record_gate_precedes_parent_extraction_and_alias_creation(monkeypatch):
    payload, _, first = paragraph()
    payload[first + 92:first + 96] = struct.pack("<I", 4)
    def forbidden(*_):
        pytest.fail("parent/alias stage reached before record gate")
    monkeypatch.setattr(runtime, "_preslot_archive_double_candidates", forbidden)
    assert runtime.extract_text_slot_candidate([bytes(payload)]) is None


def test_projection_preserves_every_canonical_field():
    payload, _, _ = paragraph()
    candidate = runtime.extract_text_slot_candidate([bytes(payload)])
    projected = without_preslot_aliases(candidate)
    assert KEY not in projected and KEY in candidate
    assert projected[CANONICAL] == candidate[CANONICAL]
    assert projected["slots"] == candidate["slots"]
    assert list(projected) == [key for key in candidate if key != KEY]


def test_corpus_alias_counts_and_canonical_preservation():
    counts = Counter()
    captures = groups = multiline = 0
    for path in sorted((ROOT / "tests/samples").rglob("*.txt")):
        try:
            raw = hex_text_to_bytes(path.read_bytes().decode("utf-8"))
        except (InvalidHexError, UnicodeDecodeError):
            continue
        captures += 1
        obj, chain = parse_type3_clipboard_bytes_with_parser(raw)
        projected = without_preslot_alias_object(obj)
        expected = asdict(obj)
        run = expected["candidate_fields"].get("text_slot_run")
        if run is not None:
            run.pop(KEY, None)
        assert projected == expected
        again, again_chain = parse_type3_clipboard_bytes_with_parser(raw)
        assert (asdict(again), again_chain) == (asdict(obj), chain)
        parser = SHADOW.Type3ChainParser()
        _, _, base = parser._read_top_level_header(raw)
        for node in parser._extract_nodes(raw[base:]):
            if node.header.class_name != "CParagraphe":
                continue
            candidate = runtime.extract_text_slot_candidate([node.payload])
            assert candidate[KEY] == ALIASES
            parent = SHADOW.derive_preslot(node.payload)
            fields = SHADOW.field_evidence(node.payload, parent)
            for neutral, field_name in (("P+0x20", "A"), ("P+0x50", "length"), ("P+0x68", "B")):
                assert candidate[CANONICAL][neutral]["raw_bytes"].hex() == fields[field_name]["raw_hex"]
                assert candidate[CANONICAL][neutral]["f64le"] == fields[field_name]["value"]
            groups += 1
            multiline += parent["line_count"] == 2
            counts.update(candidate[KEY].keys())
    assert (captures, groups, multiline) == (116, 84, 4)
    assert counts == {name: 84 for name in ALIASES}
