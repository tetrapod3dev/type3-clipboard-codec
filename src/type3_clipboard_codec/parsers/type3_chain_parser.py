from typing import List, Optional, Dict, Tuple
import math
import struct

from .base import BaseParser
from ..models.geometry import (
    GeometryObject,
    BBox3D,
    Type3Node,
    ContourPoint,
    Point,
    Type3ObjectChain,
)
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

        result = GeometryObject(
            object_type="geometry",
            raw_size=len(full_data),
            raw_data=full_data,
            markers=main_markers,
            points=main_points,
            contour_records=main_contour_records,
            bbox=main_bbox,
            object_chains=final_chains,
            declared_object_count=declared_count,
            notes=[
                f"Type3ChainParser: Extracted {len(final_chains)} object chains.",
            ],
        )
        
        if len(final_chains) > 1:
            result.notes.append("Multiple objects detected. Use object_chains for details.")
            
        return result

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
        
        if not processed_chains:
            processed_chains.append(chain)

        for c in processed_chains:
            c.bbox = (
                bbox_by_class.get("CContour")
                or bbox_by_class.get("CCourbe")
                or bbox_by_class.get("CZone")
            )
        
        return processed_chains

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
                node = self._parse_single_node(node_reader, data[idx:])
                nodes.append(node)

                # Move idx to the end of this node's header + bbox + payload
                header_size = 6 + name_len
                bbox_size = 48 if node.bbox else 0
                idx += header_size + bbox_size + len(node.payload)
            except Exception:
                idx += 1

        return nodes

    def _parse_single_node(self, reader: BytesReader, node_data: bytes) -> Type3Node:
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

        return Type3Node(header=header, bbox=bbox, payload=payload)

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