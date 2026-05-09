import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
CLI_PATH = REPO_ROOT / "tools" / "analyze_cparagraphe_structure.py"


def test_cparagraphe_structure_cli_runs_and_reports_core_fields():
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO_ROOT / "src")
    result = subprocess.run(
        [sys.executable, str(CLI_PATH)],
        text=True,
        capture_output=True,
        cwd=str(REPO_ROOT),
        env=env,
        timeout=180,
    )
    assert result.returncode == 0, result.stderr
    out = result.stdout
    assert "CParagraphe Structure Analysis" in out
    assert "[FILE] default_text.txt" in out
    assert "class=CParagraphe" in out
    assert "class_payload_relative_offset" in out
    assert "Policy: absolute offset is diagnostic only." in out
    assert "changed_ranges=" in out
