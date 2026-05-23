from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
CLI_PATH = REPO_ROOT / "tools" / "analyze_text_cproperty_anchor_record_semantics.py"


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


def _hex_byte_len(hex_text: str) -> int:
    stripped = hex_text.strip()
    if not stripped:
        return 0
    return len(stripped.split(" "))


def test_anchor_record_semantics_text_mode_is_small() -> None:
    result = _run([])
    assert result.returncode == 0, result.stderr
    assert len(result.stdout) < 50_000
    assert "Text CPropertyExtend Anchor Record Semantics (Small Analyzer)" in result.stdout
    assert "parser_behavior: not_modified" in result.stdout


def test_anchor_record_semantics_json_mode_is_small_and_valid() -> None:
    result = _run(["--json"])
    assert result.returncode == 0, result.stderr
    assert len(result.stdout) < 100_000
    payload = json.loads(result.stdout)

    for key in (
        "mode",
        "limits",
        "warnings",
        "fixtures",
        "signature_v1_summary",
        "record_layout_candidate",
        "semantic_hypothesis",
        "answers",
    ):
        assert key in payload
    assert payload["answers"]["parser_behavior"] == "not_modified"
    assert payload["signature_v1_summary"]["signature_name"] == "CPropertyExtend_CObDao_anchor_record_candidate_v1"

    max_bytes = payload["limits"]["max_local_hex_bytes"]
    for fixture in payload["fixtures"]:
        for row in fixture["anchor_record_sections"]:
            assert _hex_byte_len(row["local_context_hex"]) <= max_bytes


def test_anchor_record_semantics_fixture_and_limit_options() -> None:
    result = _run(
        [
            "--json",
            "--fixture",
            "text_three_objects_grouped_order_abc.txt",
            "--max-fixtures",
            "1",
            "--max-anchor-sections",
            "2",
            "--max-local-hex-bytes",
            "32",
        ]
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["limits"]["max_fixtures"] == 1
    assert payload["limits"]["max_anchor_sections"] == 2
    assert payload["limits"]["max_local_hex_bytes"] == 32
    assert len(payload["fixtures"]) <= 1
    if payload["fixtures"]:
        assert payload["fixtures"][0]["anchor_record_section_count"] <= 2
