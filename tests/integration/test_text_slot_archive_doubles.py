"""Five archive doubles are additive, raw-preserving, and downstream of all gates."""

import json
import math
import struct
from dataclasses import asdict
from pathlib import Path

import pytest

from tests import frozen_text_slot_candidate_v2 as before_typed
from tests.text_slot_typed_output import prior_candidate, prior_object_dict
from tests.unit.test_text_slot_candidate import make_run
from type3_clipboard_codec import parse_type3_clipboard_bytes_with_parser
from type3_clipboard_codec.exceptions import InvalidHexError
from type3_clipboard_codec.inspect.formatters import _json_safe
from type3_clipboard_codec.inspect.hex_input import hex_text_to_bytes
from type3_clipboard_codec.parsers import type3_chain_parser
from type3_clipboard_codec.parsers.text import text_slot_candidate as runtime

ROOT = Path(__file__).resolve().parents[2]
OFFSETS = (0x0C, 0x14, 0x1C, 0x40, 0x48)


@pytest.mark.parametrize("offset", OFFSETS)
def test_exact_eight_byte_values_raw_bits_and_acceptance_independence(offset):
    for value in (0.01, 0.02, 0.5, 1.0, 1.5, math.pi / 12, -math.pi / 12,
                  0.0, -0.0, -1.0, 1e300, -1e300, float("nan"), float("inf"), -float("inf")):
        payload = make_run()
        encoded = struct.pack("<d", value)
        payload[40 + offset:40 + offset + 8] = encoded
        before = bytes(payload)
        candidate = runtime.extract_text_slot_candidate([bytes(payload)])
        assert candidate is not None
        assert prior_candidate(candidate) == before_typed.extract_text_slot_candidate([payload])
        field = candidate["slots"][0]["archive_double_candidates"][hex(offset)]
        assert set(field) == {"raw_bytes", "f64le", "typed_width"}
        assert field["raw_bytes"] == encoded and field["typed_width"] == 8
        if math.isfinite(value):
            assert isinstance(field["f64le"], float)
            assert struct.pack("<d", field["f64le"]) == encoded
        else:
            assert field["f64le"] == repr(value)
        assert bytes(payload) == before
        # Nonfinite values are losslessly recoverable from raw bytes and remain JSON-safe.
        json.dumps(_json_safe(candidate), allow_nan=False)


@pytest.mark.parametrize("bits", [0x7ff8000000001234, 0xfff8000000005678, 0x7ff0000000000001])
def test_nan_payload_bits_preserved(bits):
    payload = make_run()
    raw = bits.to_bytes(8, "little")
    payload[52:60] = raw
    candidate = runtime.extract_text_slot_candidate([bytes(payload)])
    assert candidate is not None
    field = candidate["slots"][0]["archive_double_candidates"]["0xc"]
    assert field["raw_bytes"] == raw
    assert math.isnan(struct.unpack("<d", field["raw_bytes"])[0])
    assert field["f64le"] == "nan"


@pytest.mark.parametrize("offset,value", [(0, 4), (92, 4), (92, 6),
                                         (132, 1), (152, 1), (188, 1), (192, 1), (196, 1), (200, 1)])
def test_failed_record_anywhere_in_run_cannot_reach_double_decode(monkeypatch, offset, value):
    def forbidden(*args):
        pytest.fail("typed decode reached for failed run")

    monkeypatch.setattr(runtime.struct, "unpack", forbidden)
    for ordinal in range(3):
        payload = make_run()
        position = 40 + ordinal * 204 + offset
        payload[position:position + 4] = value.to_bytes(4, "little")
        assert runtime.extract_text_slot_candidate([bytes(payload)]) is None


def test_truncation_no_typed_decode(monkeypatch):
    monkeypatch.setattr(runtime.struct, "unpack", lambda *_: pytest.fail("decode before complete run"))
    payload = make_run()
    for length in range(40, 40 + 3 * 204 + 64):
        assert runtime.extract_text_slot_candidate([payload[:length]]) is None


def test_terminal_type_not_visible_ownership_and_rgb_unchanged():
    candidate = runtime.extract_text_slot_candidate([make_run()])
    assert candidate["parser_safe"] is False
    assert runtime.ARCHIVE_DOUBLE_OFFSETS == OFFSETS
    for slot in candidate["slots"]:
        assert list(slot["archive_double_candidates"]) == [hex(offset) for offset in OFFSETS]
        assert slot["ownership"] == "unresolved" and slot["matched_chain"] is None
        assert slot["rgb_bytes_candidate"] == {
            "raw_bytes": [16, 32, 48], "typed_width": None, "confidence": "provisional"}
        assert all(field["typed_width"] == 8 for field in slot["archive_double_candidates"].values())
    assert candidate["slots"][-1]["terminal_candidate"] is True


