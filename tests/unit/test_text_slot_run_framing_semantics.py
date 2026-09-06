from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


@pytest.fixture(scope="module")
def analyzer():
    path = Path(__file__).resolve().parents[2] / "tools/analyze_text_slot_run_framing_semantics.py"
    spec = importlib.util.spec_from_file_location("framing_semantics_unit", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def put_run(analyzer, data, start, codes, count=None, variant=0, valid=True):
    data[start-4:start] = (len(codes) if count is None else count).to_bytes(4, "little")
    for i, code in enumerate(codes):
        p = start+i*204
        window = bytearray(32)
        for off, value in zip(analyzer.SIGNATURE_OFFSETS, analyzer.REFERENCE_SIGNATURES[variant]):
            window[off] = value
        window[4:8] = code.to_bytes(4, "little")
        if not valid:
            window[20] ^= 0xA5
        data[p:p+32] = window
        data[p+80:p+83] = b"\x12\x34\x56"


def sample(analyzer, codes=(65, 66, 0), count=None, valid=True):
    data = bytearray(b"\xA7" * (180+(len(codes)+1)*204))
    put_run(analyzer, data, 180, codes, count, valid=valid)
    return bytes(data)


def test_valid_count_and_family(analyzer):
    result, _ = analyzer.analyze_payload(sample(analyzer))
    assert result["detector_status"] == "both_agree" and result["selected_prefix_start"] == 180
    r = result["prefix_family_runs"][0]
    assert r["count_matches"]["C2_total_including_terminal"]
    assert not r["count_matches"]["C1_nonterminal"]


def test_wrong_count_keeps_prefix_and_reports_conflict(analyzer):
    result, raw = analyzer.analyze_payload(sample(analyzer, count=99))
    assert result["detector_status"] == "conflict" and result["selected_prefix_start"] is None
    assert result["candidate_evidence"][0]["A_prefix_periodicity_and_family"]
    assert not result["candidate_evidence"][0]["B_count_equals_total"]
    assert result["prefix_family_runs"][0]["total_slot_count"] == 3
    report = analyzer.structural_report([("wrong", {"paragraphs": [result]})], [("wrong", raw)])
    assert report["count_hypothesis_summary"]["tested_runs"] == 1
    assert report["count_hypothesis_summary"]["C2"] == 0
    assert report["answers"]["candidate_parser_rfc_readiness"] == "not_ready"


def test_zero_count_reports_prefix_only(analyzer):
    result, _ = analyzer.analyze_payload(sample(analyzer, count=0))
    assert result["detector_status"] == "prefix_only" and result["selected_prefix_start"] is None


def test_correct_count_false_periodic_context_not_accepted(analyzer):
    result, _ = analyzer.analyze_payload(sample(analyzer, valid=False))
    assert result["detector_status"] == "count_only" and result["selected_prefix_start"] is None
    assert not result["prefix_family_runs"]
    filler, _ = analyzer.analyze_payload(b"\xAA" * 2200)
    assert filler["selected_prefix_start"] is None


def test_context_disambiguates_weak_competitor(analyzer):
    data = bytearray(sample(analyzer))
    put_run(analyzer, data, 272, (65, 66, 0), count=99, valid=False)
    result, _ = analyzer.analyze_payload(bytes(data))
    assert len(result["candidate_evidence"]) == 2
    assert result["detector_status"] == "both_agree" and result["selected_prefix_start"] == 180


@pytest.mark.parametrize("second_count", [3, 99])
def test_multiple_family_runs_remain_ambiguous(analyzer, second_count):
    data = bytearray(sample(analyzer))
    put_run(analyzer, data, 272, (65, 66, 0), count=second_count)
    result, _ = analyzer.analyze_payload(bytes(data))
    assert result["detector_status"] == "ambiguous" and result["selected_prefix_start"] is None
    assert len(result["prefix_family_runs"]) == 2


@pytest.mark.parametrize("shift", [37, 91])
def test_shifted_run_keeps_relative_count(analyzer, shift):
    original, _ = analyzer.analyze_payload(sample(analyzer))
    moved, _ = analyzer.analyze_payload(b"\xA7" * shift + sample(analyzer))
    assert moved["selected_prefix_start"] == original["selected_prefix_start"]+shift
    assert moved["detector_status"] == "both_agree"
    a, b = original["prefix_family_runs"][0], moved["prefix_family_runs"][0]
    assert a["count_probe"] == b["count_probe"] and a["count_matches"] == b["count_matches"]


def test_internal_zero_and_code13_are_counted_as_slots(analyzer):
    result, _ = analyzer.analyze_payload(sample(analyzer, codes=(65, 0, 13, 66, 0)))
    r = result["prefix_family_runs"][0]
    assert r["total_slot_count"] == 5 and r["nonterminal_count"] == 4
    assert r["zero_slot_count"] == 2 and r["code_13_count"] == 1
    assert r["terminal_index"] == 4 and r["count_matches"]["C2_total_including_terminal"]


def test_family_is_exact_variants_not_cartesian_wildcards(analyzer):
    rule = analyzer.family_rule()
    assert len(rule["invariant_core"]) == 20
    # Combine two independently observed changes into an unobserved fourth vector.
    mixed = bytearray(analyzer.REFERENCE_SIGNATURES[1])
    mixed[analyzer.SIGNATURE_OFFSETS.index(8)] = 1
    assert not analyzer.family_match(bytes(mixed))
    for sig in analyzer.REFERENCE_SIGNATURES:
        assert analyzer.family_match(sig)


def test_count_bytes_do_not_change_family_classification(analyzer):
    a, _ = analyzer.analyze_payload(sample(analyzer))
    b, _ = analyzer.analyze_payload(sample(analyzer, count=2))
    assert a["prefix_family_runs"][0]["variant_ids"] == b["prefix_family_runs"][0]["variant_ids"]
    assert b["prefix_family_runs"][0]["count_matches"]["C1_nonterminal"]
    assert b["detector_status"] == "conflict"


def test_narrow_count_match_does_not_override_conflicting_wide_view(analyzer):
    result, _ = analyzer.analyze_payload(sample(analyzer, count=0x01000003))
    probe = result["prefix_family_runs"][0]["count_probe"]
    assert probe["u8"] == probe["u16le"] == 3
    assert probe["u32le"] != 3
    assert result["detector_status"] == "conflict" and result["selected_prefix_start"] is None


def test_count_match_does_not_prove_terminal(analyzer):
    result, raw = analyzer.analyze_payload(sample(analyzer, codes=(65, 66, 67)))
    assert result["detector_status"] == "both_agree"
    assert result["prefix_family_runs"][0]["terminal_status"] == "unresolved"
    report = analyzer.structural_report([("no_terminal", {"paragraphs": [result]})], [("no_terminal", raw)])
    assert not report["answers"]["terminal_included_in_count"]
    assert report["answers"]["candidate_parser_rfc_readiness"] == "not_ready"
