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


def test_tag_role_evidence_cli_text_runs() -> None:
    result = _run_cli([])
    assert result.returncode == 0, result.stderr
    assert "Contour Tag/Role Evidence Analysis" in result.stdout
    assert "Unknown Tag Family Summary" in result.stdout
    assert "polygon_6_sides.txt" in result.stdout
    assert "polygon_6_sides_session2.txt" in result.stdout
    assert "polyline_5_points_session2.txt" in result.stdout
    assert "polyline_5_points_reversed.txt" in result.stdout
    assert "closed_from_polyline_5_points.txt" in result.stdout
    assert "[Pairwise Comparisons]" in result.stdout


def test_tag_role_evidence_cli_json_reports_unknown_03_and_arc_control() -> None:
    result = _run_cli(["--json"])
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)

    families = {f["family_low_byte"]: f for f in payload["unknown_tag_family_summary"]}
    assert "0x03" in families
    assert "0x0C" in families

    focus = payload["fixture_record_table_focus"]
    assert any(r["fixture"] == "polygon_6_sides.txt" and r["raw_tag"] == "0x48454C03" and r["current_role"] == "unknown" for r in focus)
    assert any(r["fixture"] == "default_circular_arc.txt" and r["current_role"] == "control" and r["low_byte"] == "0x0C" for r in focus)
    assert any(r["fixture"] == "polyline_5_points_reversed.txt" for r in focus)
    assert any(r["fixture"] == "closed_from_polyline_5_points.txt" for r in focus)
    pairs = payload["pairwise_comparisons"]
    assert "polyline5_vs_reversed" in pairs
    assert "polyline5_vs_closed_from_polyline5" in pairs
    assert "polyline5_vs_session2" in pairs
    assert "polygon6_vs_session2" in pairs
    assert pairs["polyline5_vs_reversed"]["comparison_confidence"] == "provisional"
