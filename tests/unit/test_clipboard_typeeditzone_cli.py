from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_cli_module():
    repo_root = Path(__file__).resolve().parents[2]
    cli_path = repo_root / "tools" / "clipboard_typeeditzone.py"
    spec = importlib.util.spec_from_file_location("clipboard_typeeditzone_cli", cli_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _FakeClipboardAdapter:
    payload = b""
    written = b""
    has_value = True
    formats = [13, 50107]
    format_id = 50107

    def get_typeeditzone_format_id(self) -> int:
        return self.format_id

    def has_typeeditzone(self) -> bool:
        return self.has_value

    def list_formats(self) -> list[int]:
        return list(self.formats)

    def read_typeeditzone_bytes(self) -> bytes:
        return self.payload

    def write_typeeditzone_bytes(self, data: bytes) -> None:
        type(self).written = data


def test_probe_runs_with_mock_adapter(monkeypatch, capsys) -> None:
    module = _load_cli_module()
    monkeypatch.setattr(module, "Win32ClipboardAdapter", _FakeClipboardAdapter)

    rc = module.main(["probe"])

    out = capsys.readouterr().out
    assert rc == 0
    assert "format_name=TypeEditZone" in out
    assert "registered_format_id=50107" in out


def test_dump_and_load_keep_bytes_equal(monkeypatch, tmp_path: Path) -> None:
    module = _load_cli_module()
    _FakeClipboardAdapter.payload = b"\x00\x11\x22\x00\xff\x00"
    _FakeClipboardAdapter.written = b""
    monkeypatch.setattr(module, "Win32ClipboardAdapter", _FakeClipboardAdapter)

    dump_path = tmp_path / "typeeditzone.bin"
    dump_rc = module.main(["dump", "--out", str(dump_path)])
    assert dump_rc == 0
    dumped = dump_path.read_bytes()
    assert dumped == _FakeClipboardAdapter.payload

    load_rc = module.main(["load", "--in", str(dump_path)])
    assert load_rc == 0
    assert _FakeClipboardAdapter.written == dumped


def test_dump_hex_writes_expected_hex_text(monkeypatch, tmp_path: Path) -> None:
    module = _load_cli_module()
    _FakeClipboardAdapter.payload = b"\x00\xab\xcd\xef"
    monkeypatch.setattr(module, "Win32ClipboardAdapter", _FakeClipboardAdapter)

    out_path = tmp_path / "typeeditzone.hex.txt"
    rc = module.main(["dump-hex", "--out", str(out_path)])

    assert rc == 0
    assert out_path.read_text(encoding="utf-8") == "00abcdef"


def test_inspect_reads_file_and_prints_preview(monkeypatch, tmp_path: Path, capsys) -> None:
    module = _load_cli_module()
    monkeypatch.setattr(module, "Win32ClipboardAdapter", _FakeClipboardAdapter)

    class _FakeInspectService:
        def inspect(self, adapter, verbose: bool = False) -> str:
            data = adapter.fetch_data()
            return f"len={len(data)} verbose={verbose}"

    monkeypatch.setattr(module, "InspectService", _FakeInspectService)

    in_path = tmp_path / "sample.bin"
    in_path.write_bytes(b"\x00\x01\x02\x03")

    rc = module.main(["inspect", "--in", str(in_path)])

    out = capsys.readouterr().out
    assert rc == 0
    assert "len=4 verbose=True" in out
