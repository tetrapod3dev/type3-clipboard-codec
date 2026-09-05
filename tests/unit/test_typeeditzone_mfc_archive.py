from __future__ import annotations

import importlib.util
from pathlib import Path
import struct

import pytest


@pytest.fixture(scope="module")
def audit():
    path = Path(__file__).resolve().parents[2] / "tools" / "analyze_typeeditzone_mfc_archive.py"
    spec = importlib.util.spec_from_file_location("mfc_audit_unit", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def descriptor(name="CParagraphe", schema=1, length=None):
    raw = name.encode("ascii")
    return struct.pack("<HHH", 0xFFFF, schema, len(raw) if length is None else length) + raw


@pytest.mark.parametrize("schema", [0, 1, 2, 6, 256, 0x7FFE])
def test_positive_synthetic_exact_descriptor(audit, schema):
    raw = descriptor(schema=schema)
    assert len(b"CParagraphe") == 11
    hit = audit.audit_ascii(raw)["class_hits"][0]
    assert hit["descriptor_pattern_match"] and hit["plausible_schema"]
    assert hit["candidate_schema_word"] == schema
    assert hit["candidate_name_length_word"] == 0x0B
    assert not hit["runtimeclass_store_pattern_without_newclass_tag"]


def test_wrong_length(audit):
    hit = audit.audit_ascii(descriptor(length=0x0A))["class_hits"][0]
    assert hit["new_class_tag_match"]
    assert not hit["exact_length_match"] and not hit["descriptor_pattern_match"]


def test_missing_new_class_tag_and_length_only(audit):
    raw = struct.pack("<HH", 1, 11) + b"CParagraphe"
    hit = audit.audit_ascii(raw)["class_hits"][0]
    assert hit["runtimeclass_store_pattern_without_newclass_tag"]
    assert not hit["descriptor_pattern_match"]
    short = audit.audit_ascii(struct.pack("<H", 11) + b"CParagraphe")["class_hits"][0]
    assert short["length_prefixed_ascii_class_candidate"]
    assert not short["runtimeclass_store_pattern_without_newclass_tag"]
    assert short["candidate_schema_word"] is None


def test_coincidental_ffff_and_c_prefix_are_not_descriptors(audit):
    assert audit.audit_ascii(b"\xff\xff\x00\x12random data")["class_hits"] == []
    rows = audit.audit_ascii(b"\xff\xffjunkCParagraphe\x80\x01CObDao")["class_hits"]
    assert rows and all(not h["descriptor_pattern_match"] for h in rows)
    assert audit.fixture_assessment(rows) == "insufficient_evidence"
    single = audit.audit_ascii(descriptor())["class_hits"]
    assert audit.fixture_assessment(single) == "mfc_inspired_or_custom_serialization_possible"


def test_old_class_requires_prior_state_and_cursor(audit):
    data = struct.pack("<H", 0x8001)
    unresolved = audit.tag_candidate(data, 0)
    assert unresolved["candidate_role"] == "old_class_tag_candidate"
    assert unresolved["pid_candidate"] == 1
    assert not unresolved["reference_state_match"]
    assert not audit.tag_candidate(data, 0, {1: "CZone"})["reference_state_match"]
    assert audit.tag_candidate(data, 0, {1: "CZone"}, synchronized=True)["reference_state_match"]
    assert audit.shadow_context(data, [], 0)["status"] == "desynchronized"


def test_big_tag_not_unconditionally_confirmed(audit):
    data = struct.pack("<HI", 0x7FFF, 0x80008001)
    probe = audit.tag_candidate(data, 0)
    assert probe["candidate_role"] == "extended_tag_candidate" and probe["pid_candidate"] == 0x8001
    assert not probe["reference_state_match"]
    assert not audit.tag_candidate(data[:3], 0)["reference_state_match"]
    assert not audit.tag_candidate(b"\0\0", 0)["reference_state_match"]


def test_shadow_stops_before_later_matching_descriptor(audit):
    first = descriptor("CZone")
    data = first + b"opaque Serialize bytes" + descriptor("CContour", 2) + struct.pack("<H", 0x8001)
    hits = audit.audit_ascii(data)["class_hits"]
    assert len(hits) == 2
    state = audit.shadow_context(data, hits, 0)
    assert state["stop_offset"] == len(first)
    assert state["stop_reason"] == "unknown_class_Serialize_extent"
    assert state["known_class_descriptors"] == {1: "CZone"}
    assert state["next_pid"] == 3
    assert not state["resynchronization_attempted"]


def test_repeated_names_do_not_prove_context_restart(audit):
    raw = descriptor("CObDao") + b"opaque" + descriptor("CObDao")
    result = audit.analyze_bytes(raw)
    assert result["pid_context"]["repeated_exact_descriptors"] == {"CObDao": 2}
    assert result["pid_context"]["multiple_contexts"] == "unresolved"
    assert "alone do not prove restart" in result["pid_context"]["restart_evidence"]


def test_sentinel_schema_is_visible_but_not_plausible(audit):
    hit = audit.audit_ascii(descriptor(schema=0xFFFF))["class_hits"][0]
    assert hit["descriptor_pattern_match"]  # exact bytes and schema plausibility are distinct checks
    assert not hit["plausible_schema"]


def test_hit_limit_is_explicit_and_deterministic(audit):
    raw = descriptor("CZone") * 3
    result = audit.audit_ascii(raw, max_class_hits=2)
    assert len(result["class_hits"]) == 2 and result["truncated"]
    assert audit.audit_ascii(raw, max_class_hits=2) == result
