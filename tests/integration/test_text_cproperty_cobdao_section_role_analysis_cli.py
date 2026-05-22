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


def test_cobdao_section_role_analysis_text_output() -> None:
    result = _run([])
    assert result.returncode == 0, result.stderr
    out = result.stdout

    assert "[CObDao section scan]" in out
    assert "role=anchor_bearing_candidate" in out
    assert "role=non_anchor_candidate" in out
    assert "coordinate_like=" in out
    assert "matches_chain=" in out
    assert "[Anchor-bearing vs Non-anchor Aggregate]" in out
    assert "not_ready_analyzer_only" in out


def test_cobdao_section_role_analysis_json_output() -> None:
    result = _run(["--json"])
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)

    aggregate = payload["anchor_bearing_vs_non_anchor_aggregate"]
    assert aggregate["section_count"] == 104
    assert aggregate["anchor_bearing_count"] == 21
    assert aggregate["non_anchor_count"] == 83
    assert aggregate["anchor_bearing_section_indexes"] == [1, 2, 5, 7]
    assert aggregate["anchor_bearing_coordinate_like_counts"] == {"True": 21}
    assert aggregate["anchor_bearing_matches_chain_counts"] == {"True": 21}
    assert aggregate["non_anchor_matches_chain_counts"] == {"False": 83}
    assert aggregate["coordinate_like_non_anchor_sections"]
    assert aggregate["ambiguous_non_anchor_sections"]
    assert "coordinate-like values also appear in some non-anchor sections" in aggregate[
        "features_that_do_not_distinguish_anchor_bearing_sections"
    ]
    assert payload["answers"]["parser_readiness"] == "not_ready_analyzer_only"

    by_name = {fixture["fixture"]: fixture for fixture in payload["fixtures"]}
    same_sections = by_name["text_group_same_color_two_objects.txt"]["cproperty_nodes"][0]["cobdao_sections"]
    nongrouped_sections = by_name["text_two_objects_mixed_color_not_grouped.txt"]["cproperty_nodes"][0]["cobdao_sections"]
    same_color_nongrouped_sections = by_name["text_two_objects_same_color_not_grouped.txt"]["cproperty_nodes"][0][
        "cobdao_sections"
    ]
    selection_reversed_sections = by_name["text_two_objects_not_grouped_selection_reversed.txt"]["cproperty_nodes"][0][
        "cobdao_sections"
    ]
    three_nongrouped_sections = by_name["text_three_objects_not_grouped.txt"]["cproperty_nodes"][0]["cobdao_sections"]
    grouped_abc_content_sections = by_name["text_three_objects_grouped_order_abc_content_variation.txt"][
        "cproperty_nodes"
    ][0]["cobdao_sections"]
    grouped_abc_height_sections = by_name["text_three_objects_grouped_order_abc_height_30mm.txt"]["cproperty_nodes"][0][
        "cobdao_sections"
    ]
    grouped_abc_bold_sections = by_name["text_three_objects_grouped_order_abc_font_arial_bold.txt"][
        "cproperty_nodes"
    ][0]["cobdao_sections"]
    grouped_abc_mixed_sections = by_name["text_three_objects_grouped_order_abc_mixed_color.txt"]["cproperty_nodes"][0][
        "cobdao_sections"
    ]
    grouped_abc_sections = by_name["text_three_objects_grouped_order_abc.txt"]["cproperty_nodes"][0]["cobdao_sections"]
    grouped_cba_sections = by_name["text_three_objects_grouped_order_cba.txt"]["cproperty_nodes"][0]["cobdao_sections"]
    three_nongrouped_mixed_sections = by_name["text_three_objects_not_grouped_mixed_color.txt"]["cproperty_nodes"][0][
        "cobdao_sections"
    ]

    assert same_sections[1]["section_role_candidate"] == "anchor_bearing_candidate"
    assert same_sections[1]["cobdao_plus_34_triple_analysis"]["matches_any_chain_baseline_anchor"] is True
    assert same_sections[0]["section_role_candidate"] == "non_anchor_candidate"
    assert same_sections[0]["cobdao_plus_34_triple_analysis"]["is_coordinate_like"] is True
    assert same_sections[0]["cobdao_plus_34_triple_analysis"]["matches_any_chain_baseline_anchor"] is False
    assert nongrouped_sections[2]["section_role_candidate"] == "anchor_bearing_candidate"
    assert nongrouped_sections[2]["hit_relative_to_cobdao"] == 34
    assert same_color_nongrouped_sections[2]["section_role_candidate"] == "anchor_bearing_candidate"
    assert same_color_nongrouped_sections[2]["hit_relative_to_cobdao"] == 34
    assert selection_reversed_sections[2]["section_role_candidate"] == "anchor_bearing_candidate"
    assert selection_reversed_sections[2]["hit_relative_to_cobdao"] == 34
    assert three_nongrouped_sections[2]["section_role_candidate"] == "anchor_bearing_candidate"
    assert three_nongrouped_sections[2]["hit_relative_to_cobdao"] == 34
    assert three_nongrouped_sections[7]["section_role_candidate"] == "anchor_bearing_candidate"
    assert three_nongrouped_sections[7]["hit_relative_to_cobdao"] == 34
    assert grouped_abc_sections[1]["section_role_candidate"] == "anchor_bearing_candidate"
    assert grouped_abc_sections[1]["hit_relative_to_cobdao"] == 34
    assert grouped_abc_sections[5]["section_role_candidate"] == "anchor_bearing_candidate"
    assert grouped_abc_sections[5]["hit_relative_to_cobdao"] == 34
    assert grouped_abc_content_sections[1]["section_role_candidate"] == "anchor_bearing_candidate"
    assert grouped_abc_content_sections[1]["hit_relative_to_cobdao"] == 34
    assert grouped_abc_content_sections[5]["section_role_candidate"] == "anchor_bearing_candidate"
    assert grouped_abc_content_sections[5]["hit_relative_to_cobdao"] == 34
    assert grouped_abc_height_sections[1]["section_role_candidate"] == "anchor_bearing_candidate"
    assert grouped_abc_height_sections[1]["hit_relative_to_cobdao"] == 34
    assert grouped_abc_height_sections[5]["section_role_candidate"] == "anchor_bearing_candidate"
    assert grouped_abc_height_sections[5]["hit_relative_to_cobdao"] == 34
    assert grouped_abc_bold_sections[1]["section_role_candidate"] == "anchor_bearing_candidate"
    assert grouped_abc_bold_sections[1]["hit_relative_to_cobdao"] == 34
    assert grouped_abc_bold_sections[5]["section_role_candidate"] == "anchor_bearing_candidate"
    assert grouped_abc_bold_sections[5]["hit_relative_to_cobdao"] == 34
    assert grouped_abc_mixed_sections[1]["section_role_candidate"] == "anchor_bearing_candidate"
    assert grouped_abc_mixed_sections[1]["hit_relative_to_cobdao"] == 34
    assert grouped_abc_mixed_sections[5]["section_role_candidate"] == "anchor_bearing_candidate"
    assert grouped_abc_mixed_sections[5]["hit_relative_to_cobdao"] == 34
    assert grouped_cba_sections[1]["section_role_candidate"] == "anchor_bearing_candidate"
    assert grouped_cba_sections[1]["hit_relative_to_cobdao"] == 34
    assert grouped_cba_sections[5]["section_role_candidate"] == "anchor_bearing_candidate"
    assert grouped_cba_sections[5]["hit_relative_to_cobdao"] == 34
    assert three_nongrouped_mixed_sections[2]["section_role_candidate"] == "anchor_bearing_candidate"
    assert three_nongrouped_mixed_sections[2]["hit_relative_to_cobdao"] == 34
    assert three_nongrouped_mixed_sections[7]["section_role_candidate"] == "anchor_bearing_candidate"
    assert three_nongrouped_mixed_sections[7]["hit_relative_to_cobdao"] == 34


def test_cobdao_section_role_analysis_markdown_output() -> None:
    result = _run(["--markdown"])
    assert result.returncode == 0, result.stderr
    out = result.stdout

    assert "# Text CPropertyExtend Anchor Context Analysis" in out
    assert "## Anchor-bearing vs Non-anchor Aggregate" in out
    assert "false positive risk" in out
