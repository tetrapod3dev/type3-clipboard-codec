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
CLI = ROOT / "tools/analyze_text_color_record.py"


def run_cli(*args):
    proc = subprocess.run([sys.executable, str(CLI), *args], cwd=ROOT,
                          env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
                          capture_output=True, timeout=30)
    assert proc.returncode == 0, proc.stderr.decode()
    return proc.stdout


@pytest.fixture(scope="module")
def analyzer():
    spec = importlib.util.spec_from_file_location("text_color_record_test", CLI)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def report():
    raw = run_cli("--json")
    assert len(raw) < 100000
    return json.loads(raw)


def table(value):
    return [dict(zip(value["columns"], row)) for row in value["rows"]]


def test_default_modes_and_policy(report, analyzer):
    assert len(run_cli()) < 50000
    markdown = run_cli("--markdown")
    assert len(markdown) < 50000 and b"| ---" in markdown
    assert report["policy"] == {"scope": "text_color_field_decoding_analysis_only",
        "parser_behavior": "not_modified", "decoder_behavior": "not_modified", "model_behavior": "not_modified",
        "color_ownership_assignment": "not_performed", "anchor_ownership_used": False,
        "mfc_parser_refactor": "not_performed", "oracle_isolation": True}
    assert {r["fixture"] for r in report["fixture_results"]} == set(analyzer.FIXTURES)
    assert len(report["fixture_results"]) == 14 and not report["warnings"]
    assert report["answers"]["color_ownership_readiness"] == "not_ready"
    assert "confirmed" not in json.dumps(report)


def test_all_candidates_reported_and_observed_best(report):
    rows = table(report["field_start_summary"])
    assert len(rows) == 19 * 4 * 3
    assert {r["record_relative_offset"] for r in rows} == set(range(0x83, 0x96))
    assert {r["decode_type"] for r in rows} == {"u8", "u16le", "u32le", "u32be"}
    assert report["answers"]["best_color_field_start"] == 0x8B
    assert report["answers"]["best_decode_type"] == "u32le"
    assert report["answers"]["best_palette_encoding"] == "RGB0"
    best = rows[report["field_start_summary"]["selection"]["best_candidate_indices"][0]]
    assert best["status"] == "strong_candidate"  # observed candidate, not parser semantics
    assert best["nonzero_palette_count"] == 86 and best["palette_decodable_count"] == 117
    comparison = next(r for r in rows if r["record_relative_offset"] == 0x8A and r["decode_type"] == "u32be" and r["palette_encoding"] == "BGR0")
    assert comparison["nonzero_palette_count"] == best["nonzero_palette_count"]
    assert not report["field_start_summary"]["selection"]["expected_colors_used"]


def test_primary_isolation_and_provenance(report):
    results = {r["fixture"]: r for r in report["fixture_results"]}
    for fixture, name, raw, count in (
        ("default_text.txt", "Black", "0x00000000", 9),
        ("text_color_army_green.txt", "Army Green", "0x0098CC98", 8),
        ("text_color_navy_blue.txt", "Navy Blue", "0x00CC6030", 8),
    ):
        result = results[fixture]
        obs = result["color_observations"]["CParagraphe"]
        assert obs["colors"] == {name: count} and obs["raw"][raw] == count
        records = table(result["structural"]["records"])
        assert len(records) == 10
        for i, record in enumerate(records):
            assert record["runtime_descriptor_schema"] == 6
            assert record["runtime_class_name"] == "CParagraphe"
            assert record["class_payload_start"] == record["runtime_descriptor_start"] + 6 + 11
            assert record["class_payload_relative_record_start"] == 47 + 204*i
            assert record["record_relative_color_offset"] == 0x8B
    assert report["answers"]["single_object_separation_status"] == "separated_with_unmapped_chunks"


def test_oracle_off_preserves_structure_and_selection(report):
    off = json.loads(run_cli("--json", "--no-oracle"))
    for a, b in zip(report["fixture_results"], off["fixture_results"]):
        assert a["structural"] == b["structural"]
        assert a["color_observations"] == b["color_observations"]
        assert b["oracle"] is None and b["comparison"] is None
    for key in ("runtime_descriptor_provenance", "field_start_summary", "color_record_summary", "cparagraphe_summary", "cpropertyextend_summary"):
        assert report[key] == off[key]
    for key in ("best_color_field_start", "best_decode_type", "best_palette_encoding", "field_decode_readiness"):
        assert report["answers"][key] == off["answers"][key]


def test_freeze_before_oracle_and_missing_intent(analyzer, monkeypatch, tmp_path):
    phase, reader = analyzer.structural_phase, analyzer.load_oracle
    completed = []
    def capture(*args):
        result = phase(*args)
        completed.append(analyzer.compact(result))
        return result
    def oracle(*args):
        assert len(completed) == 14
        return reader(*args)
    monkeypatch.setattr(analyzer, "structural_phase", capture)
    monkeypatch.setattr(analyzer, "load_oracle", oracle)
    before = analyzer.build_report()
    monkeypatch.setattr(analyzer, "structural_phase", phase)
    monkeypatch.setattr(analyzer, "load_oracle", reader)
    monkeypatch.setattr(analyzer, "INTENT_DIR", tmp_path)
    missing = analyzer.build_report()
    assert missing["field_start_summary"] == before["field_start_summary"]
    assert [r["structural"] for r in missing["fixture_results"]] == [r["structural"] for r in before["fixture_results"]]
    monkeypatch.setattr(analyzer, "load_oracle", lambda *_: pytest.fail("no-oracle read"))
    assert analyzer.build_report(oracle_enabled=False)["field_start_summary"] == before["field_start_summary"]


