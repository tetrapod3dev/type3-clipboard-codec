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
CLI = ROOT / "tools/analyze_text_slot_run_framing_semantics.py"


def run_cli(*args):
    result = subprocess.run([sys.executable, str(CLI), *args], cwd=ROOT,
                            env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
                            capture_output=True, timeout=30)
    assert result.returncode == 0, result.stderr.decode()
    return result.stdout


@pytest.fixture(scope="module")
def analyzer():
    spec = importlib.util.spec_from_file_location("framing_semantics_test", CLI)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def report():
    raw = run_cli("--json")
    assert len(raw) < 100000
    return json.loads(raw)


def paragraphs(report):
    return [p for f in report["fixture_results"] for p in f["structural"]["paragraphs"]]


def runs(report):
    return [r for p in paragraphs(report) for r in p["prefix_family_runs"]]


def structural(report):
    return {k: v for k, v in report.items() if k != "oracle_summary"}


def test_modes_policy_and_coverage(report, analyzer):
    assert len(run_cli()) < 50000 and len(run_cli("--markdown")) < 50000
    assert {f["fixture"] for f in report["fixture_results"]} == set(analyzer.FIXTURES)
    assert len(runs(report)) == 24 and sum(r["total_slot_count"] for r in runs(report)) == 207
    assert report["policy"] == analyzer.POLICY
    assert not report["limits"]["whole_payload_scan"]
    assert all(not r["slot_rows"] and not r["count_view_rows"] for r in runs(report))


def test_details_bounded_before_row_construction(report):
    raw = run_cli("--json", "--details")
    assert len(raw) < 100000 and len(run_cli("--details")) < 50000
    details = json.loads(raw)
    detailed = [r for r in runs(details) if r["slot_rows"]]
    assert len(detailed) == 3
    assert all(len(r["slot_rows"]) <= 5 and len(r["count_view_rows"]) <= 8 for r in detailed)
    for a, b in zip(runs(report), runs(details)):
        assert {k: v for k, v in a.items() if k not in ("slot_rows", "count_view_rows")} == {k: v for k, v in b.items() if k not in ("slot_rows", "count_view_rows")}


def test_no_oracle_equality(report):
    assert structural(report) == structural(json.loads(run_cli("--json", "--no-oracle")))


def test_complete_freeze_and_adversarial_oracle(analyzer, monkeypatch):
    before = analyzer.build_report(oracle_enabled=False)
    original = analyzer.oracle_phase
    snapshots = []

    def phase(frozen, enabled):
        assert isinstance(frozen, str)
        snapshots.append(json.loads(frozen))
        return original(frozen, enabled)

    def wrong(_):
        assert snapshots and len(snapshots[0]["evidence"]) == 24
        return {"texts": ["incorrect expected text"], "grouping": "fabricated", "cohort": "fabricated"}

    monkeypatch.setattr(analyzer, "oracle_phase", phase)
    monkeypatch.setattr(analyzer, "load_oracle", wrong)
    after = analyzer.build_report()
    assert structural(before) == structural(after)
    assert all(after[k] == v for k, v in snapshots[0]["structural"].items())
    assert all(not d["ordinal_text_match"] for f in after["oracle_summary"]["fixtures"] for d in f["diagnostics"])
    monkeypatch.setattr(analyzer, "load_oracle", lambda _: pytest.fail("oracle loaded when disabled"))
    analyzer.build_report(oracle_enabled=False)


def test_count_hypotheses_and_width(report):
    h = report["count_hypothesis_summary"]
    assert [h[k] for k in ("C1", "C2", "C3", "C4")] == [0, 24, 0, 0]
    field = report["count_field_summary"]
    assert field["best_candidate_offset"] == -4
    assert [(v["offset"], v["width"]) for v in field["best_candidate_views"]] == [(-4, 1), (-4, 2), (-4, 4)]
    assert field["observed_changed_byte_positions_in_minus4_view"] == [-4]
    assert field["observed_stable_byte_positions_in_minus4_view"] == [-3, -2, -1]
    assert field["typed_start"] is None and field["typed_width"] is None
    assert field["status"] == "ambiguous_width"
    for r in runs(report):
        assert len(r["count_window_hex"]) == 32
        assert r["count_probe"]["u32le"] == r["total_slot_count"] == r["nonterminal_count"]+1
        assert r["terminal_index"] == r["total_slot_count"]-1


def test_variants_and_family_are_frozen_before_labels(report):
    variants = report["prefix_variant_summary"]["variants"]
    assert [v["fixture_count"] for v in variants] == [22, 1, 1]
    assert all(v["first_slot_difference_count"] == 0 for v in variants)
    family = report["prefix_family_summary"]
    assert len(family["invariant_core"]) == 20
    assert family["variant_positions"] == [8, 12, 13, 14, 15, 16, 17, 18]
    assert len(family["allowed_variant_vectors"]) == 3
    assert all(str(i) not in family["invariant_core"] for i in (4, 5, 6, 7, 80, 81, 82))
    assert family["normalized_color_context_classes"] == 1
    labels = report["oracle_summary"]["variant_labels"]
    assert labels[1]["cohort_distribution"] == {"height": 1}
    assert labels[2]["cohort_distribution"] == {"multi_object": 1}
    assert labels[1]["diagnostic_text_distribution"] == labels[2]["diagnostic_text_distribution"] == {"abcdefg": 1}


