from __future__ import annotations

import copy
import importlib.util
import json
import os
from pathlib import Path
import struct
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
CLI = ROOT / "tools" / "analyze_text_cparagraphe_owner_structure.py"


def run_cli(*args):
    result = subprocess.run([sys.executable, str(CLI), *args], cwd=ROOT,
                            env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
                            capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stderr
    return result.stdout


@pytest.fixture(scope="module")
def analyzer():
    spec = importlib.util.spec_from_file_location("cpar_owner_test", CLI)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def report():
    raw = run_cli("--json")
    assert len(raw.encode("utf-8")) < 100000
    return json.loads(raw)


def parse(analyzer, index):
    fixture = analyzer.FIXTURES[index]
    blob = analyzer.visible._read_fixture(analyzer.TEXT_DIR / fixture)
    parsed, _ = analyzer.visible.parse_type3_clipboard_bytes_with_parser(blob)
    return fixture, blob, parsed, analyzer.visible._read_nodes(blob)


def test_text_mode_small():
    text = run_cli()
    assert len(text.encode("utf-8")) < 50000
    assert "CParagraphe Owner Structure" in text
    assert "no_parser_safe_cparagraphe_owner_rule_found" in text


def test_json_policy_coverage_provenance(report, analyzer):
    assert report["policy"] == {
        "scope": "cparagraphe_owner_structural_analysis_only", "parser_behavior": "not_modified",
        "ownership_assignment": "not_performed", "oracle_isolation": True, "active_anchor_behavior": "unchanged",
    }
    assert report["warnings"] == []
    assert not report["truncated"]
    assert {r["fixture"] for r in report["fixture_results"]} == set(analyzer.FIXTURES)
    unknown = [r for r in report["fixture_results"] if r["order_control_status"] == "unknown"]
    assert len(unknown) == 4
    for result in report["fixture_results"]:
        assert result["actual_stored_order"] == "unresolved"
        s = result["structural"]
        assert s["hypotheses"]
        assert len(s["cparagraphe_provenance"]) == 1
        cpar = s["cparagraphe_provenance"][0]
        assert cpar["cparagraphe_node_ordinal"] == 0
        assert cpar["node_traversal_ordinal"] == 1
        assert cpar["preceding_node_class"] == "CZone"
        assert cpar["following_node_class"] == "CCourbe"
        assert cpar["direct_anchor_local_offset"] == 158
        assert set(cpar["direct_anchor_mm"]) == {"x", "y", "z"}
        assert len(cpar["bounded_structural_fields"]) == 16
        for h in s["hypotheses"]:
            assert h["parser_safe"] is False
            assert h["status"] in {"supported", "contradicted", "unresolved", "no_signal", "blocked"}
            assert set(("structural_inputs", "evidence", "fixture_support_count", "fixture_conflict_count",
                        "fixture_abstention_count")).issubset(h)
        assert set(result["oracle"]) == {"matching_chain_indices", "status", "tolerance", "source"}
    for h in report["hypothesis_summary"]:
        assert h["parser_safe"] is False
    for forbidden in ("absolute_offset", "file_offset", "stream_offset", "start_offset", "end_offset", "hex_dump"):
        assert forbidden not in json.dumps(report)


def test_findings_and_specific_contrasts(report):
    summary = {h["name"]: h for h in report["hypothesis_summary"]}
    adjacent = summary["nearest_following_chain_source"]
    assert adjacent["fixture_support_count"] == 13
    assert adjacent["fixture_conflict_count"] == 0
    assert adjacent["evidence"]["structural_status_counts"] == {"unresolved": 13}
    assert summary["first_parser_chain_control"]["fixture_support_count"] == 8
    assert summary["first_parser_chain_control"]["fixture_conflict_count"] == 5
    for name in ("exclusive_cpar_node_membership", "local_shared_identifier", "layout_only_owner"):
        assert summary[name]["fixture_abstention_count"] == 13
    assert report["oracle_summary"] == {"unique": 13, "ambiguous": 0, "none": 0, "unavailable": 0}
    by_name = {r["fixture"]: r for r in report["fixture_results"]}
    for name, owner, length, sections in (
        ("text_three_objects_grouped_order_abc.txt", 0, 2290, 9),
        ("text_three_objects_grouped_order_cba.txt", 2, 1330, 9),
        ("text_three_objects_not_grouped.txt", 2, 1330, 11),
        ("text_three_objects_not_grouped_mixed_color.txt", 2, 1330, 11),
        ("text_three_objects_grouped_order_abc_content_variation.txt", 0, 1810, 9),
    ):
        r = by_name[name]
        s = r["structural"]
        assert s["hypotheses"][0]["possible_chain_indices"] == [owner]
        assert s["parser_chain_provenance"][owner]["source_node_class"] == "CContour"
        assert s["cparagraphe_provenance"][0]["payload_length"] == length
        assert s["cproperty_section_layout"][0]["cobdao_section_count"] == sections
    content = by_name["text_three_objects_grouped_order_abc_content_variation.txt"]
    assert content["structural"]["parser_chain_provenance"][0]["text_candidate"] == "Type3"
    assert content["attempted_selection_order"][0]["text"] == "HELLO"


def test_local_integer_signal_is_nonunique(report):
    for result in report["fixture_results"]:
        s = result["structural"]
        probe = s["cparagraphe_provenance"][0]["identifier_probe"]
        assert not probe["typed_identifier_found"]
        assert probe["shared_nonzero_field_count"] == 1
        match = probe["field_matches"][0]
        assert match["payload_relative_offset"] == 138 and match["u32le"] == 2
        assert match["chain_reference_indices"] == list(range(s["inventory_counts"]["parser_chains"]))
        assert match["candidate_section_indices"] == []


def test_no_oracle_cli_preserves_entire_structural_output(report):
    disabled = json.loads(run_cli("--json", "--no-oracle"))
    for enabled, off in zip(report["fixture_results"], disabled["fixture_results"]):
        assert enabled["structural"] == off["structural"]
        assert off["oracle"] is None
        assert off["attempted_selection_order"] == []
    assert disabled["structural_field_summary"] == report["structural_field_summary"]
    assert disabled["adjacency_summary"] == report["adjacency_summary"]


@pytest.mark.parametrize("index", range(13))
def test_parser_unchanged_and_intent_independent(analyzer, index, monkeypatch):
    fixture, blob, parsed, nodes = parse(analyzer, index)
    original, original_nodes = copy.deepcopy(parsed), copy.deepcopy(nodes)
    enabled = analyzer.analyze_parsed(parsed, nodes, fixture)

    def forbidden(*args, **kwargs):
        pytest.fail("no-oracle must never load intent")

    monkeypatch.setattr(analyzer.visible, "_intent_metadata", forbidden)
    disabled = analyzer.analyze_parsed(parsed, nodes, "unrelated_name.txt", oracle_enabled=False)
    assert analyzer.compact(enabled["structural"]) == analyzer.compact(disabled["structural"])
    assert parsed == original and nodes == original_nodes
    again, _ = analyzer.visible.parse_type3_clipboard_bytes_with_parser(blob)
    assert again == original
    assert all(c["matched_chain"] is None for c in parsed.candidate_fields["cproperty_anchor_candidates"])


def test_all_structures_frozen_before_first_intent_read(analyzer, monkeypatch):
    phase, reader = analyzer.structural_phase, analyzer.visible._intent_metadata
    completed = []

    def inventory(*args):
        result = phase(*args)
        completed.append(analyzer.compact(result))
        return result

    def intent(*args):
        assert len(completed) == 13
        return reader(*args)

    monkeypatch.setattr(analyzer, "structural_phase", inventory)
    monkeypatch.setattr(analyzer.visible, "_intent_metadata", intent)
    analyzer.build_report()


def test_missing_intent_and_changed_baseline_cannot_select_owner(analyzer, monkeypatch, tmp_path):
    fixture, _, parsed, nodes = parse(analyzer, 6)
    before = analyzer.analyze_parsed(parsed, nodes, fixture)
    monkeypatch.setattr(analyzer.visible, "INTENT_DIR", tmp_path)
    for chain in parsed.object_chains:
        chain.text_anchor = None
    after = analyzer.analyze_parsed(parsed, nodes, fixture)
    assert after["structural"] == before["structural"]
    assert after["warnings"] and after["oracle"] is None


def test_local_window_does_not_mine_coordinate_bytes(analyzer):
    payload = bytearray(214)
    before = analyzer._local_fields(payload)
    struct.pack_into("<ddd", payload, 158, 101.0, 202.0, 303.0)
    assert analyzer._local_fields(payload) == before
    assert len(before) == 16


def test_source_adjacency_changes_without_consulting_oracle(analyzer):
    fixture, _, parsed, nodes = parse(analyzer, 5)
    before = analyzer.structural_phase(parsed, nodes)
    # Reorder the supplied parser chains only: source provenance, not chain zero,
    # determines the same source-node hypothesis under a new chain index.
    parsed.object_chains.reverse()
    after = analyzer.structural_phase(parsed, nodes)
    assert before["hypotheses"][0]["possible_chain_indices"] == [0]
    assert after["hypotheses"][0]["possible_chain_indices"] == [2]


def test_shared_source_tie_does_not_force_owner(analyzer):
    _, _, parsed, nodes = parse(analyzer, 0)
    parsed.object_chains = [parsed.object_chains[0], copy.deepcopy(parsed.object_chains[0])]
    frozen = analyzer.compact(analyzer.structural_phase(parsed, nodes))
    assert json.loads(frozen)["hypotheses"][0]["possible_chain_indices"] == [0, 1]
    comparisons = analyzer.compare_frozen(frozen, {"status": "unique", "matching_chain_indices": [0]})
    assert comparisons[0]["outcome"] == "abstention"


def test_missing_cpar_and_bounded_inventory_remain_unresolved(analyzer, monkeypatch):
    _, _, parsed, nodes = parse(analyzer, 5)
    absent = analyzer.structural_phase(parsed, [n for n in nodes if n.header.class_name != "CParagraphe"])
    assert absent["hypotheses"][0]["status"] == "blocked"
    assert analyzer.oracle_phase(parsed, analyzer.compact(absent), enabled=True) is None
    monkeypatch.setattr(analyzer, "MAX_NODES", 2)
    bounded = analyzer.structural_phase(parsed, nodes)
    assert bounded["truncated"]
    assert bounded["hypotheses"][0]["possible_chain_indices"] == []


def test_output_budget_retains_summaries(analyzer, report):
    bounded = analyzer.bound_report(copy.deepcopy(report), limit=30000)
    assert bounded["truncated"] and bounded["warnings"]
    assert len(analyzer.compact(bounded).encode("utf-8")) < 30000
    assert bounded["hypothesis_summary"] == report["hypothesis_summary"]
    assert bounded["structural_field_summary"] == report["structural_field_summary"]
