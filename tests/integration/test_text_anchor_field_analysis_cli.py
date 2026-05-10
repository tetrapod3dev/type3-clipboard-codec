from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
CLI_PATH = REPO_ROOT / "tools" / "analyze_text_anchor_field_candidates.py"


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


def test_text_anchor_field_analysis_cli_text_mode() -> None:
    result = _run([])
    assert result.returncode == 0, result.stderr
    out = result.stdout
    assert "Text Anchor Field Candidate Analysis" in out
    assert "default_text.txt vs text_origin_0_0.txt" in out
    assert "default_text.txt vs text_origin_offset.txt" in out
    assert "text_origin_0_0.txt vs text_origin_offset.txt" in out
    assert "class-relative + record-relative evidence" in out
    assert "policy.absolute_offset: diagnostic_only" in out
    assert "baseline_midpoint is current recovery path" in out
    assert "[Multi-object Chain Direct Anchor Summary]" in out
    assert "text_group_same_color_two_objects.txt" in out
    assert "text_group_mixed_color_two_objects.txt" in out
    assert "text_two_objects_mixed_color_not_grouped.txt" in out
    assert "chain=0" in out and "chain=1" in out


def test_text_anchor_field_analysis_cli_json_mode() -> None:
    result = _run(["--json"])
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)

    assert payload["policy"]["absolute_offset"] == "diagnostic_only"
    assert payload["policy"]["parser_update"] == "not_applied"
    assert "fixtures" in payload
    assert "pairwise_comparisons" in payload
    assert "anchor_candidate_summary" in payload
    assert "best_candidate_summary" in payload

    pair_names = {(p["left_fixture"], p["right_fixture"]) for p in payload["pairwise_comparisons"]}
    assert ("default_text.txt", "text_origin_0_0.txt") in pair_names
    assert ("default_text.txt", "text_origin_offset.txt") in pair_names
    assert ("text_origin_0_0.txt", "text_origin_offset.txt") in pair_names

    assert any(f["fixture"] == "text_group_same_color_two_objects.txt" for f in payload["multi_object_verification"])
    assert any(f["fixture"] == "text_group_mixed_color_two_objects.txt" for f in payload["multi_object_verification"])
    assert any(f["fixture"] == "text_two_objects_mixed_color_not_grouped.txt" for f in payload["multi_object_verification"])

    first_pair = payload["pairwise_comparisons"][0]["node_pairs"][0]["diff_rows_top"][0]
    assert "class_payload_relative_offset" in first_pair
    assert "record_relative_offset" in first_pair

    same_color = next(f for f in payload["multi_object_verification"] if f["fixture"] == "text_group_same_color_two_objects.txt")
    assert "chain_direct_anchor_summary" in same_color
    assert len(same_color["chain_direct_anchor_summary"]) == 2
    assert all("associated_cparagraphe_node_index" in row for row in same_color["chain_direct_anchor_summary"])
    assert all("direct_triple_offsets" in row for row in same_color["chain_direct_anchor_summary"])
