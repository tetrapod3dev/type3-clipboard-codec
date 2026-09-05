from __future__ import annotations

import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
CLI = ROOT / "tools" / "analyze_typeeditzone_mfc_archive.py"


def run_cli(*args):
    result = subprocess.run([sys.executable, str(CLI), *args], cwd=ROOT,
                            env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
                            capture_output=True, timeout=30)
    assert result.returncode == 0, result.stderr.decode()
    return result.stdout


@pytest.fixture(scope="module")
def analyzer():
    spec = importlib.util.spec_from_file_location("mfc_audit_integration", CLI)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def report():
    raw = run_cli("--json")
    assert len(raw) < 100000
    return json.loads(raw)


def test_default_text_and_markdown():
    for args in ((), ("--markdown",)):
        raw = run_cli(*args)
        assert len(raw) < 50000
        assert b"TypeEditZone MFC CArchive Compatibility Audit" in raw
        assert b"mfc_runtimeclass_framing_supported_but_writeobject_unclear" in raw
        assert b"not_ready" in raw
    assert b"| Class |" in run_cli("--markdown")


def test_default_coverage_policy(report, analyzer):
    assert report["policy"] == {
        "scope": "mfc_carchive_compatibility_audit_only", "parser_behavior": "not_modified",
        "decoder_behavior": "not_modified", "model_behavior": "not_modified",
        "architecture_change": "not_performed",
    }
    assert len(report["fixtures"]) == 8
    assert {f["fixture"] for f in report["fixtures"]} == set(analyzer.DEFAULT_FIXTURES)
    assert {f["category"] for f in report["fixtures"]} == {"text", "geometry"}
    assert report["warnings"] == []
    assert report["answers"]["parser_refactor_readiness"] == "not_ready"
    assert report["global_assessment"]["classification"] == "mfc_runtimeclass_framing_supported_but_writeobject_unclear"
    assert all(f["classification"] == "partial_mfc_runtimeclass_framing_match" for f in report["fixtures"])
    assert all(f["absolute_offset_role"] == "diagnostic_only" and not f["truncated"] for f in report["fixtures"])


def test_descriptor_lengths_schemas_and_exact_bytes(report, analyzer):
    expected = {"CZone": (8, 1), "CParagraphe": (3, 6), "CCourbe": (8, 1),
                "CContour": (8, 2), "CPropertyExtend": (8, 5)}
    rows = {r["class_name"]: r for r in report["class_descriptor_summary"]}
    for name, (count, schema) in expected.items():
        row = rows[name]
        assert row["occurrences"] == row["descriptor_match_count"] == count
        assert row["observed_schema_values"] == [schema]
        assert row["schema_stability"] == "stable_across_fixtures"
        assert row["length_match_rate"] == 1
    assert rows["CObDao"]["occurrences"] == 48
    assert rows["CObDao"]["descriptor_match_count"] == 0
    assert rows["CObDao"]["candidate_schema_values_all_hits"] == [6]
    assert rows["CObDao"]["observed_schema_values"] == []  # candidate bytes are not class schema evidence
    assert not report["schema_summary"]["schemas_unique_to_each_class"]
    for fixture in report["fixtures"]:
        data = analyzer.hex_text_to_bytes((analyzer.SAMPLES / fixture["fixture"]).read_text())
        for hit in fixture["class_hits"]:
            pos = hit["ascii_hit_payload_offset"]
            name = hit["class_name"].encode("ascii")
            assert data[pos:pos + len(name)] == name
            assert hit["class_name_length"] == len(name)
            assert hit["exact_length_match"] == (int.from_bytes(data[pos-2:pos], "little") == len(name))
            assert analyzer.descriptor_hit(data, hit["class_name"], pos, fixture["fixture"]) == hit
        assert fixture["summary"]["runtimeclass_store_matches_without_tag"] == 0
        assert fixture["summary"]["length_only_matches"] == 0


