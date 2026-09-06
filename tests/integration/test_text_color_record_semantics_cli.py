from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
CLI = ROOT / "tools/analyze_text_color_record_semantics.py"


def run_cli(*args):
    proc = subprocess.run([sys.executable, str(CLI), *args], cwd=ROOT,
                          env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
                          capture_output=True, timeout=30)
    assert proc.returncode == 0, proc.stderr.decode()
    return proc.stdout


@pytest.fixture(scope="module")
def analyzer():
    spec = importlib.util.spec_from_file_location("semantics_test", CLI)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def report():
    raw = run_cli("--json")
    assert len(raw) < 180000
    return json.loads(raw)


def test_bounded_modes_coverage_policy(report, analyzer):
    assert len(run_cli()) < 50000
    assert len(run_cli("--markdown")) < 50000
    assert {r["fixture"] for r in report["fixture_results"]} == set(analyzer.FIXTURES)
    assert report["policy"] == analyzer.POLICY
    assert not report["warnings"]
    assert not report["limits"]["whole_record_comparison"]
    for f in report["fixture_results"]:
        for p in f["structural"]["paragraphs"]:
            assert len(p["chunks"]) <= 24
            assert all(len(c["local_signature"]) == 98 for c in p["chunks"])


def test_oracle_disabled_identical_structure(report):
    without = json.loads(run_cli("--json", "--no-oracle"))
    expected = copy.deepcopy(report)
    del expected["oracle_summary"]
    del without["oracle_summary"]
    assert expected == without


def test_freeze_before_oracle_and_adversarial_expected_colors(analyzer, monkeypatch):
    original = analyzer.oracle_phase
    snapshots = []

    def oracle(frozen, enabled):
        assert isinstance(frozen, str)
        snapshots.append(json.loads(frozen))
        return original(frozen, enabled)

    monkeypatch.setattr(analyzer, "oracle_phase", oracle)
    monkeypatch.setattr(analyzer.color, "load_oracle", lambda _: {"colors": ["fabricated"]})
    result = analyzer.build_report()
    assert all(result[k] == v for k, v in snapshots[0].items())
    monkeypatch.setattr(analyzer.color, "load_oracle", lambda _: pytest.fail("oracle loaded while disabled"))
    disabled = analyzer.build_report(oracle_enabled=False)
    assert result["fixture_results"] == disabled["fixture_results"]


def test_roles_ignore_names_and_color_bytes(analyzer):
    prepared = [(n, analyzer.extract_structure(analyzer.color.hex_text_to_bytes(
        (analyzer.TEXT_DIR / n).read_text(encoding="utf-8-sig")))) for n in analyzer.FIXTURES]
    before = analyzer.structural_report(copy.deepcopy(prepared))
    renamed = [(f"anonymous_{i}", copy.deepcopy(s)) for i, (_, s) in enumerate(prepared)]
    after = analyzer.structural_report(renamed)
    assert [r["structural"] for r in before["fixture_results"]] == [r["structural"] for r in after["fixture_results"]]
    # Change raw palette bytes before extraction; masked contexts and roles must survive.
    name = analyzer.FIXTURES[0]
    blob = bytearray(analyzer.color.hex_text_to_bytes((analyzer.TEXT_DIR / name).read_text()))
    p = prepared[0][1]["paragraphs"][0]
    for c in p["chunks"]:
        pos = p["descriptor_provenance"]["class_payload_start"] + c["payload_relative_start"] + 0x8B
        blob[pos:pos+3] = b"\x12\x34\x56"
    mutated = analyzer.structural_report([("arbitrary", analyzer.extract_structure(bytes(blob)))])
    original = analyzer.structural_report([prepared[0]])
    assert [c["role"] for c in mutated["fixture_results"][0]["structural"]["paragraphs"][0]["chunks"]] == [c["role"] for c in original["fixture_results"][0]["structural"]["paragraphs"][0]["chunks"]]


def test_character_slots_and_multiline_abstention(report):
    h = report["character_count_hypothesis"]
    assert h["supported_fixture_count"] == 22
    assert h["unresolved_fixtures"] == ["text_multiline_basic.txt"]
    assert all(r["delta"] == 1 and r["slot_grid_match"] for r in h["fixtures"] if r["delta"] is not None)
    multi = next(r for r in h["fixtures"] if r["fixture"] == "text_multiline_basic.txt")
    assert multi["visible_text"] == ["abcd\nefgh"] and multi["slot_count"] == 10
    assert multi["repeated_candidate_count"] is None
    assert report["text_run_hypothesis"]["slot_grid_match_count"] == 22
    assert report["geometry_count_hypothesis"]["single_chain_repeated_counts"] == [8, 9, 10, 11]


def test_style_homogeneity_header_terminal_and_width(report):
    assert report["style_independence_summary"]["supported_in_bounded_windows"]
    assert report["repeated_record_structure_summary"]["homogeneous_in_bounded_window"]
    rows = report["header_terminal_summary"]["fixtures"]
    assert all(r["header_distinct"] and r["terminal_distinct"] for r in rows)
    assert {r["header_count_probe_at_5"] for r in rows} == {8}
    assert not all(r["header_count_probe_equals_slot_count"] for r in rows)
    pairs = report["style_independence_summary"]["pairs"]
    primary = {"default_text.txt", "text_color_army_green.txt", "text_color_navy_blue.txt"}
    assert all(p["terminal_window_invariant"] for p in pairs if set(p["fixtures"]) <= primary)
    answer = report["answers"]
    assert answer["observed_color_byte_start"] == 0x8B and answer["observed_changed_width"] == 3
    assert answer["typed_field_width"] is None and answer["typed_field_start"] == "unresolved"
    assert answer["field_decode_readiness"] == answer["color_ownership_readiness"] == "not_ready"


def test_parser_sources_and_results_unchanged(analyzer):
    paths = sorted((ROOT / "src").rglob("*.py"))
    before = {p: hashlib.sha256(p.read_bytes()).digest() for p in paths}
    blob = analyzer.color.hex_text_to_bytes((analyzer.TEXT_DIR / analyzer.FIXTURES[0]).read_text())
    parsed_before = repr(analyzer.parse_type3_clipboard_bytes_with_parser(blob))
    analyzer.build_report(oracle_enabled=False)
    assert parsed_before == repr(analyzer.parse_type3_clipboard_bytes_with_parser(blob))
    assert before == {p: hashlib.sha256(p.read_bytes()).digest() for p in paths}


def test_limits_and_unavailable_inputs(analyzer):
    with pytest.raises(ValueError, match="payload budget"):
        analyzer.extract_structure(b"\0" * 1048577)
    with pytest.raises(ValueError, match="fixture budget"):
        analyzer.build_report([str(i) for i in range(33)])
    with pytest.raises(ValueError, match="existing file"):
        analyzer.build_report(["../outside.txt"])
    empty = analyzer.structural_report([])
    assert empty["answers"]["repeated_record_best_interpretation"] == "unresolved"
