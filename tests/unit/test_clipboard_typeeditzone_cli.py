from __future__ import annotations

import importlib.util
import json
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
    version_payload = b""
    written = b""
    written_bundle: tuple[bytes, bytes] | None = None
    has_value = True
    has_version_value = True
    formats = [13, 50107]
    format_id = 50107
    version_format_id = 50108

    def get_typeeditzone_format_id(self) -> int:
        return self.format_id

    def get_typeeditzone_version_format_id(self) -> int:
        return self.version_format_id

    def has_typeeditzone(self) -> bool:
        return self.has_value

    def has_typeeditzone_version(self) -> bool:
        return self.has_version_value

    def list_formats(self) -> list[int]:
        return list(self.formats)

    def read_typeeditzone_bytes(self) -> bytes:
        return self.payload

    def read_typeeditzone_version_bytes(self) -> bytes:
        return self.version_payload

    def fetch_data(self) -> bytes:
        return self.read_typeeditzone_bytes()

    def write_typeeditzone_bytes(self, data: bytes) -> None:
        type(self).written = data

    def write_typeeditzone_bundle(self, zone_bytes: bytes, version_bytes: bytes) -> None:
        type(self).written_bundle = (zone_bytes, version_bytes)


def test_probe_runs_with_mock_adapter(monkeypatch, capsys) -> None:
    module = _load_cli_module()
    monkeypatch.setattr(module, "Win32ClipboardAdapter", _FakeClipboardAdapter)

    rc = module.main(["probe"])

    out = capsys.readouterr().out
    assert rc == 0
    assert "format_name=TypeEditZone" in out
    assert "registered_format_id=50107" in out
    assert "version_format_name=TypeEditZoneVersion" in out
    assert "version_registered_format_id=50108" in out
    assert "version_observed_format_id=50108" in out
    assert "has_typeeditzone_version=true" in out


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


def test_dump_version_keeps_bytes_equal(monkeypatch, tmp_path: Path) -> None:
    module = _load_cli_module()
    _FakeClipboardAdapter.version_payload = b"\x01\x00\x00\x00\x51\x02\x00\x00\x00\x00\x00\x00"
    monkeypatch.setattr(module, "Win32ClipboardAdapter", _FakeClipboardAdapter)

    dump_path = tmp_path / "typeeditzone_version.bin"
    dump_rc = module.main(["dump-version", "--out", str(dump_path)])

    assert dump_rc == 0
    assert dump_path.read_bytes() == _FakeClipboardAdapter.version_payload


def test_load_with_version_in_passes_zone_and_version_bytes(monkeypatch, tmp_path: Path) -> None:
    module = _load_cli_module()
    _FakeClipboardAdapter.written = b""
    _FakeClipboardAdapter.written_bundle = None
    monkeypatch.setattr(module, "Win32ClipboardAdapter", _FakeClipboardAdapter)

    zone_path = tmp_path / "typeeditzone.bin"
    version_path = tmp_path / "typeeditzone_version.bin"
    zone_payload = b"\x00\x11\x22\x00\xff\x00"
    version_payload = b"\x01\x00\x00\x00\x51\x02\x00\x00\x00\x00\x00\x00"
    zone_path.write_bytes(zone_payload)
    version_path.write_bytes(version_payload)

    load_rc = module.main(["load", "--in", str(zone_path), "--version-in", str(version_path)])

    assert load_rc == 0
    assert _FakeClipboardAdapter.written == b""
    assert _FakeClipboardAdapter.written_bundle == (zone_payload, version_payload)


