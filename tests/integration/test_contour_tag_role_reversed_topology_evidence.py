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


def test_reversed_and_closed_topology_pairwise_evidence_is_reported() -> None:
    result = _run_cli(["--json"])
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    pairs = payload["pairwise_comparisons"]

    reversed_pair = pairs["polyline5_vs_reversed"]
    closed_pair = pairs["polyline5_vs_closed_from_polyline5"]

    assert reversed_pair["comparison_confidence"] == "provisional"
    assert closed_pair["comparison_confidence"] == "provisional"
    assert reversed_pair["tag_family_preserved_coordinates"]
    assert closed_pair["tag_family_preserved_coordinates"]
    assert reversed_pair["tag_family_added_coordinates"] == []
    assert closed_pair["tag_family_added_coordinates"] == []
    assert reversed_pair["tag_family_removed_coordinates"] == []
    assert closed_pair["tag_family_removed_coordinates"] == []
