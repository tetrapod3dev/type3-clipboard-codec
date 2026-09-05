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
CLI = ROOT / "tools/analyze_text_color_field_boundary.py"


def run_cli(*args):
    result = subprocess.run([sys.executable, str(CLI), *args], cwd=ROOT,
                            env={**os.environ, "PYTHONPATH": str(ROOT / "src")}, capture_output=True, timeout=30)
    assert result.returncode == 0, result.stderr.decode()
    return result.stdout


@pytest.fixture(scope="module")
def analyzer():
    spec = importlib.util.spec_from_file_location("color_boundary_test", CLI)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def report():
    raw = run_cli("--json")
    assert len(raw) < 100000
    return json.loads(raw)


def chunks(result):
    table = result["structural"]["chunks"]
    return [dict(zip(table["columns"], row)) for row in table["rows"]]


def prepare(analyzer):
    return [(name, analyzer.compact(analyzer.extract_structure(analyzer.color.hex_text_to_bytes(
        (analyzer.TEXT_DIR / name).read_text())))) for name in analyzer.PRIMARY]


def test_modes_policy_and_coverage(report, analyzer):
    assert len(run_cli()) < 50000 and len(run_cli("--markdown")) < 50000
    assert b"Text Color Field Boundary" in run_cli()
    assert report["policy"] == {"scope": "text_color_field_boundary_analysis_only",
        "parser_behavior": "not_modified", "ownership_assignment": "not_performed",
        "anchor_ownership_used": False, "mfc_refactor": "not_performed", "oracle_isolation": True}
    assert len(report["fixture_results"]) == 11
    assert {f["fixture"] for f in report["fixture_results"]} == set(analyzer.FIXTURES)
    assert not report["warnings"]
    assert report["answers"]["color_ownership_readiness"] == "not_ready"
    assert not report["answers"]["candidate_parser_model_ready"]


def test_exact_primary_deltas_and_neighbor_zeros(report):
    delta = report["byte_delta_summary"]
    assert delta["aligned"] and delta["dominant_changed_span"] == [0x8B, 0x8D]
    assert len(delta["ordinals"]) == 10
    for ordinal in range(1, 9):
        for pair in delta["ordinals"][ordinal]["comparisons"]:
            assert pair["changed_byte_positions"] == [0x8B, 0x8C, 0x8D]
            assert pair["changed_contiguous_runs"] == [[0x8B, 0x8D]]
    header = delta["ordinals"][0]
    assert header["comparisons"][0]["changed_byte_positions"] == [0x8D, 0x8E]
    assert header["comparisons"][1]["changed_byte_positions"] == [0x8C, 0x8D, 0x8E]
    assert delta["ordinals"][9]["same_ordinal_window_stable_across_three"]
    boundary = report["boundary_hypothesis_summary"]["candidate_field_boundary"]
    assert boundary["start"] == 0x8B and boundary["width"] is None
    assert boundary["observed_changed_width"] == 3
    assert boundary["changed_byte_support"]["pair_comparisons"] == 24
    assert boundary["neighbor_stability"] == {"0x8A": {"values": {"0": 24}, "stable": True},
                                                "0x8E": {"values": {"0": 24}, "stable": True}}


def test_hypotheses_not_distinguished_by_zeros(report):
    hypotheses = report["boundary_hypothesis_summary"]["hypotheses"]
    assert [(h["name"], h["width"]) for h in hypotheses] == [("H1", 4), ("H2", 3), ("H3", 4), ("H4", None)]
    assert all(h["changed_byte_support"] == 24 for h in hypotheses[:3])
    assert all(not h["typed_boundary_established"] and h["analyzer_only"] for h in hypotheses)
    assert report["answers"]["best_field_width"] is None


