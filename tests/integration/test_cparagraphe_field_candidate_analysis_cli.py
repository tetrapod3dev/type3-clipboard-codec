import json
import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
CLI_PATH = REPO_ROOT / "tools" / "analyze_cparagraphe_field_candidates.py"


def _run(args: list[str]) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO_ROOT / "src")
    return subprocess.run(
        [sys.executable, str(CLI_PATH), *args],
        text=True,
        capture_output=True,
        cwd=str(REPO_ROOT),
        env=env,
        timeout=240,
    )


def test_field_candidate_cli_text_mode_reports_core_signals():
    result = _run([])
    assert result.returncode == 0, result.stderr
    out = result.stdout
    assert "Paired comparison summary" in out
    assert "Ranked field candidate summary" in out
    assert "candidate_text_height" in out
    assert "candidate_width_percent" in out
    assert "candidate_rotation_angle" in out
    assert "candidate_text_color" in out
    assert "record_relative_offset" in out or "record_relative_offset_hex" in out
    assert "diagnostic_only" in out


def test_field_candidate_cli_json_mode_reports_candidates():
    result = _run(["--json"])
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["policy"]["absolute_offset"] == "diagnostic_only"
    assert payload["policy"]["parser_update"] == "not_applied"
    assert "paired_comparisons" in payload
    assert "ranked_field_candidates" in payload
    assert "multiline_pre_record_window" in payload
