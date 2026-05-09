import json
import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
CLI_PATH = REPO_ROOT / "tools" / "text_fixture_inventory.py"


def _run_cli(args: list[str]) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO_ROOT / "src")
    return subprocess.run(
        [sys.executable, str(CLI_PATH), *args],
        text=True,
        capture_output=True,
        cwd=str(REPO_ROOT),
        env=env,
        timeout=60,
    )


def test_text_fixture_inventory_text_mode_contains_core_fields():
    result = _run_cli([])
    assert result.returncode == 0, result.stderr
    assert "Type3 Text Fixture Inventory" in result.stdout
    assert "[default_text.txt]" in result.stdout
    assert "has: CZone=True" in result.stdout
    assert "CParagraphe=True" in result.stdout
    assert "parsed_chain_candidate_count:" in result.stdout
    assert "fixture_intent_text:" in result.stdout
    assert "parser_text_candidate:" in result.stdout
    assert "anchor_parse_method:" in result.stdout


def test_text_fixture_inventory_json_mode_is_valid_and_includes_text_candidates():
    result = _run_cli(["--json"])
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert isinstance(payload, list)
    default_entry = next(item for item in payload if item["file"] == "default_text.txt")
    assert default_entry["has_CParagraphe"] is True
    assert "abcdefg" in (default_entry.get("visible_text_candidates") or [])
    assert default_entry["fixture_intent_anchor"] == {"x": 111.111, "y": 222.222, "z": 0.0}
    assert default_entry["anchor_parse_method"] in {"baseline_midpoint", "bbox_center_fallback", "direct_field_candidate", "unknown"}
    assert "text_confidence" in default_entry
    assert "font_confidence" in default_entry
    assert "anchor_confidence" in default_entry
    assert "color_confidence" in default_entry


def test_text_fixture_inventory_markdown_mode_has_expected_vs_detected_columns():
    result = _run_cli(["--markdown"])
    assert result.returncode == 0, result.stderr
    assert "fixture_intent_text" in result.stdout
    assert "parser_text_candidate" in result.stdout
    assert "fixture_intent_color" in result.stdout
    assert "parser_color_candidate" in result.stdout


def test_text_fixture_inventory_json_reports_bold_fixture_status():
    result = _run_cli(["--json"])
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    item = next(row for row in payload if row["file"] == "text_font_arial_bold.txt")
    assert item["parser_text_candidate"] == "abcdefg"
    assert item["parsed_chain_candidate_count"] == 1
    assert item["recapture_required"] is False
