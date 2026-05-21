from __future__ import annotations

from .input_base import InputAdapter

TYPE_EDIT_ZONE_FORMAT_NAME = "TypeEditZone"
OBSERVED_TYPE_EDIT_ZONE_FORMAT_ID = 50107
TYPE_EDIT_ZONE_VERSION_FORMAT_NAME = "TypeEditZoneVersion"
OBSERVED_TYPE_EDIT_ZONE_VERSION_FORMAT_ID = 50108


class Win32ClipboardError(RuntimeError):
    """Raised when Win32 clipboard access fails."""


class Win32ClipboardAdapter(InputAdapter):
    """Windows TypeEditZone clipboard raw bytes adapter."""

    def __init__(self) -> None:
        self._win32clipboard = self._load_win32clipboard_module()

    def _load_win32clipboard_module(self):
        try:
            import win32clipboard  # type: ignore[import-not-found]
        except ImportError as exc:
            raise Win32ClipboardError(
                "pywin32 is required for Windows clipboard access. "
                "Install it first (for example: pip install pywin32)."
            ) from exc
        return win32clipboard

    def get_typeeditzone_format_id(self) -> int:
        return int(self._win32clipboard.RegisterClipboardFormat(TYPE_EDIT_ZONE_FORMAT_NAME))

    def get_typeeditzone_version_format_id(self) -> int:
        return int(self._win32clipboard.RegisterClipboardFormat(TYPE_EDIT_ZONE_VERSION_FORMAT_NAME))

    def has_typeeditzone(self) -> bool:
        format_id = self.get_typeeditzone_format_id()
        opened = False
        try:
            self._win32clipboard.OpenClipboard()
            opened = True
            return bool(self._win32clipboard.IsClipboardFormatAvailable(format_id))
        except Exception as exc:
            raise Win32ClipboardError(f"Failed to query TypeEditZone clipboard format: {exc}") from exc
        finally:
            if opened:
                self._safe_close_clipboard()

    def has_typeeditzone_version(self) -> bool:
        format_id = self.get_typeeditzone_version_format_id()
        opened = False
        try:
            self._win32clipboard.OpenClipboard()
            opened = True
            return bool(self._win32clipboard.IsClipboardFormatAvailable(format_id))
        except Exception as exc:
            raise Win32ClipboardError(f"Failed to query TypeEditZoneVersion clipboard format: {exc}") from exc
        finally:
            if opened:
                self._safe_close_clipboard()

    def list_formats(self) -> list[int]:
        opened = False
        formats: list[int] = []
        try:
            self._win32clipboard.OpenClipboard()
            opened = True
            current = 0
            while True:
                current = int(self._win32clipboard.EnumClipboardFormats(current))
                if current == 0:
                    break
                formats.append(current)
            return formats
        except Exception as exc:
            raise Win32ClipboardError(f"Failed to enumerate clipboard formats: {exc}") from exc
        finally:
            if opened:
                self._safe_close_clipboard()

    def read_typeeditzone_bytes(self) -> bytes:
        format_id = self.get_typeeditzone_format_id()
        opened = False
        try:
            self._win32clipboard.OpenClipboard()
            opened = True
            if not self._win32clipboard.IsClipboardFormatAvailable(format_id):
                raise Win32ClipboardError(
                    f"TypeEditZone format is not available in clipboard. format_id={format_id}"
                )
            data = self._win32clipboard.GetClipboardData(format_id)
            if not isinstance(data, (bytes, bytearray, memoryview)):
                raise Win32ClipboardError(
                    f"Unexpected clipboard payload type: {type(data).__name__}. Expected raw bytes."
                )
            return bytes(data)
        except Win32ClipboardError:
            raise
        except Exception as exc:
            raise Win32ClipboardError(f"Failed to read TypeEditZone bytes from clipboard: {exc}") from exc
        finally:
            if opened:
                self._safe_close_clipboard()

    def read_typeeditzone_version_bytes(self) -> bytes:
        format_id = self.get_typeeditzone_version_format_id()
        opened = False
        try:
            self._win32clipboard.OpenClipboard()
            opened = True
            if not self._win32clipboard.IsClipboardFormatAvailable(format_id):
                raise Win32ClipboardError(
                    f"TypeEditZoneVersion format is not available in clipboard. format_id={format_id}"
                )
            data = self._win32clipboard.GetClipboardData(format_id)
            if not isinstance(data, (bytes, bytearray, memoryview)):
                raise Win32ClipboardError(
                    f"Unexpected clipboard payload type: {type(data).__name__}. Expected raw bytes."
                )
            return bytes(data)
        except Win32ClipboardError:
            raise
        except Exception as exc:
            raise Win32ClipboardError(f"Failed to read TypeEditZoneVersion bytes from clipboard: {exc}") from exc
        finally:
            if opened:
                self._safe_close_clipboard()

    def write_typeeditzone_bytes(self, data: bytes) -> None:
        if not isinstance(data, bytes):
            raise TypeError("data must be bytes")
        format_id = self.get_typeeditzone_format_id()
        opened = False
        try:
            self._win32clipboard.OpenClipboard()
            opened = True
            self._win32clipboard.EmptyClipboard()
            self._win32clipboard.SetClipboardData(format_id, data)
        except Exception as exc:
            raise Win32ClipboardError(f"Failed to write TypeEditZone bytes to clipboard: {exc}") from exc
        finally:
            if opened:
                self._safe_close_clipboard()

    def write_typeeditzone_bundle(self, zone_bytes: bytes, version_bytes: bytes) -> None:
        if not isinstance(zone_bytes, bytes):
            raise TypeError("zone_bytes must be bytes")
        if not isinstance(version_bytes, bytes):
            raise TypeError("version_bytes must be bytes")
        zone_format_id = self.get_typeeditzone_format_id()
        version_format_id = self.get_typeeditzone_version_format_id()
        opened = False
        try:
            self._win32clipboard.OpenClipboard()
            opened = True
            self._win32clipboard.EmptyClipboard()
            self._win32clipboard.SetClipboardData(zone_format_id, zone_bytes)
            self._win32clipboard.SetClipboardData(version_format_id, version_bytes)
        except Exception as exc:
            raise Win32ClipboardError(f"Failed to write TypeEditZone bundle to clipboard: {exc}") from exc
        finally:
            if opened:
                self._safe_close_clipboard()

    def fetch_data(self) -> bytes:
        return self.read_typeeditzone_bytes()

    def _safe_close_clipboard(self) -> None:
        try:
            self._win32clipboard.CloseClipboard()
        except Exception:
            # Keep close best-effort in finally blocks to avoid masking the original failure.
            return