def test_changed_expected_colors_cannot_select_field(analyzer, monkeypatch):
    before = analyzer.build_report()
    monkeypatch.setattr(analyzer, "load_oracle", lambda _: {"colors": {"Invented Color": 7}, "object_count": 7, "grouping": "unknown"})
    after = analyzer.build_report()
    assert before["field_start_summary"] == after["field_start_summary"]
    assert after["answers"]["best_color_field_start"] == 0x8B
    assert after["answers"]["single_object_separation_status"] == "not_separated"


def test_unordered_multisets_preserve_multiplicity(analyzer, report):
    assert analyzer.compare_multiset({"Navy Blue": 1, "Army Green": 1}, {"Army Green": 1, "Navy Blue": 1})["unordered_color_multiset_match"]
    extra = analyzer.compare_multiset({"Army Green": 8, "Navy Blue": 1}, {"Army Green": 1, "Navy Blue": 1})
    assert not extra["unordered_color_multiset_match"] and extra["expected_color_presence"]
    mixed = [r for r in report["fixture_results"] if r["oracle"] and len(r["oracle"]["colors"]) > 1]
    assert len(mixed) == 4
    assert all(not r["comparison"]["CParagraphe"]["expected_color_presence"] for r in mixed)
    assert all(r["comparison"]["combined_presence_control"]["expected_color_presence"] for r in mixed)
    assert all(not r["comparison"]["combined_presence_control"]["unordered_color_multiset_match"] for r in mixed)


def test_group_contrasts_and_cproperty_bounds(report):
    contrasts = report["oracle_summary"]["contrasts"]
    assert contrasts[0]["record_counts"] == [10, 10]
    assert contrasts[0]["changed_traversal_slots"] == [0]
    assert contrasts[0]["decoded_color_multisets"] == [{"Army Green": 8}, {"Army Green": 8}]
    assert contrasts[1]["record_counts"] == [10, 14]
    assert contrasts[1]["changed_traversal_slots"] is None
    assert contrasts[2]["record_counts"] == [10, 10] and contrasts[3]["record_counts"] == [6, 6]
    assert report["cpropertyextend_summary"]["status"] == "no_stable_cpropertyextend_color_field_found"
    for f in report["fixture_results"]:
        for row in table(f["structural"]["cpropertyextend"]):
            assert row["local_field_relative_candidate_offset"] == 30
            assert len(row["bounded_probe_u32le_at_24_to_30"]) == 7


def test_parser_unchanged_and_offset_shift_independence(analyzer):
    from type3_clipboard_codec import parse_type3_clipboard_bytes_with_parser
    sources = {p: p.read_bytes() for p in (ROOT / "src").rglob("*.py")}
    for name in analyzer.FIXTURES:
        blob = analyzer.hex_text_to_bytes((analyzer.TEXT_DIR / name).read_text())
        parsed, _ = parse_type3_clipboard_bytes_with_parser(blob)
        before = copy.deepcopy(parsed)
        structure = analyzer.structural_phase(blob)
        shifted = analyzer.structural_phase(b"diagnostic prefix bytes!" + blob)
        assert [r["values"] for r in structure["records"]] == [r["values"] for r in shifted["records"]]
        assert structure["records"][0]["descriptor"]["runtime_descriptor_start"] != shifted["records"][0]["descriptor"]["runtime_descriptor_start"]
        assert analyzer.structural_candidates([structure]) == analyzer.structural_candidates([shifted])
        again, _ = parse_type3_clipboard_bytes_with_parser(blob)
        assert before == parsed == again
        assert all(c["matched_chain"] is None for c in parsed.candidate_fields.get("cproperty_anchor_candidates", []))
    assert all(p.read_bytes() == original for p, original in sources.items())


def test_narrow_scan_and_zero_only_abstention(analyzer):
    # Synthetic scanner-readable paragraph; no fixture is created.
    prefix = b"\0\0\0\0\x01\0\xff\xff\x06\x00\x0b\x00CParagraphe"
    body = bytearray(47 + 204)
    before = analyzer.structural_phase(prefix + body)
    for i in range(47, 47+0x83):
        body[i] = 0x55
    after = analyzer.structural_phase(prefix + body)
    assert before["records"][0]["values"] == after["records"][0]["values"]
    assert analyzer.structural_candidates([before])[1] == []


def test_fixture_option_and_missing(report):
    selected = json.loads(run_cli("--json", "--fixture", "default_text.txt", "--fixture", "text_color_army_green.txt"))
    assert len(selected["fixture_results"]) == 2
    assert selected["answers"]["single_object_separation_status"] == "unavailable"
    missing = json.loads(run_cli("--json", "--fixture", "missing.txt"))
    assert missing["warnings"] and not missing["fixture_results"]
