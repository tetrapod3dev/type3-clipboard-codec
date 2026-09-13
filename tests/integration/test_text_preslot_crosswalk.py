"""Pre-slot evidence is independent of fixture values and production alignment."""

import importlib.util
import json
import struct
from dataclasses import asdict
from pathlib import Path

import pytest

from tests.unit.test_text_slot_candidate import make_run
from type3_clipboard_codec import parse_type3_clipboard_bytes_with_parser
from type3_clipboard_codec.exceptions import InvalidHexError
from type3_clipboard_codec.inspect.hex_input import hex_text_to_bytes

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("preslot_shadow", ROOT / "tools/analyze_text_preslot_crosswalk.py")
SHADOW = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SHADOW)


def paragraph(key=b"k" * 20, value=b"v" * 6, lines=1):
    # Construct emission order, independently of the implementation's target shift.
    prefix = bytearray(48)
    prefix += struct.pack("<6I", 0x01001000, 8, 0, 0, 0, 0)
    prefix += struct.pack("<I", 2) + bytes(16) + struct.pack("<I", 1)
    for content in (key, value):
        prefix += struct.pack("<I", len(content)) + content
    prefix += bytes(8)  # Empty additional map.
    prefix += bytes(4 + 8 + 4 + 4 + 24)
    p = len(prefix)
    prefix += struct.pack("<I", 4) + bytes(48)
    prefix += struct.pack("<I", lines)
    for _ in range(lines):
        prefix += struct.pack("<I", 4) + bytes(64)
    prefix += struct.pack("<I", 3)
    data = make_run(start=len(prefix))
    data[:len(prefix)] = prefix
    return data, p, len(prefix)


@pytest.mark.parametrize("lines", [0, 1, 2, 3])
def test_order_derived_current_parent_and_first_record(lines):
    payload, p, first = paragraph(lines=lines)
    result = SHADOW.derive_preslot(payload)
    assert result["p_origin"] == p == 182
    assert result["first_attrchar"] == first == p + 60 + 68 * lines
    assert result["line_count"] == lines
    candidate = SHADOW.extract_text_slot_candidate([bytes(payload)])
    assert SHADOW.compare_alignment(result, candidate) == "exact_match"
    fields = SHADOW.field_evidence(payload, result)
    assert set(fields) == ({"A", "length", "B"} if lines else {"A"})
    assert fields["A"]["c_relative"] == 214


@pytest.mark.parametrize("version", [0, 1, 3, 5, 0x7fffffff, 0xffffffff])
@pytest.mark.parametrize("serializer", ["AttrPara", "AttrLine"])
def test_parent_versions_fail_closed_before_current_width(serializer, version):
    payload, p, _ = paragraph(lines=2)
    offset = p if serializer == "AttrPara" else p + 56 + 68
    payload[offset:offset + 4] = struct.pack("<I", version)
    result = SHADOW.derive_preslot(payload)
    assert result["status"] == "unsupported_parent_version"
    assert result["p_origin"] is None and result["first_attrchar"] is None
    assert SHADOW.field_evidence(payload, result) == {}
    assert result["trace"][-1]["start"] == offset


@pytest.mark.parametrize("offset,version", [(52, 7), (52, 9), (72, 1), (72, 3)])
def test_base_versions_are_structural_requirements(offset, version):
    payload, _, _ = paragraph()
    payload[offset:offset + 4] = struct.pack("<I", version)
    assert SHADOW.derive_preslot(payload)["status"] == "unsupported_parent_version"


def test_all_prefix_truncations_fail_closed():
    payload, _, first = paragraph(lines=2)
    for end in range(first):
        result = SHADOW.derive_preslot(payload[:end])
        assert result["status"] == "truncated", end
        assert result["p_origin"] is None and result["first_attrchar"] is None
    assert SHADOW.derive_preslot(payload[:first])["first_attrchar"] == first


@pytest.mark.parametrize("offset,width", [(92, 4), (96, 4), (234, 4)])
def test_impossible_count_or_string_length_is_bounded(offset, width):
    payload, _, _ = paragraph()
    payload[offset:offset + width] = b"\xff" * width
    assert SHADOW.derive_preslot(payload)["status"] == "truncated"


@pytest.mark.parametrize("flags", [0, 0x01001010, 0x01001011, 0x01001100, 0x01001101])
def test_unknown_or_ambiguous_optional_base_state_abstains(flags):
    payload, _, _ = paragraph()
    payload[48:52] = struct.pack("<I", flags)
    result = SHADOW.derive_preslot(payload)
    assert result["status"] == "unresolved" and result["p_origin"] is None


def test_nonempty_additional_map_abstains():
    payload, _, _ = paragraph()
    payload[130:138] = struct.pack("<Q", 1)
    assert SHADOW.derive_preslot(payload)["status"] == "unresolved"


@pytest.mark.parametrize("length,expected", [(5, 181), (7, 183), (37, 213)])
def test_shift_is_not_forced_and_positions_follow_variable_lengths(length, expected):
    payload, p, first = paragraph(value=b"?" * length)
    result = SHADOW.derive_preslot(payload)
    assert result["p_origin"] == p == expected
    assert result["first_attrchar"] == first
    fields = SHADOW.field_evidence(payload, result)
    assert [fields[name]["c_relative"] for name in ("A", "length", "B")] == [p + n for n in (32, 80, 104)]
    assert SHADOW.compare_alignment(result, SHADOW.extract_text_slot_candidate([bytes(payload)])) == "exact_match"