def test_primary_roles_and_palette_match_explanation(report):
    role_rows = report["chunk_role_summary"]["fixtures"][:3]
    for row in role_rows:
        assert row["roles"] == {"header_like_chunk": [0], "repeated_color_record_candidate": list(range(1, 9)), "tail_like_chunk": [9]}
    assert [r["u32le_8B_palette_nonmatching_ordinals"] for r in role_rows] == [[9], [0, 9], [0, 9]]
    for result in report["fixture_results"][:3]:
        rows = chunks(result)
        assert rows[0]["role"] == "header_like_chunk" and rows[0]["prior_marker_context"]
        assert all(r["bounded_window_identical_except_changed_span"] for r in rows[1:9])
        assert rows[9]["same_ordinal_window_stable_across_primary"]
        assert all(r["record_identical_except_color_bytes"] is None for r in rows)
    assert chunks(report["fixture_results"][0])[0]["u32le_8B_palette_candidate"] == "Black"
    assert chunks(report["fixture_results"][1])[0]["u32le_8B_palette_candidate"] is None


def test_decodes_and_provenance(report):
    rows = chunks(report["fixture_results"][2])
    assert rows[1]["bytes_89_to_90"] == "00003060cc000000"
    assert rows[1]["candidate_RGB_bytes"] == "3060cc"
    view = report["limits"]["u32_view_columns"]
    assert view == [[138, "u32le"], [138, "u32be"], [139, "u32le"], [139, "u32be"], [140, "u32le"], [140, "u32be"]]
    assert rows[1]["u32_values"][2] == 0x00CC6030
    for f in report["fixture_results"]:
        provenance = f["structural"]["provenance"][0]
        assert provenance["class_payload_start"] == provenance["runtime_descriptor_start"] + 17
        assert provenance["runtime_descriptor_schema"] == 6
    assert report["limits"]["absolute_offset_role"] == "diagnostic_only"


def test_cross_fixture_alignment_does_not_invent_edits(report):
    rows = {r["fixture"]: r for r in report["cross_fixture_alignment_summary"]["fixtures"]}
    grouped = rows["text_group_mixed_color_two_objects.txt"]
    ungrouped = rows["text_two_objects_mixed_color_not_grouped.txt"]
    three = rows["text_three_objects_not_grouped_mixed_color.txt"]
    assert grouped["repeated_subranges"] == [[1, 8]]
    assert ungrouped["repeated_subranges"] == [[1, 11]]
    assert three["repeated_subranges"] == [[1, 4]]
    assert ungrouped["count_delta_vs_primary"] == 4 and three["count_delta_vs_primary"] == -4
    assert all(not r["unique_insert_delete_alignment"] for r in rows.values())
    roles = {r["fixture"]: r for r in report["chunk_role_summary"]["fixtures"]}
    assert roles["text_two_objects_mixed_color_not_grouped.txt"]["roles"]["tail_like_chunk"] == [12, 13]


def test_cproperty_reuses_only_30_and_remains_unready(report):
    side = report["cproperty_side_evidence"]
    assert side["status"] == "no_stable_cpropertyextend_color_field_found"
    assert all(s["field_relative_offset"] == 30 for f in side["fixtures"] for s in f["sections"])
    assert all(not f["stable_color_semantic_role"] for f in side["fixtures"])
    mixed = [r for r in report["oracle_summary"]["fixtures"] if r.get("mixed_intent")]
    assert len(mixed) == 4
    assert all(r["cproperty_covers_missing_color_names"] and r["missing_color_names_in_cparagraphe"] for r in mixed)


def test_no_oracle_identical_entire_structural_report(report):
    disabled = json.loads(run_cli("--json", "--no-oracle"))
    assert disabled.pop("oracle_summary") == {"enabled": False, "fixtures": []}
    enabled = copy.deepcopy(report)
    enabled.pop("oracle_summary")
    assert disabled == enabled


def test_all_structures_frozen_before_oracle_and_expected_values_cannot_select(analyzer, monkeypatch):
    phase, finish, reader = analyzer.extract_structure, analyzer.structural_report, analyzer.color.load_oracle
    inventories, frozen = [], []
    def capture(blob):
        data = phase(blob)
        inventories.append(analyzer.compact(data))
        return data
    def freeze(prepared):
        result = finish(prepared)
        frozen.append(analyzer.compact(result))
        return result
    def read(name):
        assert len(inventories) == 11 and len(frozen) == 1
        return reader(name)
    monkeypatch.setattr(analyzer, "extract_structure", capture)
    monkeypatch.setattr(analyzer, "structural_report", freeze)
    monkeypatch.setattr(analyzer.color, "load_oracle", read)
    before = analyzer.build_report()
    monkeypatch.setattr(analyzer.color, "load_oracle", lambda _: {"colors": {"Invented": 3}})
    after = analyzer.build_report()
    for key in ("fixture_results", "byte_delta_summary", "boundary_hypothesis_summary", "chunk_role_summary", "cross_fixture_alignment_summary", "answers"):
        assert after[key] == before[key]
    monkeypatch.setattr(analyzer.color, "load_oracle", lambda *_: pytest.fail("oracle loaded"))
    assert analyzer.build_report(oracle_enabled=False)["answers"] == before["answers"]


