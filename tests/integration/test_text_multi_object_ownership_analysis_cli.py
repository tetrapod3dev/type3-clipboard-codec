from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
CLI_PATH = REPO_ROOT / "tools" / "analyze_text_multi_object_ownership.py"


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


def test_text_multi_object_ownership_analysis_cli_text_mode() -> None:
    result = _run([])
    assert result.returncode == 0, result.stderr
    out = result.stdout

    assert "Text Multi-object Ownership Analysis" in out
    assert "[Node inventory]" in out
    assert "[Chain inventory]" in out
    assert "[CParagraphe ownership analysis]" in out
    assert "[Whole-payload anchor scan]" in out
    assert "text_group_same_color_two_objects.txt" in out
    assert "text_group_mixed_color_two_objects.txt" in out
    assert "text_two_objects_mixed_color_not_grouped.txt" in out
    assert "text_three_objects_not_grouped.txt" in out
    assert "text_three_objects_grouped_order_abc.txt" in out
    assert "text_three_objects_grouped_order_cba.txt" in out
    assert "parser_chains=2 cparagraphe_count=1" in out
    assert "parser_chains=3 cparagraphe_count=1" in out


def test_text_multi_object_ownership_analysis_cli_json_mode() -> None:
    result = _run(["--json"])
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)

    assert payload["policy"]["scope"] == "structure/evidence audit only"
    assert payload["policy"]["parser_behavior"] == "not_modified"
    assert payload["policy"]["direct_anchor_promotion"] == "not_applied"
    assert payload["answers"]["cparagraphe_always_one_in_multi_object_fixtures"] is True
    assert payload["answers"]["parser_readiness"] == "not_ready"

    by_name = {fixture["fixture"]: fixture for fixture in payload["multi_object_fixtures"]}
    assert set(by_name) == {
        "text_group_same_color_two_objects.txt",
        "text_group_mixed_color_two_objects.txt",
        "text_two_objects_mixed_color_not_grouped.txt",
        "text_two_objects_same_color_not_grouped.txt",
        "text_two_objects_not_grouped_selection_reversed.txt",
        "text_three_objects_not_grouped.txt",
        "text_three_objects_grouped_order_abc.txt",
        "text_three_objects_grouped_order_cba.txt",
    }

    for name, fixture in by_name.items():
        expected_chains = 3 if name.startswith("text_three_objects_") else 2
        assert fixture["parser_chain_count"] == expected_chains
        assert fixture["cparagraphe_count"] == 1
        assert fixture["node_inventory"]
        assert fixture["chain_inventory"]
        assert fixture["cparagraphe_ownership_analysis"]
        assert fixture["whole_payload_anchor_scan"]

    same_color = by_name["text_group_same_color_two_objects.txt"]
    assert same_color["cparagraphe_ownership_analysis"][0]["exact_anchor_match_chains"] == [0]
    same_color_second_anchor = same_color["whole_payload_anchor_scan"][1]
    assert same_color_second_anchor["hit_count"] == 1
    assert same_color_second_anchor["hits"][0]["node_class"] == "CPropertyExtend"

    non_grouped = by_name["text_two_objects_mixed_color_not_grouped.txt"]
    assert non_grouped["cparagraphe_ownership_analysis"][0]["exact_anchor_match_chains"] == [1]
    first_anchor = non_grouped["whole_payload_anchor_scan"][0]
    assert first_anchor["hit_count"] == 1
    assert first_anchor["hits"][0]["node_class"] == "CPropertyExtend"

    three = by_name["text_three_objects_not_grouped.txt"]
    assert three["parser_chain_count"] == 3
    assert three["cparagraphe_ownership_analysis"][0]["exact_anchor_match_chains"] == [2]
    assert [scan["hit_count"] for scan in three["whole_payload_anchor_scan"]] == [1, 1, 1]
    assert [scan["hits"][0]["node_class"] for scan in three["whole_payload_anchor_scan"]] == [
        "CPropertyExtend",
        "CPropertyExtend",
        "CParagraphe",
    ]

    grouped_abc = by_name["text_three_objects_grouped_order_abc.txt"]
    assert grouped_abc["parser_chain_count"] == 3
    assert grouped_abc["cparagraphe_ownership_analysis"][0]["exact_anchor_match_chains"] == [0]
    assert [scan["hit_count"] for scan in grouped_abc["whole_payload_anchor_scan"]] == [1, 1, 1]
    assert [scan["hits"][0]["node_class"] for scan in grouped_abc["whole_payload_anchor_scan"]] == [
        "CParagraphe",
        "CPropertyExtend",
        "CPropertyExtend",
    ]

    grouped_cba = by_name["text_three_objects_grouped_order_cba.txt"]
    assert grouped_cba["parser_chain_count"] == 3
    assert grouped_cba["cparagraphe_ownership_analysis"][0]["exact_anchor_match_chains"] == [2]
    assert [scan["hit_count"] for scan in grouped_cba["whole_payload_anchor_scan"]] == [1, 1, 1]
    assert [scan["hits"][0]["node_class"] for scan in grouped_cba["whole_payload_anchor_scan"]] == [
        "CPropertyExtend",
        "CPropertyExtend",
        "CParagraphe",
    ]

    anchor_summary = payload["anchor_storage_scaling_summary"]
    assert anchor_summary["all_current_multi_object_fixtures_hold"] is True
    assert anchor_summary["parser_promotion_status"] == "analyzer_only"
    by_summary_name = {row["fixture"]: row for row in anchor_summary["rows"]}
    assert by_summary_name["text_three_objects_grouped_order_abc.txt"]["cparagraphe_owner_chain_indexes"] == [0]
    assert by_summary_name["text_three_objects_grouped_order_abc.txt"]["cpropertyextend_owner_chain_indexes"] == [1, 2]
    assert by_summary_name["text_three_objects_grouped_order_cba.txt"]["cparagraphe_owner_chain_indexes"] == [2]
    assert by_summary_name["text_three_objects_grouped_order_cba.txt"]["cpropertyextend_owner_chain_indexes"] == [0, 1]
    assert by_summary_name["text_three_objects_not_grouped.txt"]["cparagraphe_owner_chain_indexes"] == [2]
    assert by_summary_name["text_three_objects_not_grouped.txt"]["cpropertyextend_owner_chain_indexes"] == [0, 1]

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


def test_text_multi_object_ownership_analysis_cli_markdown_mode() -> None:
    result = _run(["--markdown"])
    assert result.returncode == 0, result.stderr
    out = result.stdout

    assert "# Text Multi-object Ownership Analysis" in out
    assert "| fixture | parser chains | CParagraphe count | ownership status |" in out
    assert "## Whole-payload Anchor Scan" in out
