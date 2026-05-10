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


def test_polygon6_session2_pairwise_lowbyte_and_fulltag_evidence() -> None:
    result = _run_cli(["--json"])
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    pair = payload["pairwise_comparisons"]["polygon6_vs_session2"]

    assert pair["comparison_confidence"] == "provisional"
    assert pair["base_fixture"] == "polygon_6_sides.txt"
    assert pair["other_fixture"] == "polygon_6_sides_session2.txt"
    assert pair["base_03_coordinates_mm"]
    assert "other_03_coordinates_mm" in pair
    assert pair["low_byte_preserved_coordinates"]
    assert pair["full_tag_changed_coordinates"]
    assert pair["high_byte_changed_coordinates"]
    assert "session_effect_conclusion" in pair
