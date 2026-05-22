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


def test_text_cproperty_anchor_context_cli_text_mode() -> None:
    result = _run([])
    assert result.returncode == 0, result.stderr
    out = result.stdout

    assert "Text CPropertyExtend Anchor Context Analysis" in out
    assert "text_group_same_color_two_objects.txt" in out
    assert "text_group_mixed_color_two_objects.txt" in out
    assert "text_two_objects_mixed_color_not_grouped.txt" in out
    assert "text_two_objects_same_color_not_grouped.txt" in out
    assert "text_two_objects_not_grouped_selection_reversed.txt" in out
    assert "CParagraphe node=" in out
    assert "cproperty_offset=472" in out
    assert "cproperty_offset=620" in out
    assert "local_context_hex=" in out
    assert "parser_behavior: not_modified" in out


def test_text_cproperty_anchor_context_cli_json_mode() -> None:
    result = _run(["--json"])
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)

    assert payload["policy"]["scope"] == "CPropertyExtend anchor context structure/evidence audit only"
    assert payload["policy"]["parser_behavior"] == "not_modified"
    assert payload["policy"]["cproperty_anchor_promotion"] == "not_applied"

    by_name = {fixture["fixture"]: fixture for fixture in payload["fixtures"]}
    same = by_name["text_group_same_color_two_objects.txt"]
    mixed = by_name["text_group_mixed_color_two_objects.txt"]
    nongrouped = by_name["text_two_objects_mixed_color_not_grouped.txt"]
    same_color_nongrouped = by_name["text_two_objects_same_color_not_grouped.txt"]
    selection_reversed = by_name["text_two_objects_not_grouped_selection_reversed.txt"]

    same_hit = same["cproperty_nodes"][0]["anchor_triple_hits_inside_node"][0]
    mixed_hit = mixed["cproperty_nodes"][0]["anchor_triple_hits_inside_node"][0]
    nongrouped_hit = nongrouped["cproperty_nodes"][0]["anchor_triple_hits_inside_node"][0]

    assert same_hit["cproperty_payload_relative_offset"] == 472
    assert mixed_hit["cproperty_payload_relative_offset"] == 472
    assert nongrouped_hit["cproperty_payload_relative_offset"] == 620

    same_color_nongrouped_hit = same_color_nongrouped["cproperty_nodes"][0]["anchor_triple_hits_inside_node"][0]
    selection_reversed_hit = selection_reversed["cproperty_nodes"][0]["anchor_triple_hits_inside_node"][0]

    assert same_color_nongrouped_hit["cproperty_payload_relative_offset"] == 620
    assert selection_reversed_hit["cproperty_payload_relative_offset"] == 620

    for hit in (same_hit, mixed_hit, nongrouped_hit, same_color_nongrouped_hit, selection_reversed_hit):
        assert hit["node_class"] == "CPropertyExtend"
        assert hit["local_context_hex"]["hex"]
        assert hit["nearby_decoded_doubles"]
        assert hit["nearby_u32_i32_values"]
        assert hit["possible_local_record_start_candidates"]
        assert any(candidate["matched_chain_baseline_anchor"] for candidate in hit["chain_match_candidates"])

    comp = payload["grouped_vs_non_grouped_comparison"]
    assert comp["grouped_cproperty_anchor_offsets"] == [472, 472]
    assert comp["non_grouped_cproperty_anchor_offsets"] == [620, 620, 620]
    assert comp["offset_delta_non_grouped_minus_grouped"] == 148
    assert [row["cobdao_section_count"] for row in comp["non_grouped_by_fixture"]] == [6, 6, 6]
    assert comp["grouped_marker_signature_identical"] is True
    assert comp["parser_promotion_status"] == "analyzer_only"
    assert same_color_nongrouped["cparagraphe_direct_anchor_ownership"][0]["direct_anchor"]["matched_chains"] == [1]
    assert selection_reversed["cparagraphe_direct_anchor_ownership"][0]["direct_anchor"]["matched_chains"] == [0]
    assert payload["answers"]["parser_readiness"] == "not_ready_analyzer_only"


def test_text_cproperty_anchor_context_cli_markdown_mode() -> None:
    result = _run(["--markdown"])
    assert result.returncode == 0, result.stderr
    out = result.stdout

    assert "# Text CPropertyExtend Anchor Context Analysis" in out
    assert (
        "| fixture | CPropertyExtend node | CObDao offset | target anchor mm | payload offset | "
        "hit rel to CObDao | matched chains |"
    ) in out
    assert "## Grouped vs Non-grouped" in out
