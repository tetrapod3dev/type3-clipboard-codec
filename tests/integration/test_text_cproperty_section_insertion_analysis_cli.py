from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
CLI_PATH = REPO_ROOT / "tools" / "analyze_text_cproperty_anchor_context.py"


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


def test_section_insertion_analysis_text_output() -> None:
    result = _run([])
    assert result.returncode == 0, result.stderr
    out = result.stdout

    assert "[Section Alignment Analysis]" in out
    assert "[Selector Candidate Evaluation]" in out
    assert "text_two_objects_same_color_not_grouped.txt" in out
    assert "text_two_objects_not_grouped_selection_reversed.txt" in out
    assert "non-grouped section index 1 is a 148-byte inserted section candidate" in out
    assert "parser_readiness" in out
    assert "not_ready_analyzer_only" in out


def test_section_insertion_analysis_json_output() -> None:
    result = _run(["--json"])
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)

    alignment = payload["section_alignment_analysis"]
    grouped = alignment["grouped_same_vs_grouped_mixed"]
    non_grouped = alignment["grouped_vs_non_grouped"]
    non_grouped_all = {
        row["non_grouped_fixture"]: row
        for row in alignment["grouped_vs_non_grouped_all"]
    }

    assert grouped["section_count_equal"] is True
    assert grouped["left_section_count"] == 5
    assert grouped["right_section_count"] == 5
    assert grouped["anchor_bearing_section_index_equal"] is True
    assert grouped["index_alignment"][1]["left_role"] == "anchor_bearing_candidate"
    assert grouped["index_alignment"][1]["right_role"] == "anchor_bearing_candidate"

    assert non_grouped["grouped_section_count"] == 5
    assert non_grouped["non_grouped_section_count"] == 6
    assert non_grouped["section_count_delta"] == 1
    inserted = non_grouped["inserted_section_candidate"]
    assert inserted["section_index"] == 1
    assert inserted["cobdao_marker_offset"] == 438
    assert inserted["section_length_candidate"] == 148
    assert inserted["section_role_candidate"] == "non_anchor_candidate"
    assert inserted["cobdao_plus_34_triple_analysis"]["is_coordinate_like"] is False
    assert inserted["matched_chains"] == []

    shift = non_grouped["anchor_bearing_shift"]
    assert shift["grouped_anchor_cobdao_offset"] == 438
    assert shift["non_grouped_anchor_cobdao_offset"] == 586
    assert shift["cobdao_offset_delta"] == 148
    assert shift["grouped_anchor_hit_offset"] == 472
    assert shift["non_grouped_anchor_hit_offset"] == 620
    assert shift["anchor_hit_offset_delta"] == 148
    assert non_grouped["insertion_explanation_candidate"].startswith("non-grouped section index 1")

    assert set(non_grouped_all) == {
        "text_two_objects_mixed_color_not_grouped.txt",
        "text_two_objects_same_color_not_grouped.txt",
        "text_two_objects_not_grouped_selection_reversed.txt",
    }
    for row in non_grouped_all.values():
        assert row["grouped_section_count"] == 5
        assert row["non_grouped_section_count"] == 6
        assert row["section_count_delta"] == 1
        assert row["inserted_section_candidate"]["section_index"] == 1
        assert row["inserted_section_candidate"]["section_length_candidate"] == 148
        assert row["anchor_bearing_shift"]["cobdao_offset_delta"] == 148
        assert row["anchor_bearing_shift"]["anchor_hit_offset_delta"] == 148

    shifted = non_grouped["shifted_alignment_candidate"]
    assert shifted[1]["left_section_index"] == 1
    assert shifted[1]["right_section_index"] == 2
    assert shifted[1]["left_role"] == "anchor_bearing_candidate"
    assert shifted[1]["right_role"] == "anchor_bearing_candidate"

    selectors = {row["selector_candidate"]: row for row in payload["selector_candidate_evaluation"]}
    assert selectors["section_index"]["parser_safe"] is False
    assert selectors["CObDao_plus_34_coordinate_like"]["false_positive_risk"] == "high"
    assert selectors["section_alignment"]["parser_safe"] is False
    assert payload["answers"]["parser_readiness"] == "not_ready_analyzer_only"
    assert payload["answers"]["same_color_not_grouped_cobdao_section_count_is_6"] is True
    assert "not-grouped structure" in payload["answers"]["inserted_section_cause_current_conclusion"]
    assert payload["answers"]["selection_reversed_section_position_same"] is True
    assert payload["answers"]["cparagraphe_direct_anchor_ownership_by_fixture"][
        "text_two_objects_same_color_not_grouped.txt"
    ] == [1]
    assert payload["answers"]["cproperty_anchor_ownership_by_fixture"][
        "text_two_objects_same_color_not_grouped.txt"
    ] == [[0]]
    assert payload["answers"]["cparagraphe_direct_anchor_ownership_by_fixture"][
        "text_two_objects_not_grouped_selection_reversed.txt"
    ] == [0]
    assert payload["answers"]["cproperty_anchor_ownership_by_fixture"][
        "text_two_objects_not_grouped_selection_reversed.txt"
    ] == [[1]]


def test_section_insertion_analysis_markdown_output() -> None:
    result = _run(["--markdown"])
    assert result.returncode == 0, result.stderr
    out = result.stdout

    assert "## Section Alignment" in out
    assert "section count delta" in out
    assert "text_two_objects_same_color_not_grouped.txt" in out
    assert "text_two_objects_not_grouped_selection_reversed.txt" in out
    assert "## Selector Candidates" in out
    assert "section_alignment" in out
