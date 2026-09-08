"""Actual parser provenance and full-corpus isolation regression."""

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
CLI = ROOT / "tools/analyze_text_slot_family_shadow.py"


@pytest.fixture(scope="module")
def shadow():
    spec = importlib.util.spec_from_file_location("shadow_integration", CLI)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def report(shadow):
    return shadow.build_report()


def test_full_corpus_actual_v1_and_exact_same_run(report):
    assert report["answers"]["real_fixture_count"] == 104
    assert report["v1_summary"]["actual_parser"]
    assert report["outcome_summary"] == dict(
        both_absent=32, both_present_same_run=62, v1_absent_v2_present=10,
        v1_present_v2_absent=0, both_present_different_run=0, v2_ambiguous=0,
        resource_or_bounds_difference=0, other_structural_disagreement=0,
    )
    assert report["answers"]["v1_present_count"] == 62
    assert report["answers"]["v2_shadow_present_count"] == 72
    for row in report["fixture_results"]:
        if row["outcome"] == "both_present_same_run":
            assert row["v2"]["run_ref"] == "v1.run"
            run = row["v1"]["run"]
            assert run["slot_count"] == len(run["prefix_positions"])
            assert run["count_valid"] and run["terminal_valid"]
    groups = report["oracle_summary"]["cohort_counts"]
    assert {k: groups[k] for k in ("controlled", "unsupported_styles", "multiline", "multi_object")} == {
        "controlled": 9, "unsupported_styles": 5, "multiline": 4, "multi_object": 7,
    }


def test_all_runtime_outputs_and_source_bytes_unchanged(shadow, report):
    baseline = json.loads(shadow.BASELINE.read_text())
    assert len(baseline["fixtures"]) == 104
    for path, expected in baseline["source_sha256"].items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == expected
    assert report["corpus_summary"]["runtime_source_equal"]
    assert report["corpus_summary"]["runtime_outputs_equal"]
    assert all(row["runtime_regression_equal"] for row in report["fixture_results"])
    assert not report["warnings"]


def test_identity_accounting_and_decoy_full_corpus(report):
    assert report["v2_identity_summary"]["raw_prefix_hits"] == 1184
    assert report["v2_identity_summary"]["identity_matches"] == 592
    assert report["v2_run_summary"]["deduplicated_runs"] == 72
    assert report["v2_run_summary"]["suffix_starts_removed"] == 520
    assert report["decoy_summary"] == dict(runs=72, slots=592, identity_matches=0, rejection_layer="identity")
    assert sum(len(r["decoys"]) for r in report["fixture_results"]) == 72


def test_challenges_and_readiness(report):
    collision = report["collision_summary"]
    assert collision["identity_clone_wrong_count"]["layer"] == "count"
    assert collision["identity_clone_missing_terminal"]["layer"] == "terminal"
    assert collision["two_full_identity_clones"]["status"] == "ambiguous"
    negatives = collision["general_negatives"]
    assert len(negatives) == 6 and all(not c["v2_present"] for c in negatives.values())
    assert all(not c["v2_present"] for c in report["structural_constant_summary"].values())
    assert all(c["status"] == "resource" for c in report["resource_summary"]["cases"].values())
    assert report["answers"]["runtime_v2_promotion_review_readiness"] == "ready_for_review"
    assert report["answers"]["parser_safe"] is False
    assert report["answers"]["ownership_readiness"] == "unresolved"


def test_oracle_boundary_and_adversarial_intent(shadow, report, monkeypatch):
    no_oracle = shadow.build_report(oracle_enabled=False)
    assert {k: v for k, v in no_oracle.items() if k != "oracle_summary"} == {
        k: v for k, v in report.items() if k != "oracle_summary"
    }
    original = shadow.oracle_phase

    def oracle(frozen, enabled):
        assert isinstance(frozen, str)
        assert len(json.loads(frozen)["fixture_results"]) == 104
        with monkeypatch.context() as patch:
            patch.setattr(shadow, "evaluate_v2", lambda *_: pytest.fail("selection after oracle"))
            patch.setattr(shadow.research, "load_labels", lambda _: {"groups": ["adversarial_wrong_text"]})
            return original(frozen, enabled)

    monkeypatch.setattr(shadow, "oracle_phase", oracle)
    adversarial = shadow.build_report()
    assert {k: v for k, v in adversarial.items() if k != "oracle_summary"} == {
        k: v for k, v in report.items() if k != "oracle_summary"
    }


def test_filename_does_not_select(shadow, tmp_path):
    source = ROOT / "tests/samples/text/text_slotstyle_a8_char4_navy.txt"
    renamed = tmp_path / "wrong_count_expected_text_geometry.txt"
    renamed.write_bytes(source.read_bytes())
    baseline = json.loads(shadow.BASELINE.read_text())
    by_raw = {v["raw_sha256"]: v for v in baseline["fixtures"].values()}
    first, state1, _ = shadow.compare_fixture(source, by_raw)
    second, state2, _ = shadow.compare_fixture(renamed, by_raw)
    first.pop("fixture")
    second.pop("fixture")
    assert first == second and state1 == state2


@pytest.mark.parametrize("args", [[], ["--json"], ["--json", "--no-oracle"], ["--json", "--details"]])
def test_cli_bounded_output(args):
    result = subprocess.run([sys.executable, str(CLI), *args], cwd=ROOT, capture_output=True, timeout=60)
    assert result.returncode == 0, result.stderr.decode()
    assert len(result.stdout) < (100_000 if "--json" in args else 50_000)
    if "--json" in args:
        assert json.loads(result.stdout)["policy"]["v2_public_candidate"] == "not_emitted"
