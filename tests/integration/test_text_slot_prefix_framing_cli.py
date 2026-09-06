from __future__ import annotations

import copy
import hashlib
import importlib.util
import inspect
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
CLI = ROOT / "tools/analyze_text_slot_prefix_framing.py"


def run_cli(*args):
    result = subprocess.run([sys.executable, str(CLI), *args], cwd=ROOT,
                            env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
                            capture_output=True, timeout=30)
    assert result.returncode == 0, result.stderr.decode()
    return result.stdout


@pytest.fixture(scope="module")
def analyzer():
    spec = importlib.util.spec_from_file_location("prefix_framing_test", CLI)
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


def structure(report):
    return {k: v for k, v in report.items() if k != "oracle_summary"}


def payload(analyzer, name="default_text.txt"):
    blob = analyzer.prior.prior.hex_text_to_bytes((analyzer.TEXT_DIR / name).read_text())
    parser = analyzer.prior.prior.Type3ChainParser()
    _, _, origin = parser._read_top_level_header(blob)
    node = next(n for n in parser._extract_nodes(blob[origin:]) if n.header.class_name == "CParagraphe")
    return blob, node


def test_modes_coverage_bounds_and_policy(report, analyzer):
    assert len(run_cli()) < 50000 and len(run_cli("--markdown")) < 50000
    assert {r["fixture"] for r in report["fixture_results"]} == set(analyzer.FIXTURES)
    assert len(report["fixture_results"]) == 24
    assert report["policy"] == analyzer.POLICY
    assert all(not p["slot_rows"] for p in paragraphs(report))
    assert all(not p["selected_run"]["parser_safe"] for p in paragraphs(report))
    assert report["answers"]["candidate_parser_model_readiness"] == "not_ready"
    assert report["answers"]["color_ownership_readiness"] == "not_ready"


def test_details_are_bounded_and_do_not_change_analysis(report):
    raw = run_cli("--json", "--details")
    assert len(raw) < 100000 and len(run_cli("--details")) < 50000
    detailed = json.loads(raw)
    with_rows = [p for p in paragraphs(detailed) if p["slot_rows"]]
    assert len(with_rows) == 3 and all(len(p["slot_rows"]) <= 5 for p in with_rows)
    for a, b in zip(paragraphs(detailed), paragraphs(report)):
        assert {k: v for k, v in a.items() if k != "slot_rows"} == {k: v for k, v in b.items() if k != "slot_rows"}


def test_no_oracle_identical_structure(report):
    assert structure(report) == structure(json.loads(run_cli("--json", "--no-oracle")))


def test_freeze_and_wrong_text_cannot_select_runs(analyzer, monkeypatch):
    baseline = analyzer.build_report(oracle_enabled=False)
    original = analyzer.oracle_phase
    snapshots = []

    def phase(frozen, enabled):
        assert isinstance(frozen, str)
        snapshots.append(json.loads(frozen))
        return original(frozen, enabled)

    def wrong(_):
        assert snapshots, "oracle read before complete freeze"
        return {"texts": ["wrong expected text"], "source": "adversarial"}

    monkeypatch.setattr(analyzer, "oracle_phase", phase)
    monkeypatch.setattr(analyzer, "load_text_oracle", wrong)
    adversarial = analyzer.build_report()
    assert structure(adversarial) == structure(baseline)
    assert all(adversarial[k] == v for k, v in snapshots[0]["structural"].items())
    assert all(not d["ordinal_match"] for r in adversarial["oracle_summary"]["fixtures"] for d in r["diagnostics"])
    monkeypatch.setattr(analyzer, "load_text_oracle", lambda _: pytest.fail("disabled oracle loaded"))
    analyzer.build_report(oracle_enabled=False)


def test_competing_prefix_and_count_framing_rules(report):
    rules = report["run_start_rule_summary"]["rules"]
    assert rules["R1"]["ambiguity_count"] == 24 and rules["R1"]["false_candidate_count"] == 24
    assert rules["R2"]["support_count"] == 24 and rules["R2"]["false_candidate_count"] == 0
    assert rules["R3"]["conflict_count"] == 24
    assert rules["R4"]["support_count"] == 20 and rules["R4"]["conflict_count"] == 4
    for p in paragraphs(report):
        assert len(p["candidate_runs"]) == 2
        assert sum(c["framing_eligible"] for c in p["candidate_runs"]) == 1
        assert p["candidate_runs"][0]["count"] == p["candidate_runs"][1]["count"]
        assert p["candidate_runs"][1]["start"]-p["candidate_runs"][0]["start"] == 92


