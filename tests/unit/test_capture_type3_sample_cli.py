from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace


def _load_cli_module():
    repo_root = Path(__file__).resolve().parents[2]
    cli_path = repo_root / "tools" / "capture_type3_sample.py"
    spec = importlib.util.spec_from_file_location("capture_type3_sample_cli", cli_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _FakeClipboardAdapter:
    payload = b"\x00\x11\x22\x33\x00\xff"
    version_payload = b"\x01\x00\x00\x00\x51\x02\x00\x00" + (b"\x00" * 24)
    has_zone = True
    has_version = True

    def get_typeeditzone_format_id(self) -> int:
        return 50107

    def get_typeeditzone_version_format_id(self) -> int:
        return 50108

    def has_typeeditzone(self) -> bool:
        return self.has_zone

    def has_typeeditzone_version(self) -> bool:
        return self.has_version

    def read_typeeditzone_bytes(self) -> bytes:
        return self.payload

    def read_typeeditzone_version_bytes(self) -> bytes:
        return self.version_payload


class _FakeInspectService:
    fail = False

    def inspect(self, adapter, verbose: bool = False) -> str:
        if self.fail:
            raise RuntimeError("inspect boom")
        data = adapter.fetch_data()
        return f"inspect len={len(data)} verbose={verbose}"


def _patch_common(monkeypatch, tmp_path: Path):
    module = _load_cli_module()
    monkeypatch.setattr(module, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(module, "Win32ClipboardAdapter", _FakeClipboardAdapter)
    monkeypatch.setattr(module, "InspectService", _FakeInspectService)
    monkeypatch.setattr(
        module,
        "parse_type3_clipboard_bytes_with_parser",
        lambda data: (
            SimpleNamespace(
                object_type="geometry",
                raw_size=len(data),
                markers=["CZone"],
                object_chains=[],
            ),
            "FakeParser",
        ),
    )
    _FakeClipboardAdapter.payload = b"\x00\x11\x22\x33\x00\xff"
    _FakeClipboardAdapter.version_payload = b"\x01\x00\x00\x00\x51\x02\x00\x00" + (b"\x00" * 24)
    _FakeClipboardAdapter.has_zone = True
    _FakeClipboardAdapter.has_version = True
    _FakeInspectService.fail = False
    return module


def test_capture_geometry_category_creates_expected_paths(monkeypatch, tmp_path: Path) -> None:
    module = _patch_common(monkeypatch, tmp_path)

    rc = module.main(["--name", "default_rectangle", "--category", "geometry", "--description", "rect"])

    assert rc == 0
    assert (tmp_path / "tests/samples/default_rectangle.txt").exists()
    assert (tmp_path / "tests/samples/bundles/geometry/default_rectangle/typeeditzone.bin").read_bytes() == (
        _FakeClipboardAdapter.payload
    )
    assert (tmp_path / "tests/samples/bundles/geometry/default_rectangle/typeeditzone_version.bin").read_bytes() == (
        _FakeClipboardAdapter.version_payload
    )
    assert (tmp_path / "tests/samples/intents/geometry/default_rectangle.md").exists()


def test_capture_text_category_creates_expected_paths_and_hex_roundtrip(monkeypatch, tmp_path: Path) -> None:
    module = _patch_common(monkeypatch, tmp_path)

    rc = module.main(["--name", "default_text_capture", "--category", "text"])

    fixture = tmp_path / "tests/samples/text/default_text_capture.txt"
    assert rc == 0
    assert module.hex_text_to_bytes(fixture.read_text(encoding="utf-8")) == _FakeClipboardAdapter.payload
    assert (tmp_path / "tests/samples/bundles/text/default_text_capture/manifest.json").exists()
    assert (tmp_path / "tests/samples/reports/text/default_text_capture.inspect.txt").exists()
    assert (tmp_path / "tests/samples/reports/text/default_text_capture.inspect.json").exists()


def test_existing_file_without_overwrite_fails(monkeypatch, tmp_path: Path) -> None:
    module = _patch_common(monkeypatch, tmp_path)
    fixture = tmp_path / "tests/samples/existing.txt"
    fixture.parent.mkdir(parents=True)
    fixture.write_text("aa", encoding="utf-8")

    rc = module.main(["--name", "existing", "--category", "geometry"])

    assert rc == 2
    assert fixture.read_text(encoding="utf-8") == "aa"


def test_overwrite_replaces_existing_file(monkeypatch, tmp_path: Path) -> None:
    module = _patch_common(monkeypatch, tmp_path)
    fixture = tmp_path / "tests/samples/existing.txt"
    fixture.parent.mkdir(parents=True)
    fixture.write_text("aa", encoding="utf-8")

    rc = module.main(["--name", "existing", "--category", "geometry", "--overwrite"])

    assert rc == 0
    assert module.hex_text_to_bytes(fixture.read_text(encoding="utf-8")) == _FakeClipboardAdapter.payload


def test_manifest_contains_expected_fields(monkeypatch, tmp_path: Path) -> None:
    module = _patch_common(monkeypatch, tmp_path)

    rc = module.main(["--name", "sample1", "--category", "text", "--description", "desc"])

    manifest_path = tmp_path / "tests/samples/bundles/text/sample1/manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert rc == 0
    assert manifest["sample_name"] == "sample1"
    assert manifest["category"] == "text"
    assert manifest["typeeditzone_size"] == len(_FakeClipboardAdapter.payload)
    assert manifest["typeeditzone_version_size"] == len(_FakeClipboardAdapter.version_payload)
    assert manifest["format_names"]["typeeditzone"] == "TypeEditZone"
    assert manifest["observed_format_ids"]["typeeditzone_version"] == 50108
    assert manifest["description"] == "desc"
    assert manifest["source"] == "windows_clipboard"


def test_intent_markdown_includes_user_fields(monkeypatch, tmp_path: Path) -> None:
    module = _patch_common(monkeypatch, tmp_path)

    rc = module.main(
        [
            "--name",
            "text_case",
            "--category",
            "text",
            "--object-count",
            "2",
            "--grouping",
            "not_grouped",
            "--text",
            "abcdefg|1234567890",
            "--anchors",
            "111.111,222.222,0;211.111,322.222,0",
            "--color",
            "Army Green",
        ]
    )

    intent = (tmp_path / "tests/samples/intents/text/text_case.md").read_text(encoding="utf-8")
    assert rc == 0
    assert "selected/copied object count: 2" in intent
    assert "grouped/not grouped: not_grouped" in intent
    assert "text content: abcdefg|1234567890" in intent
    assert "color: Army Green" in intent
    assert "anchor / position: 111.111,222.222,0;211.111,322.222,0" in intent


def test_print_readme_snippet_outputs_without_modifying_readme(monkeypatch, tmp_path: Path, capsys) -> None:
    module = _patch_common(monkeypatch, tmp_path)

    rc = module.main(["--name", "snippet_case", "--category", "text", "--print-readme-snippet"])

    out = capsys.readouterr().out
    assert rc == 0
    assert "### `snippet_case.txt`" in out
    assert "bundle: `tests\\samples\\bundles\\text\\snippet_case/`" in out or "bundle: `tests/samples/bundles/text/snippet_case/`" in out
    assert not (tmp_path / "README.md").exists()


def test_git_add_uses_generated_files_only(monkeypatch, tmp_path: Path) -> None:
    module = _patch_common(monkeypatch, tmp_path)
    calls = []

    def fake_run(cmd, cwd=None, check=False):
        calls.append((cmd, cwd, check))
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(module.subprocess, "run", fake_run)

    rc = module.main(["--name", "git_case", "--category", "geometry", "--git-add"])

    assert rc == 0
    assert len(calls) == 1
    cmd, cwd, check = calls[0]
    assert cmd[0:2] == ["git", "add"]
    assert cwd == str(tmp_path)
    assert check is True
    assert all("git_case" in item for item in cmd[2:])


def test_inspect_failure_still_writes_fixture_and_error_report(monkeypatch, tmp_path: Path) -> None:
    module = _patch_common(monkeypatch, tmp_path)
    _FakeInspectService.fail = True

    rc = module.main(["--name", "inspect_fail", "--category", "geometry"])

    assert rc == 0
    assert (tmp_path / "tests/samples/inspect_fail.txt").exists()
    report = json.loads((tmp_path / "tests/samples/reports/geometry/inspect_fail.inspect.json").read_text(encoding="utf-8"))
    assert report["status"] == "error"
    assert "inspect boom" in report["error"]
