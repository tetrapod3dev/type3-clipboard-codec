"""Read-only, untyped framing experiment; never a semantic text decoder."""

from collections.abc import Iterable
from typing import Any

MAX_PAYLOADS = 32
MAX_PAYLOAD_BYTES = 1_048_576
MAX_PREFIX_HITS = 4096
MAX_SLOTS = 256
PROBE_FACTOR = 2
PROBE_ALLOWANCE = 4096
STRIDE = 204
LOCAL_SPAN = 92  # Retained inspection context, not semantic record extent.
TOKEN = b"\x05\x00\x00\x00"
TAIL = bytes.fromhex("00 00 00 00 00 00 F0 3F 00 00 00 00")
VARIANTS = {
    (0, bytes.fromhex("7B 14 AE 47 E1 7A 84")): "v0",
    (0, bytes.fromhex("B8 1E 85 EB 51 B8 9E")): "v1",
    (1, bytes.fromhex("7B 14 AE 47 E1 7A 84")): "v2",
}


def _family(payload: bytes, p: int) -> str | None:
    """Caller guarantees all 32 predicate bytes; unknown core is distinct."""
    if (payload[p:p + 4] != TOKEN or payload[p + 9:p + 12] != b"\0" * 3
            or payload[p + 19] != 0x3F or payload[p + 20:p + 32] != TAIL):
        return None
    return VARIANTS.get((payload[p + 8], payload[p + 12:p + 19]), "unknown")


def extract_text_slot_candidate(payloads: Iterable[bytes]) -> dict[str, Any] | None:
    """Scan every eligible structural payload, returning only a complete candidate.

    Payload indices are provenance, never ownership or selection preferences.
    All budgets are global. Early failure is allowed; partial success is not.
    """
    buffers = []
    aggregate = 0
    for payload in payloads:
        aggregate += len(payload)
        if len(buffers) >= MAX_PAYLOADS or aggregate > MAX_PAYLOAD_BYTES:
            return None
        buffers.append(payload)
    budget = PROBE_FACTOR * aggregate + PROBE_ALLOWANCE
    evaluations = hits = 0
    prefixes: dict[tuple[int, int], str] = {}
    for index, payload in enumerate(buffers):
        start = 0
        while True:
            p = payload.find(TOKEN, start)
            if p < 0:
                break
            hits += 1
            if hits > MAX_PREFIX_HITS or p + 32 > len(payload):
                return None
            evaluations += 1
            if evaluations > budget:
                return None
            variant = _family(payload, p)
            if variant == "unknown":
                return None
            if variant is not None:
                prefixes[index, p] = variant
            start = p + 1
        # A token fragment at EOF cannot establish complete search absence.
        if any(payload.endswith(TOKEN[:n]) for n in (1, 2, 3)):
            return None

    roots = [key for key in prefixes if (key[0], key[1] - STRIDE) not in prefixes]
    if len(roots) != 1:
        return None
    index, first = roots[0]
    payload = buffers[index]
    positions = []
    p = first
    while (index, p) in prefixes:
        if len(positions) >= MAX_SLOTS or p + LOCAL_SPAN > len(payload):
            return None
        positions.append(p)
        p += STRIDE
    # A complete, non-token continuation probe must establish the run's end.
    if p + 32 > len(payload):
        return None
    evaluations += 1
    if evaluations > budget:
        return None
    if _family(payload, p) is not None or payload[p] == TOKEN[0]:
        return None
    if payload[positions[-1] + 4:positions[-1] + 8] != b"\0" * 4:
        return None
    if first < 16:
        return None
    views = {
        name: {"value": int.from_bytes(payload[first - 4:first - 4 + width], "little"),
               "width": width, "relative_offset": -4}
        for name, width in (("u8", 1), ("u16le", 2), ("u32le", 4))
    }
    if any(view["value"] != len(positions) for view in views.values()):
        return None
    slots = []
    for ordinal, p in enumerate(positions):
        code = payload[p + 4:p + 8]
        slots.append({
            "ordinal": ordinal,
            "prefix_relative_offset": p,
            "prefix_variant": prefixes[index, p],
            "slot_code_candidate": {
                "raw_bytes": code, "numeric_view": int.from_bytes(code, "little"),
                "typed_width": None, "confidence": "provisional",
            },
            "rgb_bytes_candidate": {
                "raw_bytes": list(payload[p + 0x50:p + 0x53]),
                "typed_width": None, "confidence": "provisional",
            },
            "terminal_candidate": ordinal == len(positions) - 1,
            "ownership": "unresolved", "matched_chain": None,
            "raw_span": {"coordinate_domain": "cparagraphe_payload_relative",
                         "start": p, "length": LOCAL_SPAN},
        })
    return {
        "source": "CParagraphe_slot_prefix_family_v1", "confidence": "provisional",
        "parser_safe": False, "ownership": "unresolved", "matched_chain": None,
        "payload_index": index, "first_prefix_relative_offset": first,
        "count_candidate": {
            "raw_window": payload[first - 16:first], "window_relative_start": -16,
            "probe_relative_offset": -4, "numeric_views": views,
            "validated_total_slot_count": len(positions), "typed_width": None,
            "confidence": "provisional",
        },
        "stride": STRIDE, "prefix_variant": prefixes[index, first], "slots": slots,
    }