def test_prefix_signatures_code_width_and_stride(report):
    assert report["prefix_signature_summary"]["P3"]["signature_classes"] == 3
    mask = report["prefix_signature_summary"]["cross_fixture_invariant_bytes"]
    assert all(str(i) not in mask for i in (4, 5, 6, 7, 80, 81, 82))
    assert report["periodic_run_summary"]["selected_slots"] == 207
    for p in paragraphs(report):
        r = p["selected_run"]
        assert r["signature_classes"] == 1 and r["upstream_context_classes"] == 2
        assert r["first_vs_later"] == "upstream_difference_only"
        assert r["nearby_stride_prefix_counts_196_to_212"][8] == r["slot_count"]
        assert all(n == 1 for i, n in enumerate(r["nearby_stride_prefix_counts_196_to_212"]) if i != 8)
        assert r["code"]["observed_code_byte_start"] == 4
        assert r["code"]["observed_variable_width"] == 1
        assert r["code"]["typed_code_start"] is None and r["code"]["typed_code_width"] is None


def test_color_normalization_and_multiline_shift(report):
    summary = report["color_normalization_summary"]
    assert summary["prior_grid_coordinate_matches"] == 20
    assert summary["cross_fixture_masked_context_classes"] == 1 and summary["shifted_run_count"] == 4
    for p in paragraphs(report):
        r = p["selected_run"]
        assert r["color"]["observed_color_offset_relative_to_prefix"] == 0x50
        assert r["color"]["observed_color_changed_width"] == 3 and r["color"]["typed_color_width"] is None
        if r["internal_code_13_count"]:
            assert r["prefix_start"] == 378 and r["slot_count"] == 10
            assert r["prefix_break_at_code_13"] is False
            assert r["color"]["prior_grid_byte_match_count"] is None
        else:
            assert r["prefix_start"] == 310
            assert r["color"]["prior_grid_byte_match_count"] == r["slot_count"]
    assert all(r["same_positive_prefix_example"] for r in report["multiline_summary"]["fixtures"])


def test_terminal_and_ascii_oracle(report):
    for p in paragraphs(report):
        r = p["selected_run"]
        terminal = r["terminal"]
        assert terminal["terminal_candidate_index"] == r["slot_count"]-1
        assert terminal["zero_code"] and not terminal["next_prefix_present"]
        assert terminal["terminal_signature_matches_previous"] and terminal["terminal_color_matches_previous"]
    for row in report["oracle_summary"]["fixtures"][:7]:
        assert row["diagnostics"][0]["ordinal_match"] and row["diagnostics"][0]["n_plus_one"]


def synthetic(codes, start=180):
    data = bytearray(b"\xA7" * (start+(len(codes)+1)*204))
    data[start-4:start] = len(codes).to_bytes(4, "little")
    for i, code in enumerate(codes):
        p = start+i*204
        data[p:p+92] = b"\0" * 92
        data[p:p+4] = b"\x05\0\0\0"
        data[p+4:p+8] = code.to_bytes(4, "little")
        data[p+80:p+83] = b"\x12\x34\x56"
    return bytes(data)


def test_synthetic_stable_prefix_run(analyzer):
    result, _ = analyzer.analyze_payload(synthetic([65, 66, 0]))
    run = result["selected_run"]
    assert run["prefix_start"] == 180 and run["slot_count"] == 3
    assert run["terminal"]["terminal_candidate_index"] == 2


@pytest.mark.parametrize("shift", [37, 68, 113])
def test_synthetic_and_real_shifted_payload_located_without_correction(analyzer, shift):
    for data in (synthetic([65, 66, 0]), payload(analyzer)[1].payload):
        original, _ = analyzer.analyze_payload(data)
        moved, _ = analyzer.analyze_payload(b"\xA7" * shift + data)
        a, b = original["selected_run"], moved["selected_run"]
        assert b["prefix_start"] == a["prefix_start"]+shift
        assert b["slot_count"] == a["slot_count"] and b["stride"] == a["stride"]
        assert b["signature_example"] == a["signature_example"]
        assert b["code"] == a["code"] and b["terminal"] == a["terminal"]
        assert b["color"]["byte_distribution"] == a["color"]["byte_distribution"]
    source = inspect.getsource(analyzer.discover_runs)
    assert all(token not in source for token in ("310", "378", "68", "47", "oracle", "fixture"))


def test_internal_zero_does_not_stop_traversal(analyzer):
    result, _ = analyzer.analyze_payload(synthetic([65, 0, 66, 0]), details=True)
    run = result["selected_run"]
    assert run["slot_count"] == 4 and run["terminal"]["terminal_candidate_index"] == 3
    assert run["terminal"]["T2_premature_stop_count"] == 1
    row = next(r for r in result["slot_rows"] if r["index"] == 1)
    assert row["code_zero"] and row["next_prefix_present"]


