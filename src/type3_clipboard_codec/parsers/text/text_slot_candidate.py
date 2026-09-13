"""Bounded framing and archive-type candidates; never a semantic text decoder."""

import math
import struct
from collections.abc import Iterable
from typing import Any

MAX_PAYLOADS = 32
MAX_PAYLOAD_BYTES = 1_048_576
MAX_PREFIX_HITS = 4096
MAX_SLOTS = 256
PROBE_FACTOR = 2
PROBE_ALLOWANCE = 4096
RECORD_SIZE = 204
STRIDE = RECORD_SIZE
ATTRCHAR_VERSION_OFFSET = 0
ATTRCHAR_CURRENT_VERSION = 5
EXTENSION_OFFSET = 92
EXTENSION_VERSION_OFFSET = EXTENSION_OFFSET
EXTENSION_CURRENT_VERSION = 5
# Reviewed v5 archive order; later offsets apply only after earlier empty guards.
EMPTY_FIELDS = ((132, "nonempty_array"), (152, "nonempty_array"),
                (188, "nonempty_string"), (192, "optional_zone_present"),
                (196, "nonempty_string"), (200, "optional_zone_present"))
# Reviewed current AttrChar binary64 emissions; offsets carry no UI ownership.
ARCHIVE_DOUBLE_OFFSETS = (0x0C, 0x14, 0x1C, 0x40, 0x48)
IDENTITY_SPAN = 64
LOCAL_SPAN = 92  # Retained inspection context, not semantic record extent.
TOKEN = b"\x05\x00\x00\x00"
STRUCTURAL_CONSTANTS = ((0x24, b"\0" * 8), (0x38, bytes.fromhex("9A9999999999D9BF")))


def _validate_current_empty_slot_layout(record: bytes) -> str | None:
    """Return a structural failure reason, or None for one complete reviewed window.

    Caller supplies existing alignment. AttrChar's fixed emissions total 92 bytes;
    the v5 empty extension adds 112. No other extension bytes are constrained.
    """
    if len(record) != RECORD_SIZE:
        return "truncated" if len(record) < RECORD_SIZE else "oversized_record_window"
    for offset, version, reason in (
        (ATTRCHAR_VERSION_OFFSET, ATTRCHAR_CURRENT_VERSION, "attrchar_version_mismatch"),
        (EXTENSION_VERSION_OFFSET, EXTENSION_CURRENT_VERSION, "extension_version_mismatch"),
    ):
        if int.from_bytes(record[offset:offset + 4], "little") != version:
            return reason
    for offset, reason in EMPTY_FIELDS:
        if int.from_bytes(record[offset:offset + 4], "little") != 0:
            return reason
    return None


def _family(payload: bytes, p: int) -> str | None:
    """Exact F4, or rejection-only Gate 8 context; None is a complete mismatch."""
    if p < 0 or p + IDENTITY_SPAN > len(payload):
        return "incomplete"
    if payload[p:p + 4] != TOKEN:
        return None
    allowed = payload[p + 8] in (0, 1)
    reserved = payload[p + 9:p + 12] == b"\0" * 3
    constants = all(payload[p + off:p + off + len(raw)] == raw for off, raw in STRUCTURAL_CONSTANTS)
    if allowed and reserved and constants:
        return "F4"
    if reserved and constants and not allowed:
        return "unknown_plus08"
    if allowed and reserved and not constants:
        return "unknown_structural_constant"
    if constants:
        return "unknown_core"
    return None


def extract_text_slot_candidate(payloads: Iterable[bytes]) -> dict[str, Any] | None:
    """Scan every eligible structural payload, returning only a complete candidate.

    Payload indices are provenance, never ownership or selection preferences.
    All budgets are global. Early failure is allowed; partial success is not.
    """
    return _evaluate(payloads)[0]


