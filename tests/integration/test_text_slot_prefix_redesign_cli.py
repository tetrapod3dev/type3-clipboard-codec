from dataclasses import asdict
import hashlib
import importlib.util
import json
import subprocess
import sys

import pytest

from type3_clipboard_codec import parse_type3_clipboard_bytes_with_parser
from type3_clipboard_codec.inspect.formatters import _json_safe
from type3_clipboard_codec.inspect.hex_input import hex_text_to_bytes
from tests import frozen_text_slot_candidate_v1 as runtime
from tests.text_slot_v1_replay import historical_root, replay_parser

# F0 is a historical v1 hypothesis, never reinterpreted as current runtime v2.
ROOT = historical_root()
CLI = ROOT / "tools/analyze_text_slot_prefix_redesign.py"
GOLDEN = json.loads((ROOT / "tests/samples/reports/text/text_slot_style_runtime_baseline.json").read_text())


@pytest.fixture(scope="module", autouse=True)
def historical_v1_runtime():
    with replay_parser():
        yield


@pytest.fixture(scope="module")
def analyzer():
    spec = importlib.util.spec_from_file_location("prefix_redesign_test", CLI)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def report(analyzer):
    return analyzer.build_report()


def structural(report):
    return {k: v for k, v in report.items() if k not in ("oracle_summary", "answers", "warnings")}


def metric(report, name, hypothesis):
    return dict(zip(report["metric_columns"], report["fixture_metrics"][name][hypothesis]))


def synthetic_metric(report, name, hypothesis):
    return dict(zip(report["metric_columns"], report["synthetic_controls"][name]["metrics"][hypothesis]))


def run_cli(*args):
    result = subprocess.run([sys.executable, str(CLI), *args], capture_output=True, cwd=ROOT, timeout=30)
    assert result.returncode == 0, result.stderr.decode()
    return result.stdout


def test_corpus_and_independent_reference_coverage(report):
    assert len(report["fixture_inventory"]) == 104
    assert sum(r["reference_count"] for r in report["fixture_inventory"]) == 72
    assert sum(r["reference_slots"] for r in report["fixture_inventory"]) == 592
    assert sum(r["decoy_present"] for r in report["fixture_inventory"]) == 72
    assert not report["warnings"]
    groups = report["oracle_summary"]["group_metrics"]
    assert groups["controlled"]["F4"]["unique_reference_matches"] == 9
    assert groups["previous24"]["F4"]["reference_slots"] == 207
    assert groups["geometry_scope_negative"]["F4"]["fixtures"] == 32
    assert "unresolved_paragraph" not in groups


@pytest.mark.parametrize(
    "h,total,controlled,ambiguity",
    [("F0", 62, 4, 5), ("F1", 63, 5, 4), ("F2", 68, 7, 2), ("F3", 72, 9, 0), ("F4", 72, 9, 0)],
)
def test_hypothesis_recall(report, h, total, controlled, ambiguity):
    assert report["identity_and_layer_totals"][h]["full_reference_matches"] == total
    assert report["identity_and_layer_totals"][h]["ambiguity_count"] == ambiguity
    assert report["oracle_summary"]["group_metrics"]["controlled"][h]["full_reference_matches"] == controlled
    for group, n in [("previous24", 24), ("multiline", 4), ("multi_object", 7)]:
        assert report["oracle_summary"]["group_metrics"][group][h]["full_reference_matches"] == n


def test_known_decoy_never_hidden_by_count(report):
    for h, row in report["identity_and_layer_totals"].items():
        assert row["known_decoy_runs"] == 72
        assert row["known_decoy_slot_hits"] == row["known_decoy_matches"] == 0
    assert report["raw_layer_summary"]["recurring_runs"] >= 144


def test_freeze_before_labels(analyzer, report, monkeypatch):
    original = analyzer.oracle_phase
    seen = []

    def phase(frozen, enabled):
        assert isinstance(frozen, str)
        evidence = json.loads(frozen)
        assert len(evidence["fixture_metrics"]) == 104
        assert len(evidence["_frozen_profiles"]) == 72
        seen.append(True)
        with monkeypatch.context() as patch:
            patch.setattr(analyzer, "predicate", lambda *a: pytest.fail("matching after oracle boundary"))
            return original(frozen, enabled)

    monkeypatch.setattr(analyzer, "oracle_phase", phase)
    assert analyzer.build_report() == report
    assert seen


def test_no_oracle_structural_equality(analyzer, report, monkeypatch):
    monkeypatch.setattr(analyzer, "load_labels", lambda _: pytest.fail("labels accessed"))
    no_oracle = analyzer.build_report(oracle_enabled=False)
    assert structural(no_oracle) == structural(report)
    assert structural(json.loads(run_cli("--json", "--no-oracle"))) == structural(report)