def test_comparison_cannot_feed_back_into_derivation():
    payload, _, first = paragraph()
    result = SHADOW.derive_preslot(payload)
    assert SHADOW.compare_alignment(result, None) == "insufficient_context"
    for fake in ({"first_prefix_relative_offset": first + 1, "slots": [0] * 3},
                 {"first_prefix_relative_offset": first, "slots": [0] * 4}):
        assert SHADOW.compare_alignment(result, fake) == "mismatch"
    assert SHADOW.derive_preslot(payload) == result


def test_values_do_not_select_layout_or_field_identity():
    payload, p, _ = paragraph()
    before = SHADOW.derive_preslot(payload)
    for offset, value in zip((32, 80, 104), (float("nan"), -0.06, float("inf")), strict=True):
        payload[p + offset:p + offset + 8] = struct.pack("<d", value)
    after = SHADOW.derive_preslot(payload)
    assert after == before
    fields = SHADOW.field_evidence(payload, after)
    assert fields["A"]["value"] == "nan" and fields["B"]["value"] == "inf"
    assert fields["length"]["value"] == -0.06
    json.dumps(fields, allow_nan=False)


def recognized_rows(raw):
    parser = SHADOW.Type3ChainParser()
    _, _, base = parser._read_top_level_header(raw)
    return [(base + n.payload_offset, SHADOW.derive_preslot(n.payload))
            for n in parser._extract_nodes(raw[base:]) if n.header.class_name == "CParagraphe"]


def test_enclosing_offset_and_multiple_nodes_independent():
    descriptor = bytes.fromhex("ffff06000b00") + b"CParagraphe"
    one, _, _ = paragraph()
    two, _, _ = paragraph(value=b"v" * 7, lines=2)
    expected = [SHADOW.derive_preslot(one), SHADOW.derive_preslot(two)]
    header = bytes.fromhex("010000004172")  # Existing top-level heuristic keeps base zero.
    for offset in (0, 27, 4096):
        raw = header + b"\xcc" * offset + descriptor + one + descriptor + two
        rows = recognized_rows(raw)
        assert [r for _, r in rows] == expected
        assert rows[0][0] == len(header) + offset + len(descriptor)
        assert rows[1][0] == len(header) + offset + 2 * len(descriptor) + len(one)
    reversed_rows = recognized_rows(header + descriptor + two + descriptor + one)
    assert [r for _, r in reversed_rows] == expected[::-1]


def test_corpus_report_and_production_output_preservation():
    paths = sorted((ROOT / "tests/samples").rglob("*.txt"))
    before = {}
    raw_sources = {}
    for path in paths:
        content = path.read_bytes()
        try:
            raw = hex_text_to_bytes(content.decode("utf-8"))
        except (InvalidHexError, UnicodeDecodeError):
            continue
        obj, chain = parse_type3_clipboard_bytes_with_parser(raw)
        before[path] = (asdict(obj), chain)
        raw_sources[path] = (content, raw)
    report = SHADOW.build_report(paths)
    assert report["pre_slot_crosswalk_readiness"] == "broad_current_corpus_supported"
    assert (report["valid_captures"], report["text_captures"], report["paragraphs_examined"]) == (116, 84, 84)
    assert report["production_candidates"] == report["independently_derived_p"] == report["exact_182"] == 84
    assert report["shift_histogram"] == {182: 84} and not report["other_shifts"]
    assert report["comparison_counts"] == {state: 84 if state == "exact_match" else 0 for state in SHADOW.STATES}
    assert report["line_count_histogram"] == {1: 80, 2: 4}
    assert report["first_record_c_relative_histogram"] == {310: 80, 378: 4}
    assert report["field_c_relative_histograms"] == {"A": {214: 84}, "length": {262: 84}, "B": {286: 84}}
    assert report["ab_diagnostic"] == {"pairs": 84, "equal_raw": 84, "equal_numeric": 84}
    assert report["observed_versions"]["AttrLine version"] == {4: 88}
    # Reverse caller order; only report row order may change, not any structural result.
    again = SHADOW.build_report(list(reversed(paths)))
    def key(row):
        return row["capture"], row["c_absolute"]

    assert sorted(report["paragraphs"], key=key) == sorted(again["paragraphs"], key=key)
    for path, (content, raw) in raw_sources.items():
        obj, chain = parse_type3_clipboard_bytes_with_parser(raw)
        assert (asdict(obj), chain) == before[path]
        assert path.read_bytes() == content


def test_filename_is_reporting_only(tmp_path):
    source = ROOT / "tests/samples/text/text_slotstyle_a8_baseline.txt"
    renamed = tmp_path / "unrelated.txt"
    renamed.write_bytes(source.read_bytes())
    first = SHADOW.build_report([source])["paragraphs"]
    second = SHADOW.build_report([renamed])["paragraphs"]
    for rows in (first, second):
        for row in rows:
            row.pop("capture")
    assert first == second


def test_report_retains_other_shifts_and_unsupported_nodes(monkeypatch):
    descriptor = bytes.fromhex("ffff06000b00") + b"CParagraphe"
    short, _, _ = paragraph(value=b"v" * 5)
    long, _, _ = paragraph(value=b"v" * 7)
    bad, p, _ = paragraph()
    bad[p:p + 4] = struct.pack("<I", 3)
    raw = bytes.fromhex("010000004172") + descriptor + short + descriptor + long + descriptor + bad
    monkeypatch.setattr(Path, "read_bytes", lambda _: raw.hex().encode())
    report = SHADOW.build_report([Path("synthetic")])
    assert report["paragraphs_examined"] == report["production_candidates"] == 3
    assert report["shift_histogram"] == report["other_shifts"] == {181: 1, 183: 1}
    assert report["exact_182"] == 0
    assert report["comparison_counts"]["unsupported_parent_version"] == 1
    assert report["comparison_counts"]["exact_match"] == 2
    assert report["pre_slot_crosswalk_readiness"] == "partially_supported"