def _evaluate(payloads: Iterable[bytes]) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    """Private bounded accounting, never attached to parser output or used as a score."""
    audit = dict(raw_token_hits=0, identity_positions=0, maximal_runs=0, suffix_positions_removed=0,
                 unsupported_contexts=0, globally_competing_runs=0, traversed_slots=0,
                 probe_evaluations=0, scan_complete=False, failing_layer=None, reason=None)

    def fail(layer: str, reason: str):
        audit.update(failing_layer=layer, reason=reason)
        return None, audit

    buffers = []
    aggregate = 0
    for payload in payloads:
        aggregate += len(payload)
        if len(buffers) >= MAX_PAYLOADS or aggregate > MAX_PAYLOAD_BYTES:
            return fail("resource", "payload_cap")
        buffers.append(payload)
    budget = PROBE_FACTOR * aggregate + PROBE_ALLOWANCE
    evaluations = hits = 0
    prefixes: dict[tuple[int, int], int] = {}
    for index, payload in enumerate(buffers):
        start = 0
        while True:
            p = payload.find(TOKEN, start)
            if p < 0:
                break
            hits += 1
            audit["raw_token_hits"] = hits
            if hits > MAX_PREFIX_HITS:
                return fail("resource", "token_cap")
            if p + IDENTITY_SPAN > len(payload):
                return fail("bounds", "incomplete_identity")
            evaluations += 1
            audit["probe_evaluations"] = evaluations
            if evaluations > budget:
                return fail("resource", "probe_cap")
            identity = _family(payload, p)
            if identity == "F4":
                prefixes[index, p] = payload[p + 8]
                audit["identity_positions"] += 1
            elif identity is not None:
                audit["unsupported_contexts"] += 1
                return fail("identity", identity)
            start = p + 1
        # A token fragment at EOF cannot establish complete search absence.
        if any(payload.endswith(TOKEN[:n]) for n in (1, 2, 3)):
            return fail("bounds", "partial_token")

    audit["scan_complete"] = True
    roots = [key for key in prefixes if (key[0], key[1] - STRIDE) not in prefixes]
    audit["maximal_runs"] = len(roots)
    audit["suffix_positions_removed"] = len(prefixes) - len(roots)
    audit["globally_competing_runs"] = len(roots) if len(roots) > 1 else 0
    if len(roots) != 1:
        return fail("uniqueness", "multiple_runs" if roots else "no_run")
    index, first = roots[0]
    payload = buffers[index]
    positions = []
    p = first
    while (index, p) in prefixes:
        if len(positions) >= MAX_SLOTS:
            return fail("resource", "slot_cap")
        if p + LOCAL_SPAN > len(payload):
            return fail("bounds", "incomplete_raw_rgb_span")
        if prefixes[index, p] != prefixes[index, first]:
            return fail("identity", "plus08_switch")
        # Root/stride topology above is candidate alignment only. Validate the first
        # record before advancing, and every later record (including the zero tail).
        layout_error = _validate_current_empty_slot_layout(payload[p:p + RECORD_SIZE])
        if layout_error is not None:
            return fail("bounds" if layout_error == "truncated" else "layout", layout_error)
        positions.append(p)
        audit["traversed_slots"] = len(positions)
        p += STRIDE
    # A complete, non-token continuation probe must establish the run's end.
    if p + IDENTITY_SPAN > len(payload):
        return fail("bounds", "incomplete_next_prefix")
    evaluations += 1
    audit["probe_evaluations"] = evaluations
    if evaluations > budget:
        return fail("resource", "probe_cap")
    if _family(payload, p) is not None or payload[p] == TOKEN[0]:
        return fail("terminal", "unsupported_continuation")
    if payload[positions[-1] + 4:positions[-1] + 8] != b"\0" * 4:
        return fail("terminal", "nonzero_terminal")
    if first < 16:
        return fail("bounds", "incomplete_count_window")
    views = {
        name: {"value": int.from_bytes(payload[first - 4:first - 4 + width], "little"),
               "width": width, "relative_offset": -4}
        for name, width in (("u8", 1), ("u16le", 2), ("u32le", 4))
    }
    if any(view["value"] != len(positions) for view in views.values()):
        return fail("count", "count_mismatch")
    slots = []
    for ordinal, p in enumerate(positions):
        code = payload[p + 4:p + 8]
        # Every record and the entire run have passed structural validation above.
        # Decode only here: numeric values never participate in candidate selection.
        archive_doubles = {}
        for offset in ARCHIVE_DOUBLE_OFFSETS:
            raw = payload[p + offset:p + offset + 8]
            value = struct.unpack("<d", raw)[0]
            archive_doubles[hex(offset)] = {
                "raw_bytes": bytes(raw), "f64le": value if math.isfinite(value) else repr(value),
                "typed_width": 8,
            }
        slots.append({
            "ordinal": ordinal,
            "prefix_relative_offset": p,
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
            "archive_double_candidates": archive_doubles,
        })
    return {
        "source": "CParagraphe_slot_prefix_family_v2", "confidence": "provisional",
        "parser_safe": False, "ownership": "unresolved", "matched_chain": None,
        "payload_index": index, "first_prefix_relative_offset": first,
        "count_candidate": {
            "raw_window": payload[first - 16:first], "window_relative_start": -16,
            "probe_relative_offset": -4, "numeric_views": views,
            "validated_total_slot_count": len(positions), "typed_width": None,
            "confidence": "provisional",
        },
        "stride": STRIDE, "prefix_family": "F4", "plus08_value": prefixes[index, first], "slots": slots,
    }, audit
