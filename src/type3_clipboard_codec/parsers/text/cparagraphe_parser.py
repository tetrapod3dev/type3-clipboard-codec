import struct
from typing import Any, List, Optional, Sequence, Tuple

from ...models.geometry import Point, Type3Node, Type3ObjectChain


def extract_font_candidates(data: bytes) -> List[dict[str, Any]]:
    scan_limit = min(len(data), 2048)
    idx = 0
    out: List[dict[str, Any]] = []
    seen: set[tuple[str, int]] = set()

    while idx < scan_limit:
        if not (32 <= data[idx] <= 126):
            idx += 1
            continue
        start = idx
        while idx < scan_limit and 32 <= data[idx] <= 126:
            idx += 1
        if idx < len(data) and data[idx] == 0:
            try:
                candidate = data[start:idx].decode("ascii")
            except UnicodeDecodeError:
                candidate = ""
            if len(candidate) >= 3:
                key = (candidate, start)
                if key not in seen:
                    seen.add(key)
                    out.append({"name": candidate, "offset": start})
        idx += 1
    return out


def extract_font_name(
    data: bytes,
    known_font_markers: Sequence[str],
    font_candidates: Optional[List[dict[str, Any]]] = None,
) -> Tuple[Optional[str], Optional[int], Optional[bytes]]:
    candidates = font_candidates if font_candidates is not None else extract_font_candidates(data)
    for item in candidates:
        candidate = item.get("name", "")
        start = int(item.get("offset", 0))
        if candidate in known_font_markers:
            end = start + len(candidate)
            context_start = max(0, start - 16)
            context_end = min(len(data), end + 17)
            return candidate, start, data[context_start:context_end]
    return None, None, None


def records_to_text_run(records: List[bytes]) -> Optional[dict[str, Any]]:
    codes: List[int] = []
    for record in records:
        if len(record) < 8:
            return None
        codes.append(struct.unpack("<I", record[4:8])[0])

    if not codes:
        return None

    decoded_chars: List[str] = []
    for code in codes:
        if code == 0:
            continue
        if code == 13:
            decoded_chars.append("\n")
            continue
        if 32 <= code <= 126:
            decoded_chars.append(chr(code))
            continue
        return None

    text = "".join(decoded_chars)
    if not text:
        return None
    line_count = text.count("\n") + 1
    return {"text": text, "codes": codes, "line_count": line_count}


def read_slot_record_runs_from_blob(payload: bytes) -> List[List[bytes]]:
    record_stride = 204
    runs: List[tuple[int, List[bytes]]] = []
    seen_starts: set[int] = set()

    for offset in range(0, max(0, len(payload) - 8)):
        if payload[offset : offset + 4] != b"\x05\x00\x00\x00":
            continue
        if offset - record_stride >= 0 and payload[offset - record_stride : offset - record_stride + 4] == b"\x05\x00\x00\x00":
            continue
        if offset in seen_starts:
            continue
        if offset + record_stride + 4 > len(payload):
            continue
        if payload[offset + record_stride : offset + record_stride + 4] != b"\x05\x00\x00\x00":
            continue

        records: List[bytes] = []
        cursor = offset
        for _ in range(256):
            if cursor + 8 > len(payload):
                break
            if payload[cursor : cursor + 4] != b"\x05\x00\x00\x00":
                break
            record_end = min(len(payload), cursor + record_stride)
            records.append(payload[cursor:record_end])
            code = struct.unpack("<I", payload[cursor + 4 : cursor + 8])[0]
            cursor += record_stride
            if code == 0:
                break

        if len(records) < 2:
            continue
        run = records_to_text_run(records)
        if run is None:
            continue
        runs.append((offset, records))
        seen_starts.add(offset)

    runs.sort(key=lambda item: len(item[1]), reverse=True)
    filtered: List[tuple[int, List[bytes]]] = []
    for start, recs in runs:
        if any(abs(start - kept_start) < 150 for kept_start, _kept in filtered):
            continue
        filtered.append((start, recs))

    filtered.sort(key=lambda item: item[0])
    return [records for _start, records in filtered]


def read_paragraphe_slot_record_runs(payload: bytes) -> List[List[bytes]]:
    return read_slot_record_runs_from_blob(payload)


