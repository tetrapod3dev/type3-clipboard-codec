from collections import Counter
from typing import Any, List, Optional

from ...models.colors import TYPE3_COLORS_BY_RAW, TYPE3_COLORS_BY_RGB0_RAW
from ...models.geometry import StyleProperties, Type3ObjectChain


def read_optional_u32_le(data: bytes, offset: int) -> Optional[int]:
    if offset < 0 or offset + 4 > len(data):
        return None
    return int.from_bytes(data[offset : offset + 4], byteorder="little", signed=False)


def confidence_rank(confidence: str) -> int:
    if confidence == "confirmed":
        return 0
    if confidence == "strong":
        return 1
    return 2


def collect_palette_color_candidates(
    payload: bytes,
    fixed_primary: Optional[int],
    fixed_secondary: Optional[int],
    primary_offset: int,
    secondary_offset: int,
    group_primary_offset: int,
    group_secondary_offset: int,
) -> List[dict[str, Any]]:
    entries: List[dict[str, Any]] = []
    occurrences: dict[tuple[str, int], List[int]] = {}
    max_scan_candidates_per_raw = 12
    group_primary = read_optional_u32_le(payload, group_primary_offset)
    group_secondary = read_optional_u32_le(payload, group_secondary_offset)
    has_group_confirmed_nonzero = (
        group_primary is not None
        and group_primary == group_secondary
        and group_primary != 0
        and group_primary in TYPE3_COLORS_BY_RGB0_RAW
    )

    for offset in range(0, max(0, len(payload) - 3)):
        raw = int.from_bytes(payload[offset : offset + 4], byteorder="little", signed=False)
        if raw in TYPE3_COLORS_BY_RAW:
            occurrences.setdefault(("legacy", raw), []).append(offset)
        if raw in TYPE3_COLORS_BY_RGB0_RAW:
            occurrences.setdefault(("rgb0", raw), []).append(offset)

    for (encoding, raw), offsets in occurrences.items():
        if raw == 0 and encoding == "rgb0":
            continue
        color = TYPE3_COLORS_BY_RAW[raw] if encoding == "legacy" else TYPE3_COLORS_BY_RGB0_RAW[raw]
        scan_added = 0
        sorted_offsets = sorted(offsets)
        has_pair_12 = any((sorted_offsets[i + 1] - sorted_offsets[i]) == 12 for i in range(len(sorted_offsets) - 1))
        max_fixed_offset_for_encoding = secondary_offset if encoding == "legacy" else group_secondary_offset
        for idx, offset in enumerate(sorted_offsets):
            prev_close = idx > 0 and (offset - sorted_offsets[idx - 1]) <= 16
            next_close = idx + 1 < len(sorted_offsets) and (sorted_offsets[idx + 1] - offset) <= 16
            has_close_neighbor = prev_close or next_close
            confidence = "strong" if has_close_neighbor else "weak"
            source = "payload_scan"

            is_legacy_fixed = encoding == "legacy" and (offset == primary_offset or offset == secondary_offset)
            is_group_fixed = encoding == "rgb0" and (offset == group_primary_offset or offset == group_secondary_offset)
            is_fixed = is_legacy_fixed or is_group_fixed
            if is_fixed:
                source = "fixed_offset"

            # Rectangle-era fixed offsets are currently legacy/provisional evidence.
            if has_group_confirmed_nonzero and raw == 0 and encoding == "legacy":
                continue

            if not is_fixed:
                if not has_close_neighbor and raw == 0:
                    continue
                if scan_added >= max_scan_candidates_per_raw:
                    if encoding == "legacy" and raw == 0 and offset > (max_fixed_offset_for_encoding + 16):
                        break
                    continue
                scan_added += 1

            if is_legacy_fixed:
                if fixed_primary == fixed_secondary == raw:
                    confidence = "confirmed"
                elif fixed_primary == raw or fixed_secondary == raw:
                    confidence = "strong"
                else:
                    confidence = "weak"
            elif is_group_fixed:
                if group_primary == group_secondary == raw:
                    confidence = "confirmed"
                elif group_primary == raw or group_secondary == raw:
                    confidence = "strong"
                else:
                    confidence = "weak"
            elif has_pair_12 and raw != 0:
                confidence = "strong"

            entries.append(
                {
                    "offset": offset,
                    "raw": raw,
                    "raw_hex": f"0x{raw:08X}",
                    "name": color.name,
                    "hex_rgb": color.hex_rgb,
                    "confidence": confidence,
                    "source": source,
                    "encoding": encoding,
                }
            )

    entries.sort(
        key=lambda item: (
            confidence_rank(item["confidence"]),
            0 if item["raw"] != 0 else 1,
            0 if item["source"] == "fixed_offset" else 1,
            abs(item["offset"] - primary_offset),
        )
    )
    suppress_keys = {
        (item["offset"], item["raw"])
        for item in entries
        if item.get("encoding") == "rgb0" and item.get("source") == "payload_scan"
    }
    return [
        item
        for item in entries
        if not (
            item.get("encoding") == "legacy"
            and item.get("source") == "payload_scan"
            and (item["offset"], item["raw"]) in suppress_keys
        )
    ]


