from __future__ import annotations

import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import struct
from types import SimpleNamespace

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
CLI_PATH = REPO_ROOT / "tools" / "analyze_text_anchor_shadow_mapping.py"


def _run(*args):
    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT / "src")}
    result = subprocess.run([sys.executable, str(CLI_PATH), *args], cwd=REPO_ROOT,
                            capture_output=True, text=True, env=env, timeout=60)
    assert result.returncode == 0, result.stderr
    return result.stdout


@pytest.fixture(scope="module")
def analyzer():
    spec = importlib.util.spec_from_file_location("anchor_shadow_test", CLI_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def report():
    raw = _run("--json")
    assert len(raw) < 100000
    assert len(raw.encode("utf-8")) < 100000
    return json.loads(raw)


def _parse(analyzer, fixture):
    blob = analyzer.visible._read_fixture(analyzer.TEXT_DIR / fixture)
    parsed, _ = analyzer.visible.parse_type3_clipboard_bytes_with_parser(blob)
    return blob, parsed, analyzer.visible._read_nodes(blob)


def test_default_text_mode_small():
    raw = _run()
    assert "Text Anchor Shadow Mapping" in raw
    assert "parser_safe=false" in raw
    assert len(raw) < 50000


def test_json_coverage_policy_provenance_and_strategies(report, analyzer):
    assert report["policy"] == {
        "scope": "phase_2a_shadow_mapping_analyzer_only", "parser_behavior": "not_modified",
        "ownership_assignment": "not_performed", "matched_chain_behavior": "unchanged_none",
        "active_anchor_behavior": "unchanged", "oracle_isolation": True,
    }
    assert report["warnings"] == []
    assert report["truncated"] is False
    assert {r["fixture"] for r in report["fixture_results"]} == set(analyzer.FIXTURES)
    assert len(report["fixture_results"]) == 13
    unknown = [r for r in report["fixture_results"] if r["order_control_status"] == "unknown"]
    assert len(unknown) == 4
    for row in report["fixture_results"]:
        assert row["actual_stored_order"] == "unresolved"
        assert row["intent_reporting"]["attempted_order_source"] == "yaml"
        if row in unknown:
            assert row["intent_reporting"]["attempted_selection_order"] == []
        assert len(row["candidate_provenance"]) == len(row["parser_chains"]) - 1
        for candidate in row["candidate_provenance"]:
            assert set(candidate) == {
                "candidate_index", "cproperty_node_ordinal", "cobdao_section_ordinal", "signature_match_ordinal",
                "cobdao_payload_relative_offset", "anchor_relative_to_cobdao", "candidate_anchor_mm", "signature_values",
            }
            assert candidate["anchor_relative_to_cobdao"] == 34
            assert candidate["signature_values"] == {"+12": 131072, "+56": 262144, "+108": 65536, "+112": 262144}
        assert len(row["structural_hypotheses"]) == 3
        for strategy in row["structural_hypotheses"]:
            assert strategy["parser_safe"] is False
            assert strategy["status"] in analyzer.STATUSES
            assert "evidence" in strategy and "unmet_dependencies" in strategy
            assert len(strategy["mapping_hypotheses"]) <= len(row["parser_chains"])
        assert all(c["outcome"] == "abstention" for c in row["comparisons"])
    serialized = json.dumps(report)
    for forbidden in ("stream_offset", "absolute_offset", "file_offset", "start_offset", "end_offset", "raw_hex"):
        assert forbidden not in serialized


def test_summary_keeps_conditional_comparisons_separate(report):
    for name, status in (("chain_order_pairing", "blocked"), ("payload_order", "unresolved"),
                         ("structural_linkage", "no_link_found")):
        summary = report["strategy_summary"][name]
        assert summary["evaluated"] == summary[status] == summary["abstention"] == 13
        assert summary["oracle_agreement"] == summary["oracle_contradiction"] == 0
        if name != "structural_linkage":
            assert summary["conditional_applicable_agreement"] == 10
            assert summary["conditional_applicable_contradiction"] == 3
    assert report["oracle_summary"]["candidate_anchor_equality"] == {
        "unique": 21, "ambiguous": 0, "none": 0, "unavailable": 0,
    }
    contradictions = {row["fixture"] for row in report["fixture_results"]
                      if any(c["condition_comparison"] == "agreement" and c["mapping_comparison"] == "contradiction"
                             for c in row["comparisons"][1]["conditional_results"])}
    assert contradictions == {"text_three_objects_grouped_order_cba.txt", "text_three_objects_not_grouped.txt",
                              "text_three_objects_not_grouped_mixed_color.txt"}


def test_cli_no_oracle_has_identical_structural_results(report):
    disabled = json.loads(_run("--json", "--no-oracle"))
    for enabled, off in zip(report["fixture_results"], disabled["fixture_results"]):
        assert enabled["structural_hypotheses"] == off["structural_hypotheses"]
        assert off["intent_reporting"] is None
        assert all(c["outcome"] == "oracle_unavailable" for c in off["comparisons"])


@pytest.mark.parametrize("fixture_index", range(13))
def test_full_parser_unchanged_and_structural_oracle_isolation(analyzer, fixture_index, monkeypatch):
    fixture = analyzer.FIXTURES[fixture_index]
    blob, parsed, nodes = _parse(analyzer, fixture)
    before = copy.deepcopy(parsed)
    nodes_before = copy.deepcopy(nodes)
    enabled = analyzer.analyze_parsed(parsed, nodes, fixture)

    def forbidden(*args, **kwargs):
        pytest.fail("disabled oracle must not load intent")

    monkeypatch.setattr(analyzer.visible, "_intent_metadata", forbidden)
    disabled = analyzer.analyze_parsed(parsed, nodes, "arbitrary_name.txt", oracle_enabled=False)
    assert analyzer._json(enabled["structural_hypotheses"]) == analyzer._json(disabled["structural_hypotheses"])
    assert parsed == before
    assert nodes == nodes_before
    again, _ = analyzer.visible.parse_type3_clipboard_bytes_with_parser(blob)
    assert again == before
    assert all(c["matched_chain"] is None and c["ownership"] == "unresolved"
               for c in parsed.candidate_fields["cproperty_anchor_candidates"])


def test_missing_intent_and_modified_active_anchors_cannot_affect_hypotheses(analyzer, tmp_path, monkeypatch):
    fixture = analyzer.FIXTURES[5]
    _, parsed, nodes = _parse(analyzer, fixture)
    enabled = analyzer.analyze_parsed(parsed, nodes, fixture)
    monkeypatch.setattr(analyzer.visible, "INTENT_DIR", tmp_path)
    missing = analyzer.analyze_parsed(parsed, nodes, fixture)
    assert missing["warnings"] and missing["order_control_status"] == "unknown"
    assert missing["structural_hypotheses"] == enabled["structural_hypotheses"]
    for chain in parsed.object_chains:
        chain.text_anchor = None
    changed = analyzer.analyze_parsed(parsed, nodes, fixture)
    assert changed["structural_hypotheses"] == enabled["structural_hypotheses"]
    assert all(r["status"] == "unavailable" for r in changed["oracle_results"]["anchor_equality"])


def test_structural_phase_finishes_before_intent_and_oracle(analyzer, monkeypatch):
    fixture = analyzer.FIXTURES[0]
    _, parsed, nodes = _parse(analyzer, fixture)
    events = []
    phase_a, intent, phase_b = analyzer.structural_phase, analyzer.visible._intent_metadata, analyzer.oracle_phase

    def structural(*args):
        result = phase_a(*args)
        events.append("structural_complete")
        return result

    def load_intent(*args):
        assert events == ["structural_complete"]
        events.append("intent")
        return intent(*args)

    def oracle(*args, **kwargs):
        assert events == ["structural_complete", "intent"]
        events.append("oracle")
        return phase_b(*args, **kwargs)

    monkeypatch.setattr(analyzer, "structural_phase", structural)
    monkeypatch.setattr(analyzer.visible, "_intent_metadata", load_intent)
    monkeypatch.setattr(analyzer, "oracle_phase", oracle)
    analyzer.analyze_parsed(parsed, nodes, fixture)
    assert events == ["structural_complete", "intent", "oracle"]


@pytest.mark.parametrize("anchors,enabled,expected", [
    ([0.0], True, "unique"), ([0.0, 0.0], True, "ambiguous"), ([3.0], True, "none"),
    ([0.0], False, "unavailable"), ([], True, "unavailable"), ([0.0000005], True, "unique"),
])
def test_anchor_oracle_outcomes(analyzer, anchors, enabled, expected):
    chains = [{"parser_chain_index": i, "current_active_anchor": {"x": x, "y": 0.0, "z": 0.0}}
              for i, x in enumerate(anchors)]
    result = analyzer.anchor_oracle({"x": 0.0, "y": 0.0, "z": 0.0}, chains, enabled=enabled)
    assert result["status"] == expected


def test_comparison_ambiguous_and_unavailable_are_not_agreements(analyzer):
    frozen = analyzer._json([{"strategy": "payload_order", "mapping_hypotheses": [
        {"if_cpar_owner_chain": 0, "candidate_order": [0], "remaining_chain_order": [1]}]}])
    for status, expected in (("ambiguous", "oracle_ambiguous"), ("unavailable", "oracle_unavailable")):
        oracles = {"anchor_equality": [{"candidate_index": 0, "status": status, "matching_chain_indices": []}],
                   "cparagraphe_anchor_equality": {"status": "unique", "matching_chain_indices": [0]}}
        result = analyzer.compare_frozen(frozen, oracles)[0]
        assert result["outcome"] == expected
        assert result["conditional_results"][0]["mapping_comparison"] == expected


def test_bounded_search_and_nonfactorial_generation(analyzer, monkeypatch):
    assert analyzer._conditional_pairings(list(range(8)), 9) == []
    _, parsed, nodes = _parse(analyzer, analyzer.FIXTURES[5])
    monkeypatch.setattr(analyzer, "MAX_SECTIONS", 1)
    result = analyzer.structural_phase(parsed, nodes)
    assert result["truncated"] is True
    for strategy in result["structural_hypotheses"]:
        assert strategy["mapping_hypotheses"] == []
        assert "bounded_analysis_incomplete" in strategy["unmet_dependencies"]


def test_output_budget_retains_summary_and_counts(analyzer, report):
    bounded = analyzer._bound_report(copy.deepcopy(report), limit=20000)
    assert bounded["truncated"] is True
    assert bounded["warnings"]
    assert bounded["strategy_summary"] == report["strategy_summary"]
    assert bounded["oracle_summary"] == report["oracle_summary"]
    assert len(analyzer._json(bounded)) < 20000
    assert len(bounded["fixture_results"]) == 13
    assert all("provenance_counts" in r for r in bounded["fixture_results"])


@pytest.mark.parametrize("relative,expected_hits", [(16, 1), (36, 0), (12, 0)])
def test_linkage_probe_excludes_anchor_and_signature_words(analyzer, relative, expected_hits):
    # Untyped integer coincidence in a synthetic local record is diagnostic only.
    node = SimpleNamespace(header=SimpleNamespace(class_name="CContour"), payload_offset=0,
                           payload=bytes(16) + struct.pack("<4I", 1, 1, 1, 1))
    chain = SimpleNamespace(source_payload_offset=32, source_stream_offset=32,
                            source_node_class="CContour", nodes=[node])
    parsed = SimpleNamespace(object_chains=[chain])
    payload = bytearray(128)
    struct.pack_into("<I", payload, relative, 1)
    evidence = analyzer._local_linkage(parsed, [(bytes(payload), 0)])
    assert evidence["untyped_coincidence_count"] == expected_hits
    assert evidence["candidate_words_scanned"] <= 30
    assert "not typed object identifiers" in evidence["interpretation"]


def test_provenance_ordinals_reset_for_each_cproperty_node(analyzer):
    _, parsed, nodes = _parse(analyzer, analyzer.FIXTURES[5])
    node = next(n for n in nodes if n.header.class_name == "CPropertyExtend")
    duplicate_nodes = [node, copy.deepcopy(node)]
    parser = analyzer.visible.Type3ChainParser()
    parsed.candidate_fields["cproperty_anchor_candidates"] = parser._extract_cproperty_anchor_candidates(duplicate_nodes)
    rows, _, truncated = analyzer._provenance(parsed, duplicate_nodes)
    assert not truncated
    assert [r["cproperty_node_ordinal"] for r in rows] == [0, 0, 1, 1]
    assert [r["signature_match_ordinal"] for r in rows] == [0, 1, 0, 1]
    assert [r["cobdao_section_ordinal"] for r in rows] == [1, 5, 1, 5]