def test_wrong_intent_labels_cannot_change_predicates(analyzer, report, monkeypatch):
    monkeypatch.setattr(
        analyzer,
        "load_labels",
        lambda _: dict(
            groups=["fabricated"],
            intent=dict(
                changed_value=999999,
                visible_text="wrong",
                color="wrong",
                target_character_index_1based=200,
                changed_property="fabricated",
                grouping="invented",
            ),
        ),
    )
    wrong = analyzer.build_report()
    assert structural(wrong) == structural(report)
    assert wrong["answers"]["runtime_prefix_redesign_readiness"] == "not_ready"


def test_filename_renaming_and_order_do_not_affect_identity(analyzer, tmp_path):
    paths = [analyzer.SAMPLES / "text" / (name + ".txt") for name in analyzer.CONTROLLED]
    original = analyzer.build_report(paths, oracle_enabled=False)
    renamed = []
    mapping = {}
    for i, path in enumerate(paths):
        dest = tmp_path / f"unlabelled_{i}.txt"
        dest.write_bytes(path.read_bytes())
        renamed.append(dest)
        mapping[path.name] = dest.name
    changed = analyzer.build_report(list(reversed(renamed)), oracle_enabled=False)
    for name, metrics in original["fixture_metrics"].items():
        assert changed["fixture_metrics"][mapping[name]] == metrics
    for key in (
        "positional_variability_map",
        "synthetic_controls",
        "identity_and_layer_totals",
        "predicate_hypotheses",
    ):
        assert changed[key] == original[key]


@pytest.mark.parametrize(
    "offset", list(range(4, 8)) + list(range(12, 36)) + [44, 45, 46, 47, 48, 55, 64, 71, 72, 79, 80, 82, 95]
)
def test_style_and_aux_bytes_cannot_break_f4(analyzer, offset):
    data = bytearray(96)
    for start, raw in analyzer.F4_RANGES:
        data[start : start + len(raw)] = raw
    assert analyzer.predicate(data, 0, "F4")
    for value in (1, 5, 127, 255):
        data[offset] = value
        assert analyzer.predicate(data, 0, "F4")


@pytest.mark.parametrize("value,expected", [(0, True), (1, True), (2, False), (77, False), (255, False)])
def test_byte08_is_bounded_not_wildcard(analyzer, value, expected):
    data = bytearray(96)
    for start, raw in analyzer.F4_RANGES:
        data[start : start + len(raw)] = raw
    data[8] = value
    assert analyzer.predicate(data, 0, "F4") is expected


def test_byte08_variability_and_no_semantic_assignment(report):
    rows = report["oracle_summary"]["byte08_inventory"]
    assert all(r[2] for r in rows)
    nonzero = [r for r in rows if r[1] != [0]]
    assert len(nonzero) == 1 and nonzero[0][0] == "text_group_mixed_color_two_objects.txt"
    assert nonzero[0][1] == [1]
    assert report["oracle_summary"]["byte08_interpretation"].startswith("unresolved")


def test_wider_constants_and_variable_aux_area(report):
    positions = {r[0]: r for r in report["positional_variability_map"]["rows"]}
    assert set(positions) == set(range(-16, 96))
    assert len(positions[44][1]) > 1
    assert all(positions[p][4] for p in range(36, 44))
    assert all(positions[p][4] for p in range(56, 64))
    discriminators = {r["offset"] for r in report["wider_structural_inventory"] if r["discriminates_decoy"]}
    assert 36 in discriminators and 56 in discriminators


def test_synthetic_negatives_expose_mask_weakness(report):
    assert report["synthetic_false_positive_summary"]["F3"]["identity_false_positive_cases"] == 3
    assert report["synthetic_false_positive_summary"]["F2"]["identity_false_positive_cases"] == 1
    assert report["synthetic_false_positive_summary"]["F4"]["identity_false_positive_cases"] == 0
    for h in ("F0", "F4"):
        row = report["synthetic_false_positive_summary"][h]
        assert row["identity_collision_cases"] == 2
        assert row["all_identity_false_positive_rate"] == 0.25
    assert synthetic_metric(report, "periodic_zero_filler", "F3")["prefix_hits"] > 0
    assert synthetic_metric(report, "periodic_zero_filler", "F4")["prefix_hits"] == 0


def test_layers_do_not_hide_identity_clones_or_ambiguity(report):
    count = synthetic_metric(report, "identity_clone_wrong_count", "F4")
    terminal = synthetic_metric(report, "identity_clone_missing_terminal", "F4")
    ambiguity = synthetic_metric(report, "two_full_identity_clones", "F4")
    assert count["prefix_hits"] > 0 and count["recurring_runs"] == 1 and count["count_valid_runs"] == 0
    assert terminal["prefix_hits"] > 0 and terminal["count_valid_runs"] == 1 and terminal["terminal_valid_runs"] == 0
    assert ambiguity["all_four_layers"] == 2 and ambiguity["ambiguous"]
    assert not ambiguity["unique_reference"]