def test_dump_bundle_writes_files_and_manifest(monkeypatch, tmp_path: Path) -> None:
    module = _load_cli_module()
    _FakeClipboardAdapter.payload = b"\x00\x11\x22\x00\xff\x00"
    _FakeClipboardAdapter.version_payload = b"\x01\x00\x00\x00\x51\x02\x00\x00\x00\x00\x00\x00"
    monkeypatch.setattr(module, "Win32ClipboardAdapter", _FakeClipboardAdapter)

    bundle_dir = tmp_path / "bundle"
    rc = module.main(["dump-bundle", "--dir", str(bundle_dir)])

    assert rc == 0
    assert (bundle_dir / "typeeditzone.bin").read_bytes() == _FakeClipboardAdapter.payload
    assert (bundle_dir / "typeeditzone_version.bin").read_bytes() == _FakeClipboardAdapter.version_payload
    manifest = json.loads((bundle_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest == {
        "formats": [
            {
                "byte_length": len(_FakeClipboardAdapter.payload),
                "file_name": "typeeditzone.bin",
                "format_name": "TypeEditZone",
                "observed_id": 50107,
                "registered_id": 50107,
            },
            {
                "byte_length": len(_FakeClipboardAdapter.version_payload),
                "file_name": "typeeditzone_version.bin",
                "format_name": "TypeEditZoneVersion",
                "observed_id": 50108,
                "registered_id": 50108,
            },
        ]
    }


def test_load_bundle_passes_zone_and_version_bytes(monkeypatch, tmp_path: Path) -> None:
    module = _load_cli_module()
    _FakeClipboardAdapter.written_bundle = None
    monkeypatch.setattr(module, "Win32ClipboardAdapter", _FakeClipboardAdapter)

    bundle_dir = tmp_path / "bundle"
    bundle_dir.mkdir()
    zone_payload = b"\x00\x11\x22\x00\xff\x00"
    version_payload = b"\x01\x00\x00\x00\x51\x02\x00\x00\x00\x00\x00\x00"
    (bundle_dir / "typeeditzone.bin").write_bytes(zone_payload)
    (bundle_dir / "typeeditzone_version.bin").write_bytes(version_payload)
    (bundle_dir / "manifest.json").write_text(
        json.dumps(
            {
                "formats": [
                    {"format_name": "TypeEditZone", "file_name": "typeeditzone.bin"},
                    {"format_name": "TypeEditZoneVersion", "file_name": "typeeditzone_version.bin"},
                ]
            }
        ),
        encoding="utf-8",
    )

    rc = module.main(["load-bundle", "--dir", str(bundle_dir)])

    assert rc == 0
    assert _FakeClipboardAdapter.written_bundle == (zone_payload, version_payload)


def test_verify_bundle_returns_zero_when_both_payloads_match(monkeypatch, tmp_path: Path, capsys) -> None:
    module = _load_cli_module()
    _FakeClipboardAdapter.payload = b"\x00\x11\x22\x00\xff\x00"
    _FakeClipboardAdapter.version_payload = b"\x01\x00\x00\x00\x51\x02\x00\x00\x00\x00\x00\x00"
    monkeypatch.setattr(module, "Win32ClipboardAdapter", _FakeClipboardAdapter)

    bundle_dir = tmp_path / "bundle"
    bundle_dir.mkdir()
    (bundle_dir / "typeeditzone.bin").write_bytes(_FakeClipboardAdapter.payload)
    (bundle_dir / "typeeditzone_version.bin").write_bytes(_FakeClipboardAdapter.version_payload)

    rc = module.main(["verify-bundle", "--dir", str(bundle_dir)])

    out = capsys.readouterr().out
    assert rc == 0
    assert "typeeditzone_match=true" in out
    assert "typeeditzone_version_match=true" in out


def test_verify_bundle_returns_one_when_any_payload_mismatches(monkeypatch, tmp_path: Path, capsys) -> None:
    module = _load_cli_module()
    _FakeClipboardAdapter.payload = b"\x00\x11\x22"
    _FakeClipboardAdapter.version_payload = b"\x01\x00\x00\x00"
    monkeypatch.setattr(module, "Win32ClipboardAdapter", _FakeClipboardAdapter)

    bundle_dir = tmp_path / "bundle"
    bundle_dir.mkdir()
    (bundle_dir / "typeeditzone.bin").write_bytes(b"\x00\x11\x22")
    (bundle_dir / "typeeditzone_version.bin").write_bytes(b"\x01\x00\x00\x01")

    rc = module.main(["verify-bundle", "--dir", str(bundle_dir)])

    out = capsys.readouterr().out
    assert rc == 1
    assert "typeeditzone_match=true" in out
    assert "typeeditzone_version_match=false" in out
    assert "typeeditzone_version_expected_length=4" in out
    assert "typeeditzone_version_actual_length=4" in out


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


def test_inspect_clipboard_uses_adapter_fetch_data(monkeypatch, capsys) -> None:
    module = _load_cli_module()
    _FakeClipboardAdapter.payload = b"\x00\x01\x02\x03\x04"
    monkeypatch.setattr(module, "Win32ClipboardAdapter", _FakeClipboardAdapter)

    class _FakeInspectService:
        def inspect(self, adapter, verbose: bool = False) -> str:
            data = adapter.fetch_data()
            return f"clipboard_len={len(data)} verbose={verbose}"

    monkeypatch.setattr(module, "InspectService", _FakeInspectService)

    rc = module.main(["inspect-clipboard"])

    out = capsys.readouterr().out
    assert rc == 0
    assert "clipboard_len=5 verbose=True" in out
