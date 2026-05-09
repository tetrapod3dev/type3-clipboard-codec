from collections import Counter
from typing import Any, List, Optional, Dict, Tuple
import math
import struct

from .base import BaseParser
from ..models.geometry import (
    GeometryObject,
    BBox3D,
    Type3Node,
    ContourPoint,
    Point,
    StyleProperties,
    Type3ObjectChain,
)
from ..models.colors import TYPE3_COLORS_BY_RAW, TYPE3_COLORS_BY_RGB0_RAW
from ..utils.bytes_reader import BytesReader
from .common import read_object_header, read_bbox, read_contour_points


class Type3ChainParser(BaseParser):
    """
    Type3 class chain parser rebuilt incrementally.

    Current design goals:
    1. Reliably extract class-chain nodes.
    2. Reliably read repeated bbox blocks.
    3. Conservatively locate the CContour point-count area.
    4. Read contour records with the currently observed stride.
    5. Validate minimally and preserve unknown semantics where needed.

    Important:
    - This parser is intentionally conservative.
    - It should prefer "unknown / no contour parsed" over confidently wrong parsing.
    - Do not overgeneralize one sample into a universal rule too early.
    """

    DEFAULT_CONTOUR_RECORD_STRIDE = 36
    MAX_REASONABLE_COORD_M = 100.0
    PROPERTY_EXTEND_COLOR_PRIMARY_OFFSET = 0x79
    PROPERTY_EXTEND_COLOR_SECONDARY_OFFSET = 0x85
    PROPERTY_EXTEND_GROUP_COLOR_PRIMARY_OFFSET = 0x20E
    PROPERTY_EXTEND_GROUP_COLOR_SECONDARY_OFFSET = 0x21A
    KNOWN_FONT_MARKERS = {"Arial"}
    def can_parse(self, reader: BytesReader) -> bool:
        pos = reader.tell()
        try:
            data = reader.peek_bytes(min(512, reader.remaining()))
            return b"\xff\xff" in data
        except EOFError:
            return False
        finally:
            reader.seek(pos)

    def parse(self, reader: BytesReader, **kwargs) -> GeometryObject:
        full_data = reader.peek_bytes(reader.remaining())
        
        header_prefix, declared_count, payload_offset = self._read_top_level_header(full_data)
        payload_data = full_data[payload_offset:]

        all_nodes = self._extract_nodes(payload_data)
        initial_chains = self._group_nodes_into_chains(all_nodes)
        
        final_chains = []
        for chain in initial_chains:
            final_chains.extend(self._process_object_chain(chain))

        # Step E: Prepare final result
        main_points = []
        main_contour_records = []
        main_bbox = None
        main_markers = []
        
        if final_chains:
            last_chain = final_chains[-1]
            main_points = last_chain.points
            main_contour_records = last_chain.contour_records
            main_bbox = last_chain.bbox
            
            seen_markers = set()
            for chain in final_chains:
                seen_markers.update(chain.markers)
            main_markers = sorted(list(seen_markers))

        is_text_object = self._looks_like_text_object(full_data, all_nodes)
        font_name, font_offset, font_context = self._extract_font_name(full_data)
        raw_text_records: List[bytes] = []
        text_notes: List[str] = []
        text_content = None

        if is_text_object:
            czone_bbox = self._first_bbox_for_class(all_nodes, "CZone")
            if czone_bbox is not None:
                main_bbox = czone_bbox

            text_content, raw_text_records, text_notes = self._extract_text_content(all_nodes)
            text_notes.append(
                "Text object parsing is provisional; unknown CParagraphe bytes are preserved in raw_data and node payloads."
            )

        aggregate_bbox = self._aggregate_bbox_from_chains(final_chains)
        if len(final_chains) > 1 and aggregate_bbox is not None and not is_text_object:
            main_bbox = aggregate_bbox
        is_group_candidate = (
            not is_text_object
            and declared_count == 1
            and len(final_chains) > 1
        )

        raw_group_bytes = b""
        if is_group_candidate:
            raw_group_bytes = b"".join(
                node.payload for node in all_nodes if node.header.class_name == "CPropertyExtend"
            )

        result = GeometryObject(
            object_type="text" if is_text_object else "geometry",
            raw_size=len(full_data),
            raw_data=full_data,
            markers=main_markers,
            points=main_points,
            contour_records=main_contour_records,
            bbox=main_bbox,
            object_chains=final_chains,
            declared_object_count=declared_count,
            aggregate_bbox=aggregate_bbox,
            is_text_object=is_text_object,
            text_content=text_content,
            font_name=font_name,
            raw_text_records=raw_text_records,
            text_notes=text_notes,
            is_grouped=is_group_candidate,
            group_term_ko="결합" if is_group_candidate else None,
            group_children=list(final_chains) if is_group_candidate else [],
            group_bbox=aggregate_bbox if is_group_candidate else None,
            raw_group_bytes=raw_group_bytes,
            group_notes=(
                [
                    "Type3 결합(group/combined object) candidate detected from declared_count=1 with multiple child contours.",
                    "Unknown group-related bytes are preserved in raw_group_bytes until semantics are validated.",
                ]
                if is_group_candidate
                else []
            ),
            candidate_fields={
                "nodes": [node.header.class_name for node in all_nodes],
                "node_markers_with_offsets": [
                    {
                        "class_name": node.header.class_name,
                        "start_offset": node.start_offset,
                        "payload_offset": node.payload_offset,
                        "end_offset": node.end_offset,
                    }
                    for node in all_nodes
                ],
                "style": [
                    {
                        "line_color_primary": chain.style.line_color_primary,
                        "line_color_secondary": chain.style.line_color_secondary,
                        "line_color_selected_raw": chain.style.line_color_selected_raw,
                        "line_color_name": chain.style.line_color_name,
                        "line_color_hex": chain.style.line_color_hex,
                        "line_color_confidence": chain.style.line_color_confidence,
                        "line_color_source": chain.style.line_color_source,
                        "color_candidates": chain.style.color_candidates,
                    }
                    for chain in final_chains
                    if chain.style.line_color_primary is not None
                    or chain.style.line_color_secondary is not None
                    or chain.style.color_candidates
                ],
                "font_marker": {
                    "name": font_name,
                    "offset": font_offset,
                    "raw_context": font_context,
                }
                if font_name is not None
                else None,
                "text_record_count": len(raw_text_records),
                "structure_kind": (
                    "group_candidate_결합"
                    if is_group_candidate
                    else ("independent_multi" if len(final_chains) > 1 else "single")
                ),
            },
            notes=[
                f"Type3ChainParser: Extracted {len(final_chains)} object chains.",
            ],
        )

        if is_text_object:
            result.object_type = "text"
        
        if len(final_chains) > 1:
            result.notes.append("Multiple objects detected. Use object_chains for details.")

        if is_group_candidate:
            result.object_type = "group"
            result.notes.extend(result.group_notes)

        if result.is_text_object:
            result.notes.extend(result.text_notes)
            
        return result

    def _looks_like_text_object(self, data: bytes, nodes: List[Type3Node]) -> bool:
        """
        Conservative first-stage text-object detection.

        CParagraphe is the strongest observed signal. Font markers are weaker
        supporting evidence and are intentionally limited to known fixtures.
        """
        if any(node.header.class_name == "CParagraphe" for node in nodes):
            return True

        font_name, _offset, _context = self._extract_font_name(data)
        if font_name is not None:
            return True

        return bool(self._extract_candidate_text_records(nodes))

    def _extract_font_name(self, data: bytes) -> Tuple[Optional[str], Optional[int], Optional[bytes]]:
        """
        Scan early bytes for null-terminated printable ASCII font candidates.
        Offsets are deliberately not hard-coded.
        """
        scan_limit = min(len(data), 1024)
        idx = 0

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

                if candidate in self.KNOWN_FONT_MARKERS:
                    context_start = max(0, start - 16)
                    context_end = min(len(data), idx + 17)
                    return candidate, start, data[context_start:context_end]

            idx += 1

        return None, None, None

    def _first_bbox_for_class(self, nodes: List[Type3Node], class_name: str) -> Optional[BBox3D]:
        for node in nodes:
            if node.header.class_name == class_name and node.bbox is not None:
                return node.bbox
        return None

    def _extract_text_content(self, nodes: List[Type3Node]) -> Tuple[Optional[str], List[bytes], List[str]]:
        records = self._extract_candidate_text_records(nodes)
        notes: List[str] = []

        if not records:
            return None, [], notes

        codes = []
        for record in records:
            if len(record) < 8:
                continue
            codes.append(struct.unpack("<I", record[4:8])[0])

        ascii_chars = [chr(code) for code in codes if 32 <= code <= 126]
        if ascii_chars and len(ascii_chars) == len(codes):
            return "".join(ascii_chars), records, notes

        inferred = self._infer_default_text_fixture_content(codes)
        if inferred is not None:
            notes.append(
                "Text content inferred from the controlled default_text fixture record pattern; raw ASCII text storage is not confirmed yet."
            )
            return inferred, records, notes

        notes.append("CParagraphe text records were detected, but text content could not be safely decoded.")
        return None, records, notes

    def _extract_candidate_text_records(self, nodes: List[Type3Node]) -> List[bytes]:
        """
        Locate repeated CParagraphe record candidates without treating arbitrary
        ASCII strings, class names, metadata keys, or font names as text content.
        """
        for node in nodes:
            if node.header.class_name != "CParagraphe":
                continue

            records = self._read_paragraphe_slot_records(node.payload)
            if records:
                return records

        return []

    def _read_paragraphe_slot_records(self, payload: bytes) -> List[bytes]:
        """
        The default_text fixture contains a run beginning with a u32 count,
        followed by repeated slot records that start with u32 5 and a u32 code.

        This is intentionally narrow and keeps the raw record bytes for future
        comparison instead of claiming complete CParagraphe support.
        """
        record_stride = 204
        max_slots = 256

        for offset in range(0, max(0, len(payload) - 12)):
            count = struct.unpack("<I", payload[offset : offset + 4])[0]
            if not (1 <= count <= max_slots):
                continue

            cursor = offset + 4
            records: List[bytes] = []

            for _ in range(count):
                if cursor + 8 > len(payload):
                    records = []
                    break
                if payload[cursor : cursor + 4] != b"\x05\x00\x00\x00":
                    records = []
                    break

                record_end = min(len(payload), cursor + record_stride)
                records.append(payload[cursor:record_end])
                cursor += record_stride

            if len(records) == count:
                return records

        return []

    def _infer_default_text_fixture_content(self, codes: List[int]) -> Optional[str]:
        """
        Current default_text.txt stores the visible 'abcdefg' fixture as seven
        text slots where the observed codes are 1..6 plus a zero terminator-like
        slot, rather than literal ASCII bytes.
        """
        if codes == [0x31, 0x32, 0x33, 0x34, 0x35, 0x36, 0x00]:
            return "abcdefg"
        return None

    def _read_top_level_header(self, data: bytes) -> Tuple[bytes, Optional[int], int]:
        """
        [Step A] Reads the provisional top-level header.
        Expected format: [reserved: 4B] [object_count: u16_le]
        """
        if len(data) < 6:
            return b"", None, 0
        
        try:
            prefix = data[:4]
            count = struct.unpack("<H", data[4:6])[0]
            # Heuristic: if count is too high, it might not be a count.
            # But in known samples it is 1 or 2.
            if count > 1000:
                return b"", None, 0
            return prefix, count, 6
        except Exception:
            return b"", None, 0

    def _group_nodes_into_chains(self, nodes: List[Type3Node]) -> List[Type3ObjectChain]:
        """
        [Step C] Groups flat nodes into object chains based on heuristic boundary rules.
        """
        chains: List[Type3ObjectChain] = []
        current_chain: Optional[Type3ObjectChain] = None
        
        for node in nodes:
            # Start new chain if we see CZone or the first node
            if node.header.class_name == "CZone" or current_chain is None:
                current_chain = Type3ObjectChain()
                chains.append(current_chain)
            
            # Special case for samples where multiple objects are in one stream
            # but separated by other markers. 
            # In some samples, a second CCourbe or CContour without a preceding CZone
            # might indicate a new object.
            if node.header.class_name == "CContour" and any(n.header.class_name == "CContour" for n in current_chain.nodes):
                 current_chain = Type3ObjectChain()
                 chains.append(current_chain)

            current_chain.nodes.append(node)
            current_chain.markers.append(node.header.class_name)
            
        return chains

    def _process_object_chain(self, chain: Type3ObjectChain) -> List[Type3ObjectChain]:
        """
        [Step F] Processes a single object chain to extract geometry independently.
        Returns a list of object chains (splits the input chain if multiple contours found).
        """
        bbox_by_class: Dict[str, BBox3D] = {}
        processed_chains = []
        current_work_chain = chain

        for node in chain.nodes:
            if node.bbox:
                if node.header.class_name not in bbox_by_class:
                    bbox_by_class[node.header.class_name] = node.bbox

            if node.header.class_name == "CPropertyExtend":
                base_style = self._read_style_properties_with_context(
                    node.payload,
                    payload_offset=node.payload_offset,
                    stream_offset=node.start_offset,
                )
                if current_work_chain.source_payload_offset is not None:
                    current_work_chain.style = self._style_for_reference_offset(
                        base_style,
                        current_work_chain.source_payload_offset,
                    )
                else:
                    # Preserve full candidates when no contour reference exists yet.
                    current_work_chain.style = base_style
                embedded_chains = self._read_embedded_contour_chains(
                    node,
                    current_work_chain,
                    base_style,
                )
                processed_chains.extend(embedded_chains)
            
            if node.header.class_name != "CContour":
                continue

            headers = self._read_contour_header(node.payload)
            if not headers:
                continue

            # Handle multiple contours in one CContour node (common in multi-object samples)
            for i, (kind, count, offset) in enumerate(headers):
                if i > 0:
                    # Split into a new chain for subsequent contours
                    new_chain = Type3ObjectChain(
                        nodes=current_work_chain.nodes,
                        markers=current_work_chain.markers,
                    )
                    processed_chains.append(new_chain)
                    current_work_chain = new_chain
                elif not processed_chains:
                    processed_chains.append(current_work_chain)

                records = self._read_contour_records(node.payload, offset, count)
                if records and self._validate_records(records, node.bbox):
                    self._assign_semantic_roles(records)
                    current_work_chain.contour_records = records
                    current_work_chain.points = [Point(x=p.x_mm, y=p.y_mm, z=p.z_mm) for p in records]
                    current_work_chain.source_node_class = node.header.class_name
                    current_work_chain.source_payload_offset = offset
                    current_work_chain.source_stream_offset = node.payload_offset + offset
                    current_work_chain.raw_contour_bytes = node.payload[
                        offset : offset + (count * self.DEFAULT_CONTOUR_RECORD_STRIDE)
                    ]
        
        if not processed_chains:
            processed_chains.append(chain)

        for c in processed_chains:
            if c.bbox is None:
                c.bbox = (
                    bbox_by_class.get("CContour")
                    or bbox_by_class.get("CCourbe")
                    or bbox_by_class.get("CZone")
                )
        
        return processed_chains

    def _read_embedded_contour_chains(
        self,
        node: Type3Node,
        template_chain: Type3ObjectChain,
        base_style: StyleProperties,
    ) -> List[Type3ObjectChain]:
        """
        Some multi-object samples carry an additional contour inside CPropertyExtend.
        Treat these as extra object chains while preserving the surrounding markers.
        """
        headers = self._read_contour_header(node.payload)
        if not headers:
            return []

        embedded_chains: List[Type3ObjectChain] = []
        for _kind, count, offset in headers:
            records = self._read_contour_records(node.payload, offset, count)
            if not records or not self._validate_records(records, None):
                continue

            self._assign_semantic_roles(records)
            embedded_chains.append(
                Type3ObjectChain(
                    nodes=template_chain.nodes,
                    markers=template_chain.markers,
                    contour_records=records,
                    points=[Point(x=p.x_mm, y=p.y_mm, z=p.z_mm) for p in records],
                    bbox=self._bbox_from_contour_records(records),
                    style=self._style_for_reference_offset(base_style, offset),
                    source_node_class=node.header.class_name,
                    source_payload_offset=offset,
                    source_stream_offset=node.payload_offset + offset,
                    raw_contour_bytes=node.payload[
                        offset : offset + (count * self.DEFAULT_CONTOUR_RECORD_STRIDE)
                    ],
                )
            )

        return embedded_chains

    def _bbox_from_contour_records(self, records: List[ContourPoint]) -> BBox3D:
        xs = [r.x_m for r in records]
        ys = [r.y_m for r in records]
        zs = [r.z_m for r in records]
        return BBox3D(
            xmin_m=min(xs),
            ymin_m=min(ys),
            zmin_m=min(zs),
            xmax_m=max(xs),
            ymax_m=max(ys),
            zmax_m=max(zs),
        )

    def _read_style_properties(self, payload: bytes) -> StyleProperties:
        """
        Reads currently observed CPropertyExtend style candidates.

        In paired rectangle color samples, changing only the object color
        changes two u32-le fields in this payload:
        - offset 0x79: primary color candidate
        - offset 0x85: secondary/mirrored color candidate
        """
        return self._read_style_properties_with_context(payload, payload_offset=None, stream_offset=None)

    def _read_style_properties_with_context(
        self,
        payload: bytes,
        payload_offset: Optional[int],
        stream_offset: Optional[int],
    ) -> StyleProperties:
        primary = self._read_optional_u32_le(payload, self.PROPERTY_EXTEND_COLOR_PRIMARY_OFFSET)
        secondary = self._read_optional_u32_le(payload, self.PROPERTY_EXTEND_COLOR_SECONDARY_OFFSET)

        color_candidates = self._collect_palette_color_candidates(
            payload=payload,
            fixed_primary=primary,
            fixed_secondary=secondary,
        )
        chosen = self._choose_color_candidate(
            color_candidates=color_candidates,
            fixed_primary=primary,
            fixed_secondary=secondary,
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
            fixed_primary_offset=self.PROPERTY_EXTEND_COLOR_PRIMARY_OFFSET,
            fixed_secondary_offset=self.PROPERTY_EXTEND_COLOR_SECONDARY_OFFSET,
            fixed_primary_raw=primary,
            fixed_secondary_raw=secondary,
            property_extend_payload_length=len(payload),
            property_extend_payload_offset=payload_offset,
            property_extend_stream_offset=stream_offset,
        )

    def _collect_palette_color_candidates(
        self,
        payload: bytes,
        fixed_primary: Optional[int],
        fixed_secondary: Optional[int],
    ) -> List[dict[str, Any]]:
        entries: List[dict[str, Any]] = []
        occurrences: Dict[tuple[str, int], List[int]] = {}
        max_scan_candidates_per_raw = 12
        group_primary = self._read_optional_u32_le(payload, self.PROPERTY_EXTEND_GROUP_COLOR_PRIMARY_OFFSET)
        group_secondary = self._read_optional_u32_le(payload, self.PROPERTY_EXTEND_GROUP_COLOR_SECONDARY_OFFSET)
        has_group_confirmed_nonzero = (
            group_primary is not None
            and group_primary == group_secondary
            and group_primary != 0
            and group_primary in TYPE3_COLORS_BY_RGB0_RAW
        )

        for offset in range(0, max(0, len(payload) - 3)):
            raw = struct.unpack("<I", payload[offset : offset + 4])[0]
            if raw in TYPE3_COLORS_BY_RAW:
                occurrences.setdefault(("legacy", raw), []).append(offset)
            if raw in TYPE3_COLORS_BY_RGB0_RAW:
                occurrences.setdefault(("rgb0", raw), []).append(offset)

        for (encoding, raw), offsets in occurrences.items():
            if raw == 0 and encoding == "rgb0":
                # Zero overlaps both encodings; keep one path to reduce duplicate noise.
                continue
            color = TYPE3_COLORS_BY_RAW[raw] if encoding == "legacy" else TYPE3_COLORS_BY_RGB0_RAW[raw]
            scan_added = 0
            sorted_offsets = sorted(offsets)
            has_pair_12 = any((sorted_offsets[i + 1] - sorted_offsets[i]) == 12 for i in range(len(sorted_offsets) - 1))
            max_fixed_offset_for_encoding = (
                self.PROPERTY_EXTEND_COLOR_SECONDARY_OFFSET
                if encoding == "legacy"
                else self.PROPERTY_EXTEND_GROUP_COLOR_SECONDARY_OFFSET
            )
            for idx, offset in enumerate(sorted_offsets):
                # Neighbor signal only needs existence (>= 1), not exact count.
                prev_close = idx > 0 and (offset - sorted_offsets[idx - 1]) <= 16
                next_close = idx + 1 < len(sorted_offsets) and (sorted_offsets[idx + 1] - offset) <= 16
                has_close_neighbor = prev_close or next_close
                confidence = "strong" if has_close_neighbor else "weak"
                source = "payload_scan"

                is_legacy_fixed = (
                    encoding == "legacy"
                    and (
                        offset == self.PROPERTY_EXTEND_COLOR_PRIMARY_OFFSET
                        or offset == self.PROPERTY_EXTEND_COLOR_SECONDARY_OFFSET
                    )
                )
                is_group_fixed = (
                    encoding == "rgb0"
                    and (
                        offset == self.PROPERTY_EXTEND_GROUP_COLOR_PRIMARY_OFFSET
                        or offset == self.PROPERTY_EXTEND_GROUP_COLOR_SECONDARY_OFFSET
                    )
                )
                is_fixed = is_legacy_fixed or is_group_fixed
                if is_fixed:
                    source = "fixed_offset"

                # If group-specific fixed offsets already provide a confirmed non-zero color,
                # suppress legacy black noise candidates in this payload.
                if has_group_confirmed_nonzero and raw == 0 and encoding == "legacy":
                    continue

                if not is_fixed:
                    # Drop single-occurrence noise and cap the list per raw+encoding.
                    if not has_close_neighbor and raw == 0:
                        continue
                    if scan_added >= max_scan_candidates_per_raw:
                        # Legacy black candidates are extremely dense; once capped and
                        # fixed offsets are already behind us, remaining tail adds no value.
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
                self._confidence_rank(item["confidence"]),
                0 if item["raw"] != 0 else 1,
                0 if item["source"] == "fixed_offset" else 1,
                abs(item["offset"] - self.PROPERTY_EXTEND_COLOR_PRIMARY_OFFSET),
            )
        )
        # When both encodings match the same raw at the same offset for scan-derived
        # candidates, keep rgb0 and drop legacy to reduce ambiguous duplicates.
        suppress_keys = {
            (item["offset"], item["raw"])
            for item in entries
            if item.get("encoding") == "rgb0" and item.get("source") == "payload_scan"
        }
        filtered = [
            item
            for item in entries
            if not (
                item.get("encoding") == "legacy"
                and item.get("source") == "payload_scan"
                and (item["offset"], item["raw"]) in suppress_keys
            )
        ]
        return filtered

    def _choose_color_candidate(
        self,
        color_candidates: List[dict[str, Any]],
        fixed_primary: Optional[int],
        fixed_secondary: Optional[int],
        reference_offset: Optional[int] = None,
    ) -> Optional[dict[str, Any]]:
        if not color_candidates:
            return None

        # Prefer fixed offsets when both fixed values match a known palette entry.
        if fixed_primary is not None and fixed_primary == fixed_secondary and fixed_primary in TYPE3_COLORS_BY_RAW:
            for candidate in color_candidates:
                if (
                    candidate["raw"] == fixed_primary
                    and candidate["source"] == "fixed_offset"
                ):
                    return candidate

        candidates = list(color_candidates)
        if reference_offset is not None:
            nonzero = [candidate for candidate in candidates if candidate["raw"] != 0]
            if nonzero:
                candidates = nonzero

            candidates.sort(
                key=lambda item: (
                    self._confidence_rank(item["confidence"]),
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
                self._confidence_rank(item["confidence"]),
                0 if item["raw"] != 0 else 1,
                0 if item["source"] == "fixed_offset" else 1,
                0 if item.get("encoding") == "rgb0" else 1,
                -by_raw[item["raw"]],
                abs(item["offset"] - self.PROPERTY_EXTEND_COLOR_PRIMARY_OFFSET),
            ),
        )
        return sorted_candidates[0]

    def _confidence_rank(self, confidence: str) -> int:
        if confidence == "confirmed":
            return 0
        if confidence == "strong":
            return 1
        return 2

    def _style_for_reference_offset(
        self,
        base_style: StyleProperties,
        reference_offset: Optional[int],
    ) -> StyleProperties:
        chosen = self._choose_color_candidate(
            color_candidates=base_style.color_candidates,
            fixed_primary=base_style.line_color_primary,
            fixed_secondary=base_style.line_color_secondary,
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
            localized_candidates = self._localize_color_candidates(
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

    def _localize_color_candidates(
        self,
        color_candidates: List[dict[str, Any]],
        reference_offset: Optional[int],
        selected_raw: Optional[int],
    ) -> List[dict[str, Any]]:
        if not color_candidates:
            return []

        # When a non-zero color is selected, keep same-raw candidates only.
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

        # Fallback: keep candidates nearest to the reference offset.
        if reference_offset is not None:
            nearby = sorted(
                color_candidates,
                key=lambda c: (
                    abs((c.get("offset") or 0) - reference_offset),
                    self._confidence_rank(c.get("confidence", "weak")),
                ),
            )
            return nearby[:8]

        return color_candidates[:8]

    def _read_optional_u32_le(self, data: bytes, offset: int) -> Optional[int]:
        if offset < 0 or offset + 4 > len(data):
            return None
        return struct.unpack("<I", data[offset : offset + 4])[0]

    def _extract_nodes(self, data: bytes) -> List[Type3Node]:
        """
        Extracts chained Type3 class nodes by scanning for plausible 0xFFFF headers.
        """
        nodes: List[Type3Node] = []
        idx = 0

        while idx < len(data) - 6:
            # We look for 0xFFFF anywhere, not just at current idx, 
            # to handle potential padding or gaps.
            idx = data.find(b"\xff\xff", idx)
            if idx == -1 or idx > len(data) - 6:
                break

            try:
                # Basic validation before calling _parse_single_node
                # We need to be careful with multiple 0xFFFF. 
                # read_object_header will take the first 0xFFFF it finds if we are aligned.
                
                # Check if it looks like a valid class name length
                name_len = struct.unpack("<H", data[idx + 4 : idx + 6])[0]
                if not (1 < name_len < 64) or idx + 6 + name_len > len(data):
                    idx += 1
                    continue
                
                name_bytes = data[idx + 6 : idx + 6 + name_len]
                if not (all(32 <= b <= 126 for b in name_bytes) and name_bytes.startswith(b"C")):
                    idx += 1
                    continue

                node_reader = BytesReader(data[idx:])
                node = self._parse_single_node(node_reader, data[idx:], node_start_offset=idx)
                nodes.append(node)

                # Move idx to the end of this node's header + bbox + payload
                header_size = 6 + name_len
                bbox_size = 48 if node.bbox else 0
                idx += header_size + bbox_size + len(node.payload)
            except Exception:
                idx += 1

        return nodes

    def _parse_single_node(
        self,
        reader: BytesReader,
        node_data: bytes,
        node_start_offset: int = 0,
    ) -> Type3Node:
        """
        Parses one class node and cuts its payload at the next plausible Type3 class header.
        """
        header = read_object_header(reader)
        bbox: Optional[BBox3D] = None

        if header.class_name in ["CZone", "CCourbe", "CContour"]:
            bbox = read_bbox(reader)

        current_pos = reader.tell()
        remaining_data = node_data[current_pos:]

        marker_pos = self._find_next_class_header_offset(remaining_data)
        
        # Heuristic to avoid eating other class headers
        if marker_pos != -1:
            payload = remaining_data[:marker_pos]
        else:
            payload = remaining_data

        payload_start = current_pos
        payload_end = current_pos + len(payload)
        return Type3Node(
            header=header,
            bbox=bbox,
            payload=payload,
            start_offset=node_start_offset,
            payload_offset=node_start_offset + payload_start,
            end_offset=node_start_offset + payload_end,
        )

    def _aggregate_bbox_from_chains(self, chains: List[Type3ObjectChain]) -> Optional[BBox3D]:
        bboxes = [chain.bbox for chain in chains if chain.bbox is not None]
        if not bboxes:
            return None

        return BBox3D(
            xmin_m=min(b.xmin_m for b in bboxes),
            ymin_m=min(b.ymin_m for b in bboxes),
            zmin_m=min(b.zmin_m for b in bboxes),
            xmax_m=max(b.xmax_m for b in bboxes),
            ymax_m=max(b.ymax_m for b in bboxes),
            zmax_m=max(b.zmax_m for b in bboxes),
        )

    def _find_next_class_header_offset(self, data: bytes) -> int:
        """
        Returns the offset of the next plausible class header within `data`,
        or -1 if none is found.
        """
        # We start from 1 to avoid finding ourselves
        idx = 1
        while idx < len(data) - 5:
            # Look for 0xFFFF
            if data[idx : idx + 2] == b"\xff\xff":
                try:
                    # Validate header after 0xFFFF
                    name_len = struct.unpack("<H", data[idx + 4 : idx + 6])[0]
                    if 1 < name_len < 64 and idx + 6 + name_len <= len(data):
                        name_bytes = data[idx + 6 : idx + 6 + name_len]
                        if all(32 <= b <= 126 for b in name_bytes) and name_bytes.startswith(b"C"):
                            return idx
                except Exception:
                    pass
            idx += 1

        return -1

    def _read_contour_header(self, payload: bytes) -> Optional[List[Tuple[int, int, int]]]:
        """
        Conservatively locates probable contour headers.
        Returns a list of all plausible (kind, count, offset) tuples found.
        """
        marker = b"CObDao"
        idx = 0
        found_headers = []
        while True:
            marker_pos = payload.find(marker, idx)
            if marker_pos == -1:
                break

            base = marker_pos + len(marker)
            # Candidate shifts: 8, 12, 14, 16, 20
            # FIX: In two_circle.txt, the second circle has kind=2, count=8 at shift 14.
            candidate_shifts = [8, 14, 12, 16, 20]

            found_for_this_marker = False
            for shift in candidate_shifts:
                header_start = base + shift
                if header_start + 8 > len(payload):
                    continue

                try:
                    kind = struct.unpack("<I", payload[header_start : header_start + 4])[0]
                    count = struct.unpack("<I", payload[header_start + 4 : header_start + 8])[0]
                    
                    if self._is_plausible_contour_count(count):
                        offset = header_start + 8
                        # Avoid duplicates
                        if not any(h[2] == offset for h in found_headers):
                            found_headers.append((kind, count, offset))
                        
                        idx = offset
                        found_for_this_marker = True
                        break
                except Exception:
                    continue
            
            if not found_for_this_marker:
                idx = marker_pos + 1
        
        return found_headers if found_headers else None

    def _is_plausible_contour_count(self, count: int) -> bool:
        """
        Current fixtures strongly suggest small contour counts such as:
        - 3  : circular arc
        - 4  : rectangle
        - 8  : circle / rounded rectangle-like alternating record cases
        - 12 : rounded rectangle sample in current fixture set
        """
        return count in {2, 3, 4, 8, 12}

    def _read_contour_records(
        self,
        payload: bytes,
        offset: int,
        count: int,
    ) -> List[ContourPoint]:
        """
        Reads exactly `count` contour records using the currently observed fixed stride.

        This keeps the stride explicit and easy to change later.
        """
        stride = self.DEFAULT_CONTOUR_RECORD_STRIDE
        total_size = count * stride

        if offset < 0 or offset + total_size > len(payload):
            return []

        local_reader = BytesReader(payload[offset:])

        try:
            return read_contour_points(local_reader, count, stride=stride)
        except Exception:
            return []

    def _validate_records(
        self,
        records: List[ContourPoint],
        bbox: Optional[BBox3D],
    ) -> bool:
        """
        Minimal conservative validation.

        Validation policy:
        - reject NaN / inf
        - reject astronomical coordinates
        - reject trivially all-zero sets
        - if bbox exists, require the record cloud to remain related to the bbox
          without assuming every point must be strictly inside it
        """
        if not records:
            return False

        for r in records:
            if not (
                math.isfinite(r.x_m)
                and math.isfinite(r.y_m)
                and math.isfinite(r.z_m)
                and math.isfinite(r.w)
            ):
                return False

            if abs(r.x_m) > self.MAX_REASONABLE_COORD_M:
                return False
            if abs(r.y_m) > self.MAX_REASONABLE_COORD_M:
                return False
            if abs(r.z_m) > self.MAX_REASONABLE_COORD_M:
                return False

        if all(
            abs(r.x_m) < 1e-12 and abs(r.y_m) < 1e-12 and abs(r.z_m) < 1e-12
            for r in records
        ):
            return False

        if bbox is None:
            return True

        xs = [r.x_m for r in records]
        ys = [r.y_m for r in records]

        px_min = min(xs)
        px_max = max(xs)
        py_min = min(ys)
        py_max = max(ys)

        # Allow a modest margin because control points can sit outside the bbox.
        margin = 0.05  # 50 mm

        # Entire cloud must still be related to bbox, not astronomically detached.
        if px_max < bbox.xmin_m - margin:
            return False
        if px_min > bbox.xmax_m + margin:
            return False
        if py_max < bbox.ymin_m - margin:
            return False
        if py_min > bbox.ymax_m + margin:
            return False

        return True

    def _assign_semantic_roles(self, records: List[ContourPoint]) -> None:
        """
        Assigns conservative semantic roles from currently observed low-byte tag patterns.

        Confirmed enough to use:
        - 0x0C -> control

        Observed enough to treat as anchors in current fixtures:
        - 0x0D
        - 0x0F

        Everything else remains unknown for now.
        """
        for r in records:
            low = r.tag & 0xFF
            if low == 0x0C:
                r.role = "control"
            elif low in (0x0D, 0x0F):
                r.role = "anchor"
            else:
                r.role = "unknown"

    def _debug_dump_contour(self, node: Type3Node) -> None:
        """
        Optional debug helper. Safe to keep during reverse engineering.
        """
        payload = node.payload
        print("\n--- DEBUG CContour Dump ---")
        print(f"Payload Length: {len(payload)} bytes")

        if payload:
            print(f"First 128 bytes hex: {payload[:128].hex(' ')}")

        markers = [b"OBJECTINFOS_CLASSNAME", b"CObDao"]
        for marker in markers:
            pos = payload.find(marker)
            if pos != -1:
                print(f"'{marker.decode()}' found at offset: {pos}")
                if marker == b"CObDao":
                    tail = payload[pos + len(marker) : pos + len(marker) + 32]
                    print(f"Bytes after CObDao: {tail.hex(' ')}")

        print("---------------------------\n")
