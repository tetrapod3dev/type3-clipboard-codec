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


def test_polygon_candidate_evidence_cli_text_contains_required_sections() -> None:
    result = _run_cli([])
    assert result.returncode == 0, result.stderr
    assert "Polygon Candidate Evidence Analysis" in result.stdout
    assert "[polygon_5_sides.txt]" in result.stdout
    assert "[polygon_6_sides.txt]" in result.stdout
    assert "record_table:" in result.stdout
    assert "closure_detail:" in result.stdout


def test_polygon_candidate_evidence_cli_json_includes_unknown_and_closed_sources() -> None:
    result = _run_cli(["--json"])
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    fixtures = {item["fixture"]: item for item in payload["fixtures"]}

    p6 = fixtures["polygon_6_sides.txt"]
    assert p6["record_count"] == 6
    assert p6["anchor_record_count"] + p6["unknown_record_count"] >= 6 - p6["control_record_count"]
    assert "closed_like_evidence_sources" in p6
    assert len(p6["record_table"]) == 6
    assert any(row["assigned_role"] == "unknown" for row in p6["record_table"])
    assert "kind_observed" in p6["closure_evidence_detail"]

