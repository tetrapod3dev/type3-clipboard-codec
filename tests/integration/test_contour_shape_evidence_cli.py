from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
CLI_PATH = REPO_ROOT / "tools" / "compare_contour_shape_evidence.py"


def _run_cli(args: list[str]) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO_ROOT / "src")
    return subprocess.run(
        [sys.executable, str(CLI_PATH), *args],
        text=True,
        capture_output=True,
        cwd=str(REPO_ROOT),
        env=env,
        timeout=120,
    )


def test_contour_shape_evidence_cli_text_output_contains_required_sets_and_policy():
    result = _run_cli([])
    assert result.returncode == 0, result.stderr
    assert "[Set A] same_count_3_different_intent" in result.stdout
    assert "[Set B] same_count_5_open_vs_closed" in result.stdout
    assert "[Set C] closed_polygon_count_extension" in result.stdout
    assert "diagnostic only" in result.stdout
    assert "provisional" in result.stdout
    assert "known incomplete whitelist" in result.stdout


def test_contour_shape_evidence_cli_json_reports_expected_count_evidence():
    result = _run_cli(["--json"])
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    groups = payload["comparison_sets"]

    def _find_fixture(name: str):
        for g in groups:
            for row in g["fixtures"]:
                if row["fixture"] == name:
                    return row
        raise AssertionError(f"fixture not found: {name}")

    arc = _find_fixture("default_circular_arc.txt")
    poly3 = _find_fixture("polyline_3_points.txt")
    assert arc["selected_count"] == 3
    assert poly3["selected_count"] == 3

    poly5 = _find_fixture("polyline_5_points.txt")
    pg5 = _find_fixture("polygon_5_sides.txt")
    pg6 = _find_fixture("polygon_6_sides.txt")

    assert any(item.get("count") == 5 for item in poly5["raw_count_candidates_shift8"])
    assert any(item.get("count") == 5 for item in pg5["raw_count_candidates_shift8"])
    assert any(item.get("count") == 6 for item in pg6["raw_count_candidates_shift8"])
    assert isinstance(poly3["current_classifier_result"], str)
