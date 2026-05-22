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


def test_cobdao_section_scan_text_output() -> None:
    result = _run([])
    assert result.returncode == 0, result.stderr
    out = result.stdout

    assert "[CObDao section scan]" in out
    assert "cobdao_offset=438" in out
    assert "known_anchor=true role=anchor_bearing_candidate hit_relative_to_cobdao=34" in out
    assert "matched_chains=[1]" in out
    assert "cobdao_offset=586" in out
    assert "matched_chains=[0]" in out
    assert "cproperty_offset=472" in out
    assert "cproperty_offset=620" in out


def test_cobdao_section_scan_json_normalizes_anchor_hits() -> None:
    result = _run(["--json"])
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)

    assert payload["policy"]["parser_behavior"] == "not_modified"
    assert payload["policy"]["cproperty_anchor_promotion"] == "not_applied"

    by_name = {fixture["fixture"]: fixture for fixture in payload["fixtures"]}
    same = by_name["text_group_same_color_two_objects.txt"]["cproperty_nodes"][0]
    mixed = by_name["text_group_mixed_color_two_objects.txt"]["cproperty_nodes"][0]
    nongrouped = by_name["text_two_objects_mixed_color_not_grouped.txt"]["cproperty_nodes"][0]
    same_color_nongrouped = by_name["text_two_objects_same_color_not_grouped.txt"]["cproperty_nodes"][0]
    selection_reversed = by_name["text_two_objects_not_grouped_selection_reversed.txt"]["cproperty_nodes"][0]
    three_nongrouped = by_name["text_three_objects_not_grouped.txt"]["cproperty_nodes"][0]
    grouped_abc = by_name["text_three_objects_grouped_order_abc.txt"]["cproperty_nodes"][0]
    grouped_abc_height = by_name["text_three_objects_grouped_order_abc_height_30mm.txt"]["cproperty_nodes"][0]
    grouped_abc_bold = by_name["text_three_objects_grouped_order_abc_font_arial_bold.txt"]["cproperty_nodes"][0]
    grouped_abc_mixed = by_name["text_three_objects_grouped_order_abc_mixed_color.txt"]["cproperty_nodes"][0]
    grouped_cba = by_name["text_three_objects_grouped_order_cba.txt"]["cproperty_nodes"][0]
    three_nongrouped_mixed = by_name["text_three_objects_not_grouped_mixed_color.txt"]["cproperty_nodes"][0]

    same_anchor_sections = [section for section in same["cobdao_sections"] if section["known_anchor_triple_hit"]]
    mixed_anchor_sections = [section for section in mixed["cobdao_sections"] if section["known_anchor_triple_hit"]]
    nongrouped_anchor_sections = [section for section in nongrouped["cobdao_sections"] if section["known_anchor_triple_hit"]]
    same_color_nongrouped_anchor_sections = [
        section for section in same_color_nongrouped["cobdao_sections"] if section["known_anchor_triple_hit"]
    ]
    selection_reversed_anchor_sections = [
        section for section in selection_reversed["cobdao_sections"] if section["known_anchor_triple_hit"]
    ]
    three_nongrouped_anchor_sections = [
        section for section in three_nongrouped["cobdao_sections"] if section["known_anchor_triple_hit"]
    ]
    grouped_abc_anchor_sections = [
        section for section in grouped_abc["cobdao_sections"] if section["known_anchor_triple_hit"]
    ]
    grouped_abc_height_anchor_sections = [
        section for section in grouped_abc_height["cobdao_sections"] if section["known_anchor_triple_hit"]
    ]
    grouped_abc_bold_anchor_sections = [
        section for section in grouped_abc_bold["cobdao_sections"] if section["known_anchor_triple_hit"]
    ]
    grouped_abc_mixed_anchor_sections = [
        section for section in grouped_abc_mixed["cobdao_sections"] if section["known_anchor_triple_hit"]
    ]
    grouped_cba_anchor_sections = [
        section for section in grouped_cba["cobdao_sections"] if section["known_anchor_triple_hit"]
    ]
    three_nongrouped_mixed_anchor_sections = [
        section for section in three_nongrouped_mixed["cobdao_sections"] if section["known_anchor_triple_hit"]
    ]

    assert len(same["cobdao_sections"]) == 5
    assert len(mixed["cobdao_sections"]) == 5
    assert len(nongrouped["cobdao_sections"]) == 6
    assert len(same_color_nongrouped["cobdao_sections"]) == 6
    assert len(selection_reversed["cobdao_sections"]) == 6
    assert len(three_nongrouped["cobdao_sections"]) == 11
    assert len(grouped_abc["cobdao_sections"]) == 9
    assert len(grouped_abc_height["cobdao_sections"]) == 9
    assert len(grouped_abc_bold["cobdao_sections"]) == 9
    assert len(grouped_abc_mixed["cobdao_sections"]) == 9
    assert len(grouped_cba["cobdao_sections"]) == 9
    assert len(three_nongrouped_mixed["cobdao_sections"]) == 11
    assert same_anchor_sections[0]["cobdao_marker_offset"] == 438
    assert mixed_anchor_sections[0]["cobdao_marker_offset"] == 438
    assert nongrouped_anchor_sections[0]["cobdao_marker_offset"] == 586
    assert same_color_nongrouped_anchor_sections[0]["cobdao_marker_offset"] == 586
    assert selection_reversed_anchor_sections[0]["cobdao_marker_offset"] == 586
    assert [section["cobdao_marker_offset"] for section in three_nongrouped_anchor_sections] == [586, 4428]
    assert [section["cobdao_marker_offset"] for section in grouped_abc_anchor_sections] == [438, 4132]
    assert [section["cobdao_marker_offset"] for section in grouped_abc_height_anchor_sections] == [438, 4132]
    assert [section["cobdao_marker_offset"] for section in grouped_abc_bold_anchor_sections] == [438, 4132]
    assert [section["cobdao_marker_offset"] for section in grouped_abc_mixed_anchor_sections] == [438, 4132]
    assert [section["cobdao_marker_offset"] for section in grouped_cba_anchor_sections] == [438, 4132]
    assert [section["cobdao_marker_offset"] for section in three_nongrouped_mixed_anchor_sections] == [586, 4428]
    assert same_anchor_sections[0]["hit_relative_to_cobdao"] == 34
    assert mixed_anchor_sections[0]["hit_relative_to_cobdao"] == 34
    assert nongrouped_anchor_sections[0]["hit_relative_to_cobdao"] == 34
    assert same_color_nongrouped_anchor_sections[0]["hit_relative_to_cobdao"] == 34
    assert selection_reversed_anchor_sections[0]["hit_relative_to_cobdao"] == 34
    assert [section["hit_relative_to_cobdao"] for section in three_nongrouped_anchor_sections] == [34, 34]
    assert [section["hit_relative_to_cobdao"] for section in grouped_abc_anchor_sections] == [34, 34]
    assert [section["hit_relative_to_cobdao"] for section in grouped_abc_height_anchor_sections] == [34, 34]
    assert [section["hit_relative_to_cobdao"] for section in grouped_abc_bold_anchor_sections] == [34, 34]
    assert [section["hit_relative_to_cobdao"] for section in grouped_abc_mixed_anchor_sections] == [34, 34]
    assert [section["hit_relative_to_cobdao"] for section in grouped_cba_anchor_sections] == [34, 34]
    assert [section["hit_relative_to_cobdao"] for section in three_nongrouped_mixed_anchor_sections] == [34, 34]

    for section in (
        *same_anchor_sections,
        *mixed_anchor_sections,
        *nongrouped_anchor_sections,
            *same_color_nongrouped_anchor_sections,
            *selection_reversed_anchor_sections,
            *three_nongrouped_anchor_sections,
            *grouped_abc_anchor_sections,
            *grouped_abc_height_anchor_sections,
            *grouped_abc_bold_anchor_sections,
            *grouped_abc_mixed_anchor_sections,
            *grouped_cba_anchor_sections,
            *three_nongrouped_mixed_anchor_sections,
        ):
        assert section["local_triple_at_cobdao_plus_34"] is not None
        assert section["nearby_objectinfos_marker"]["marker"] == "OBJETINFOS_CLASSNAME"
        assert section["nearby_objectinfos_marker"]["distance_before_cobdao"] == 24
        assert section["marker_context_hex"]["hex"]
        assert section["matched_chains"]

    comp = payload["grouped_vs_non_grouped_comparison"]
    assert comp["all_anchor_hits_relative_to_cobdao_are_34"] is True
    assert comp["grouped_cobdao_anchor_section_offsets"] == [
        438,
        438,
        438,
        4132,
        438,
        4132,
        438,
        4132,
        438,
        4132,
        438,
        4132,
    ]
    assert comp["non_grouped_cobdao_anchor_section_offsets"] == [586, 586, 586, 586, 4428, 586, 4428]
    assert comp["cobdao_offset_delta_non_grouped_minus_grouped"] == 148
    assert comp["cobdao_section_counts_identical"] is False
    assert payload["answers"]["parser_readiness"] == "not_ready_analyzer_only"


def test_cobdao_section_scan_markdown_output() -> None:
    result = _run(["--markdown"])
    assert result.returncode == 0, result.stderr
    out = result.stdout

    assert "# Text CPropertyExtend Anchor Context Analysis" in out
    assert "hit rel to CObDao" in out
    assert "| text_group_same_color_two_objects.txt | 4 | 438 |" in out
    assert "| text_two_objects_mixed_color_not_grouped.txt | 4 | 586 |" in out
