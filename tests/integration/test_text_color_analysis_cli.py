import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
CLI_PATH = REPO_ROOT / "tools" / "analyze_text_color_diff.py"


def test_analyze_text_color_diff_cli_runs_and_reports_ranges():
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO_ROOT / "src")
    result = subprocess.run(
        [sys.executable, str(CLI_PATH)],
        text=True,
        capture_output=True,
        cwd=str(REPO_ROOT),
        env=env,
        timeout=120,
    )
    assert result.returncode == 0, result.stderr
    assert "Type3 Text Color Diff Analysis" in result.stdout
    assert "changed_ranges:" in result.stdout
    assert "palette_candidates:" in result.stdout
    assert "diagnostic only" in result.stdout
    assert "class_payload_relative_offset=" in result.stdout
