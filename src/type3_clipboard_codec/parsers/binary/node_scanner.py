from typing import List

from ...models.geometry import Type3Node
from ...utils.bytes_reader import BytesReader
from .header_parser import is_plausible_class_header_at
from .node_parser import parse_single_node


def extract_nodes(data: bytes) -> List[Type3Node]:
    """
    Extracts chained Type3 class nodes by scanning for plausible 0xFFFF headers.
    """
    nodes: List[Type3Node] = []
    idx = 0

    while idx < len(data) - 6:
        idx = data.find(b"\xff\xff", idx)
        if idx == -1 or idx > len(data) - 6:
            break

        try:
            if not is_plausible_class_header_at(data, idx):
                idx += 1
                continue

            node = parse_single_node(BytesReader(data[idx:]), data[idx:], node_start_offset=idx)
            nodes.append(node)

            header_size = 6 + len(node.header.class_name.encode("ascii"))
            bbox_size = 48 if node.bbox else 0
            idx += header_size + bbox_size + len(node.payload)
        except Exception:
            idx += 1

    return nodes
