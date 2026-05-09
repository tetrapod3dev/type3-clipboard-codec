import re

from ..exceptions import InvalidHexError

_NON_HEX_RE = re.compile(r"[^0-9A-Fa-f]")


def normalize_hex_text(text: str) -> str:
    """
    Normalize user-pasted hex text.

    Rules:
    - remove `0x` / `0X` prefixes
    - remove all whitespace
    - reject non-hex characters
    - reject odd-length hex
    """
    without_prefix = re.sub(r"0[xX]", "", text)
    compact = re.sub(r"\s+", "", without_prefix)

    if not compact:
        return ""

    bad_match = _NON_HEX_RE.search(compact)
    if bad_match is not None:
        bad = compact[bad_match.start()]
        raise InvalidHexError(f"Invalid hex character '{bad}' at normalized index {bad_match.start()}.")

    if len(compact) % 2 != 0:
        raise InvalidHexError(
            f"Hex length must be even after normalization, but got {len(compact)} characters."
        )

    return compact


def hex_text_to_bytes(text: str) -> bytes:
    normalized = normalize_hex_text(text)
    if not normalized:
        return b""
    return bytes.fromhex(normalized)