def test_first_context_difference_is_not_rejected_by_definition(analyzer):
    data = bytearray(synthetic([65, 66, 0]))
    data[180+12] = 0x91
    result, _ = analyzer.analyze_payload(bytes(data))
    assert result["selected_run"]["signature_classes"] == 2
    assert result["selected_run"]["first_vs_later"] == "first_slot_signature_candidate"
    assert result["rules"]["R3"]["status"] == "support"


def test_periodic_filler_and_count_disagreement_abstain(analyzer):
    result, _ = analyzer.analyze_payload(b"\xAA" * 2200)
    assert result["selected_run"] is None
    data = bytearray(synthetic([65, 66, 0]))
    data[176:180] = (99).to_bytes(4, "little")
    result, _ = analyzer.analyze_payload(bytes(data))
    assert result["selected_run"] is None and result["candidate_runs"][0]["count"] == 3


def test_two_count_framed_candidates_remain_ambiguous(analyzer):
    data = bytearray(synthetic([65, 66, 0]))
    second = 272
    data[second-4:second] = (3).to_bytes(4, "little")
    for i in range(3):
        p = second+i*204
        data[p:p+32] = b"\x05\0\0\0" + b"\0" * 28
    result, _ = analyzer.analyze_payload(bytes(data))
    assert result["status"] == "ambiguous_count_framed_candidates"
    assert result["selected_run"] is None
    assert result["rules"]["R2"]["status"] == "ambiguity"


def test_code_and_color_bytes_do_not_select_prefix(analyzer):
    data = bytearray(synthetic([65, 66, 0]))
    before = analyzer.discover_runs(bytes(data))
    for i, code in enumerate((0x12345678, 0, 0x7F223344)):
        p = 180+i*204
        data[p+4:p+8] = code.to_bytes(4, "little")
        data[p+80:p+83] = bytes([i+1, 0x80, 0xFE])
    assert analyzer.discover_runs(bytes(data)) == before


def test_descriptor_shift_and_no_filename_or_ownership_rule(analyzer, monkeypatch):
    from types import SimpleNamespace

    blob, node = payload(analyzer)
    original, _ = analyzer.extract_structure(blob)
    moved_node = SimpleNamespace(payload=node.payload, header=node.header, start_offset=100, payload_offset=180)

    class Scanner:
        def _read_top_level_header(self, _):
            return None, None, 19

        def _extract_nodes(self, _):
            return [moved_node]

    monkeypatch.setattr(analyzer.prior.prior, "Type3ChainParser", Scanner)
    moved, _ = analyzer.extract_structure(b"\0" * 400)
    a, b = original["paragraphs"][0], moved["paragraphs"][0]
    assert {k: v for k, v in a.items() if k != "provenance"} == {k: v for k, v in b.items() if k != "provenance"}
    assert b["provenance"]["runtime_descriptor_start"] == 119
    assert b["provenance"]["class_payload_start"] == 199
    one = analyzer.structural_report([("ordinary.txt", copy.deepcopy(original))])
    two = analyzer.structural_report([("multiline_grouped.txt", copy.deepcopy(original))])
    assert one["answers"] == two["answers"]
    assert one["fixture_results"][0]["structural"] == two["fixture_results"][0]["structural"]


def test_parser_model_sources_and_results_unchanged(analyzer):
    from type3_clipboard_codec import parse_type3_clipboard_bytes_with_parser

    paths = sorted((ROOT / "src").rglob("*.py"))
    hashes = {p: hashlib.sha256(p.read_bytes()).digest() for p in paths}
    blob, _ = payload(analyzer)
    before = repr(parse_type3_clipboard_bytes_with_parser(blob))
    analyzer.build_report()
    assert repr(parse_type3_clipboard_bytes_with_parser(blob)) == before
    assert hashes == {p: hashlib.sha256(p.read_bytes()).digest() for p in paths}


def test_limits_and_search_scope(analyzer):
    with pytest.raises(ValueError, match="payload budget"):
        analyzer.discover_runs(b"\0" * 1048577)
    with pytest.raises(ValueError, match="slot traversal"):
        analyzer.discover_runs(synthetic([65] * 25))
    with pytest.raises(ValueError, match="fixture budget"):
        analyzer.build_report([str(i) for i in range(25)])
    with pytest.raises(ValueError, match="inside text samples"):
        analyzer.build_report(["../outside.txt"])
    # A genuine run outside the declared leading region must not trigger a full scan.
    assert analyzer.discover_runs(synthetic([65, 66, 0], start=1000))["selected"] is None
    single = json.loads(run_cli("--json", "--fixture", "text_multiline_basic.txt", "--no-oracle"))
    assert len(single["fixture_results"]) == 1
