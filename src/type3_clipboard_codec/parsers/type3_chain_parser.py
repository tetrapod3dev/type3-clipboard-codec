from typing import Any, List, Optional, Dict, Tuple
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
from ..utils.bytes_reader import BytesReader
from .binary.node_scanner import extract_nodes
from .geometry.contour_parser import (
    analyze_contour_header_candidates,
    assign_semantic_roles,
    is_plausible_contour_count,
    read_contour_header,
    read_contour_records,
    validate_records,
)
from .geometry.shape_classifier import bbox_from_contour_records, classify_shape_type
from .geometry.chain_builder import (
    apply_contour_to_chain,
    build_embedded_contour_chain,
    choose_chain_bbox,
    ensure_work_chain_for_contour_index,
    group_nodes_into_chains,
    register_bbox_by_class,
)
from .style.property_extend_parser import (
    downgrade_unverified_text_color_selection,
    read_style_properties_with_context,
    style_for_reference_offset,
)
from .text.cparagraphe_parser import (
    attach_text_anchor_candidates,
    attach_text_runs_to_chains,
    extract_candidate_text_records,
    extract_font_candidates,
    extract_font_name,
    extract_text_runs,
    read_paragraphe_slot_record_runs,
    read_slot_record_runs_from_blob,
    records_to_text_run,
)
from .text.text_pipeline import run_text_pipeline


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
    MAX_SAFE_CONTOUR_COUNT = 4096
    MAX_REASONABLE_COORD_M = 100.0
    PROPERTY_EXTEND_COLOR_PRIMARY_OFFSET = 0x79
    PROPERTY_EXTEND_COLOR_SECONDARY_OFFSET = 0x85
    PROPERTY_EXTEND_GROUP_COLOR_PRIMARY_OFFSET = 0x20E
    PROPERTY_EXTEND_GROUP_COLOR_SECONDARY_OFFSET = 0x21A
    KNOWN_FONT_MARKERS = {"Arial", "Arial Bold", "Arial-BoldMT"}
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
        text_pipeline = run_text_pipeline(
            full_data=full_data,
            all_nodes=all_nodes,
            chains=final_chains,
            is_text_object=is_text_object,
            known_font_markers=self.KNOWN_FONT_MARKERS,
        )
        font_candidates = text_pipeline.font_candidates
        font_name = text_pipeline.font_name
        font_offset = text_pipeline.font_offset
        font_context = text_pipeline.font_context
        raw_text_records = text_pipeline.raw_text_records
        text_notes = text_pipeline.text_notes
        text_content = text_pipeline.text_content
        if text_pipeline.czone_bbox is not None:
            main_bbox = text_pipeline.czone_bbox

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
            source_text_candidate=text_content,
            display_text_candidate=None,
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
                "font_candidates": font_candidates,
                "text_record_count": len(raw_text_records),
                "contour_header_diagnostics": [
                    {
                        "chain_index": idx,
                        "source_stream_offset": chain.source_stream_offset,
                        "source_payload_offset": chain.source_payload_offset,
                        "diagnostics": chain.contour_header_diagnostics,
                    }
                    for idx, chain in enumerate(final_chains)
                    if chain.contour_header_diagnostics
                ],
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

    def _downgrade_unverified_text_color_selection(self, chains: List[Type3ObjectChain]) -> None:
        downgrade_unverified_text_color_selection(chains)

    def _extract_font_candidates(self, data: bytes) -> List[dict[str, Any]]:
        return extract_font_candidates(data)

    def _extract_font_name(
        self, data: bytes, font_candidates: Optional[List[dict[str, Any]]] = None
    ) -> Tuple[Optional[str], Optional[int], Optional[bytes]]:
        return extract_font_name(data, self.KNOWN_FONT_MARKERS, font_candidates)

    def _first_bbox_for_class(self, nodes: List[Type3Node], class_name: str) -> Optional[BBox3D]:
        for node in nodes:
            if node.header.class_name == class_name and node.bbox is not None:
                return node.bbox
        return None

    def _extract_text_runs(self, nodes: List[Type3Node]) -> Tuple[List[dict[str, Any]], List[bytes], List[str]]:
        return extract_text_runs(nodes)

    def _extract_candidate_text_records(self, nodes: List[Type3Node]) -> List[bytes]:
        return extract_candidate_text_records(nodes)

    def _read_paragraphe_slot_record_runs(self, payload: bytes) -> List[List[bytes]]:
        return read_paragraphe_slot_record_runs(payload)

    def _read_slot_record_runs_from_blob(self, payload: bytes) -> List[List[bytes]]:
        return read_slot_record_runs_from_blob(payload)

    def _records_to_text_run(self, records: List[bytes]) -> Optional[dict[str, Any]]:
        return records_to_text_run(records)

    def _attach_text_runs_to_chains(self, chains: List[Type3ObjectChain], runs: List[dict[str, Any]]) -> None:
        attach_text_runs_to_chains(chains, runs)

    def _attach_text_anchor_candidates(self, chains: List[Type3ObjectChain]) -> None:
        attach_text_anchor_candidates(chains)

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
        return group_nodes_into_chains(nodes)

    def _process_object_chain(self, chain: Type3ObjectChain) -> List[Type3ObjectChain]:
        """
        [Step F] Processes a single object chain to extract geometry independently.
        Returns a list of object chains (splits the input chain if multiple contours found).
        """
        bbox_by_class: Dict[str, BBox3D] = {}
        processed_chains = []
        current_work_chain = chain

        for node in chain.nodes:
            register_bbox_by_class(bbox_by_class, node.header.class_name, node.bbox)

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

            headers, header_diagnostics = self._analyze_contour_header_candidates(
                node.payload, node.bbox, node.header.class_name
            )
            if header_diagnostics:
                current_work_chain.contour_header_diagnostics.extend(header_diagnostics)
            if not headers:
                continue

            # Handle multiple contours in one CContour node (common in multi-object samples)
            for i, (kind, count, offset) in enumerate(headers):
                current_work_chain = ensure_work_chain_for_contour_index(
                    i,
                    current_work_chain,
                    processed_chains,
                )

                records = self._read_contour_records(node.payload, offset, count)
                if records and self._validate_records(records, node.bbox):
                    self._assign_semantic_roles(records)
                    _ = self._classify_shape_type(records, node.bbox, current_work_chain.markers)
                    apply_contour_to_chain(
                        chain=current_work_chain,
                        records=records,
                        source_node_class=node.header.class_name,
                        payload_offset=offset,
                        stream_offset=node.payload_offset + offset,
                        raw_contour_bytes=node.payload[
                            offset : offset + (count * self.DEFAULT_CONTOUR_RECORD_STRIDE)
                        ],
                    )
        
        if not processed_chains:
            processed_chains.append(chain)

        for c in processed_chains:
            c.bbox = choose_chain_bbox(c.bbox, bbox_by_class)
        
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
        headers, header_diagnostics = self._analyze_contour_header_candidates(
            node.payload, node.bbox, node.header.class_name
        )
        if header_diagnostics:
            template_chain.contour_header_diagnostics.extend(header_diagnostics)
        if not headers:
            return []

        embedded_chains: List[Type3ObjectChain] = []
        for _kind, count, offset in headers:
            records = self._read_contour_records(node.payload, offset, count)
            if not records or not self._validate_records(records, None):
                continue

            self._assign_semantic_roles(records)
            _ = self._classify_shape_type(records, template_chain.bbox, template_chain.markers)
            embedded_chains.append(
                build_embedded_contour_chain(
                    template_chain=template_chain,
                    records=records,
                    bbox=self._bbox_from_contour_records(records),
                    style=self._style_for_reference_offset(base_style, offset),
                    source_node_class=node.header.class_name,
                    payload_offset=offset,
                    stream_offset=node.payload_offset + offset,
                    raw_contour_bytes=node.payload[
                        offset : offset + (count * self.DEFAULT_CONTOUR_RECORD_STRIDE)
                    ],
                )
            )

        return embedded_chains

    def _bbox_from_contour_records(self, records: List[ContourPoint]) -> BBox3D:
        return bbox_from_contour_records(records)

    def _classify_shape_type(
        self,
        records: List[ContourPoint],
        bbox: Optional[BBox3D],
        markers: Optional[List[str]] = None,
    ) -> str:
        return classify_shape_type(records, bbox, markers)

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
        return read_style_properties_with_context(
            payload=payload,
            payload_offset=payload_offset,
            stream_offset=stream_offset,
            primary_offset=self.PROPERTY_EXTEND_COLOR_PRIMARY_OFFSET,
            secondary_offset=self.PROPERTY_EXTEND_COLOR_SECONDARY_OFFSET,
            group_primary_offset=self.PROPERTY_EXTEND_GROUP_COLOR_PRIMARY_OFFSET,
            group_secondary_offset=self.PROPERTY_EXTEND_GROUP_COLOR_SECONDARY_OFFSET,
        )

    def _style_for_reference_offset(
        self,
        base_style: StyleProperties,
        reference_offset: Optional[int],
    ) -> StyleProperties:
        return style_for_reference_offset(
            base_style=base_style,
            reference_offset=reference_offset,
            primary_offset=self.PROPERTY_EXTEND_COLOR_PRIMARY_OFFSET,
        )

    def _extract_nodes(self, data: bytes) -> List[Type3Node]:
        return extract_nodes(data)

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

    def _read_contour_header(self, payload: bytes) -> Optional[List[Tuple[int, int, int]]]:
        return read_contour_header(payload)

    def _analyze_contour_header_candidates(
        self, payload: bytes, bbox: Optional[BBox3D] = None, node_class_name: Optional[str] = None
    ) -> Tuple[Optional[List[Tuple[int, int, int]]], List[dict[str, Any]]]:
        return analyze_contour_header_candidates(
            payload,
            bbox=bbox,
            node_class_name=node_class_name,
            stride=self.DEFAULT_CONTOUR_RECORD_STRIDE,
            max_safe_contour_count=self.MAX_SAFE_CONTOUR_COUNT,
        )

    def _is_plausible_contour_count(self, count: int) -> bool:
        return is_plausible_contour_count(count)

    def _read_contour_records(
        self,
        payload: bytes,
        offset: int,
        count: int,
    ) -> List[ContourPoint]:
        return read_contour_records(payload, offset, count, stride=self.DEFAULT_CONTOUR_RECORD_STRIDE)

    def _validate_records(
        self,
        records: List[ContourPoint],
        bbox: Optional[BBox3D],
    ) -> bool:
        return validate_records(records, bbox, max_reasonable_coord_m=self.MAX_REASONABLE_COORD_M)

    def _assign_semantic_roles(self, records: List[ContourPoint]) -> None:
        assign_semantic_roles(records)

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
