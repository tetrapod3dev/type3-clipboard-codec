from __future__ import annotations

import importlib.util
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


def test_safe_summary_text_mode_is_small_and_lightweight() -> None:
    result = _run([])
    assert result.returncode == 0, result.stderr
    out = result.stdout

    assert len(out) < 100_000
    assert "safe lightweight summary only" in out
    assert "heavy_sections_included: false" in out
    assert "local_context_hex" not in out
    assert "[CObDao section scan]" not in out


def test_safe_summary_json_mode_is_small_and_structured() -> None:
    result = _run(["--json"])
    assert result.returncode == 0, result.stderr
    assert len(result.stdout) < 200_000
    payload = json.loads(result.stdout)

    assert payload.get("mode") == "safe_summary" or payload["policy"]["scope"] == "safe lightweight summary only"
    assert "limits" in payload
    assert "warnings" in payload
    assert "truncated" in payload
    assert payload["summary"]["heavy_sections_included"] is False
    assert payload["fixtures"]
    first = payload["fixtures"][0]
    assert "fixture" in first
    assert "node_count" in first
    assert "cproperty_node_count" in first
    assert "cparagraphe_node_count" in first
    assert "cproperty_nodes" not in first


def test_deep_mode_smoke_with_small_limits() -> None:
    result = _run(["--json", "--deep", "--max-sections", "2", "--max-output-rows", "10"])
    assert result.returncode == 0, result.stderr
    assert len(result.stdout) < 200_000
    payload = json.loads(result.stdout)
    assert "limits" in payload
    assert payload["limits"]["max_total_cobdao_sections"] == 8
    assert payload["limits"]["max_output_rows"] == 40
    assert payload["policy"]["parser_behavior"] == "not_modified"


def test_marker_scan_helper_truncates_by_iteration_limit() -> None:
    spec = importlib.util.spec_from_file_location("anchor_context_analyzer", CLI_PATH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules["anchor_context_analyzer"] = module
    spec.loader.exec_module(module)

    module._ACTIVE_CONTEXT = module.AnalysisContext(limits=module.AnalysisLimits(max_marker_scan_iterations=2))
    positions = module._marker_positions(b"aaaa", b"a")

    assert positions == [0, 1]
    assert module._ACTIVE_CONTEXT.truncated is True
    assert any("marker scan truncated" in warning for warning in module._ACTIVE_CONTEXT.warnings)
