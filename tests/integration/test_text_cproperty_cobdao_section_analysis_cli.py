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

    same_anchor_sections = [section for section in same["cobdao_sections"] if section["known_anchor_triple_hit"]]
    mixed_anchor_sections = [section for section in mixed["cobdao_sections"] if section["known_anchor_triple_hit"]]
    nongrouped_anchor_sections = [section for section in nongrouped["cobdao_sections"] if section["known_anchor_triple_hit"]]

    assert len(same["cobdao_sections"]) == 5
    assert len(mixed["cobdao_sections"]) == 5
    assert len(nongrouped["cobdao_sections"]) == 6
    assert same_anchor_sections[0]["cobdao_marker_offset"] == 438
    assert mixed_anchor_sections[0]["cobdao_marker_offset"] == 438
    assert nongrouped_anchor_sections[0]["cobdao_marker_offset"] == 586
    assert same_anchor_sections[0]["hit_relative_to_cobdao"] == 34
    assert mixed_anchor_sections[0]["hit_relative_to_cobdao"] == 34
    assert nongrouped_anchor_sections[0]["hit_relative_to_cobdao"] == 34

    for section in (*same_anchor_sections, *mixed_anchor_sections, *nongrouped_anchor_sections):
        assert section["local_triple_at_cobdao_plus_34"] is not None
        assert section["nearby_objectinfos_marker"]["marker"] == "OBJETINFOS_CLASSNAME"
        assert section["nearby_objectinfos_marker"]["distance_before_cobdao"] == 24
        assert section["marker_context_hex"]["hex"]
        assert section["matched_chains"]

    comp = payload["grouped_vs_non_grouped_comparison"]
    assert comp["all_anchor_hits_relative_to_cobdao_are_34"] is True
    assert comp["grouped_cobdao_anchor_section_offsets"] == [438, 438]
    assert comp["non_grouped_cobdao_anchor_section_offsets"] == [586]
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
