from __future__ import annotations

import json
import os
import subprocess
import sys
import runpy
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
CLI_PATH = REPO_ROOT / "tools" / "analyze_text_visible_ownership.py"


def _run(args: list[str]) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO_ROOT / "src")
    return subprocess.run(
        [sys.executable, str(CLI_PATH), *args],
        text=True,
        capture_output=True,
        cwd=str(REPO_ROOT),
        env=env,
        timeout=180,
    )


def test_text_visible_ownership_analysis_cli_text_mode() -> None:
    result = _run([])
    assert result.returncode == 0, result.stderr
    out = result.stdout
    assert "Text Visible Ownership Analysis" in out
    assert "Fixture Summary Table" in out
    assert len(out) < 50000


def test_text_visible_ownership_analysis_cli_json_mode() -> None:
    result = _run(["--json"])
    assert result.returncode == 0, result.stderr
    assert len(result.stdout) < 100000
    payload = json.loads(result.stdout)

    assert payload["policy"]["parser_behavior"] == "not_modified"
    assert payload["answers"]["parser_behavior"] == "not_modified"
    assert "fixture_summaries" in payload
    assert "chain_details" in payload
    assert "missing_fixtures" in payload

    fixture_names = {row["fixture"] for row in payload["fixture_summaries"]}
    expected = {
        "text_group_same_color_two_objects.txt",
        "text_group_mixed_color_two_objects.txt",
        "text_two_objects_mixed_color_not_grouped.txt",
        "text_two_objects_same_color_not_grouped.txt",
        "text_two_objects_not_grouped_selection_reversed.txt",
        "text_three_objects_grouped_order_abc.txt",
        "text_three_objects_grouped_order_cba.txt",
        "text_three_objects_not_grouped.txt",
        "text_three_objects_grouped_order_abc_mixed_color.txt",
        "text_three_objects_not_grouped_mixed_color.txt",
        "text_three_objects_grouped_order_abc_height_30mm.txt",
        "text_three_objects_grouped_order_abc_font_arial_bold.txt",
        "text_three_objects_grouped_order_abc_content_variation.txt",
    }
    available_expected = expected - set(payload["missing_fixtures"])
    assert available_expected.issubset(fixture_names)

    by_name = {row["fixture"]: row for row in payload["fixture_summaries"]}
    assert payload["intent_metadata_summary"] == {
        "total_fixtures": 13, "with_yaml_metadata": 13, "missing_metadata": 0,
        "unknown_order_count": 4, "attempted_order_count": 9, "controlled_observed_count": 0,
    }
    assert payload["missing_intent_files"] == []
    assert payload["missing_fixtures"] == []
    assert payload["warnings"] == []
    for row in by_name.values():
        assert row["actual_stored_order"] == "unresolved"
        assert row["attempted_order_source"] == "yaml"
        assert row["normalized_intent_metadata"]["schema_version"] == 1
        assert row["normalized_intent_metadata"]["actual_stored_order"] == "unresolved"
        assert row["cproperty_anchor_candidate_count"] == (2 if "three_objects" in row["fixture"] else 1)
    for fixture, grouping in {
        "text_group_same_color_two_objects.txt": "grouped",
        "text_group_mixed_color_two_objects.txt": "grouped",
        "text_two_objects_mixed_color_not_grouped.txt": "not_grouped",
        "text_two_objects_same_color_not_grouped.txt": "not_grouped",
    }.items():
        row = by_name[fixture]
        assert row["grouping"] == grouping
        assert row["order_control_status"] == "unknown"
        assert row["normalized_intent_metadata"]["attempted_selection_order"] == []
        assert row["attempted_order"] is None
    assert by_name["text_three_objects_grouped_order_cba.txt"]["attempted_order"] == ["XYZ", "1234567890", "abcdefg"]
    assert by_name["text_two_objects_not_grouped_selection_reversed.txt"]["attempted_order"] == ["1234567890", "abcdefg"]
    if "text_three_objects_grouped_order_abc_content_variation.txt" in by_name:
        row = by_name["text_three_objects_grouped_order_abc_content_variation.txt"]
        assert row["parser_chain_text_order"]
        merged = " ".join(str(x) for x in row["parser_chain_text_order"])
        assert "Type3" in merged
        assert "9876543210" in merged
        assert "HELLO" in merged

    if "text_three_objects_grouped_order_abc.txt" in by_name and "text_three_objects_grouped_order_cba.txt" in by_name:
        abc = by_name["text_three_objects_grouped_order_abc.txt"]
        cba = by_name["text_three_objects_grouped_order_cba.txt"]
        assert abc["attempted_order"] is not None
        assert cba["attempted_order"] is not None
        assert abc["cparagraphe_owner_text"] is not None
        assert cba["cparagraphe_owner_text"] is not None


