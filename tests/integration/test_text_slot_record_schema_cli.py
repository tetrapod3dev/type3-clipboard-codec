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
CLI = ROOT / "tools/analyze_text_slot_record_schema.py"


def run_cli(*args):
    result = subprocess.run([sys.executable, str(CLI), *args], cwd=ROOT,
                            env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
                            capture_output=True, timeout=30)
    assert result.returncode == 0, result.stderr.decode()
    return result.stdout


@pytest.fixture(scope="module")
def analyzer():
    spec = importlib.util.spec_from_file_location("slot_schema_test", CLI)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def report():
    raw = run_cli("--json")
    assert len(raw) < 100000
    return json.loads(raw)


def paragraphs(report):
    return [p for row in report["fixture_results"] for p in row["structural"]["paragraphs"]]


def without_oracle(report):
    return {k: v for k, v in report.items() if k != "oracle_summary"}


def test_compact_modes_coverage_and_policy(report, analyzer):
    assert {f["fixture"] for f in report["fixture_results"]} == set(analyzer.FIXTURES)
    assert len(report["fixture_results"]) == 21
    assert len(run_cli()) < 50000 and len(run_cli("--markdown")) < 50000
    assert report["policy"] == analyzer.POLICY
    assert not report["limits"]["whole_record_comparison"]
    assert all(not p["record_rows"] and not p["signature_examples"] for p in paragraphs(report))
    assert report["answers"]["candidate_parser_model_readiness"] == "not_ready"
    assert report["answers"]["color_ownership_readiness"] == "not_ready"


def test_details_bounded_before_row_construction(report):
    raw = run_cli("--json", "--details")
    assert len(raw) < 100000
    detail = json.loads(raw)
    assert len(run_cli("--details")) < 50000
    detailed = [p for p in paragraphs(detail) if p["record_rows"]]
    assert len(detailed) == 3
    assert all(len(p["record_rows"]) <= 4 and len(p["signature_examples"]) <= 2 for p in detailed)
    for row, original in zip(paragraphs(detail), paragraphs(report)):
        assert {k: v for k, v in row.items() if k not in ("record_rows", "signature_examples")} == {k: v for k, v in original.items() if k not in ("record_rows", "signature_examples")}


def test_no_oracle_identical_structure(report):
    assert without_oracle(report) == without_oracle(json.loads(run_cli("--json", "--no-oracle")))


def test_freeze_order_and_expected_text_never_selects_boundary(analyzer, monkeypatch):
    baseline = analyzer.build_report(oracle_enabled=False)
    original = analyzer.oracle_phase
    frozen_inputs = []

    def phase(frozen, enabled):
        assert isinstance(frozen, str)
        frozen_inputs.append(json.loads(frozen))
        return original(frozen, enabled)

    def expected(_):
        assert frozen_inputs, "expected text loaded before full structural freeze"
        return {"texts": ["wrong text", ""], "source": "adversarial"}

    monkeypatch.setattr(analyzer, "oracle_phase", phase)
    monkeypatch.setattr(analyzer, "load_text_oracle", expected)
    adversarial = analyzer.build_report()
    assert without_oracle(adversarial) == without_oracle(baseline)
    assert all(adversarial[k] == v for k, v in frozen_inputs[0].items())
    assert all(d["ordinal_code_match"] is False for r in adversarial["oracle_summary"]["fixtures"] for d in r["diagnostics"])
    monkeypatch.setattr(analyzer, "load_text_oracle", lambda _: pytest.fail("oracle read when disabled"))
    analyzer.build_report(oracle_enabled=False)


def test_boundary_competitors_and_prefix_count(report):
    for p in paragraphs(report):
        assert p["candidate_start"] == 47 and p["candidate_stride"] == 204
        assert not p["boundary_confirmed"]
        assert len(p["H2_shift_scores"]) == 17
        assert len(p["best_repetition_start_candidates"]) > 1
        evidence = p["prefix_evidence"]
        assert evidence["equals_enumerated_count"]
        assert evidence["nearby_stride_prefix_counts"][8] == evidence["prefix_count"]
        assert all(n == 1 for i, n in enumerate(evidence["nearby_stride_prefix_counts"]) if i != 8)
        assert p["stop_reason"] == "prefix_mismatch"
    assert report["answers"]["best_record_start"] is None
    assert report["answers"]["best_record_stride"] == 204
    assert report["boundary_hypothesis_summary"]["H3"]["status"] == "viable"
    assert report["boundary_hypothesis_summary"]["H4"]["status"] == "viable"