def test_pid_desync_and_scanner_relationship(report):
    assert report["tag_summary"]["structurally_supported_newclass_candidates"] == 35
    for key in ("confirmed_old_class_references", "confirmed_null_tags", "confirmed_extended_tags", "confirmed_object_references"):
        assert report["tag_summary"][key] == 0
    assert report["pid_context_summary"]["coherent_full_contexts"] == 0
    assert report["pid_context_summary"]["desynchronized_paths"] == 16
    assert report["pid_context_summary"]["verified_restarts"] == 0
    assert report["scanner_relationship_summary"]["descriptor_start_matches"] == 35
    assert report["scanner_relationship_summary"]["ascii_start_matches"] == 0
    assert not report["scanner_relationship_summary"]["independent_fingerprint"]
    for fixture in report["fixtures"]:
        context = fixture["pid_context"]
        assert context["repeated_exact_descriptors"] == {}
        assert set(context["repeated_ascii_names"]) == {"CObDao"}
        seeded = context["paths"][-1]
        assert seeded["next_pid"] == 3 and seeded["known_class_descriptors"] == {"1": "CZone"}
        assert seeded["class_only_alternative_next_pid"] == 2
        assert seeded["stop_reason"] == "unknown_class_Serialize_extent"
        assert all(not p["resynchronization_attempted"] for p in context["paths"])
        for node in fixture["scanner_relationship"]["nodes"]:
            assert node["scanner_header_location"] == node["descriptor_start"] == node["class_name_start"] - 6
            assert node["mfc_descriptor_match"]


def test_selection_limits_missing_and_determinism(report):
    assert json.loads(run_cli("--json")) == report
    selected = json.loads(run_cli("--json", "--fixture", "default_text.txt",
                                 "--fixture", "default_rectangle.txt", "--max-fixtures", "2"))
    assert len(selected["fixtures"]) == 2
    limited = json.loads(run_cli("--json", "--max-fixtures", "1", "--max-class-hits", "2", "--context-bytes", "0"))
    assert limited["warnings"]
    assert len(limited["fixtures"][0]["class_hits"]) == 2
    assert limited["fixtures"][0]["truncated"]
    assert all(h["context_before_hex"] == h["context_after_hex"] == "" for h in limited["fixtures"][0]["class_hits"])
    missing = json.loads(run_cli("--json", "--fixture", "missing_fixture.txt"))
    assert not missing["fixtures"] and missing["warnings"]
    assert missing["global_assessment"]["classification"] == "evidence_insufficient"


def test_extended_context_output_budget_preserves_counts(report):
    raw = run_cli("--json", "--context-bytes", "64")
    assert len(raw) < 100000
    extended = json.loads(raw)
    assert extended["class_descriptor_summary"] == report["class_descriptor_summary"]
    assert extended["global_assessment"] == report["global_assessment"]


def test_parser_decoder_models_unchanged_and_active_objects_identical(analyzer):
    from type3_clipboard_codec import parse_type3_clipboard_bytes_with_parser

    sources = {p: p.read_bytes() for p in (ROOT / "src").rglob("*.py")}
    for name in analyzer.DEFAULT_FIXTURES:
        data = analyzer.hex_text_to_bytes((analyzer.SAMPLES / name).read_text())
        parsed, _ = parse_type3_clipboard_bytes_with_parser(data)
        snapshot = copy.deepcopy(parsed)
        analyzer.analyze_bytes(data, name)
        again, _ = parse_type3_clipboard_bytes_with_parser(data)
        assert parsed == snapshot == again
        assert all(c["matched_chain"] is None for c in parsed.candidate_fields.get("cproperty_anchor_candidates", []))
    assert all(p.read_bytes() == original for p, original in sources.items())


def test_raw_audit_does_not_consult_scanner(analyzer, monkeypatch):
    from type3_clipboard_codec.parsers.type3_chain_parser import Type3ChainParser

    data = analyzer.hex_text_to_bytes((analyzer.SAMPLES / analyzer.DEFAULT_FIXTURES[0]).read_text())
    before = analyzer.audit_ascii(data)
    monkeypatch.setattr(Type3ChainParser, "_extract_nodes", lambda *_: pytest.fail("Phase A called scanner"))
    assert analyzer.audit_ascii(data) == before
