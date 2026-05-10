from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
CLI_PATH = REPO_ROOT / "tools" / "report_contour_selection_shadow_diff.py"


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


def test_shadow_diff_cli_text_runs_and_includes_required_sections() -> None:
    result = _run_cli([])
    assert result.returncode == 0, result.stderr
    assert "Contour Selection Shadow Diff Report" in result.stdout
    assert "[A. Fixture-level Winner Mismatch]" in result.stdout
    assert "[B. Marker-level Auxiliary Observations]" in result.stdout
    assert "[C. Suppressed Auxiliary Candidates]" in result.stdout
    assert "actual selection is refined structural ranking" in result.stdout


def test_shadow_diff_cli_json_reports_expected_outside_gate_and_auxiliary_summary() -> None:
    result = _run_cli(["--json"])
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)

    fixtures = {row["fixture"]: row for row in payload["fixtures"]}
    assert fixtures["polyline_5_points.txt"]["legacy_vs_actual_status"] == "refined_adds_outside_gate_candidate"
    assert fixtures["polygon_5_sides.txt"]["legacy_vs_actual_status"] == "refined_adds_outside_gate_candidate"
    assert fixtures["polygon_6_sides.txt"]["legacy_vs_actual_status"] == "refined_adds_outside_gate_candidate"

    assert payload["aggregate_summary"]["fixtures_with_unexpected_refined_difference"] == 0
    assert payload["aggregate_summary"]["total_auxiliary_candidates_observed"] >= 1
    assert payload["aggregate_summary"]["total_auxiliary_candidates_suppressed"] >= 1
    assert payload["refined_vs_actual_mismatch_fixtures"] == []