def choose_color_candidate(
    color_candidates: List[dict[str, Any]],
    fixed_primary: Optional[int],
    fixed_secondary: Optional[int],
    primary_offset: int,
    reference_offset: Optional[int] = None,
) -> Optional[dict[str, Any]]:
    if not color_candidates:
        return None

    if fixed_primary is not None and fixed_primary == fixed_secondary and fixed_primary in TYPE3_COLORS_BY_RAW:
        for candidate in color_candidates:
            if candidate["raw"] == fixed_primary and candidate["source"] == "fixed_offset":
                return candidate

    candidates = list(color_candidates)
    if reference_offset is not None:
        nonzero = [candidate for candidate in candidates if candidate["raw"] != 0]
        if nonzero:
            candidates = nonzero
        candidates.sort(
            key=lambda item: (
                confidence_rank(item["confidence"]),
                abs(item["offset"] - reference_offset),
                0 if item["source"] == "fixed_offset" else 1,
                0 if item.get("encoding") == "rgb0" else 1,
                0 if item["raw"] != 0 else 1,
            )
        )
        return candidates[0]

    by_raw = Counter(candidate["raw"] for candidate in color_candidates)
    sorted_candidates = sorted(
        color_candidates,
        key=lambda item: (
            confidence_rank(item["confidence"]),
            0 if item["raw"] != 0 else 1,
            0 if item["source"] == "fixed_offset" else 1,
            0 if item.get("encoding") == "rgb0" else 1,
            -by_raw[item["raw"]],
            abs(item["offset"] - primary_offset),
        ),
    )
    return sorted_candidates[0]


def localize_color_candidates(
    color_candidates: List[dict[str, Any]],
    reference_offset: Optional[int],
    selected_raw: Optional[int],
) -> List[dict[str, Any]]:
    if not color_candidates:
        return []
    if selected_raw is not None and selected_raw != 0:
        same_raw = [c for c in color_candidates if c.get("raw") == selected_raw]
        if same_raw:
            return sorted(
                same_raw,
                key=lambda c: (
                    0 if c.get("source") == "fixed_offset" else 1,
                    abs((c.get("offset") or 0) - (reference_offset or 0)),
                ),
            )[:8]
    if reference_offset is not None:
        nearby = sorted(
            color_candidates,
            key=lambda c: (
                abs((c.get("offset") or 0) - reference_offset),
                confidence_rank(c.get("confidence", "weak")),
            ),
        )
        return nearby[:8]
    return color_candidates[:8]