def test_no_palette_scoring_in_boundary_or_roles(analyzer, monkeypatch):
    prepared = prepare(analyzer)
    before = analyzer.structural_report(prepared)
    monkeypatch.setattr(analyzer.color, "color_name", lambda *_: None)
    after = analyzer.structural_report(prepared)
    assert after["boundary_hypothesis_summary"] == before["boundary_hypothesis_summary"]
    assert after["byte_delta_summary"] == before["byte_delta_summary"]
    assert [r["roles"] for r in after["chunk_role_summary"]["fixtures"]] == [r["roles"] for r in before["chunk_role_summary"]["fixtures"]]


def test_boundary_follows_changed_bytes_not_fixed_offset(analyzer):
    prepared = prepare(analyzer)
    moved = []
    for name, frozen in prepared:
        data = json.loads(frozen)
        for rec in data["paragraphs"][0]["records"][1:9]:
            old = rec["window"][11:14]
            rec["window"][11:15] = [0] + old
        moved.append((name, analyzer.compact(data)))
    result = analyzer.structural_report(moved)
    assert result["byte_delta_summary"]["dominant_changed_span"] == [0x8C, 0x8E]
    assert result["answers"]["best_field_start"] == 0x8C


def test_bounded_byte_window_and_full_record_equality_not_claimed(analyzer):
    blob = bytearray(analyzer.color.hex_text_to_bytes((analyzer.TEXT_DIR / analyzer.PRIMARY[1]).read_text()))
    before = analyzer.extract_structure(blob)
    payload = before["paragraphs"][0]["class_payload_start"]
    # Outside comparison window and prior fixed marker context: not examined.
    blob[payload + 47 + 204 + 20] ^= 0x55
    blob[payload + 47 + 204 + 180] ^= 0x55
    assert analyzer.extract_structure(blob) == before
    blob[payload + 47 + 204 + 0x98] ^= 0x55
    assert analyzer.extract_structure(blob) != before


def test_parser_sources_objects_and_prefix_shift(analyzer):
    from type3_clipboard_codec import parse_type3_clipboard_bytes_with_parser
    sources = {p: p.read_bytes() for p in (ROOT / "src").rglob("*.py")}
    for name in analyzer.FIXTURES:
        blob = analyzer.color.hex_text_to_bytes((analyzer.TEXT_DIR / name).read_text())
        parsed, _ = parse_type3_clipboard_bytes_with_parser(blob)
        snapshot = copy.deepcopy(parsed)
        structure = analyzer.extract_structure(blob)
        shifted = analyzer.extract_structure(b"diagnostic prefix bytes!" + blob)
        assert analyzer.only_records(structure) == analyzer.only_records(shifted)
        assert structure["paragraphs"][0]["runtime_descriptor_start"] != shifted["paragraphs"][0]["runtime_descriptor_start"]
        again, _ = parse_type3_clipboard_bytes_with_parser(blob)
        assert snapshot == parsed == again
        assert all(c["matched_chain"] is None for c in parsed.candidate_fields.get("cproperty_anchor_candidates", []))
    assert all(p.read_bytes() == original for p, original in sources.items())


def test_missing_primary_and_truncation_abstain(analyzer, monkeypatch):
    subset = json.loads(run_cli("--json", "--fixture", "default_text.txt"))
    assert not subset["byte_delta_summary"]["aligned"]
    assert subset["answers"]["best_field_start"] is None
    monkeypatch.setattr(analyzer, "MAX_RECORDS", 2)
    bounded = analyzer.build_report(oracle_enabled=False)
    assert bounded["warnings"] and bounded["answers"]["best_field_start"] is None
