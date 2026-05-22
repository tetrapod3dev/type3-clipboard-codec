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
    assert "text_three_objects_not_grouped.txt" in out
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
    three_nongrouped = by_name["text_three_objects_not_grouped.txt"]
    grouped_abc = by_name["text_three_objects_grouped_order_abc.txt"]
    grouped_cba = by_name["text_three_objects_grouped_order_cba.txt"]

    same_hit = same["cproperty_nodes"][0]["anchor_triple_hits_inside_node"][0]
    mixed_hit = mixed["cproperty_nodes"][0]["anchor_triple_hits_inside_node"][0]
    nongrouped_hit = nongrouped["cproperty_nodes"][0]["anchor_triple_hits_inside_node"][0]

    assert same_hit["cproperty_payload_relative_offset"] == 472
    assert mixed_hit["cproperty_payload_relative_offset"] == 472
    assert nongrouped_hit["cproperty_payload_relative_offset"] == 620

    same_color_nongrouped_hit = same_color_nongrouped["cproperty_nodes"][0]["anchor_triple_hits_inside_node"][0]
    selection_reversed_hit = selection_reversed["cproperty_nodes"][0]["anchor_triple_hits_inside_node"][0]
    three_hits = three_nongrouped["cproperty_nodes"][0]["anchor_triple_hits_inside_node"]
    grouped_abc_hits = grouped_abc["cproperty_nodes"][0]["anchor_triple_hits_inside_node"]
    grouped_cba_hits = grouped_cba["cproperty_nodes"][0]["anchor_triple_hits_inside_node"]

    assert same_color_nongrouped_hit["cproperty_payload_relative_offset"] == 620
    assert selection_reversed_hit["cproperty_payload_relative_offset"] == 620
    assert [hit["cproperty_payload_relative_offset"] for hit in three_hits] == [4462, 620]
    assert [hit["cproperty_payload_relative_offset"] for hit in grouped_abc_hits] == [472, 4166]
    assert [hit["cproperty_payload_relative_offset"] for hit in grouped_cba_hits] == [4166, 472]

    for hit in (
        same_hit,
        mixed_hit,
        nongrouped_hit,
        same_color_nongrouped_hit,
        selection_reversed_hit,
        *three_hits,
        *grouped_abc_hits,
        *grouped_cba_hits,
    ):
        assert hit["node_class"] == "CPropertyExtend"
        assert hit["local_context_hex"]["hex"]
        assert hit["nearby_decoded_doubles"]
        assert hit["nearby_u32_i32_values"]
        assert hit["possible_local_record_start_candidates"]
        assert any(candidate["matched_chain_baseline_anchor"] for candidate in hit["chain_match_candidates"])

    comp = payload["grouped_vs_non_grouped_comparison"]
    assert comp["grouped_cproperty_anchor_offsets"] == [472, 472, 472, 4166, 4166, 472]
    assert comp["non_grouped_cproperty_anchor_offsets"] == [620, 620, 620, 4462, 620]
    assert comp["offset_delta_non_grouped_minus_grouped"] == 148
    assert [row["cobdao_section_count"] for row in comp["non_grouped_by_fixture"]] == [6, 6, 6, 11]
    assert comp["grouped_marker_signature_identical"] is True
    assert comp["parser_promotion_status"] == "analyzer_only"
    assert same_color_nongrouped["cparagraphe_direct_anchor_ownership"][0]["direct_anchor"]["matched_chains"] == [1]
    assert selection_reversed["cparagraphe_direct_anchor_ownership"][0]["direct_anchor"]["matched_chains"] == [0]
    assert three_nongrouped["cparagraphe_direct_anchor_ownership"][0]["direct_anchor"]["matched_chains"] == [2]
    assert grouped_abc["cparagraphe_direct_anchor_ownership"][0]["direct_anchor"]["matched_chains"] == [0]
    assert grouped_cba["cparagraphe_direct_anchor_ownership"][0]["direct_anchor"]["matched_chains"] == [2]
    assert payload["answers"]["text_three_objects_not_grouped_summary"]["cproperty_anchor_hit_count"] == 2
    assert payload["answers"]["parser_readiness"] == "not_ready_analyzer_only"

    anchor_summary = payload["anchor_storage_scaling_summary"]
    assert anchor_summary["all_current_multi_object_fixtures_hold"] is True
    assert anchor_summary["parser_promotion_status"] == "analyzer_only"
    by_summary_name = {row["fixture"]: row for row in anchor_summary["rows"]}
    assert by_summary_name["text_three_objects_grouped_order_abc.txt"]["cparagraphe_owner_chain_indexes"] == [0]
    assert by_summary_name["text_three_objects_grouped_order_abc.txt"]["cpropertyextend_owner_chain_indexes"] == [1, 2]
    assert by_summary_name["text_three_objects_grouped_order_cba.txt"]["cparagraphe_owner_chain_indexes"] == [2]
    assert by_summary_name["text_three_objects_grouped_order_cba.txt"]["cpropertyextend_owner_chain_indexes"] == [1, 0]
    assert by_summary_name["text_three_objects_not_grouped.txt"]["cparagraphe_owner_chain_indexes"] == [2]
    assert by_summary_name["text_three_objects_not_grouped.txt"]["cpropertyextend_owner_chain_indexes"] == [1, 0]

    section_summary = payload["grouped_not_grouped_section_scaling_summary"]
    assert section_summary["candidate_formula"] == "not_grouped_delta = object_count - 1"
    assert section_summary["candidate_formula_holds_for_comparable_counts"] is True
    by_object_count = {row["object_count"]: row for row in section_summary["comparisons_by_object_count"]}
    assert by_object_count[2]["grouped_section_counts"] == [5]
    assert by_object_count[2]["not_grouped_section_counts"] == [6]
    assert by_object_count[2]["not_grouped_minus_grouped_delta"] == 1
    assert by_object_count[3]["grouped_section_counts"] == [9]
    assert by_object_count[3]["not_grouped_section_counts"] == [11]
    assert by_object_count[3]["not_grouped_minus_grouped_delta"] == 2

    selection_summary = payload["selection_order_primary_owner_summary"]
    assert selection_summary["grouped_order_effect_observed"] is True
    by_selection_name = {row["fixture"]: row for row in selection_summary["rows"]}
    assert by_selection_name["text_three_objects_grouped_order_abc.txt"][
        "attempted_order_first_maps_to_cparagraphe_owner"
    ] is True
    assert by_selection_name["text_three_objects_grouped_order_cba.txt"][
        "attempted_order_first_maps_to_cparagraphe_owner"
    ] is True
    assert by_selection_name["text_three_objects_not_grouped.txt"][
        "attempted_order_last_maps_to_cparagraphe_owner"
    ] is True


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