def extract_text_runs(nodes: List[Type3Node]) -> Tuple[List[dict[str, Any]], List[bytes], List[str]]:
    notes: List[str] = []
    runs: List[dict[str, Any]] = []
    primary_records: List[bytes] = []

    for node in nodes:
        if node.header.class_name != "CParagraphe":
            continue
        for recs in read_paragraphe_slot_record_runs(node.payload):
            run = records_to_text_run(recs)
            if run is None:
                continue
            if run["text"] in [r["text"] for r in runs]:
                continue
            runs.append(run)
            if not primary_records:
                primary_records = recs

    if len(runs) < 2:
        full_blob = b"".join(node.payload for node in nodes)
        for recs in read_slot_record_runs_from_blob(full_blob):
            run = records_to_text_run(recs)
            if run is None:
                continue
            if run["text"] in [r["text"] for r in runs]:
                continue
            runs.append(run)

    if runs:
        return runs, primary_records, notes

    notes.append("CParagraphe text records were detected, but text content could not be safely decoded.")
    return [], primary_records, notes


def extract_candidate_text_records(nodes: List[Type3Node]) -> List[bytes]:
    for node in nodes:
        if node.header.class_name != "CParagraphe":
            continue
        runs = read_paragraphe_slot_record_runs(node.payload)
        if not runs:
            continue
        runs.sort(key=lambda rs: len(rs), reverse=True)
        return runs[0]
    return []


def attach_text_runs_to_chains(chains: List[Type3ObjectChain], runs: List[dict[str, Any]]) -> None:
    if not chains or not runs:
        return

    if len(runs) == 1 or len(chains) == 1:
        chains[0].text_candidate = runs[0]["text"]
        chains[0].source_text_candidate = runs[0]["text"]
        chains[0].line_count = runs[0]["line_count"]
        chains[0].text_notes.append("Text candidate extracted from CParagraphe slot records.")
        if len(runs) > 1:
            chains[0].text_notes.append("Multiple text runs detected; mapping to objects is provisional.")
        return

    chain_indices = list(range(len(chains)))
    chain_indices.sort(
        key=lambda idx: (
            chains[idx].bbox.width_mm if chains[idx].bbox is not None else float("inf"),
            chains[idx].bbox.center_mm.x if chains[idx].bbox is not None else float("inf"),
        )
    )
    run_indices = list(range(len(runs)))
    run_indices.sort(key=lambda idx: len(runs[idx]["text"]))

    for chain_idx, run_idx in zip(chain_indices, run_indices):
        chain = chains[chain_idx]
        run = runs[run_idx]
        chain.text_candidate = run["text"]
        chain.source_text_candidate = run["text"]
        chain.line_count = run["line_count"]
        chain.text_notes.append(
            "Text candidate mapped from CParagraphe run by width/length heuristic (provisional for multi-object text)."
        )


def attach_text_anchor_candidates(chains: List[Type3ObjectChain]) -> None:
    for chain in chains:
        if len(chain.contour_records) >= 2:
            xs = [p.x_mm for p in chain.contour_records]
            ys = [p.y_mm for p in chain.contour_records]
            zs = [p.z_mm for p in chain.contour_records]
            chain.text_anchor = Point(
                x=(min(xs) + max(xs)) / 2.0,
                y=(min(ys) + max(ys)) / 2.0,
                z=(min(zs) + max(zs)) / 2.0,
            )
            chain.text_anchor_expected_source = "confirmed_from_fixture_setup"
            chain.text_anchor_parse_method = "baseline_midpoint"
            chain.text_anchor_parse_confidence = "provisional"
            chain.text_anchor_source = chain.text_anchor_parse_method
            chain.text_anchor_confidence = chain.text_anchor_parse_confidence
            chain.text_notes.append(
                "UI anchor value is confirmed by fixture setup, but direct binary offset is not confirmed yet."
            )
        elif chain.bbox is not None:
            c = chain.bbox.center_mm
            chain.text_anchor = Point(x=c.x, y=c.y, z=c.z)
            chain.text_anchor_expected_source = "confirmed_from_fixture_setup"
            chain.text_anchor_parse_method = "bbox_center_fallback"
            chain.text_anchor_parse_confidence = "fallback"
            chain.text_anchor_source = chain.text_anchor_parse_method
            chain.text_anchor_confidence = chain.text_anchor_parse_confidence
            chain.text_notes.append(
                "Anchor fallback from bbox center; direct binary anchor offset is not confirmed."
            )