def test_independent_detector_evidence_retains_rejected_candidate(report):
    summary = report["detector_agreement_summary"]
    assert summary["fixture_paragraph_status_counts"] == {"both_agree": 24}
    assert summary["candidate_evidence_relations"] == {"both_agree": 24, "neither": 24}
    assert summary["disagreement_count"] == summary["candidate_disagreement_count"] == 0
    assert all(len(p["candidate_evidence"]) == 2 for p in paragraphs(report))


def test_multiline_and_normalized_offsets(report):
    multiline = report["multiline_summary"]["code_13_runs"]
    assert len(multiline) == 4
    assert all(r["count_offset"] == -4 and r["total_slots"] == 10 and r["nonterminal_slots"] == 9 for r in multiline)
    assert all(r["code_13_count"] == 1 and r["terminal_included"] for r in multiline)
    for r in runs(report):
        assert r["slot_code_offset"] == 4 and r["typed_slot_code_width"] is None
        assert r["color_offset"] == 80 and r["typed_color_width"] is None
        assert r["terminal_color_matches_previous"]


def test_rfc_readiness_is_scoped_and_not_model_authorization(report):
    assert report["answers"]["candidate_parser_rfc_readiness"] == "ready"
    assert all(report["prefix_family_summary"]["rfc_prerequisites"].values())
    assert not report["prefix_family_summary"]["parser_safe"]
    assert report["answers"]["candidate_parser_model_readiness"] == "not_ready"
    assert report["answers"]["color_ownership_readiness"] == "not_ready"
    single = json.loads(run_cli("--json", "--fixture", "default_text.txt", "--no-oracle"))
    assert single["answers"]["candidate_parser_rfc_readiness"] == "not_ready"


def test_parser_model_and_results_unchanged(analyzer):
    from type3_clipboard_codec import parse_type3_clipboard_bytes_with_parser

    paths = sorted((ROOT / "src").rglob("*.py"))
    hashes = {p: hashlib.sha256(p.read_bytes()).digest() for p in paths}
    blob = analyzer.base.hex_text_to_bytes((analyzer.TEXT_DIR / "default_text.txt").read_text())
    before = repr(parse_type3_clipboard_bytes_with_parser(blob))
    analyzer.build_report()
    assert repr(parse_type3_clipboard_bytes_with_parser(blob)) == before
    assert hashes == {p: hashlib.sha256(p.read_bytes()).digest() for p in paths}


def test_no_absolute_offset_or_filename_rule(analyzer, monkeypatch):
    from types import SimpleNamespace

    blob = analyzer.base.hex_text_to_bytes((analyzer.TEXT_DIR / "default_text.txt").read_text())
    parser = analyzer.base.Type3ChainParser()
    _, _, origin = parser._read_top_level_header(blob)
    node = next(n for n in parser._extract_nodes(blob[origin:]) if n.header.class_name == "CParagraphe")
    before, evidence = analyzer.extract_structure(blob)
    fake = SimpleNamespace(payload=node.payload, header=node.header, start_offset=100, payload_offset=170)

    class Scanner:
        def _read_top_level_header(self, _):
            return None, None, 11

        def _extract_nodes(self, _):
            return [fake]

    monkeypatch.setattr(analyzer.base, "Type3ChainParser", Scanner)
    moved, _ = analyzer.extract_structure(b"\0" * 400)
    a, b = before["paragraphs"][0], moved["paragraphs"][0]
    assert b["provenance"]["runtime_descriptor_start"] == 111
    assert b["provenance"]["class_payload_start"] == 181
    assert {k: v for k, v in a.items() if k != "provenance"} == {k: v for k, v in b.items() if k != "provenance"}
    one = analyzer.structural_report([("arbitrary", copy.deepcopy(before))], [("arbitrary", evidence)])
    two = analyzer.structural_report([("multiline_grouped", copy.deepcopy(before))], [("multiline_grouped", evidence)])
    assert one["answers"] == two["answers"]
    assert one["count_field_summary"] == two["count_field_summary"]


def test_limits(analyzer):
    with pytest.raises(ValueError, match="payload budget"):
        analyzer.extract_structure(b"\0" * 1048577)
    with pytest.raises(ValueError, match="fixture budget"):
        analyzer.build_report([str(i) for i in range(25)])
    with pytest.raises(ValueError, match="inside text samples"):
        analyzer.build_report(["../outside.txt"])