def test_geometry_scope_negative_is_explicit(report):
    negatives = [r for r in report["fixture_inventory"] if r["paragraph_count"] == 0]
    assert len(negatives) == 32
    for item in negatives:
        assert metric(report, item["fixture"], "F4")["prefix_hits"] == 0
    assert any("Geometry" in note for note in report["answers"]["limitations"])


@pytest.mark.parametrize("name,required", [("F0", 32), ("F1", 32), ("F2", 32), ("F3", 12), ("F4", 64)])
def test_local_bounds(analyzer, name, required):
    assert not analyzer.predicate(b"\0" * (required - 1), 0, name)
    assert not analyzer.predicate(b"\0" * 96, -1, name)
    assert analyzer.BOUNDS[name] == required


def test_f0_matches_runtime_exact_family(analyzer):
    for path in (analyzer.SAMPLES / "text").glob("*.txt"):
        result = analyzer.read_capture(path)
        for payload in result["payloads"]:
            for p in analyzer.raw_hits(payload):
                if p + 32 <= len(payload):
                    assert analyzer.predicate(payload, p, "F0") == (runtime._family(payload, p) in ("v0", "v1", "v2"))
    assert runtime.VARIANTS == {
        (0, bytes.fromhex("7b14ae47e17a84")): "v0",
        (0, bytes.fromhex("b81e85eb51b89e")): "v1",
        (1, bytes.fromhex("7b14ae47e17a84")): "v2",
    }


@pytest.mark.parametrize("path,digest", GOLDEN["source_sha256"].items())
def test_current_runtime_source_unchanged(path, digest):
    assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == digest


@pytest.mark.parametrize("name,old", GOLDEN["fixtures"].items())
def test_candidate_output_and_all_semantics_unchanged(name, old):
    path = ROOT / "tests/samples/text" / name
    assert hashlib.sha256(path.read_bytes()).hexdigest() == old["fixture_file_sha256"]
    parsed, _ = parse_type3_clipboard_bytes_with_parser(hex_text_to_bytes(path.read_text()))
    encoded = json.dumps(
        _json_safe(asdict(parsed)), ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode()
    assert hashlib.sha256(encoded).hexdigest() == old["parser_result_sha256"]
    assert ("text_slot_run" in parsed.candidate_fields) == old["candidate_present"]


@pytest.mark.parametrize(
    "args,limit", [(("--json",), 100000), (("--json", "--details"), 100000), ((), 50000), (("--details",), 50000)]
)
def test_output_bounds(args, limit):
    assert len(run_cli(*args)) < limit


def test_details_preserve_results(analyzer, report):
    details = analyzer.build_report(details=True)
    details.pop("details")
    details["mode"] = "summary"
    assert details == report


def test_resource_failure_is_not_partial_success(analyzer, monkeypatch):
    monkeypatch.setitem(analyzer.LIMITS, "max_prefix_hits", 1)
    changed = analyzer.build_report()
    assert changed["warnings"]
    assert changed["answers"]["runtime_prefix_redesign_readiness"] == "not_ready"


def test_missing_control_blocks_review_readiness(analyzer):
    paths = [analyzer.SAMPLES / "text" / (n + ".txt") for n in analyzer.CONTROLLED[:-1]]
    changed = analyzer.build_report(paths)
    assert changed["warnings"]
    assert changed["answers"]["runtime_prefix_redesign_readiness"] == "not_ready"


def test_no_promotion_or_ownership(report):
    assert report["answers"]["runtime_prefix_redesign_readiness"] == "ready_for_rfc_review"
    assert report["answers"]["parser_safe"] is False
    assert report["answers"]["typed_widths"] is None
    assert report["answers"]["ownership"] == "unresolved"
    assert report["policy"]["anchor_ownership_used"] is False
    assert report["policy"]["runtime_parser_behavior"] == "not_modified"


def test_identity_is_complete_before_count_and_never_reprobed(analyzer, monkeypatch):
    captured = analyzer.read_capture(analyzer.SAMPLES / "text/text_slotstyle_a8_baseline.txt")
    original_predicate = analyzer.predicate
    original_count = analyzer.count_valid
    expected = sum(len(analyzer.raw_hits(p)) for p in captured["payloads"]) * len(analyzer.NAMES)
    calls = []
    phase = {"count_started": False}

    def predicate(payload, p, hypothesis):
        assert not phase["count_started"]
        calls.append((p, hypothesis))
        return original_predicate(payload, p, hypothesis)

    def count(payload, run):
        assert len(calls) == expected
        phase["count_started"] = True
        return original_count(payload, run)

    monkeypatch.setattr(analyzer, "predicate", predicate)
    monkeypatch.setattr(analyzer, "count_valid", count)
    repeated = analyzer.inspect_payloads(captured["payloads"])
    assert repeated["metrics"] == captured["metrics"]
    assert len(calls) == expected