def read_style_properties_with_context(
    payload: bytes,
    payload_offset: Optional[int],
    stream_offset: Optional[int],
    primary_offset: int,
    secondary_offset: int,
    group_primary_offset: int,
    group_secondary_offset: int,
) -> StyleProperties:
    primary = read_optional_u32_le(payload, primary_offset)
    secondary = read_optional_u32_le(payload, secondary_offset)
    color_candidates = collect_palette_color_candidates(
        payload=payload,
        fixed_primary=primary,
        fixed_secondary=secondary,
        primary_offset=primary_offset,
        secondary_offset=secondary_offset,
        group_primary_offset=group_primary_offset,
        group_secondary_offset=group_secondary_offset,
    )
    chosen = choose_color_candidate(
        color_candidates=color_candidates,
        fixed_primary=primary,
        fixed_secondary=secondary,
        primary_offset=primary_offset,
    )

    color_name = None
    color_hex = None
    line_color_selected_raw = None
    line_color_confidence = None
    line_color_source = None
    if chosen is not None:
        color_name = chosen["name"]
        color_hex = chosen["hex_rgb"]
        line_color_selected_raw = chosen["raw"]
        line_color_confidence = chosen["confidence"]
        line_color_source = chosen["source"]

    return StyleProperties(
        line_color_primary=primary,
        line_color_secondary=secondary,
        line_color_selected_raw=line_color_selected_raw,
        line_color_name=color_name,
        line_color_hex=color_hex,
        line_color_confidence=line_color_confidence,
        line_color_source=line_color_source,
        color_candidates=color_candidates,
        fixed_primary_offset=primary_offset,
        fixed_secondary_offset=secondary_offset,
        fixed_primary_raw=primary,
        fixed_secondary_raw=secondary,
        property_extend_payload_length=len(payload),
        property_extend_payload_offset=payload_offset,
        property_extend_stream_offset=stream_offset,
    )


def style_for_reference_offset(base_style: StyleProperties, reference_offset: Optional[int], primary_offset: int) -> StyleProperties:
    chosen = choose_color_candidate(
        color_candidates=base_style.color_candidates,
        fixed_primary=base_style.line_color_primary,
        fixed_secondary=base_style.line_color_secondary,
        primary_offset=primary_offset,
        reference_offset=reference_offset,
    )

    selected_raw = None
    selected_name = None
    selected_hex = None
    selected_confidence = None
    selected_source = None
    localized_candidates = list(base_style.color_candidates)
    if chosen is not None:
        selected_raw = chosen["raw"]
        selected_name = chosen["name"]
        selected_hex = chosen["hex_rgb"]
        selected_confidence = chosen["confidence"]
        selected_source = chosen["source"]
        localized_candidates = localize_color_candidates(
            color_candidates=base_style.color_candidates,
            reference_offset=reference_offset,
            selected_raw=selected_raw,
        )

    return StyleProperties(
        line_color_primary=base_style.line_color_primary,
        line_color_secondary=base_style.line_color_secondary,
        line_color_selected_raw=selected_raw,
        line_color_name=selected_name,
        line_color_hex=selected_hex,
        line_color_confidence=selected_confidence,
        line_color_source=selected_source,
        color_candidates=localized_candidates,
        fixed_primary_offset=base_style.fixed_primary_offset,
        fixed_secondary_offset=base_style.fixed_secondary_offset,
        fixed_primary_raw=base_style.fixed_primary_raw,
        fixed_secondary_raw=base_style.fixed_secondary_raw,
        property_extend_payload_length=base_style.property_extend_payload_length,
        property_extend_payload_offset=base_style.property_extend_payload_offset,
        property_extend_stream_offset=base_style.property_extend_stream_offset,
    )


def downgrade_unverified_text_color_selection(chains: List[Type3ObjectChain]) -> None:
    for chain in chains:
        style = chain.style
        if style is None:
            continue
        if style.line_color_source == "fixed_offset":
            style.line_color_source = "fixed_offset_text_unverified"
        elif style.line_color_source in {"payload_scan", "fixed_offset_text_unverified"}:
            style.line_color_source = "text_candidate_unverified"

        style.line_color_confidence = "provisional" if style.line_color_name is not None else "unresolved"

        downgraded_candidates: List[dict[str, Any]] = []
        for candidate in style.color_candidates:
            c = dict(candidate)
            if c.get("source") in {"fixed_offset", "payload_scan"}:
                c["source"] = "text_candidate_unverified"
            c["confidence"] = "provisional"
            downgraded_candidates.append(c)
        style.color_candidates = downgraded_candidates

        chain.text_notes.append(
            "Text color mapping is provisional for text objects; absolute/payload offsets are diagnostic evidence only."
        )
