import json
import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
CLI_PATH = REPO_ROOT / "tools" / "validate_cparagraphe_field_offsets.py"


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


def test_field_offset_validation_text_mode_runs():
    result = _run([])
    assert result.returncode == 0, result.stderr
    out = result.stdout
    assert "Expected-value scoring summary" in out
    assert "Best field-start candidates" in out
    assert "candidate_text_height" in out
    assert "candidate_rotation_angle" in out
    assert "candidate_text_color" in out
    assert "Text color byte-order validation" in out
    assert "Parser update status: not applied" in out
    assert "diagnostic_only" in out


def test_field_offset_validation_json_mode_schema():
    result = _run(["--json"])
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["policy"]["absolute_offset"] == "diagnostic_only"
    assert payload["policy"]["parser_update"] == "not_applied"
    assert "expected_value_scoring_summary" in payload
    assert "best_field_start_candidates" in payload
    assert "text_color_byte_order_validation" in payload
    assert "field_validation_details" in payload
    assert "cross_record_consistency" in payload