def test_slot_codes_zero_and_homogeneity(report):
    aligned = [p for p in paragraphs(report) if p["aligned_record_count"] is not None]
    assert len(aligned) == 20
    for p in aligned:
        assert p["slot_codes"]["candidate_record_relative_offset"] == 0x3F
        assert p["prefix_evidence"]["payload_relative_start"] == 310
        assert p["slot_codes"]["typed_code_width"] is None
        assert p["terminal"]["only_last_zero"] and p["terminal"]["count_equals_nonzero_plus_one"]
        assert p["terminal"]["interpretation"] == "zero_code_terminal_candidate"
        assert p["homogeneity"]["masked_signature_classes"] == 2
        assert p["homogeneity"]["color_local_masked_classes"] == 1
        assert p["homogeneity"]["first_differs_from_second"]
        assert p["terminal"]["local_signature_matches_previous"]
        assert p["terminal"]["color_matches_previous"]


def test_ascii_diagnostic_correspondence(report):
    oracle = {r["fixture"]: r for r in report["oracle_summary"]["fixtures"]}
    for name in ("default_text.txt", "text_ascii_lowercase.txt", "text_ascii_uppercase.txt",
                 "text_digits.txt", "text_alphanumeric.txt", "text_spaces.txt", "text_special_characters.txt"):
        diag = oracle[name]["diagnostics"][0]
        assert diag["ordinal_code_match"] and diag["n_plus_one"] and diag["final_zero"]
    assert oracle["text_spaces.txt"]["diagnostics"][0]["space_slot_count"] == 2


def test_multiline_not_forced_and_color_width_preserved(report):
    p = next(r for r in report["fixture_results"] if r["fixture"] == "text_multiline_basic.txt")["structural"]["paragraphs"][0]
    assert p["aligned_record_count"] is None and p["status"] == "alternate_layout_or_unresolved"
    assert p["prefix_evidence"]["payload_relative_start"] == 378
    assert p["alternate_layout"]["shift_from_single_line_prefix_lead"] == 68
    assert p["alternate_layout"]["slot_count"] == 10 and p["alternate_layout"]["code_13_ordinals"] == [5]
    assert not p["alternate_layout"]["single_line_schema_applied"]
    assert p["homogeneity"]["status"] == "unresolved"
    assert p["color"]["inside_all_aligned_records"] is None
    for p in paragraphs(report):
        assert p["color"]["observed_color_byte_start"] == 0x8B
        assert p["color"]["observed_changed_width"] == 3
        assert p["color"]["typed_color_field_width"] is None


def test_parser_model_sources_results_and_names_unchanged(analyzer):
    from type3_clipboard_codec import parse_type3_clipboard_bytes_with_parser

    paths = sorted((ROOT / "src").rglob("*.py"))
    before = {p: hashlib.sha256(p.read_bytes()).digest() for p in paths}
    blob = analyzer.prior.hex_text_to_bytes((analyzer.TEXT_DIR / "default_text.txt").read_text())
    parsed = repr(parse_type3_clipboard_bytes_with_parser(blob))
    structure = analyzer.extract_structure(blob)
    a = analyzer.structural_report([("default_text.txt", copy.deepcopy(structure))])
    b = analyzer.structural_report([("anonymous.txt", copy.deepcopy(structure))])
    assert a["fixture_results"][0]["structural"] == b["fixture_results"][0]["structural"]
    assert a["answers"] == b["answers"]
    analyzer.build_report()
    assert repr(parse_type3_clipboard_bytes_with_parser(blob)) == parsed
    assert before == {p: hashlib.sha256(p.read_bytes()).digest() for p in paths}


