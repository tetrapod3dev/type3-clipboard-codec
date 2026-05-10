from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
CLI_PATH = REPO_ROOT / "tools" / "analyze_contour_candidate_competition.py"


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


def test_competition_cli_text_includes_kind3_and_diagnostic_wording():
    result = _run_cli([])
    assert result.returncode == 0, result.stderr
    assert "policy: diagnostic only; parser selection unchanged" in result.stdout
    assert "kind=3 count=1" in result.stdout
    assert "multiple_structural_valid" in result.stdout


def test_competition_cli_json_reports_outside_gate_and_auxiliary_candidates():
    result = _run_cli(["--json"])
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    fixtures = {item["fixture"]: item for item in payload["fixtures"]}

    def _all_candidates(fixture_name: str):
        out = []
        for marker in fixtures[fixture_name]["markers"]:
            out.extend(marker["candidates"])
        return out

    poly5 = _all_candidates("polyline_5_points.txt")
    pg5 = _all_candidates("polygon_5_sides.txt")
    pg6 = _all_candidates("polygon_6_sides.txt")
    tworect = _all_candidates("two_rectangle.txt")

    assert any(c["marker_context"]["decoded_count"] == 5 for c in poly5)
    assert any(c["marker_context"]["decoded_count"] == 5 for c in pg5)
    assert any(c["marker_context"]["decoded_count"] == 6 for c in pg6)
    assert any(
        c["marker_context"]["decoded_kind"] == 3 and c["marker_context"]["decoded_count"] == 1
        for c in tworect
    )
