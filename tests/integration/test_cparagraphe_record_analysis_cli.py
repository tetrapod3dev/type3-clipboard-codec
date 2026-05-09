import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
CLI_PATH = REPO_ROOT / "tools" / "analyze_cparagraphe_records.py"


def test_cparagraphe_record_analysis_cli_runs_and_reports_record_fields():
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO_ROOT / "src")
    result = subprocess.run(
        [sys.executable, str(CLI_PATH)],
        text=True,
        capture_output=True,
        cwd=str(REPO_ROOT),
        env=env,
        timeout=240,
    )
    assert result.returncode == 0, result.stderr
    out = result.stdout
    assert "CParagraphe 204-byte Record Analyzer" in out
    assert "candidate_stride=204" in out
    assert "candidate_start_offset=47" in out
    assert "record_relative_offset" in out
    assert "diagnostic only" in out
    assert "left=default_text.txt right=text_height_30mm.txt" in out
    assert "Field map candidate summary" in out
