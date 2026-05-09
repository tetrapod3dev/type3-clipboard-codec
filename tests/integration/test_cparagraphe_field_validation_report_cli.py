import json
import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
CLI_PATH = REPO_ROOT / "tools" / "report_cparagraphe_field_validation.py"


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


def test_report_cli_text_mode_sections():
    result = _run([])
    assert result.returncode == 0, result.stderr
    out = result.stdout
    assert "Best offset validation summary" in out
    assert "Parser candidate readiness summary" in out
    assert "Text color byte-order detail" in out
    assert "Parser update status: not applied" in out


def test_report_cli_json_schema():
    result = _run(["--json"])
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["policy"]["parser_update"] == "not_applied"
    assert "best_offset_validation_summary" in payload
    assert "parser_candidate_readiness_summary" in payload
    assert "text_color_byte_order_detail" in payload
    assert "provisional_record_type_classification" in payload
