"""Archive evidence is additive analyzer metadata, never a parser permission."""
import hashlib
import importlib.util
import inspect
import shutil
from contextlib import nullcontext
from dataclasses import asdict
from pathlib import Path

import pytest

from tests.text_slot_v1_replay import replay_parser
from type3_clipboard_codec import parse_type3_clipboard_bytes_with_parser
from type3_clipboard_codec.inspect.hex_input import hex_text_to_bytes
from type3_clipboard_codec.parsers.text.text_slot_candidate import extract_text_slot_candidate

ROOT = Path(__file__).resolve().parents[2]
STYLE_NAMES = (
    "text_slotstyle_a8_baseline.txt", "text_slotstyle_a8_char4_height20.txt",
    "text_slotstyle_a8_char4_width50.txt", "text_slotstyle_a8_char4_width150.txt",
    "text_slotstyle_a8_char4_slant_p15.txt", "text_slotstyle_a8_char4_slant_m15.txt",
    "text_slotstyle_a8_char4_rotation_p15.txt", "text_slotstyle_a8_char4_rotation_m15.txt",
    "text_slotstyle_a8_char4_navy.txt",
)
ADDITIVE_KEYS = {"archive_type_evidence", "archive_type_provenance"}


@pytest.fixture(scope="module")
def modules():
    loaded = []
    for name in ("analyze_text_slot_style_fields", "analyze_text_slot_spacing_fields",
                 "analyze_text_maximum_length", "analyze_text_maximum_length_numeric"):
        spec = importlib.util.spec_from_file_location("archive_evidence_" + name, ROOT / "tools" / (name + ".py"))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        loaded.append(module)
    return loaded


def without_evidence(value):
    if isinstance(value, dict):
        return {k: without_evidence(v) for k, v in value.items() if k not in ADDITIVE_KEYS}
    if isinstance(value, list):
        return [without_evidence(v) for v in value]
    return value


@pytest.mark.parametrize("field,start,member,write", [
    ("height", 12, "0x10", "0x4d7f1"),
    ("width", 20, "0x18", "0x4d7fe"),
    ("slant", 28, "0x20", "0x4d80b"),
    ("spacing", 64, "0x30", "0x4d84c"),
    ("rotation", 72, "0x38", "0x4d859"),
])
def test_five_code_evidence_fields(modules, field, start, member, write):
    metadata = modules[0].archive_type_metadata(field)
    assert metadata["archive_type_evidence"] == "confirmed_archive_double"
    source = metadata["archive_type_provenance"]
    assert source["code_record_relative_range"] == [start, start + 8]
    assert source["source_member_offset"] == member
    assert source["write_rva"] == write
    assert source["archive_width_bytes"] == 8
    assert source["runtime_layout_applicability"] == "not_established_by_this_metadata"
    assert source["semantic_ownership"] == "unchanged"
    assert "typed_width" not in metadata


@pytest.mark.parametrize("kind,enabled,ratio", [
    ("style", True, False), ("style", False, False),
    ("spacing", True, False), ("spacing", False, False),
    ("spacing", True, True), ("spacing", False, True),
])
def test_complete_old_report_unchanged_after_removing_additions(modules, monkeypatch, kind, enabled, ratio):
    style, spacing, _, _ = modules
    if kind == "style":
        def build():
            return style.build_report(paths=[style.TEXT_DIR / name for name in STYLE_NAMES], oracle_enabled=enabled)
        owner = style
        context = replay_parser()
        keys = [name + "_candidate_summary" for name in ("height", "width", "slant", "rotation")]
    else:
        def build():
            return spacing.build_report(oracle_enabled=enabled, spacing_ratio=ratio)
        owner = spacing.prior
        context = nullcontext()
        keys = ["spacing_encoding_summary"] + (["spacing_ratio_summary"] if ratio else [])
    with context:
        # Disabling the append-only provider restores the pre-batch report shape.
        with monkeypatch.context() as patch:
            patch.setattr(owner, "archive_type_metadata", lambda field: {})
            before = build()
        after = build()
    assert without_evidence(after) == before
    for key in keys:
        assert list(after[key]) == list(before[key]) + ["archive_type_evidence", "archive_type_provenance"]
        assert after[key]["archive_type_evidence"] == "confirmed_archive_double"
        assert after[key]["typed_width"] is None


def runtime_snapshot(names):
    result = {}
    for name in sorted(names):
        raw = hex_text_to_bytes((ROOT / "tests/samples/text" / name).read_text(encoding="utf-8"))
        obj, parser = parse_type3_clipboard_bytes_with_parser(raw)
        assert obj.raw_data == raw
        result[name] = {"parser": parser, "object": asdict(obj)}
    return result


