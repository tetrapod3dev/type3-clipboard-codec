import json
import subprocess
import sys
import os
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
CLI_PATH = REPO_ROOT / "tools" / "inspect_clipboard_hex.py"
SAMPLES_DIR = REPO_ROOT / "tests" / "samples"


def _run_cli(args: list[str], input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO_ROOT / "src")
    return subprocess.run(
        [sys.executable, str(CLI_PATH), *args],
        input=input_text,
        text=True,
        capture_output=True,
        cwd=str(REPO_ROOT),
        env=env,
        timeout=30,
    )


def test_cli_file_mode_default_rectangle_summary():
    result = _run_cli([str(SAMPLES_DIR / "default_rectangle.txt")])
    assert result.returncode == 0, result.stderr
    assert "TYPE3 Clipboard Hex Inspector" in result.stdout
    assert "Parsed objects: 1" in result.stdout
    assert "[Object #1]" in result.stdout


def test_cli_file_mode_two_rectangle_includes_two_objects():
    result = _run_cli([str(SAMPLES_DIR / "two_rectangle.txt")])
    assert result.returncode == 0, result.stderr
    assert "Parsed objects: 2" in result.stdout
    assert "[Object #1]" in result.stdout
    assert "[Object #2]" in result.stdout


def test_cli_file_mode_two_rectangle_group_includes_결합():
    result = _run_cli([str(SAMPLES_DIR / "two_rectangle_group.txt")])
    assert result.returncode == 0, result.stderr
    assert "Detected structure: grouped / 결합 candidate" in result.stdout
    assert "Korean Type3 term: 결합" in result.stdout


def test_cli_file_mode_default_text_reports_text_info():
    result = _run_cli([str(SAMPLES_DIR / "text" / "default_text.txt")])
    assert result.returncode == 0, result.stderr
    assert "Text object info:" in result.stdout
    assert "font_name:" in result.stdout


def test_cli_json_mode_emits_valid_json():
    result = _run_cli([str(SAMPLES_DIR / "default_rectangle.txt"), "--json"])
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["raw_size"] > 0
    assert payload["parser"] == "Type3ChainParser"
    assert isinstance(payload["objects"], list)


@pytest.mark.parametrize(
    ("filename", "expected_name", "expected_hex"),
    [
        ("color_black_rectangle.txt", "Black", "#000000"),
        ("color_blue_rectangle.txt", "Blue", "#000080"),
        ("color_green_rectangle.txt", "Green", "#008000"),
        ("color_cyan_rectangle.txt", "Cyan", "#008080"),
        ("color_light_cyan_rectangle.txt", "Light Cyan", "#00FFFF"),
    ],
)
def test_cli_color_fixture_json_includes_color_name_and_hex(filename, expected_name, expected_hex):
    result = _run_cli([str(SAMPLES_DIR / filename), "--json"])
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    style = payload["objects"][0]["style_candidates"]
    assert style["line_color_name"] == expected_name
    assert style["line_color_hex"] == expected_hex


@pytest.mark.parametrize(
    ("filename", "expected_name", "expected_hex"),
    [
        ("color_black_rectangle.txt", "Black", "#000000"),
        ("color_blue_rectangle.txt", "Blue", "#000080"),
        ("color_green_rectangle.txt", "Green", "#008000"),
        ("color_cyan_rectangle.txt", "Cyan", "#008080"),
        ("color_light_cyan_rectangle.txt", "Light Cyan", "#00FFFF"),
    ],
)
def test_cli_color_fixture_text_includes_style_block(filename, expected_name, expected_hex):
    result = _run_cli([str(SAMPLES_DIR / filename)])
    assert result.returncode == 0, result.stderr
    assert "Style:" in result.stdout
    assert f"Line color: {expected_name} ({expected_hex})" in result.stdout


def test_cli_group_json_has_non_empty_color_candidates():
    result = _run_cli([str(SAMPLES_DIR / "two_rectangle_group.txt"), "--json"])
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    group_obj = payload["objects"][0]
    assert group_obj["object_type"] == "group"
    group_style = group_obj.get("style_candidates")
    if group_style is not None:
        assert len(group_style.get("color_candidates") or []) > 0
    else:
        child_candidates = []
        for child in group_obj.get("children", []):
            child_candidates.extend(child.get("style_candidates", {}).get("color_candidates", []))
        assert len(child_candidates) > 0


@pytest.mark.parametrize(
    ("filename", "expected_name", "expected_hex"),
    [
        ("two_rectangle_group_navy_blue.txt", "Navy Blue", "#3060CC"),
        ("two_rectangle_group_army_green.txt", "Army Green", "#98CC98"),
    ],
)
def test_cli_group_color_samples_include_detected_color(filename, expected_name, expected_hex):
    result = _run_cli([str(SAMPLES_DIR / filename)])
    assert result.returncode == 0, result.stderr
    assert f"Line color: {expected_name} ({expected_hex})" in result.stdout


def test_cli_mixed_color_rectangles_show_both_colors():
    result = _run_cli([str(SAMPLES_DIR / "turquoise_rectangle_and_army_green_rectangle.txt")])
    assert result.returncode == 0, result.stderr
    assert "Line color: Turquoise (#64FFCC)" in result.stdout
    assert "Line color: Army Green (#98CC98)" in result.stdout


def test_cli_diff_mode_outputs_structural_comparison():
    result = _run_cli(
        [
            "--diff",
            str(SAMPLES_DIR / "two_rectangle.txt"),
            str(SAMPLES_DIR / "two_rectangle_group.txt"),
        ]
    )
    assert result.returncode == 0, result.stderr
    assert "TYPE3 Clipboard Hex Diff" in result.stdout
    assert "Changed byte ranges:" in result.stdout
    assert "declared object count changed" in result.stdout


def test_cli_invalid_hex_input_exits_cleanly():
    result = _run_cli([], input_text="GG\n\n")
    assert result.returncode != 0
    assert "[ERROR]" in result.stderr


def test_cli_debug_style_outputs_offsets_and_confidence():
    result = _run_cli([str(SAMPLES_DIR / "color_light_cyan_rectangle.txt"), "--debug-style"])
    assert result.returncode == 0, result.stderr
    assert "STYLE DEBUG" in result.stdout
    assert "fixed[121]=0x0000FFFF" in result.stdout
    assert "fixed[133]=0x0000FFFF" in result.stdout
    assert "chosen color: Light Cyan (#00FFFF)" in result.stdout
    assert "confidence=confirmed" in result.stdout