def test_full_corpus_additive_projection_and_exact_raw_values(monkeypatch):
    captures = visible = terminal = records = 0
    for path in sorted((ROOT / "tests/samples").rglob("*.txt")):
        content = path.read_bytes()
        try:
            raw = hex_text_to_bytes(content.decode("utf-8"))
        except (InvalidHexError, UnicodeDecodeError):
            continue
        captures += 1
        with monkeypatch.context() as patch:
            patch.setattr(type3_chain_parser, "extract_text_slot_candidate", before_typed.extract_text_slot_candidate)
            before, old_chain = parse_type3_clipboard_bytes_with_parser(raw)
        after, new_chain = parse_type3_clipboard_bytes_with_parser(raw)
        assert (prior_object_dict(after), new_chain) == (asdict(before), old_chain), path.name
        parser = type3_chain_parser.Type3ChainParser()
        _, _, base = parser._read_top_level_header(raw)
        for node in parser._extract_nodes(raw[base:]):
            if node.header.class_name != "CParagraphe":
                continue
            candidate = runtime.extract_text_slot_candidate([node.payload])
            assert prior_candidate(candidate) == before_typed.extract_text_slot_candidate([node.payload])
            if candidate is None:
                continue
            for slot in candidate["slots"]:
                start = slot["prefix_relative_offset"]
                for offset in OFFSETS:
                    field = slot["archive_double_candidates"][hex(offset)]
                    expected = node.payload[start + offset:start + offset + 8]
                    assert field["raw_bytes"] == expected
                    value = struct.unpack("<d", expected)[0]
                    assert field["f64le"] == (value if math.isfinite(value) else repr(value))
                records += 1
                terminal += bool(slot["terminal_candidate"])
                visible += not slot["terminal_candidate"]
        assert path.read_bytes() == content
    assert (captures, records, visible, terminal) == (116, 700, 616, 84)


@pytest.mark.parametrize("label,offset,controls", [
    ("height", 12, [("height20", 0.02)]),
    ("width", 20, [("width50", 0.5), ("width150", 1.5)]),
    ("slant", 28, [("slant_p15", math.pi / 12), ("slant_m15", -math.pi / 12)]),
    ("spacing", 64, [("spacing50", 0.5), ("spacing150", 1.5)]),
    ("rotation", 72, [("rotation_p15", math.pi / 12), ("rotation_m15", -math.pi / 12)]),
])
def test_controlled_correlations_only_after_structural_extraction(label, offset, controls):
    def extract(name):
        raw = hex_text_to_bytes((ROOT / "tests/samples/text" / name).read_text())
        obj, _ = parse_type3_clipboard_bytes_with_parser(raw)
        # Production has no name/intent arguments. Oracle comparison begins after extraction.
        return obj.candidate_fields["text_slot_run"]["slots"]

    baseline = extract("text_slotstyle_a8_baseline.txt")
    expected = 0.01 if label == "height" else 1.0 if label in ("width", "spacing") else 0.0
    assert baseline[3]["archive_double_candidates"][hex(offset)]["f64le"] == expected
    for suffix, expected in controls:
        slots = extract(f"text_slotstyle_a8_char4_{suffix}.txt")
        field = slots[3]["archive_double_candidates"][hex(offset)]
        assert math.isclose(field["f64le"], expected, abs_tol=1e-9)
        assert struct.pack("<d", field["f64le"]) == field["raw_bytes"]


def test_offset_input_order_and_fixture_names_have_no_numeric_role(tmp_path):
    for start in (16, 40, 1100):
        payload = make_run(start=start)
        a = runtime.extract_text_slot_candidate([payload, b"opaque"])
        b = runtime.extract_text_slot_candidate([b"opaque", payload])
        assert a.pop("payload_index") == 0 and b.pop("payload_index") == 1
        assert a == b
    source = ROOT / "tests/samples/text/text_slotstyle_a8_baseline.txt"
    renamed = tmp_path / "unknown.txt"
    renamed.write_bytes(source.read_bytes())
    a, ac = parse_type3_clipboard_bytes_with_parser(hex_text_to_bytes(source.read_text()))
    b, bc = parse_type3_clipboard_bytes_with_parser(hex_text_to_bytes(renamed.read_text()))
    assert (asdict(a), ac) == (asdict(b), bc)
