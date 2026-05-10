from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
CLI_PATH = REPO_ROOT / "tools" / "report_contour_header_candidates.py"


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


def test_contour_header_report_cli_text_output_contains_required_sections():
    result = _run_cli([])
    assert result.returncode == 0, result.stderr
    assert "Type3 Contour Header Candidate Report (Geometry Fixtures)" in result.stdout
    assert "[Per Fixture Selected Header]" in result.stdout
    assert "[Selected Shift Distribution]" in result.stdout
    assert "[Rejection Reason Distribution]" in result.stdout
    assert "[Candidate Shift Observations]" in result.stdout
    assert "policy: absolute offset is diagnostic only" in result.stdout
    assert "shift=8" in result.stdout


def test_contour_header_report_cli_json_output_has_raw_header_and_shift_distribution():
    result = _run_cli(["--json"])
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)

    fixture_rows = payload["fixture_selected"]
    focus = {
        row["fixture"]: row
        for row in fixture_rows
        if row["fixture"] in {
            "default_rectangle.txt",
            "default_circle.txt",
            "default_circular_arc.txt",
            "default_rounded_rectangle.txt",
        }
    }
    assert len(focus) == 4
    for item in focus.values():
        assert item["selected_shift"] == 8
        assert isinstance(item["selected_raw_header_hex"], str)
        assert len(item["selected_raw_header_hex"]) == 16
        assert isinstance(item["selected_count"], int)

    shift_dist = payload["selected_shift_distribution"]
    assert "8" in shift_dist or 8 in shift_dist
    assert payload["policy"].endswith("remains provisional")
