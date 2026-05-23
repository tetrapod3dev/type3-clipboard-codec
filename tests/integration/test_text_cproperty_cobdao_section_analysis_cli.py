from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
CLI_PATH = REPO_ROOT / "tools" / "analyze_text_cproperty_anchor_context.py"


def _run(args: list[str]) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO_ROOT / "src")
    return subprocess.run(
        [sys.executable, str(CLI_PATH), *args],
        text=True,
        capture_output=True,
        cwd=str(REPO_ROOT),
        env=env,
        timeout=180,
    )


def test_cobdao_section_analysis_safe_summary_default() -> None:
    result = _run(["--json"])
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["mode"] == "safe_summary"
    assert payload["summary"]["heavy_sections_included"] is False


def test_cobdao_section_analysis_deep_smoke_small_limits() -> None:
    result = _run(["--json", "--deep", "--max-sections", "2", "--max-output-rows", "10"])
    assert result.returncode == 0, result.stderr
    assert len(result.stdout) < 200_000
    payload = json.loads(result.stdout)
    assert "policy" in payload
    assert payload["policy"]["parser_behavior"] == "not_modified"
    assert payload["limits"]["max_total_cobdao_sections"] == 8
