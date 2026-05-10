from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
CLI_PATH = REPO_ROOT / "tools" / "analyze_polygon_candidate_evidence.py"


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


def test_rotated_start_and_closed_open_comparison_is_reported() -> None:
    result = _run_cli(["--json"])
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    comps = payload["comparisons"]

    c1 = comps["polygon_6_vs_rotated_start"]
    assert c1["base_unknown_03_point"]["raw_tag"].endswith("03")
    assert c1["rotated_unknown_03_point"]["raw_tag"].endswith("03")

    c2 = comps["polygon5_vs_polyline_from_polygon5"]
    assert c2["closed_fixture"] == "polygon_5_sides.txt"
    assert c2["open_fixture"] == "polyline_from_polygon_5_points.txt"
    assert c2["closed_unknown_03_count"] >= 0
    assert c2["open_unknown_03_count"] >= 0

