from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


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
