from __future__ import annotations

import sys
import types

import pytest

from type3_clipboard_codec.adapters.win32_clipboard import (
    OBSERVED_TYPE_EDIT_ZONE_FORMAT_ID,
    OBSERVED_TYPE_EDIT_ZONE_VERSION_FORMAT_ID,
    TYPE_EDIT_ZONE_FORMAT_NAME,
    TYPE_EDIT_ZONE_VERSION_FORMAT_NAME,
    Win32ClipboardAdapter,
    Win32ClipboardError,
)


class _FakeWin32Clipboard:
    def __init__(self) -> None:
        self.open_calls = 0
        self.close_calls = 0
        self.register_calls: list[str] = []
        self.available = True
        self.payload = b""
        self.version_payload = b""
        self.enumerated_formats = [1, 2, 50107]
        self.empty_calls = 0
        self.set_calls: list[tuple[int, bytes]] = []
        self.raise_on_get = False

    def RegisterClipboardFormat(self, name: str) -> int:
        self.register_calls.append(name)
        if name == "TypeEditZoneVersion":
            return 50108
        return 50107

    def OpenClipboard(self) -> None:
        self.open_calls += 1

    def CloseClipboard(self) -> None:
        self.close_calls += 1

    def IsClipboardFormatAvailable(self, format_id: int) -> bool:
        return self.available and format_id in (50107, 50108)

    def GetClipboardData(self, format_id: int):
        if self.raise_on_get:
            raise RuntimeError("boom")
        if format_id == 50107:
            return self.payload
        if format_id == 50108:
            return self.version_payload
        raise RuntimeError("wrong format")

    def EmptyClipboard(self) -> None:
        self.empty_calls += 1
        return None

    def SetClipboardData(self, format_id: int, data: bytes) -> None:
        self.set_calls.append((format_id, data))

    def EnumClipboardFormats(self, current: int) -> int:
        if current == 0:
            return self.enumerated_formats[0]
        try:
            idx = self.enumerated_formats.index(current)
        except ValueError:
            return 0
        next_idx = idx + 1
        return self.enumerated_formats[next_idx] if next_idx < len(self.enumerated_formats) else 0


@pytest.fixture
def fake_win32clipboard(monkeypatch: pytest.MonkeyPatch) -> _FakeWin32Clipboard:
    fake = _FakeWin32Clipboard()
    module = types.SimpleNamespace(
        RegisterClipboardFormat=fake.RegisterClipboardFormat,
        OpenClipboard=fake.OpenClipboard,
        CloseClipboard=fake.CloseClipboard,
        IsClipboardFormatAvailable=fake.IsClipboardFormatAvailable,
        GetClipboardData=fake.GetClipboardData,
        EmptyClipboard=fake.EmptyClipboard,
        SetClipboardData=fake.SetClipboardData,
        EnumClipboardFormats=fake.EnumClipboardFormats,
    )
    monkeypatch.setitem(sys.modules, "win32clipboard", module)
    return fake


def test_constants() -> None:
    assert TYPE_EDIT_ZONE_FORMAT_NAME == "TypeEditZone"
    assert OBSERVED_TYPE_EDIT_ZONE_FORMAT_ID == 50107
    assert TYPE_EDIT_ZONE_VERSION_FORMAT_NAME == "TypeEditZoneVersion"
    assert OBSERVED_TYPE_EDIT_ZONE_VERSION_FORMAT_ID == 50108


def test_get_typeeditzone_format_id_registers_name(fake_win32clipboard: _FakeWin32Clipboard) -> None:
    adapter = Win32ClipboardAdapter()
    format_id = adapter.get_typeeditzone_format_id()

    assert format_id == 50107
    assert fake_win32clipboard.register_calls == ["TypeEditZone"]


def test_get_typeeditzone_version_format_id_registers_name(fake_win32clipboard: _FakeWin32Clipboard) -> None:
    adapter = Win32ClipboardAdapter()
    format_id = adapter.get_typeeditzone_version_format_id()

    assert format_id == 50108
    assert fake_win32clipboard.register_calls == ["TypeEditZoneVersion"]


def test_read_typeeditzone_bytes_keeps_raw_bytes_unchanged(fake_win32clipboard: _FakeWin32Clipboard) -> None:
    payload = b"\x00\x01\x02\x00\xffraw\x00tail\x00"
    fake_win32clipboard.payload = payload
    adapter = Win32ClipboardAdapter()

    data = adapter.read_typeeditzone_bytes()

    assert data == payload
    assert fake_win32clipboard.open_calls == 1
    assert fake_win32clipboard.close_calls == 1


def test_read_typeeditzone_version_bytes_keeps_raw_bytes_unchanged(
    fake_win32clipboard: _FakeWin32Clipboard,
) -> None:
    payload = b"\x01\x00\x00\x00\x51\x02\x00\x00\x00\x00tail\x00"
    fake_win32clipboard.version_payload = payload
    adapter = Win32ClipboardAdapter()

    data = adapter.read_typeeditzone_version_bytes()

    assert data == payload
    assert fake_win32clipboard.open_calls == 1
    assert fake_win32clipboard.close_calls == 1


def test_write_typeeditzone_bytes_passes_identical_bytes(fake_win32clipboard: _FakeWin32Clipboard) -> None:
    payload = b"\x00\x10\x20\x30\x00\x00"
    adapter = Win32ClipboardAdapter()

    adapter.write_typeeditzone_bytes(payload)

    assert fake_win32clipboard.set_calls == [(50107, payload)]
    assert fake_win32clipboard.open_calls == 1
    assert fake_win32clipboard.close_calls == 1


def test_write_typeeditzone_bundle_sets_both_formats_after_empty(
    fake_win32clipboard: _FakeWin32Clipboard,
) -> None:
    zone_payload = b"\x00\x10\x20\x30\x00\x00"
    version_payload = b"\x01\x00\x00\x00\x51\x02\x00\x00\x00\x00\x00\x00"
    adapter = Win32ClipboardAdapter()

    adapter.write_typeeditzone_bundle(zone_payload, version_payload)

    assert fake_win32clipboard.empty_calls == 1
    assert fake_win32clipboard.set_calls == [(50107, zone_payload), (50108, version_payload)]
    assert fake_win32clipboard.open_calls == 1
    assert fake_win32clipboard.close_calls == 1


def test_read_closes_clipboard_on_exception(fake_win32clipboard: _FakeWin32Clipboard) -> None:
    fake_win32clipboard.raise_on_get = True
    adapter = Win32ClipboardAdapter()

    with pytest.raises(Win32ClipboardError):
        adapter.read_typeeditzone_bytes()

    assert fake_win32clipboard.open_calls == 1
    assert fake_win32clipboard.close_calls == 1
