from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
CLI_PATH = REPO_ROOT / "tools" / "analyze_contour_tag_role_evidence.py"


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


def test_polyline5_session2_pairwise_evidence_is_reported() -> None:
    result = _run_cli(["--json"])
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    pair = payload["pairwise_comparisons"]["polyline5_vs_session2"]

    assert pair["comparison_confidence"] == "provisional"
    assert pair["base_fixture"] == "polyline_5_points.txt"
    assert pair["other_fixture"] == "polyline_5_points_session2.txt"
    assert "session_reproducibility_status" in pair
    assert "volatile_family_candidate" in pair
    assert "full_tag_changed_coordinates" in pair