def test_runtime_raw_chains_and_rgb_unchanged(modules):
    style, spacing, maximum, _ = modules
    names = set(STYLE_NAMES) | set(spacing.FIXTURES) | set(maximum.FIXTURES)
    paths = [ROOT / "tests/samples/text" / name for name in names]
    hashes = {p: hashlib.sha256(p.read_bytes()).digest() for p in paths}
    before = runtime_snapshot(names)
    with replay_parser():
        style.build_report(paths=[style.TEXT_DIR / name for name in STYLE_NAMES])
    spacing.build_report(spacing_ratio=True)
    after = runtime_snapshot(names)
    assert after == before  # Includes parser, chain order, unknown/raw bytes and every candidate value.
    for item in after.values():
        candidate = item["object"]["candidate_fields"].get("text_slot_run")
        if candidate:
            assert candidate["parser_safe"] is False
            assert candidate["ownership"] == "unresolved" and candidate["matched_chain"] is None
            for slot in candidate["slots"]:
                rgb = slot["rgb_bytes_candidate"]
                assert len(rgb["raw_bytes"]) == 3
                assert rgb["typed_width"] is None
                assert not ADDITIVE_KEYS.intersection(rgb)
                assert "archive_container_width" not in rgb  # No fourth channel or runtime container addition.
    assert {p: hashlib.sha256(p.read_bytes()).digest() for p in paths} == hashes


def test_f4_stride_and_unknown_extension_behavior_unchanged(modules):
    spacing = modules[1]
    raw = hex_text_to_bytes((spacing.TEXT / spacing.BASELINE).read_text(encoding="utf-8"))
    obj, _ = parse_type3_clipboard_bytes_with_parser(raw)
    candidate = obj.candidate_fields["text_slot_run"]
    span = candidate["payload_span"]
    payload = raw[span["start"]:span["start"] + span["length"]]
    first = candidate["first_prefix_relative_offset"]
    original = extract_text_slot_candidate([payload])
    assert original["stride"] == 204 and original["prefix_family"] == "F4"
    assert original["parser_safe"] is False
    changed = bytearray(payload)
    changed[first + 0x24] ^= 1
    assert extract_text_slot_candidate([bytes(changed)]) is None
    # The old recognizer still does not validate empty-extension state.
    changed = bytearray(payload)
    changed[first + 92 + 40] ^= 1
    assert extract_text_slot_candidate([bytes(changed)]) == original
    spacing.build_report()
    assert extract_text_slot_candidate([payload]) == original


def test_maximum_and_scalar_reports_do_not_consume_new_evidence(modules, monkeypatch):
    _, spacing, maximum, numeric = modules
    before_max, before_numeric = maximum.build_report(), numeric.build_report()
    with monkeypatch.context() as patch:
        patch.setattr(spacing.prior, "archive_type_metadata", lambda field: pytest.fail("Unexpected dependency"))
        assert maximum.build_report() == before_max
        assert numeric.build_report() == before_numeric
    assert before_max["answers"]["maximum_length_field_readiness"] == "strong_object_setting_candidate"
    assert before_numeric["answers"]["typed_width"] is None
    assert before_numeric["answers"]["ownership_status"] == "unresolved"
    assert before_numeric["structural"]["duplicated_scalars"]["byte_identical"] is True


def test_metadata_is_independent_of_capture_names_and_oracle(modules, tmp_path):
    style, spacing, _, _ = modules
    original = spacing.build_report(oracle_enabled=False, spacing_ratio=True)
    renamed = []
    for index, name in enumerate(spacing.FIXTURES):
        path = tmp_path / f"renamed_{index}.txt"
        shutil.copyfile(spacing.TEXT / name, path)
        renamed.append(path)
    other = spacing.build_report(paths=renamed, baseline=renamed[0].name,
                                 oracle_enabled=False, spacing_ratio=True)
    for key in ("spacing_encoding_summary", "spacing_ratio_summary"):
        for addition in ADDITIVE_KEYS:
            assert other[key][addition] == original[key][addition]
    assert list(inspect.signature(style.archive_type_metadata).parameters) == ["field"]
    with pytest.raises(KeyError):
        style.archive_type_metadata("some_fixture_name.txt")


def test_metadata_returns_independent_values(modules):
    style = modules[0]
    first = style.archive_type_metadata("height")
    first["archive_type_provenance"]["code_record_relative_range"][0] = -1
    assert style.archive_type_metadata("height")["archive_type_provenance"]["code_record_relative_range"] == [12, 20]
