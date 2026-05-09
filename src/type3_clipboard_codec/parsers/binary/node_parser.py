from typing import Optional

from ...models.geometry import BBox3D, Type3Node
from ...utils.bytes_reader import BytesReader
from ..common import read_bbox, read_object_header
from .header_parser import find_next_class_header_offset


_BBOX_CLASS_NAMES = {"CZone", "CCourbe", "CContour"}


def parse_single_node(
    reader: BytesReader,
    node_data: bytes,
    node_start_offset: int = 0,
) -> Type3Node:
    """
    Parses one class node and cuts its payload at the next plausible Type3 class header.
    """
    header = read_object_header(reader)
    bbox: Optional[BBox3D] = None

    if header.class_name in _BBOX_CLASS_NAMES:
        bbox = read_bbox(reader)

    current_pos = reader.tell()
    remaining_data = node_data[current_pos:]
    marker_pos = find_next_class_header_offset(remaining_data, start_idx=1)
    payload = remaining_data[:marker_pos] if marker_pos != -1 else remaining_data

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