def test_payload_relative_rule_with_shifted_descriptor(analyzer, monkeypatch):
    from types import SimpleNamespace

    blob = analyzer.prior.hex_text_to_bytes((analyzer.TEXT_DIR / "default_text.txt").read_text())
    base = analyzer.extract_structure(blob)
    parser = analyzer.prior.Type3ChainParser()
    _, _, origin = parser._read_top_level_header(blob)
    nodes = parser._extract_nodes(blob[origin:])
    node = next(n for n in nodes if n.header.class_name == "CParagraphe")
    shifted = SimpleNamespace(payload=node.payload, header=node.header,
                              start_offset=100, payload_offset=150)

    class Scanner:
        def _read_top_level_header(self, _):
            return None, None, 23

        def _extract_nodes(self, _):
            return [shifted]

    monkeypatch.setattr(analyzer.prior, "Type3ChainParser", Scanner)
    moved = analyzer.extract_structure(b"\0" * 300)
    p = moved["paragraphs"][0]
    assert p["provenance"]["runtime_descriptor_start"] == 123
    assert p["provenance"]["class_payload_start"] == 173
    assert {k: v for k, v in p.items() if k != "provenance"} == {k: v for k, v in base["paragraphs"][0].items() if k != "provenance"}


def synthetic(codes, shift=0):
    data = bytearray(47+(len(codes)+2)*204)
    prefix = 47+204+59+shift
    data[prefix-4:prefix] = len(codes).to_bytes(4, "little")
    for i, code in enumerate(codes):
        p = prefix+i*204
        data[p:p+4] = b"\x05\0\0\0"
        data[p+4:p+8] = code.to_bytes(4, "little")
    return bytes(data)


def test_synthetic_exact_period_does_not_confirm_outer_boundary(analyzer):
    p = analyzer.analyze_payload(synthetic([65, 66, 0]))
    assert p["aligned_record_count"] == 3
    assert p["slot_codes"]["u32le_values"] == [65, 66, 0]
    assert p["prefix_evidence"]["equals_enumerated_count"]
    assert not p["boundary_confirmed"]


def test_synthetic_shifted_prefix_does_not_force_code_3f(analyzer):
    p = analyzer.analyze_payload(synthetic([65, 66, 0], shift=3))
    assert p["slot_codes"]["candidate_record_relative_offset"] == 0x42
    assert p["prefix_evidence"]["record_relative_offset"] == 0x3E
    assert not p["boundary_confirmed"]


def test_synthetic_internal_zero_does_not_stop_enumeration(analyzer):
    p = analyzer.analyze_payload(synthetic([65, 0, 66, 0]))
    assert p["aligned_record_count"] == 4
    assert not p["terminal"]["only_last_zero"]
    assert not p["terminal"]["count_equals_nonzero_plus_one"]
    # Count prefix disagreement is reported, not used to force enumeration.
    data = bytearray(synthetic([65, 66, 0]))
    data[306:310] = (99).to_bytes(4, "little")
    p = analyzer.analyze_payload(bytes(data))
    assert p["aligned_record_count"] == 3 and not p["prefix_evidence"]["equals_enumerated_count"]


def test_synthetic_periodicity_without_prefix_is_not_schema(analyzer):
    p = analyzer.analyze_payload(b"\xAA" * (47+6*204))
    assert p["H1_boundary_score"]["equal_adjacent_boundaries"] > 0
    assert p["aligned_record_count"] is None
    assert p["homogeneity"]["status"] == "unresolved"
    assert not p["boundary_confirmed"]


def test_limits_and_fixture_selection(analyzer):
    single = json.loads(run_cli("--json", "--fixture", "text_digits.txt", "--no-oracle"))
    assert len(single["fixture_results"]) == 1
    with pytest.raises(ValueError, match="payload budget"):
        analyzer.extract_structure(b"\0" * 1048577)
    with pytest.raises(ValueError, match="record examination budget"):
        analyzer.analyze_payload(b"\0" * 10000)
    with pytest.raises(ValueError, match="fixture budget"):
        analyzer.build_report([str(i) for i in range(25)])
    with pytest.raises(ValueError, match="inside text samples"):
        analyzer.build_report(["../outside.txt"])