def test_text_visible_ownership_analysis_cli_markdown_mode() -> None:
    result = _run(["--markdown"])
    assert result.returncode == 0, result.stderr
    out = result.stdout
    assert "# Text Visible Ownership Analysis" in out
    assert "## Fixture Summary Table" in out
    assert "| fixture | grouping | attempted_order |" in out


@pytest.fixture
def analyzer():
    return runpy.run_path(str(CLI_PATH))


@pytest.mark.parametrize("block", [
    "", "```yaml\nintent_metadata: [\n```\n",
    "```yaml\nintent_metadata:\n  schema_version: 99\n```\n",
])
def test_metadata_fallback_warns(analyzer, tmp_path, block):
    reader = analyzer["_intent_metadata"]
    reader.__globals__["INTENT_DIR"] = tmp_path
    path = tmp_path / "text_two_objects_same_color_not_grouped.md"
    path.write_text(block + "- text content: first|second\n- attempted selection order: B -> A\n", encoding="utf-8")
    meta = reader(path.with_suffix(".txt").name)
    assert meta["warnings"]
    assert meta["attempted_order_source"] == "loose_text"
    assert meta["attempted_selection_order"] == ["second", "first"]
    assert meta["actual_stored_order"] == "unresolved"
    path.write_text("- attempted selection order: unknown\n", encoding="utf-8")
    meta = reader(path.with_suffix(".txt").name)
    assert meta["attempted_order_source"] == "filename_or_unknown"
    assert meta["order_control_status"] == "unknown"
    assert meta["attempted_selection_order"] is None


def test_missing_intent_and_payload_do_not_fail(analyzer, tmp_path):
    builder = analyzer["_build_report"]
    builder.__globals__["INTENT_DIR"] = tmp_path
    builder.__globals__["TEXT_DIR"] = tmp_path
    report = builder()
    assert len(report["missing_intent_files"]) == 13
    assert len(report["missing_fixtures"]) == 13
    assert report["intent_metadata_summary"]["total_fixtures"] == 0


def test_intent_changes_only_reporting(analyzer, tmp_path):
    fixture = "text_three_objects_grouped_order_abc.txt"
    reporter = analyzer["_fixture_report"]
    before = reporter(fixture)
    path = analyzer["INTENT_DIR"] / fixture.replace(".txt", ".md")
    content = path.read_text(encoding="utf-8")
    # Contradict both loose notes and payload text using valid YAML.
    (tmp_path / path.name).write_text(content.replace("text: abcdefg", "text: reporting-only"), encoding="utf-8")
    reporter.__globals__["INTENT_DIR"] = tmp_path
    after = reporter(fixture)
    assert after["attempted_selection_order"][0] == "reporting-only"
    for key in ("parser_chain_text_order", "parser_chain_anchor_order", "chain_details",
                "cproperty_anchor_candidate_count", "cproperty_anchor_ownership_status"):
        assert before[key] == after[key]


@pytest.mark.parametrize("field,value", [
    ("object_count", True), ("grouping", []), ("order_control_status", "confirmed"),
    ("actual_stored_order", "ABC"), ("attempted_selection_order", []), ("notes", "bad"),
])
def test_invalid_schema_rejected(analyzer, field, value):
    meta = analyzer["_intent_metadata"]("text_three_objects_grouped_order_abc.txt")["normalized_intent_metadata"]
    meta[field] = value
    with pytest.raises(ValueError):
        analyzer["_validate_intent_metadata"](meta)
